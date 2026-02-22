# Caching Optimization Plan

## Current State: API Calls Per Session

For a session with **N assistant messages** and all 4 scanners enabled:

| Scanner | API | Calls | Cacheable Prefix? |
|---------|-----|-------|--------------------|
| AlignmentCheck | Together (LlamaFirewall) | N | Yes — cumulative trace grows incrementally |
| PromptGuard | None (local heuristics) | 0 | N/A |
| FactsChecker — self-contradiction | OpenAI (gpt-4o-mini) | 1 | Partial — full conversation history |
| FactsChecker — RAG ungroundedness | OpenAI (gpt-4o-mini) | N | Yes — shared system prompt + purpose |
| DataDisclosureGuard — PII | None (local Presidio) | 0 | N/A |
| DataDisclosureGuard — alignment | Together | 0–1 | No (single call) |
| **Total** | | **2N + 1 (+ 0–1)** | |

**Example:** 5 assistant messages → 11–12 API calls per run.

---

## Optimization 1: Provider-Side Prefix Caching (Free, Zero Code Change)

### How It Works
Together and OpenAI automatically cache KV tensors for identical prompt prefixes. When consecutive requests share the same beginning, the provider skips recomputing those tokens.

### AlignmentCheck (Together API)
Each `scan_replay()` builds a cumulative trace:
```
Call 1: [System] [U1] [A1]
Call 2: [System] [U1] [A1] [U2] [A2]
Call 3: [System] [U1] [A1] [U2] [A2] [U3] [A3]
```
The prefix of call 2 is identical to call 1. Call 3's prefix is identical to call 2. Together can reuse cached KV computation for the shared prefix.

**Requirement: Sequential execution.** Parallel requests (current `max_workers=3`) scatter across different GPU servers, destroying cache locality. To maximize prefix cache hits, AlignmentCheck calls must be sequential.

**Trade-off:**
- Sequential: ~30s per call × N messages (but cheaper per call)
- Parallel (current): ~30s total for 3 calls (but no cache reuse)
- **Recommendation:** Make this configurable. Default to sequential for cost optimization; allow parallel for latency optimization.

### FactsChecker RAG Ungroundedness (OpenAI API)
Each per-message call shares the same system prompt + purpose + date. OpenAI auto-caches prefixes ≥1024 tokens. If the shared prefix is long enough, cache kicks in automatically.

**Current:** These calls already run sequentially within `_check_rag_ungroundedness()`.

### Action Items
- [ ] Add a config flag: `ALIGNMENT_PREFER_CACHE = True` (default)
- [ ] When `True`, run AlignmentCheck sequentially (bypass `ThreadPoolExecutor`)
- [ ] When `False`, use current parallel execution for minimum latency
- [ ] No code changes needed for FactsChecker (already sequential)

### Estimated Savings
- AlignmentCheck: 30–50% reduction in input token cost (provider-dependent)
- FactsChecker: 10–20% reduction (shorter shared prefix)
- Latency: Increases ~2–3x for AlignmentCheck when sequential

---

## Optimization 2: Application-Level Result Cache

### Problem
Re-running scanners on the same session produces identical results. In the UI, users often click "Run" multiple times or switch scanners and re-run. Currently every run makes full API calls.

### Design
In-memory cache keyed by `(scanner_name, conversation_hash)`:

```python
import hashlib, json, time

_result_cache = {}  # {cache_key: (timestamp, result)}
CACHE_TTL = 300     # 5 minutes

def _cache_key(scanner_name: str, purpose: str, messages: list) -> str:
    content = json.dumps({"purpose": purpose, "messages": messages}, sort_keys=True)
    return f"{scanner_name}:{hashlib.sha256(content.encode()).hexdigest()}"

def get_cached(scanner_name, purpose, messages):
    key = _cache_key(scanner_name, purpose, messages)
    if key in _result_cache:
        ts, result = _result_cache[key]
        if time.time() - ts < CACHE_TTL:
            return result
        del _result_cache[key]
    return None

def set_cached(scanner_name, purpose, messages, result):
    key = _cache_key(scanner_name, purpose, messages)
    _result_cache[key] = (time.time(), result)
```

