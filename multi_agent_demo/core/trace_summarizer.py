"""
Smart Trace Summarization for AlignmentCheck

Produces compact behavioral summaries of large messages for AlignmentCheck traces.
Only context messages (not the target assistant message being evaluated) are
summarized. The summary preserves intent and key facts while stripping
voluminous raw data that confuses the alignment model.

Pluggable architecture: domain-specific summarizers are tried first, then
generic JSON/structured fallbacks, then natural language truncation.
"""

import json
import re
from typing import Optional


# Messages below this size are passed through unchanged
SUMMARIZE_THRESHOLD = 3000  # chars (~750 tokens)

# Maximum summary size — must leave room for the rest of the trace
MAX_SUMMARY_SIZE = 1500  # chars (~375 tokens)


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
            if isinstance(first, dict) and any(
                k in first for k in ("severity", "cve", "cveName", "vulnerabilityDetails")
            ):
                return _summarize_vulnerability_scan(data)

        # API response pattern
        if any(k in data for k in ("status_code", "statusCode")):
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
    scan_id = data.get("scan_id", data.get("scanId", "unknown"))

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
        if r.get("severity") in ("HIGH", "CRITICAL", "High", "Critical"):
            cve = r.get("id", r.get("cve", "unknown"))
            desc = r.get("description", "")[:200]
            pkg = ""
            if isinstance(r.get("data"), dict) and r["data"].get("packageIdentifier"):
                pkg = f" ({r['data']['packageIdentifier']})"
            rec = ""
            if isinstance(r.get("data"), dict) and r["data"].get("recommendedVersion"):
                rec = f" -> fix: {r['data']['recommendedVersion']}"
            high_findings.append(f"  - {cve}{pkg}: {desc}{rec}")

    lines = [
        f"[Vulnerability scan: {len(results)} findings from scan {str(scan_id)[:12]}]",
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
