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

    # Load the problematic scenario
    scenario_path = '/Users/philc/dev/openops/langfuse-exporter/sessions/environment_prod_15f5dcc5.json'
    with open(scenario_path, 'r') as f:
        scenario = json.load(f)

    # Initialize scanner
    scanner = DataDisclosureGuardScanner()

    # Test on the scenario messages
    messages = scenario.get('messages', [])
    purpose = scenario.get('purpose', 'Build a workflow to monitor H&M product page for size 24 availability')

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