### Where to Integrate
In `scanner_runner.py`, wrap each scanner runner:

```python
def _run_alignment_check(purpose, messages, ...):
    cached = get_cached("AlignmentCheck", purpose, messages)
    if cached:
        return cached
    result = ... # existing logic
    set_cached("AlignmentCheck", purpose, messages, result)
    return result
```

### Cache Invalidation
- TTL-based: 5 minutes (configurable)
- Immediate invalidation when conversation is edited (messages change → different hash)
- No invalidation needed for scanner toggle (different scanner = different key)

### Action Items
- [ ] Create `multi_agent_demo/core/cache.py` with `get_cached()` / `set_cached()`
- [ ] Wrap `_run_alignment_check()`, `_run_facts_checker()`, `_run_data_disclosure_guard()` with cache lookup
- [ ] Add "Cache hit" indicator in UI results (optional)
- [ ] Same wrapping in `firewall.py` for the UI path

### Estimated Savings
- Repeat runs on same session: **100% token savings** (zero API calls)
- Typical usage pattern (run → tweak purpose → re-run): miss on purpose change, hit on message-only re-run

---

## Optimization 3: Smart Trace Summarization for Data-Heavy Sessions

### Problem

User messages often contain large structured data (vulnerability scan results, API responses,
config dumps, log files) that carry no behavioral signal for AlignmentCheck but dominate the
token budget and trigger hard limits that skip scanning entirely.

**Real-world example:** A Checkmarx vulnerability scan result (`results.txt`):
- 55K chars (~14K tokens) — a single user message
- 20 vulnerability entries (19 SCA + 1 SAST) with CVE IDs, CVSS scores, descriptions, package data
- Agent replies are short natural-language summaries

**What happens today:**
1. `validate_session_messages()` **rejects the entire session** (55K > `SESSION_MSG_SIZE_LIMIT` of 50K)
2. Even if loaded, `check_trace_for_large_messages()` skips AlignmentCheck (55K > `MSG_SIZE_LIMIT` of 12K)
3. `is_data_blob()` returns `True` (starts with `{`) — every assistant message gets WARNING + skipped
4. **Result: AlignmentCheck cannot evaluate any agent response in the session**

### Design: Pluggable Smart Summarizer

Instead of a generic `[structured data, 55K chars]` placeholder, extract the **behavioral
signal** — what the user provided and what they're asking about — so AlignmentCheck can still
evaluate whether the agent's response is aligned with the purpose.

#### Architecture

```
summarize_for_trace(content, msg_type)
  │
  ├── len(content) <= SUMMARIZE_THRESHOLD? → return as-is
  │
  ├── Try JSON parse
  │     ├── Detect known schema → domain summarizer
  │     │     ├── vulnerability scan (has "results" with "severity"/"cve")
  │     │     ├── API response (has "status"/"data"/"error")
  │     │     ├── OTEL trace (has "resourceSpans"/"traceId")
  │     │     └── ... extensible
  │     │
  │     └── Unknown JSON → generic JSON summarizer
  │           (top-level keys, array lengths, nested depth)
  │
  ├── Not JSON but structured (XML, CSV, logs) → generic structured summarizer
  │
  └── Long natural language → truncate with indicator
```

#### Core Module: `multi_agent_demo/core/trace_summarizer.py`

