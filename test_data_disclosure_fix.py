"""
Test script to verify DataDisclosureGuard false positive fixes

This script tests the scenario that previously generated false positives:
- Product IDs in URLs (e.g., 1292976003)
- SKU numbers in JSON (e.g., 770711062)
- Session tokens in cookies
- Browser version numbers (e.g., Chrome/139.0.0.0)
- Timestamp-like numbers (e.g., 1764414892)
"""

import json
import importlib.util

# Direct import to avoid pulling in nemo_scanners (needs openai)
_spec = importlib.util.spec_from_file_location(
    "data_disclosure_scanner",
    "multi_agent_demo/scanners/data_disclosure_scanner.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
DataDisclosureGuardScanner = _mod.DataDisclosureGuardScanner


def test_h_and_m_scenario():
    """Test the H&M workflow scenario that previously had false positives"""
    print("Testing H&M workflow scenario for false positives...")
    print("=" * 80)

    # Generate synthetic test data that mimics the problematic patterns
    # This avoids depending on external files while testing the same scenarios
    messages = [
        {
            "type": "user",
            "content": "build a workflow like this one, but it monitors this page for size 24\nhttps://www2.hm.com/de_ch/productpage.1292976003.html?utm_source=google&utm_medium=cpc&utm_campaign=13173887996&utm_term=&gad_source=1"
        },
        {
            "type": "assistant",
            "content": "Yes, I'm building a **new workflow** from scratch that will monitor this H&M product page:\n\n**https://www2.hm.com/de_ch/productpage.1292976003.html**"
        },
        {
            "type": "user",
            "content": """curl 'https://www2.hm.com/de_ch/productpage.1292976003.html' \\
  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9' \\
  -H 'accept-language: en-US,en;q=0.9' \\
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36' \\
  -b 'session_id=770711062; INGRESSCOOKIE=1764414892.896.393.109617; ak_bmsc=22DC03A4068D7864E719A5E7B7785FC2~000000000000000000000000000000~YAAQJmzerU9HSaaaAQAA9qhSzx1'"""
        },
        {
            "type": "assistant",
            "content": """I've updated the code. Here's the product schema:

        <script id="product-group-schema" type="application/ld+json">
        {
          "variants": [
            {"sku": "1292976001007", "url": "productpage.1292976001.html"},
            {"sku": "1292976002008", "url": "productpage.1292976002.html"},
            {"sku": "1292976003009", "url": "productpage.1292976003.html"}
          ]
        }
        </script>"""
        }
    ]

    purpose = 'Build a workflow to monitor H&M product page for size 24 availability'

    # Initialize scanner
    scanner = DataDisclosureGuardScanner()

    if not scanner.presidio_available:
        print("⚠️  Presidio not installed — skipping H&M full-scan test")
        return None  # skip

    print(f"Scenario: {len(messages)} messages")
    print(f"Purpose: {purpose}")
    print("\nRunning DataDisclosureGuard scan...")
    print("=" * 80)

    # Run the scanner
    result = scanner.scan(messages, purpose)

    # Display results
    print("\nSCAN RESULTS:")
    print("=" * 80)
    print(f"Decision:       {result.get('decision')}")
    print(f"Overall Decision: {result.get('overall_decision', 'N/A')}")
    if 'counts' in result:
        print(f"Counts:         Safe={result['counts']['safe']}, Warning={result['counts']['warning']}, Block={result['counts']['block']}")
    print(f"Is Safe:        {result.get('is_safe')}")
    print(f"PII Count:      {result.get('total_pii_count')}")
    print(f"Reason:         {result.get('reason', 'N/A')}")
    print("=" * 80)

    # Verify fix
    if result.get('total_pii_count', 0) == 0 and result.get('is_safe') == True:
        print("\n✅ TEST PASSED: No false positives detected!")
        print("\nSuccessfully filtered:")
        print("  • Product IDs in URLs (e.g., 1292976003)")
        print("  • SKU numbers in JSON (e.g., 770711062, 1292976001007)")
        print("  • Session tokens in cookies")
        print("  • Browser version numbers (e.g., Chrome/139.0.0.0)")
        print("  • Timestamp-like numbers (e.g., 1764414892)")
        return True
    else:
        print(f"\n❌ TEST FAILED: Still detecting {result.get('total_pii_count', 0)} PII entities")
        if 'pii_findings' in result:
            print("\nRemaining PII detections:")
            for finding in result['pii_findings']:
                for entity in finding['pii_entities']:
                    print(f"  • {entity['type']}: {entity['text']}")
        return False


def test_json_field_value_filtering():
    """Test that numeric values in JSON fields are filtered unless the field name indicates PII"""
    print("\nTesting JSON field-value filtering...")
    print("=" * 80)

    scanner = DataDisclosureGuardScanner()

    # Helper: build a synthetic entity dict at the right position within text
    def make_entity(text, value, entity_type):
        start = text.index(value)
        return {"text": value, "type": entity_type, "start": start, "end": start + len(value)}

    passed = 0
    failed = 0

    # --- Cases that SHOULD be filtered (technical JSON data, not PII) ---
    filter_cases = [
        # SAST-style structured data
        ('{"similarityId": "703764369", "status": "NEW"}', "703764369", "US_SSN",
         "SAST similarityId"),
        ('{"similarityId": "-1325423813", "state": "TO_VERIFY"}', "1325423813", "US_SSN",
         "negative similarityId (digits only)"),
        ('{"queryId": 14171746259763180000, "queryName": "Stored_Path_Traversal"}', "14171746259763180000", "PHONE_NUMBER",
         "SAST queryId"),
        # Generic application IDs
        ('{"orderId": "123456789", "total": 59.99}', "123456789", "US_SSN",
         "orderId"),
        ('{"transactionRef": "987654321", "status": "complete"}', "987654321", "US_PASSPORT",
         "transactionRef"),
        ('{"invoiceNumber": "112233445", "amount": 100}', "112233445", "US_BANK_NUMBER",
         "invoiceNumber"),
        ('{"correlationId": "5551234567", "service": "api"}', "5551234567", "PHONE_NUMBER",
         "correlationId"),
        ('{"resultHash": "770711062", "algo": "sha1"}', "770711062", "US_SSN",
         "resultHash"),
    ]

    for text, value, entity_type, label in filter_cases:
        entity = make_entity(text, value, entity_type)
        result = scanner._is_technical_context(text, entity)
        if result:
            print(f"  ✅ Filtered {entity_type} in {label}")
            passed += 1
        else:
            print(f"  ❌ FAILED to filter {entity_type} in {label}")
            failed += 1

    # --- Cases that should NOT be filtered (real PII in JSON) ---
    keep_cases = [
        ('{"ssn": "123456789", "name": "John"}', "123456789", "US_SSN",
         "ssn field (real PII)"),
        ('{"phone": "5551234567", "name": "Jane"}', "5551234567", "PHONE_NUMBER",
         "phone field (real PII)"),
        ('{"passport": "987654321", "country": "US"}', "987654321", "US_PASSPORT",
         "passport field (real PII)"),
        ('{"bank_account": "123456789012", "routing": "021000021"}', "123456789012", "US_BANK_NUMBER",
         "bank_account field (real PII)"),
        ('{"phone_number": "2025551234", "type": "mobile"}', "2025551234", "PHONE_NUMBER",
         "phone_number field (real PII)"),
    ]

    for text, value, entity_type, label in keep_cases:
        entity = make_entity(text, value, entity_type)
        result = scanner._is_technical_context(text, entity)
        if not result:
            print(f"  ✅ Kept {entity_type} in {label}")
            passed += 1
        else:
            print(f"  ❌ FAILED — incorrectly filtered {entity_type} in {label}")
            failed += 1

    # --- Cases that should NOT be filtered (plain text PII, not JSON) ---
    plain_cases = [
        ("My SSN is 123456789 and I need help", "123456789", "US_SSN",
         "plain text SSN"),
        ("Call me at 5551234567 please", "5551234567", "PHONE_NUMBER",
         "plain text phone"),
        ("Passport number 987654321", "987654321", "US_PASSPORT",
         "plain text passport"),
    ]

    for text, value, entity_type, label in plain_cases:
        entity = make_entity(text, value, entity_type)
        result = scanner._is_technical_context(text, entity)
        if not result:
            print(f"  ✅ Kept {entity_type} in {label}")
            passed += 1
        else:
            print(f"  ❌ FAILED — incorrectly filtered {entity_type} in {label}")
            failed += 1

    total = passed + failed
    print(f"\nJSON field-value filtering: {passed}/{total} passed")
    return failed == 0, passed, total


def test_float_fraction_filtering():
    """Test that fractional digits of floating-point numbers are not flagged as bank numbers.

    Checkmarx/SCA cvssScore values like 7.099999904632568 have 15-digit fractional
    parts that Presidio detects as US_BANK_NUMBER.
    """
    print("\nTesting float-fraction false-positive filtering...")
    print("=" * 80)

    scanner = DataDisclosureGuardScanner()

    def make_entity(text, value, entity_type):
        start = text.index(value)
        return {"text": value, "type": entity_type, "start": start, "end": start + len(value)}

    passed = 0
    failed = 0

    # --- Float fractions that SHOULD be filtered ---
    filter_cases = [
        ('"cvssScore": 7.099999904632568,', "099999904632568", "US_BANK_NUMBER",
         "cvssScore 7.099999904632568"),
        ('"cvssScore": 9.800000190734863,', "800000190734863", "US_BANK_NUMBER",
         "cvssScore 9.800000190734863"),
        ('"cvssScore": 4.400000095367432,', "400000095367432", "US_BANK_NUMBER",
         "cvssScore 4.400000095367432"),
        ('"cvssScore": 4.199999809265137,', "199999809265137", "US_BANK_NUMBER",
         "cvssScore 4.199999809265137"),
        ('"cvssScore": 8.899999618530273,', "899999618530273", "US_BANK_NUMBER",
         "cvssScore 8.899999618530273"),
        # Also works for non-cvss floats
        ('"weight": 3.141592653589793,', "141592653589793", "US_BANK_NUMBER",
         "pi fractional digits"),
        ('"price": 0.123456789012345,', "123456789012345", "US_BANK_NUMBER",
         "price fractional digits"),
    ]

    for text, value, entity_type, label in filter_cases:
        entity = make_entity(text, value, entity_type)
        result = scanner._is_technical_context(text, entity)
        if result:
            print(f"  ✅ Filtered {entity_type} in {label}")
            passed += 1
        else:
            print(f"  ❌ FAILED to filter {entity_type} in {label}")
            failed += 1

    # --- Real bank numbers that should NOT be filtered ---
    keep_cases = [
        ('account number 123456789012345 is active', "123456789012345", "US_BANK_NUMBER",
         "plain text bank number"),
        ('"bank_account": "123456789012345"', "123456789012345", "US_BANK_NUMBER",
         "bank_account JSON field"),
    ]

    for text, value, entity_type, label in keep_cases:
        entity = make_entity(text, value, entity_type)
        result = scanner._is_technical_context(text, entity)
        if not result:
            print(f"  ✅ Kept {entity_type} in {label}")
            passed += 1
        else:
            print(f"  ❌ FAILED — incorrectly filtered {entity_type} in {label}")
            failed += 1

    total = passed + failed
    print(f"\nFloat-fraction filtering: {passed}/{total} passed")
    return failed == 0, passed, total


def test_vulnerability_scan_file():
    """End-to-end test: a Checkmarx vulnerability scan should produce zero PII findings"""
    print("\nTesting vulnerability scan file (end-to-end)...")
    print("=" * 80)

    scanner = DataDisclosureGuardScanner()
    if not scanner.presidio_available:
        print("⚠️  Presidio not installed — skipping")
        return None, 0, 0

    # Build a minimal vulnerability scan with the problematic float cvssScores
    scan_data = {
        "scan_id": "6f694598-faf4-434f-948a-b55267b867f4",
        "results": [
            {
                "type": "sca",
                "id": "CVE-2021-43818",
                "similarityId": "CVE-2021-43818",
                "severity": "HIGH",
                "vulnerabilityDetails": {
                    "cvssScore": 7.099999904632568,
                    "cveName": "CVE-2021-43818",
                    "cweId": "CWE-79"
                }
            },
            {
                "type": "sast",
                "id": "cZZy3qIIiYPCTqvXRIWQpihYst4=",
                "similarityId": "124927330",
                "severity": "HIGH",
                "data": {
                    "queryId": 9372117855007486000,
                    "queryName": "Deserialization_of_Untrusted_Data"
                },
                "vulnerabilityDetails": {
                    "cvssScore": 9.800000190734863,
                    "cweId": 502
                }
            }
        ],
        "totalCount": 2
    }

    import json
    assistant_content = json.dumps(scan_data, indent=2)
    pii_results = scanner.detect_pii(assistant_content)

    if len(pii_results) == 0:
        print("  ✅ Zero PII detected in vulnerability scan output")
        return True, 1, 1
    else:
        print(f"  ❌ {len(pii_results)} false positive(s) remain:")
        for r in pii_results:
            print(f"     {r['type']}: \"{r['text']}\"")
        return False, 0, 1


if __name__ == "__main__":
    results = []

    success1 = test_h_and_m_scenario()
    if success1 is None:
        hm_passed, hm_total = 0, 0  # skipped
    else:
        results.append(success1)
        hm_passed, hm_total = (1 if success1 else 0), 1

    success2, json_passed, json_total = test_json_field_value_filtering()
    results.append(success2)

    success3, float_passed, float_total = test_float_fraction_filtering()
    results.append(success3)

    success4, scan_passed, scan_total = test_vulnerability_scan_file()
    if success4 is not None:
        results.append(success4)

    total_passed = hm_passed + json_passed + float_passed + scan_passed
    total_tests = hm_total + json_total + float_total + scan_total
    print(f"\nTEST_COUNTS:{total_passed}/{total_tests}")
    exit(0 if all(results) else 1)
