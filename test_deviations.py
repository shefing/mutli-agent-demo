#!/usr/bin/env python3
"""
Test script for deviation and bias detection
Tests the core functionality without requiring Streamlit
"""

import json
from datetime import datetime, timedelta
import random

# Import our modules
from multi_agent_demo.deviations import parse_otel_data, detect_deviations, detect_bias


def generate_test_otel_data():
    """Generate test OTEL data with known deviations and bias"""
    print("\n" + "="*80)
    print("GENERATING TEST OTEL DATA")
    print("="*80)

    base_time = datetime.now() - timedelta(days=30)
    traces = []

    # Banking commission refund example (showing deviation over time)
    print("\n1. Generating banking refund data with temporal deviation...")
    for week in range(4):
        for day in range(7):
            for i in range(random.randint(5, 15)):
                timestamp = base_time + timedelta(weeks=week, days=day, hours=random.randint(0, 23))

                # Average refund increases over weeks (deviation pattern)
                base_refund = 50 + (week * 15)  # $50 -> $95 over 4 weeks
                refund_amount = base_refund + random.uniform(-10, 10)

                trace = {
                    "trace_id": f"trace_{week}_{day}_{i}",
                    "timestamp": timestamp.isoformat(),
                    "span_name": "process_refund_request",
                    "attributes": {
                        "agent.purpose": "Banking customer service - handle refund requests",
                        "action": "approve_commission_refund",
                        "refund_amount": round(refund_amount, 2),
                        "week": week + 1,
                        "customer_age": random.randint(25, 65),
                        "customer_tenure_years": random.randint(1, 20)
                    }
                }
                traces.append(trace)

    print(f"   ✅ Generated {len([t for t in traces if 'refund_amount' in t['attributes']])} refund traces")

    # Hiring CV scoring example (showing bias pattern)
    print("\n2. Generating hiring data with age bias...")
    hiring_traces = 0
    for i in range(100):
        age = random.randint(22, 60)
        # Bias: people under 40 get higher scores
        if age < 40:
            base_score = random.uniform(70, 95)
        else:
            base_score = random.uniform(40, 70)

        timestamp = base_time + timedelta(days=random.randint(0, 28))

        trace = {
            "trace_id": f"hiring_trace_{i}",
            "timestamp": timestamp.isoformat(),
            "span_name": "score_candidate",
            "attributes": {
                "agent.purpose": "HR screening agent - score candidate CVs",
                "action": "calculate_cv_score",
                "cv_score": round(base_score, 2),
                "candidate_age": age,
                "years_experience": random.randint(0, 30),
                "education_level": random.choice(["Bachelor", "Master", "PhD"])
            }
        }
        traces.append(trace)
        hiring_traces += 1

    print(f"   ✅ Generated {hiring_traces} hiring traces")
    print(f"\n📊 Total traces: {len(traces)}")

    return {"traces": traces}


def test_parser(otel_data):
    """Test OTEL parser"""
    print("\n" + "="*80)
    print("TESTING OTEL PARSER")
    print("="*80)

    parsed_data = parse_otel_data(otel_data)

    print(f"\n✅ Parsed {parsed_data['trace_count']} traces")
    print(f"✅ Found {len(parsed_data['metrics'])} numeric metrics:")
    for metric_name, values in list(parsed_data['metrics'].items())[:5]:
        print(f"   - {metric_name}: {len(values)} values")

    print(f"\n✅ Found {len(parsed_data['attributes'])} attributes")
    print(f"✅ Temporal groups: {len(parsed_data['temporal_groups']['by_week'])} weeks")
    print(f"✅ Parameter groups: {len(parsed_data['parameter_groups'])} parameters")

    return parsed_data


def test_deviation_detection(parsed_data):
    """Test deviation detection"""
    print("\n" + "="*80)
    print("TESTING DEVIATION DETECTION")
    print("="*80)

    agent_purpose = "Banking customer service - handle refund requests"

    deviations = detect_deviations(
        parsed_data,
        threshold=2.0,
        agent_purpose=agent_purpose
    )

    print(f"\n✅ Found {len(deviations)} deviations")

    for i, deviation in enumerate(deviations[:3], 1):
        print(f"\n{i}. {deviation['type'].upper()}")
        print(f"   Metric: {deviation['metric']}")
        print(f"   Severity: {deviation['severity_score']:.2%}")
        print(f"   Description: {deviation['description']}")

        if 'details' in deviation:
            details = deviation['details']
            if 'percent_change' in details:
                print(f"   Change: {details['percent_change']:.1f}%")
            if 'direction' in details:
                print(f"   Direction: {details['direction']}")

    return deviations


def test_bias_detection(parsed_data):
    """Test bias detection"""
    print("\n" + "="*80)
    print("TESTING BIAS DETECTION")
    print("="*80)

    agent_purpose = "HR screening agent - score candidate CVs"

    bias_results = detect_bias(
        parsed_data,
        threshold=0.3,
        agent_purpose=agent_purpose
    )

    print(f"\n✅ Found {len(bias_results)} bias patterns")

    for i, bias in enumerate(bias_results[:3], 1):
        print(f"\n{i}. {'PROTECTED ATTRIBUTE' if bias.get('is_protected_attribute') else 'BIAS'}")
        print(f"   Metric: {bias['metric']}")
        if bias['type'] == 'intersectional_bias':
            print(f"   Parameters: {', '.join(bias['parameters'])}")
        else:
            print(f"   Parameter: {bias['parameter']}")
        print(f"   Severity: {bias['severity_score']:.2%}")
        print(f"   Description: {bias['description']}")

        details = bias.get('details', {})
        if 'disparity_ratio' in details:
            print(f"   Disparity Ratio: {details['disparity_ratio']:.2f}x")
        if 'cohens_d' in details:
            print(f"   Effect Size: {details['cohens_d']:.2f}")

    return bias_results


def main():
    """Main test function"""
    print("\n" + "="*80)
    print("DEVIATION & BIAS DETECTION TEST SUITE")
    print("="*80)

    try:
        # Generate test data
        otel_data = generate_test_otel_data()

        # Test parser
        parsed_data = test_parser(otel_data)

        # Test deviation detection
        deviations = test_deviation_detection(parsed_data)

        # Test bias detection
        bias_results = test_bias_detection(parsed_data)

        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"\n✅ Total Deviations Found: {len(deviations)}")
        print(f"✅ Total Bias Patterns Found: {len(bias_results)}")

        high_severity = sum(1 for r in deviations + bias_results if r['severity_score'] > 0.7)
        print(f"⚠️  High Severity Issues: {high_severity}")

        protected_bias = sum(1 for b in bias_results if b.get('is_protected_attribute', False))
        print(f"🚨 Protected Attribute Bias: {protected_bias}")

        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)

        return True

    except Exception as e:
        print("\n" + "="*80)
        print("❌ TEST FAILED")
        print("="*80)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