```python
import json
from typing import Optional

# Messages below this size are passed through unchanged
SUMMARIZE_THRESHOLD = 3000  # chars (~750 tokens)

# Maximum summary size — must leave room for the rest of the trace
MAX_SUMMARY_SIZE = 1500     # chars (~375 tokens)


def summarize_for_trace(content: str, msg_type: str = "user") -> str:
    """Produce a compact behavioral summary of a message for AlignmentCheck traces.

    Only context messages (not the target assistant message being evaluated) are
    summarized. The summary preserves intent and key facts while stripping
    voluminous raw data that confuses the alignment model.

    Returns original content if below SUMMARIZE_THRESHOLD.
    """
    if len(content) <= SUMMARIZE_THRESHOLD:
        return content

    # Try JSON-based summarization
    json_summary = _try_json_summary(content)
    if json_summary:
        return json_summary

    # Try generic structured data detection
    if _is_structured(content):
        return _summarize_structured(content, msg_type)

    # Long natural language — keep beginning and end (most relevant parts)
    half = MAX_SUMMARY_SIZE // 2
    return (
        content[:half]
        + f"\n\n[... {len(content):,} chars total, middle truncated for trace ...]\n\n"
        + content[-half:]
    )


def _try_json_summary(content: str) -> Optional[str]:
    """Attempt to parse as JSON and apply domain-aware or generic summarization."""
    stripped = content.strip()
    if not stripped.startswith(("{", "[")):
        return None
    try:
        data = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        # Try stripping common non-JSON prefixes (zero-width spaces, BOM)
        import re
        cleaned = re.sub(r'^[\s\u200b\u200c\u200d\ufeff]+', '', content)
        try:
            data = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            return None

    # --- Domain detection and dispatch ---

    if isinstance(data, dict):
        # Vulnerability scan results (Checkmarx, Snyk, etc.)
        if "results" in data and isinstance(data["results"], list):
            first = data["results"][0] if data["results"] else {}
            if any(k in first for k in ("severity", "cve", "cveName", "vulnerabilityDetails")):
                return _summarize_vulnerability_scan(data)

        # API response pattern
        if any(k in data for k in ("status_code", "statusCode", "error", "data")):
            return _summarize_api_response(data)

        # OTEL trace pattern
        if any(k in data for k in ("resourceSpans", "traceId", "spans")):
            return _summarize_otel_trace(data)

    # Generic JSON fallback
    return _summarize_generic_json(data, len(content))


# --- Domain Summarizers ---

def _summarize_vulnerability_scan(data: dict) -> str:
    """Summarize security scan results preserving severity distribution and key findings."""
    results = data.get("results", [])
    scan_id = data.get("scan_id", "unknown")

    # Aggregate by type and severity
    by_type = {}
    by_severity = {}
    for r in results:
        t = r.get("type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
        s = r.get("severity", "unknown")
        by_severity[s] = by_severity.get(s, 0) + 1

    # Extract high/critical findings (most relevant for agent behavior)
    high_findings = []
    for r in results:
        if r.get("severity") in ("HIGH", "CRITICAL"):
            cve = r.get("id", "unknown")
            desc = r.get("description", "")[:200]
            pkg = ""
            if r.get("data", {}).get("packageIdentifier"):
                pkg = f" ({r['data']['packageIdentifier']})"
            rec = ""
            if r.get("data", {}).get("recommendedVersion"):
                rec = f" → fix: {r['data']['recommendedVersion']}"
            high_findings.append(f"  - {cve}{pkg}: {desc}{rec}")

    lines = [
        f"[Vulnerability scan: {len(results)} findings from scan {scan_id[:12]}]",
        f"Types: {', '.join(f'{v} {k.upper()}' for k, v in sorted(by_type.items()))}",
        f"Severities: {', '.join(f'{v} {k}' for k, v in sorted(by_severity.items()))}",
    ]
    if high_findings:
        lines.append(f"High/Critical findings ({len(high_findings)}):")
        lines.extend(high_findings[:8])  # Cap at 8 to stay within budget
        if len(high_findings) > 8:
            lines.append(f"  ... and {len(high_findings) - 8} more")

    return "\n".join(lines)


def _summarize_api_response(data: dict) -> str:
    """Summarize API response preserving status, error info, and data shape."""
    status = data.get("status_code") or data.get("statusCode") or data.get("status", "?")
    error = data.get("error") or data.get("message") or ""

    # Describe data shape
    data_field = data.get("data") or data.get("response") or data.get("body")
    if isinstance(data_field, list):
        shape = f"array of {len(data_field)} items"
    elif isinstance(data_field, dict):
        shape = f"object with keys: {', '.join(list(data_field.keys())[:10])}"
    else:
        shape = f"keys: {', '.join(list(data.keys())[:10])}"

    summary = f"[API response: status={status}, {shape}]"
    if error:
        summary += f"\nError: {str(error)[:300]}"
    return summary


def _summarize_otel_trace(data: dict) -> str:
    """Summarize OpenTelemetry trace data."""
    spans = data.get("resourceSpans") or data.get("spans") or []
    span_count = len(spans) if isinstance(spans, list) else "?"
    trace_id = data.get("traceId", "unknown")
    return f"[OTEL trace: {span_count} spans, traceId={str(trace_id)[:12]}]"


def _summarize_generic_json(data, original_size: int) -> str:
    """Fallback: describe JSON structure without including raw values."""
    if isinstance(data, list):
        item_types = set()
        for item in data[:5]:
            if isinstance(item, dict):
                item_types.update(list(item.keys())[:5])
            else:
                item_types.add(type(item).__name__)
        return (
            f"[JSON array: {len(data)} items, {original_size:,} chars. "
            f"Item fields: {', '.join(sorted(item_types)[:10])}]"
        )
    elif isinstance(data, dict):
        top_keys = list(data.keys())[:15]
        # Show nested structure for first level
        structure = []
        for k in top_keys[:10]:
            v = data[k]
            if isinstance(v, list):
                structure.append(f"{k}: [{len(v)} items]")
            elif isinstance(v, dict):
                structure.append(f"{k}: {{{', '.join(list(v.keys())[:5])}}}")
            elif isinstance(v, str) and len(v) > 100:
                structure.append(f"{k}: \"{v[:80]}...\"")
            else:
                structure.append(f"{k}: {json.dumps(v)}"[:80])
        return (
            f"[JSON object: {len(data)} keys, {original_size:,} chars]\n"
            + "\n".join(structure)
        )
    return f"[JSON data: {original_size:,} chars]"


def _is_structured(content: str) -> bool:
    """Detect non-JSON structured data (XML, CSV, logs)."""
    stripped = content.strip()
    if stripped.startswith("<?xml") or stripped.startswith("<"):
        return True
    # CSV heuristic: consistent comma/tab counts across first few lines
    lines = stripped.split("\n", 10)
    if len(lines) >= 3:
        sep_counts = [line.count(",") for line in lines[:5]]
        if sep_counts[0] > 2 and all(c == sep_counts[0] for c in sep_counts):
            return True
    return False


def _summarize_structured(content: str, msg_type: str) -> str:
    """Summarize non-JSON structured data."""
    lines = content.strip().split("\n")
    line_count = len(lines)
    if content.strip().startswith("<"):
        return (
            f"[{msg_type} message: XML/HTML data, {len(content):,} chars, "
            f"{line_count} lines]\n"
            f"Root: {lines[0][:100]}"
        )
    return (
        f"[{msg_type} message: structured data, {len(content):,} chars, "
        f"{line_count} lines]\n"
        f"Header: {lines[0][:100]}"
    )
```

