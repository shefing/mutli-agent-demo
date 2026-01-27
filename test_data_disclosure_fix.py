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
from multi_agent_demo.scanners.data_disclosure_scanner import DataDisclosureGuardScanner


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
    print(f"Is Safe:        {result.get('is_safe')}")
    print(f"Score:          {result.get('score')}")
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


if __name__ == "__main__":
    success = test_h_and_m_scenario()
    exit(0 if success else 1)
