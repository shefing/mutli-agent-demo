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

## Optimization 3: Trace Summarization for Data-Heavy Sessions

### Problem
User messages containing large JSON objects (API responses, config dumps) consume many tokens but carry no behavioral signal for AlignmentCheck. A 10K JSON blob in the trace adds ~2,500 tokens per call, and it's included in every subsequent cumulative trace.

### Design
Before building the AlignmentCheck trace, replace data blobs with compact summaries:

```python
def summarize_for_trace(content: str, msg_type: str) -> str:
    """Replace data blobs with compact summaries for AlignmentCheck traces."""
    if len(content) <= 2000:
        return content
    if is_data_blob(content):
        # Extract key signals: top-level keys, array lengths, error fields
        preview = _extract_data_summary(content)
        return f"[{msg_type} message: structured data, {len(content):,} chars. Keys: {preview}]"
    # Long natural language: truncate with indicator
    return content[:2000] + f"\n[... truncated, {len(content):,} chars total]"

def _extract_data_summary(content: str) -> str:
    """Extract top-level JSON keys or first line for non-JSON data."""
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return ", ".join(list(data.keys())[:10])
        elif isinstance(data, list):
            return f"array of {len(data)} items"
    except json.JSONDecodeError:
        pass
    return content[:100]
```

### Where to Integrate
In `_scan_single_message()` (scanner_runner.py) during trace construction:

```python
# Current (line ~195):
trace_content = m.get("content", "")

# Proposed:
trace_content = summarize_for_trace(m.get("content", ""), m.get("type", "unknown"))
```

### What Changes
- AlignmentCheck traces become much shorter for data-heavy sessions
- The actual scanning target (the assistant message being evaluated) is **NOT summarized** — only context messages in the trace prefix
- FactsChecker is NOT affected (it needs full content for fact-checking)
- PromptGuard is NOT affected (local, scans raw content)

### Action Items
- [ ] Add `summarize_for_trace()` to `scanner_runner.py`
- [ ] Apply to trace context messages (not the target assistant message)
- [ ] Raise `MSG_SIZE_LIMIT` from 12K to 50K (traces are now compact enough)
- [ ] This enables AlignmentCheck to run on sessions it currently skips entirely

### Estimated Savings
- Sessions with JSON user inputs: 60–80% reduction in AlignmentCheck tokens
- Sessions currently skipped (>12K messages): now scannable
- No impact on scan quality (behavioral signals are in natural language, not data blobs)

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

| # | Optimization | Effort | Token Savings | Latency Impact |
|---|-------------|--------|---------------|----------------|
| 1 | Application-level result cache | Low (new file + wrapping) | 100% on re-runs | Instant on cache hit |
| 2 | Trace summarization for data blobs | Medium (new function + integration) | 60–80% on data-heavy sessions | Slight improvement (smaller payloads) |
| 3 | Provider prefix caching (sequential mode) | Low (config flag + conditional) | 30–50% AlignmentCheck input tokens | 2–3x slower (trade-off) |
| 4 | FactsChecker prompt restructuring | Low (refactor prompt construction) | 40–60% FactsChecker input tokens | Slight improvement |

**Recommended order:** 1 → 2 → 4 → 3

Optimization 1 is highest ROI (zero API calls on re-runs). Optimization 2 unlocks scanning for sessions currently rejected. Optimization 4 is a small refactor with good savings. Optimization 3 is a trade-off (cost vs latency) and should be optional.

---

## Files to Modify

| File | Optimizations |
|------|---------------|
| `multi_agent_demo/core/cache.py` (new) | #1 — result cache module |
| `multi_agent_demo/core/scanner_runner.py` | #1 (cache wrapping), #2 (trace summarization), #3 (sequential flag) |
| `multi_agent_demo/firewall.py` | #1 (cache wrapping for UI path) |
| `multi_agent_demo/scanners/nemo_scanners.py` | #4 (prompt restructuring) |

## Metrics to Track
- Cache hit rate (optimization 1)
- Tokens per session before/after (all optimizations)
- AlignmentCheck skip rate reduction (optimization 2)
- Wall-clock time per session (optimization 3 trade-off)