#### Real-World Example

Input: Checkmarx vulnerability scan (55K chars, ~14K tokens, 20 CVEs):

```
[Vulnerability scan: 20 findings from scan 6f694598-faf]
Types: 1 SAST, 19 SCA
Severities: 11 HIGH, 1 LOW, 8 MEDIUM
High/Critical findings (11):
  - CVE-2021-43818 (Python-lxml-4.6.1): lxml HTML Cleaner lets crafted script content pass through → fix: 6.0.2
  - CVE-2017-18342 (Python-PyYAML-3.12): yaml.load() API could execute arbitrary Python commands → fix: 6.0.2
  - CVE-2025-66471 (Python-urllib3-1.23): Streaming API improperly handles highly compressed data → fix: 2.6.0
  - CVE-2018-18074 (Python-requests-2.18.4): Sends HTTP Authorization header to unintended hosts → fix: 2.32.4
  - CVE-2024-35195 (Python-requests-2.18.4): Session object does not verify requests after making first → fix: 2.32.4
  - cZZy3qIIi (sast): yaml_processor.py deserialized by load — insecure deserialization
  ...
```

**Result: ~800 chars instead of 55K** — 98.5% reduction — while preserving:
- What the user provided (vulnerability scan with severity breakdown)
- Key findings the agent should address (HIGH CVEs with package names and fixes)
- The SAST finding (code-level vulnerability, different from SCA)

