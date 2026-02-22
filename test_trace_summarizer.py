#!/usr/bin/env python3
"""
Unit tests for trace_summarizer module.

Tests the smart trace summarization that compacts large messages for
AlignmentCheck traces while preserving behavioral signals.

No API keys needed — all tests are local.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from multi_agent_demo.core.trace_summarizer import (
    summarize_for_trace,
    SUMMARIZE_THRESHOLD,
    MAX_SUMMARY_SIZE,
    _try_json_summary,
    _is_structured,
    _summarize_vulnerability_scan,
    _summarize_api_response,
    _summarize_otel_trace,
    _summarize_generic_json,
    _summarize_structured,
)


passed = 0
failed = 0


def check(condition, label):
    global passed, failed
    if condition:
        print(f"  ✅ {label}")
        passed += 1
    else:
        print(f"  ❌ {label}")
        failed += 1


# ── 1. Threshold boundary ──────────────────────────────────────────────

def test_threshold_boundary():
    print("\n" + "=" * 70)
    print("TEST: Threshold boundary (SUMMARIZE_THRESHOLD = %d)" % SUMMARIZE_THRESHOLD)
    print("=" * 70)

    short = "x" * (SUMMARIZE_THRESHOLD - 1)
    check(summarize_for_trace(short) == short,
          f"{SUMMARIZE_THRESHOLD - 1} chars passes through unchanged")

    exact = "x" * SUMMARIZE_THRESHOLD
    check(summarize_for_trace(exact) == exact,
          f"{SUMMARIZE_THRESHOLD} chars passes through unchanged (<=)")

    over = "x" * (SUMMARIZE_THRESHOLD + 1)
    result = summarize_for_trace(over)
    check(result != over,
          f"{SUMMARIZE_THRESHOLD + 1} chars is summarized (different from input)")
    check(len(result) < len(over),
          f"  output ({len(result)} chars) shorter than input ({len(over)} chars)")


# ── 2. Empty and trivial content ────────────────────────────────────────

def test_empty_and_trivial():
    print("\n" + "=" * 70)
    print("TEST: Empty and trivial content")
    print("=" * 70)

    check(summarize_for_trace("") == "", "Empty string passes through")
    check(summarize_for_trace("{}") == "{}", "Trivial JSON object passes through")
    check(summarize_for_trace("[]") == "[]", "Trivial JSON array passes through")
    check(summarize_for_trace("Hello") == "Hello", "Short text passes through")
    check(summarize_for_trace("   ") == "   ", "Whitespace-only passes through")


# ── 3. Natural language truncation ──────────────────────────────────────

def test_natural_language_truncation():
    print("\n" + "=" * 70)
    print("TEST: Natural language truncation")
    print("=" * 70)

    long_text = "deployment pipeline failing " * 200  # ~5400 chars
    result = summarize_for_trace(long_text)

    check(len(result) < len(long_text),
          f"Truncated: {len(long_text)} -> {len(result)} chars")
    check("truncated for trace" in result,
          "Contains truncation indicator")
    check(result.startswith(long_text[:100]),
          "Starts with beginning of original")
    check(result.endswith(long_text[-100:]),
          "Ends with end of original")
    # Output should be roughly MAX_SUMMARY_SIZE + indicator overhead
    check(len(result) < MAX_SUMMARY_SIZE + 100,
          f"Output ({len(result)}) near MAX_SUMMARY_SIZE ({MAX_SUMMARY_SIZE})")


# ── 4. Vulnerability scan summarizer ────────────────────────────────────

def test_vulnerability_scan():
    print("\n" + "=" * 70)
    print("TEST: Vulnerability scan domain summarizer")
    print("=" * 70)

    scan_data = {
        "scan_id": "6f694598-faf4-4c1b-9a1a-abc123",
        "results": [
            {
                "id": "CVE-2021-43818", "type": "sca", "severity": "HIGH",
                "description": "lxml HTML Cleaner vulnerability",
                "data": {"packageIdentifier": "Python-lxml-4.6.1", "recommendedVersion": "6.0.2"}
            },
            {
                "id": "CVE-2017-18342", "type": "sca", "severity": "HIGH",
                "description": "yaml.load unsafe deserialization",
                "data": {"packageIdentifier": "Python-PyYAML-3.12", "recommendedVersion": "6.0.2"}
            },
            {"id": "LOW-001", "type": "sca", "severity": "LOW", "description": "Minor issue"},
            {"id": "MED-001", "type": "sca", "severity": "MEDIUM", "description": "Medium issue"},
            {
                "id": "SAST-001", "type": "sast", "severity": "HIGH",
                "description": "Insecure deserialization in yaml_processor.py"
            },
        ]
    }

    # Pad to exceed threshold
    big_scan = json.dumps(scan_data)
    if len(big_scan) <= SUMMARIZE_THRESHOLD:
        scan_data["results"].extend([
            {"id": f"PAD-{i}", "type": "sca", "severity": "MEDIUM",
             "description": "Padding vulnerability " * 20}
            for i in range(20)
        ])
        big_scan = json.dumps(scan_data)

    result = summarize_for_trace(big_scan)
    check("Vulnerability scan" in result, "Detected as vulnerability scan")
    check("HIGH" in result, "Contains HIGH severity")
    check("CVE-2021-43818" in result, "Contains HIGH CVE ID")
    check("Python-lxml" in result, "Contains package identifier")
    check("6.0.2" in result, "Contains recommended fix version")
    check("SAST" in result.upper(), "Contains SAST type")
    check(len(result) < len(big_scan),
          f"Reduced: {len(big_scan)} -> {len(result)} chars")

    # Edge: empty results list
    empty_scan = _summarize_vulnerability_scan({"results": []})
    check("0 findings" in empty_scan, "Empty results: reports 0 findings")

    # Edge: missing fields in result entry
    sparse = _summarize_vulnerability_scan({
        "results": [{"severity": "HIGH"}]
    })
    check("HIGH" in sparse, "Sparse entry: severity still reported")


# ── 5. API response summarizer ──────────────────────────────────────────

def test_api_response():
    print("\n" + "=" * 70)
    print("TEST: API response domain summarizer")
    print("=" * 70)

    # List data
    api_data = {
        "status_code": 200,
        "data": [{"id": i, "name": f"item-{i}", "desc": "x" * 100} for i in range(50)]
    }
    big_api = json.dumps(api_data)
    if len(big_api) <= SUMMARIZE_THRESHOLD:
        api_data["data"].extend([
            {"id": i, "name": f"item-{i}", "desc": "x" * 200} for i in range(50, 100)
        ])
        big_api = json.dumps(api_data)

    result = summarize_for_trace(big_api)
    check("API response" in result, "Detected as API response")
    check("200" in result, "Contains status code")
    check("array" in result.lower() or "items" in result.lower(),
          "Describes data shape (array)")

    # statusCode variant
    summary = _summarize_api_response({"statusCode": 404, "error": "Not Found"})
    check("404" in summary, "statusCode variant works")
    check("Not Found" in summary, "Error message included")

    # Dict data
    summary = _summarize_api_response({
        "status_code": 200,
        "data": {"users": [], "count": 42}
    })
    check("object" in summary.lower() or "keys" in summary.lower(),
          "Dict data described as object/keys")


# ── 6. OTEL trace summarizer ────────────────────────────────────────────

def test_otel_trace():
    print("\n" + "=" * 70)
    print("TEST: OTEL trace domain summarizer")
    print("=" * 70)

    otel_data = {
        "resourceSpans": [
            {"resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "my-service"}}]},
             "scopeSpans": [{"spans": [{"traceId": "abc123", "name": "GET /api"}]}]}
        ] * 3,
        "traceId": "abcdef1234567890abcdef"
    }
    big_otel = json.dumps(otel_data)
    if len(big_otel) <= SUMMARIZE_THRESHOLD:
        otel_data["resourceSpans"] = otel_data["resourceSpans"] * 20
        big_otel = json.dumps(otel_data)

    result = summarize_for_trace(big_otel)
    check("OTEL trace" in result, "Detected as OTEL trace")
    check("spans" in result.lower(), "Contains span count")
    check("abcdef12" in result, "Contains truncated traceId")

    # Edge: spans key variant
    summary = _summarize_otel_trace({"spans": [1, 2, 3]})
    check("3 spans" in summary, "spans key variant: correct count")

    # Edge: empty spans
    summary = _summarize_otel_trace({"resourceSpans": []})
    check("0 spans" in summary, "Empty spans: reports 0")


# ── 7. Generic JSON summarizer ──────────────────────────────────────────

def test_generic_json():
    print("\n" + "=" * 70)
    print("TEST: Generic JSON summarizer")
    print("=" * 70)

    # Large dict
    big_dict = {f"key_{i}": f"value_{i}" * 100 for i in range(50)}
    big_json = json.dumps(big_dict)
    result = summarize_for_trace(big_json)
    check("JSON object" in result, "Dict detected as JSON object")
    check("50 keys" in result, "Reports key count")
    check("key_0" in result, "Shows top-level key names")

    # Large list with dicts
    big_list = [{"id": i, "name": f"item-{i}", "value": "x" * 100} for i in range(100)]
    big_json = json.dumps(big_list)
    result = summarize_for_trace(big_json)
    check("JSON array" in result, "List detected as JSON array")
    check("100 items" in result, "Reports item count")

    # List with primitives
    prim_list = list(range(1000))
    summary = _summarize_generic_json(prim_list, 5000)
    check("1000 items" in summary, "Primitive list: reports count")
    check("int" in summary, "Primitive list: reports type")

    # Empty dict and list
    summary = _summarize_generic_json({}, 2)
    check("0 keys" in summary, "Empty dict: 0 keys")

    summary = _summarize_generic_json([], 2)
    check("0 items" in summary, "Empty list: 0 items")


# ── 8. Structured (non-JSON) data ───────────────────────────────────────

def test_structured_data():
    print("\n" + "=" * 70)
    print("TEST: Structured non-JSON data (XML, CSV)")
    print("=" * 70)

    # XML detection
    xml_content = '<?xml version="1.0"?>\n' + '<root>\n' + '  <item id="1">data</item>\n' * 200
    check(_is_structured(xml_content), "XML detected as structured")
    result = summarize_for_trace(xml_content)
    check("XML" in result or "xml" in result, "XML summary mentions XML")
    check(len(result) < len(xml_content), "XML summarized shorter")

    # HTML-like
    html = '<div class="container">\n' + '  <p>Content paragraph</p>\n' * 200
    check(_is_structured(html), "HTML detected as structured")

    # CSV detection
    csv_header = "name,age,city,state,zip\n"
    csv_rows = "".join([f"person{i},30,CityName,ST,12345\n" for i in range(200)])
    csv_content = csv_header + csv_rows
    check(_is_structured(csv_content), "CSV detected as structured")
    result = summarize_for_trace(csv_content)
    check("structured data" in result.lower() or "CSV" in result,
          "CSV summary indicates structured data")

    # Non-structured natural language
    check(not _is_structured("Hello world, this is a normal sentence."),
          "Natural language NOT detected as structured")


# ── 9. Malformed JSON fallback ──────────────────────────────────────────

def test_malformed_json():
    print("\n" + "=" * 70)
    print("TEST: Malformed JSON falls back gracefully")
    print("=" * 70)

    # Partial JSON (no closing brace) — should fall through to NL truncation
    partial = '{"key": "value", "data": [1, 2, 3' + 'x' * 4000
    result = summarize_for_trace(partial)
    check(len(result) < len(partial),
          "Partial JSON: still summarized (fell through to truncation)")
    # Since it starts with {, _try_json_summary fails, then _is_structured
    # might catch it or fall to NL truncation

    # JSON with BOM prefix
    bom_json = '\ufeff' + json.dumps({"status_code": 200, "data": "x" * 4000})
    result = summarize_for_trace(bom_json)
    check("API response" in result or "JSON" in result or "truncated" in result,
          "BOM-prefixed JSON: handled (parsed or truncated)")

    # Large string that looks like JSON but isn't
    fake_json = '{"broken": ' + '"value"' * 500 + '...'
    result = summarize_for_trace(fake_json)
    check(len(result) < len(fake_json),
          "Fake JSON: summarized via fallback")


# ── 10. Integration: context vs target message ──────────────────────────

def test_context_vs_target():
    """Verify _scan_single_message summarizes context but not the target."""
    print("\n" + "=" * 70)
    print("TEST: Integration - context summarized, target preserved")
    print("=" * 70)

    # We test the trace-building logic by importing _scan_single_message
    # and checking the trace it builds. Since we can't run LlamaFirewall
    # locally, we mock at the trace level.

    # Build a message list with a large user message and assistant target
    large_user_content = json.dumps({
        "status_code": 200,
        "data": [{"id": i, "value": "x" * 100} for i in range(50)]
    })
    target_content = "Based on the API response, the data looks correct."

    messages = [
        {"type": "user", "content": large_user_content},
        {"type": "assistant", "content": target_content},
    ]

    # Verify the summarizer would compact the user message
    summarized_user = summarize_for_trace(large_user_content, "user")
    check(len(summarized_user) < len(large_user_content),
          f"User context summarized: {len(large_user_content)} -> {len(summarized_user)} chars")

    # Verify the target message would NOT be summarized (it's below threshold anyway,
    # but let's test with a large target too)
    large_target = "The analysis shows " + "detailed findings " * 300
    check(summarize_for_trace(large_target) != large_target,
          "Large content IS summarized when passed to summarize_for_trace()")

    # The key integration point: in _scan_single_message, the target (i == msg_idx)
    # goes through the `pass` branch and is NOT passed to summarize_for_trace.
    # We verify this by checking the source code structure:
    import inspect
    from multi_agent_demo.core.scanner_runner import _scan_single_message
    source = inspect.getsource(_scan_single_message)
    check("summarize_for_trace" in source,
          "_scan_single_message imports summarize_for_trace")
    check('i == msg_idx' in source and 'pass' in source,
          "Target message has explicit pass (no summarization)")
    # The summarize_for_trace calls are in user and context-assistant branches
    check(source.count("summarize_for_trace") == 3,  # 1 import + 2 calls
          "summarize_for_trace called for user messages and context assistants (not target)")


# ── 11. SESSION_MSG_SIZE_LIMIT ──────────────────────────────────────────

def test_session_msg_size_limit():
    print("\n" + "=" * 70)
    print("TEST: SESSION_MSG_SIZE_LIMIT raised to 200K")
    print("=" * 70)

    from multi_agent_demo.core.scanner_runner import validate_session_messages, SESSION_MSG_SIZE_LIMIT

    check(SESSION_MSG_SIZE_LIMIT == 200_000,
          f"SESSION_MSG_SIZE_LIMIT is 200,000 (got {SESSION_MSG_SIZE_LIMIT})")

    # 100K message should be accepted (was rejected at old 50K limit)
    messages = [{"type": "user", "content": "x" * 100_000}]
    ok, err = validate_session_messages(messages)
    check(ok, "100K message accepted (was rejected at old 50K limit)")

    # 250K message should be rejected
    messages = [{"type": "user", "content": "x" * 250_000}]
    ok, err = validate_session_messages(messages)
    check(not ok, "250K message rejected (exceeds 200K limit)")
    check(err is not None and "250,000" in err, "Error message shows size")


# ── Run all ─────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("TRACE SUMMARIZER UNIT TESTS")
    print("No API keys needed — all tests are local")
    print("=" * 70)

    test_threshold_boundary()
    test_empty_and_trivial()
    test_natural_language_truncation()
    test_vulnerability_scan()
    test_api_response()
    test_otel_trace()
    test_generic_json()
    test_structured_data()
    test_malformed_json()
    test_context_vs_target()
    test_session_msg_size_limit()

    total = passed + failed
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"TEST_COUNTS:{passed}/{total}")

    if failed == 0:
        print(f"\n✅ ALL TESTS PASSED ({passed}/{total})")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"\n❌ {failed} TESTS FAILED ({passed}/{total} passed)")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