AlignmentCheck can now evaluate whether the agent's reply properly addresses the
high-severity findings vs. going off-topic or hallucinating non-existent CVEs.

### Where to Integrate

**1. Trace construction in `_scan_single_message()` (scanner_runner.py:194):**

```python
# Current:
if m["type"] == "user":
    msg_trace.append(UserMessage(content=m["content"]))

# Proposed — summarize context messages, never the target:
if m["type"] == "user":
    content = summarize_for_trace(m["content"], "user") if i < msg_idx else m["content"]
    msg_trace.append(UserMessage(content=content))
elif m["type"] == "assistant":
    content = m.get("content", "")
    if i == msg_idx:
        # Target message: always full content
        ...
    elif i in has_user_after:
        content = summarize_for_trace(content, "assistant")
        ...
```

**2. Session validation in `validate_session_messages()` (scanner_runner.py:65):**

```python
# Current: reject if any message > 50K
# Proposed: raise limit or remove — summarization handles large messages at scan time
SESSION_MSG_SIZE_LIMIT = 200_000  # generous limit; summarizer compacts at trace time
```

**3. Large message check in `check_trace_for_large_messages()` (scanner_runner.py:114):**

```python
# Current: skip if any trace message > 12K
# Proposed: remove this check entirely — summarizer ensures traces stay compact
# OR: check the *summarized* trace size instead of raw message size
```

**4. Same changes in `firewall.py` (UI path) for consistency.**

### What Changes

| Component | Before | After |
|-----------|--------|-------|
| `SESSION_MSG_SIZE_LIMIT` | 50K (rejects session) | 200K (load it, summarize at scan time) |
| `MSG_SIZE_LIMIT` check | 12K (skip AlignmentCheck) | Removed — summarizer keeps traces compact |
| User messages in trace | Raw content (55K chars) | Summarized (~800 chars) |
| Assistant messages in trace | Raw content | Summarized if context (not target) |
| Target assistant message | Raw content | **Unchanged — always full content** |
| FactsChecker | N/A | **Unchanged — needs full content for fact-checking** |
| PromptGuard | N/A | **Unchanged — local heuristic on raw content** |

### Adding New Domain Summarizers

To support a new data type (e.g., Terraform plans, CloudFormation outputs):

```python
# In _try_json_summary(), add detection:
if "terraform_version" in data or "planned_values" in data:
    return _summarize_terraform_plan(data)

# Then implement the summarizer:
def _summarize_terraform_plan(data: dict) -> str:
    resources = data.get("planned_values", {}).get("root_module", {}).get("resources", [])
    changes = data.get("resource_changes", [])
    create = sum(1 for c in changes if "create" in c.get("change", {}).get("actions", []))
    destroy = sum(1 for c in changes if "delete" in c.get("change", {}).get("actions", []))
    return (
        f"[Terraform plan: {len(resources)} resources, "
        f"{create} to create, {destroy} to destroy]"
    )
```

### Action Items
- [ ] Create `multi_agent_demo/core/trace_summarizer.py` with pluggable summarizer chain
- [ ] Implement domain summarizers: vulnerability scan, API response, OTEL trace, generic JSON
- [ ] Integrate into `_scan_single_message()` — summarize context messages only
- [ ] Raise `SESSION_MSG_SIZE_LIMIT` to 200K (or remove)
- [ ] Remove or soften `check_trace_for_large_messages()` — no longer needed with summarization
- [ ] Same changes in `firewall.py` for UI path
- [ ] Add tests: verify vulnerability scan JSON → compact summary → AlignmentCheck runs
- [ ] Add tests: verify target assistant message is never summarized

### Estimated Savings
- Vulnerability scan sessions (55K user input): **98%+ token reduction** in AlignmentCheck traces
- Sessions currently rejected at load time: **now scannable**
- Sessions currently skipped by AlignmentCheck: **now scannable**
- Generic JSON sessions: 80–95% reduction depending on structure
- No impact on scan quality — behavioral signals preserved, raw data stripped

---

## Optimization 4: Deduplicate FactsChecker Prompt Prefix

### Problem
Each RAG ungroundedness call (`nemo_scanners.py:390–411`) sends the same system instructions + conversation context + purpose. Only the target assistant message differs.

### Design
Restructure the OpenAI calls to use the `system` role for shared context:

```python
# Current: single user message with everything concatenated
messages=[{"role": "user", "content": full_prompt_with_context_and_message}]

# Proposed: split into system (cached) + user (varies)
messages=[
    {"role": "system", "content": instructions + conversation_history + purpose},
    {"role": "user", "content": f"Analyze this assistant message:\n{assistant_message}"}
]
```

OpenAI caches system message prefixes automatically when ≥1024 tokens. The conversation history easily exceeds this threshold, so the shared prefix gets cached across all N per-message calls.

### Action Items
- [ ] Refactor `_check_rag_ungroundedness()` in `nemo_scanners.py` to split system/user roles
- [ ] Refactor `_check_self_contradiction()` similarly (lower priority — single call)
- [ ] Verify OpenAI cache hits via response headers (`x-cache` or usage breakdown)

### Estimated Savings
- Per-message RAG checks: 40–60% input token reduction after first call
- Self-contradiction: minimal (single call per session)

---

## Implementation Priority

| # | Optimization | Effort | Token Savings | Latency Impact | Unlocks |
|---|-------------|--------|---------------|----------------|---------|
| 3 | Smart trace summarization | Medium (new module + integration) | 80–98% on data-heavy sessions | Faster (smaller payloads) | Sessions currently rejected/skipped |
| 2 | Application-level result cache | Low (new file + wrapping) | 100% on re-runs | Instant on cache hit | — |
| 4 | FactsChecker prompt restructuring | Low (refactor prompt construction) | 40–60% FactsChecker input tokens | Slight improvement | — |
| 1 | Provider prefix caching (sequential mode) | Low (config flag + conditional) | 30–50% AlignmentCheck input tokens | 2–3x slower (trade-off) | — |

**Recommended order:** 3 → 2 → 4 → 1

Optimization 3 (smart summarization) is now highest priority — it's the only optimization
that **unlocks scanning for sessions that are currently completely rejected or skipped**.
Without it, large JSON sessions (vulnerability scans, API responses) cannot be analyzed at all.
Optimization 2 (result cache) is next for repeat-run savings. Optimization 4 is a small
refactor with good per-call savings. Optimization 1 is a latency-vs-cost trade-off and should
be optional.

---

## Files to Modify

| File | Optimizations |
|------|---------------|
| `multi_agent_demo/core/trace_summarizer.py` (new) | #3 — pluggable summarizer chain with domain detectors |
| `multi_agent_demo/core/cache.py` (new) | #2 — result cache module |
| `multi_agent_demo/core/scanner_runner.py` | #3 (integrate summarizer + raise/remove size limits), #2 (cache wrapping), #1 (sequential flag) |
| `multi_agent_demo/firewall.py` | #3 (integrate summarizer for UI path), #2 (cache wrapping) |
| `multi_agent_demo/scanners/nemo_scanners.py` | #4 (prompt restructuring) |

## Metrics to Track
- AlignmentCheck skip rate before/after (optimization 3 — should drop to near zero)
- Session rejection rate before/after (optimization 3 — currently rejects >50K sessions)
- Summarized trace size vs original message size (optimization 3)
- Cache hit rate (optimization 2)
- Tokens per session before/after (all optimizations)
- Wall-clock time per session (optimization 1 trade-off)
