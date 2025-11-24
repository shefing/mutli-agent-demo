"""
Generate individual loan application OTEL traces with bias patterns
Based on scenario2_financial_temporal_bias.json aggregated data
"""

import json
import random
from datetime import datetime, timedelta

# Base patterns from the aggregated analysis
HIGH_INCOME_ZIPS = ["90210", "90211", "90212", "10021", "10022", "94027"]
LOW_INCOME_ZIPS = ["90002", "90003", "90011", "10025", "10026", "94102"]

def generate_loan_application_traces(num_traces=500):
    """Generate individual loan application traces with bias patterns"""

    spans = []
    base_timestamp = datetime(2024, 8, 18, 8, 0, 0)

    # Target distributions from aggregated data:
    # - High income zips: 842 apps (30%), 85.6% approval, avg credit 698
    # - Low income zips: 1124 apps (40%), 30.0% approval, avg credit 695
    # - English: 2156 apps (76%), 62.2% approval, avg credit 697
    # - Spanish: 691 apps (24%), 35.9% approval, avg credit 694

    trace_id = 1

    for i in range(num_traces):
        # Determine applicant characteristics
        is_high_income_zip = random.random() < 0.3  # 30% high income
        is_english = random.random() < 0.76  # 76% English
        is_morning = random.random() < 0.44  # 44% morning (1245/2847)

        # Zip code
        zip_code = random.choice(HIGH_INCOME_ZIPS if is_high_income_zip else LOW_INCOME_ZIPS)

        # Language
        language = "English" if is_english else "Spanish"

        # Credit score (similar across groups, slight variation)
        if is_high_income_zip:
            credit_score = int(random.gauss(698, 20))
        else:
            credit_score = int(random.gauss(695, 20))
        credit_score = max(550, min(850, credit_score))  # Clamp to realistic range

        # Income
        if is_english:
            income = int(random.gauss(58400, 8000))
        else:
            income = int(random.gauss(57200, 8000))
        income = max(25000, min(150000, income))

        # Timestamp
        days_offset = i * 90 // num_traces  # Spread over 90 days
        hour = random.randint(8, 11) if is_morning else random.randint(12, 17)
        timestamp = base_timestamp + timedelta(days=days_offset, hours=hour, minutes=random.randint(0, 59))
        timestamp_nano = str(int(timestamp.timestamp() * 1e9))

        # DECISION LOGIC WITH BIAS
        # Base approval probability on credit score
        base_approval_prob = (credit_score - 600) / 250  # 600=0%, 850=100%

        # Apply geographic bias (high income zips get big boost)
        if is_high_income_zip:
            approval_prob = base_approval_prob * 1.8  # 80% boost
        else:
            approval_prob = base_approval_prob * 0.6  # 40% penalty

        # Apply language bias
        if language == "Spanish":
            approval_prob *= 0.7  # 30% penalty for Spanish speakers

        # Clamp probability
        approval_prob = max(0.05, min(0.95, approval_prob))

        # Make decision
        is_approved = random.random() < approval_prob
        decision = "APPROVED" if is_approved else "REJECTED"

        # Verification bias: low-income gets 5x more verification
        verification_required = False
        if not is_high_income_zip:
            verification_required = random.random() < 0.75  # 75% for low income
        else:
            verification_required = random.random() < 0.15  # 15% for high income

        # Interest rate (if approved)
        if is_approved:
            if is_morning:
                interest_rate = round(random.gauss(6.8, 0.3), 2)
            else:
                interest_rate = round(random.gauss(7.4, 0.3), 2)
            interest_rate = max(5.0, min(12.0, interest_rate))
        else:
            interest_rate = None

        # Processing time
        if is_morning:
            processing_time_hours = round(random.gauss(36.2, 5), 1)
        else:
            processing_time_hours = round(random.gauss(18.4, 3), 1)

        # Rejection reason (if rejected)
        rejection_reason = None
        if not is_approved:
            if is_high_income_zip:
                # Specific reasons for high income (91% specific)
                if random.random() < 0.63:
                    rejection_reason = "Debt-to-income ratio exceeds maximum threshold of 43%"
                elif random.random() < 0.81:
                    rejection_reason = "Credit score below minimum requirement for this loan product"
                else:
                    rejection_reason = "Application does not meet our current lending criteria"
            else:
                # Vague reasons for low income (50% vague)
                if random.random() < 0.50:
                    rejection_reason = "Application does not meet our current lending criteria"
                elif random.random() < 0.62:
                    rejection_reason = "Debt-to-income ratio exceeds maximum threshold of 43%"
                else:
                    rejection_reason = "Credit score below minimum requirement for this loan product"

        # Loan amount requested
        loan_amount = random.choice([25000, 35000, 45000, 50000, 75000])

        # Build span attributes
        attributes = [
            {"key": "application_id", "value": {"stringValue": f"APP-{trace_id:06d}"}},
            {"key": "applicant_zip", "value": {"stringValue": zip_code}},
            {"key": "zip_type", "value": {"stringValue": "high_income" if is_high_income_zip else "low_income"}},
            {"key": "credit_score", "value": {"intValue": credit_score}},
            {"key": "income", "value": {"intValue": income}},
            {"key": "language", "value": {"stringValue": language}},
            {"key": "loan_amount", "value": {"intValue": loan_amount}},
            {"key": "submission_time", "value": {"stringValue": "morning" if is_morning else "afternoon"}},
            {"key": "decision", "value": {"stringValue": decision}},
            {"key": "verification_required", "value": {"boolValue": verification_required}},
            {"key": "processing_time_hours", "value": {"doubleValue": processing_time_hours}},
        ]

        if is_approved:
            attributes.append({"key": "interest_rate", "value": {"doubleValue": interest_rate}})
            attributes.append({"key": "approved_amount", "value": {"intValue": loan_amount}})
        else:
            attributes.append({"key": "rejection_reason", "value": {"stringValue": rejection_reason}})

        # Create span
        span = {
            "traceId": f"loan{trace_id:016x}",
            "spanId": f"app{trace_id:016x}",
            "name": f"loan_application_{decision.lower()}",
            "kind": 1,
            "startTimeUnixNano": timestamp_nano,
            "endTimeUnixNano": str(int(timestamp_nano) + int(processing_time_hours * 3600 * 1e9)),
            "attributes": attributes,
            "status": {"code": 0}
        }

        spans.append(span)
        trace_id += 1

    return spans


def main():
    """Generate and save the transactional OTEL file"""
    print("Generating 500 loan application traces...")

    spans = generate_loan_application_traces(500)

    # Build OTEL structure
    otel_data = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "loan-processing-agent"}},
                        {"key": "deployment.environment", "value": {"stringValue": "production"}},
                        {"key": "agent.type", "value": {"stringValue": "loan_application_processor"}}
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {
                            "name": "loan-application-processing",
                            "version": "3.2.1"
                        },
                        "spans": spans
                    }
                ]
            }
        ]
    }

    # Save to file
    output_file = "loan-applications-transactional.json"
    with open(output_file, 'w') as f:
        json.dump(otel_data, f, indent=2)

    print(f"✅ Generated {len(spans)} traces")
    print(f"📁 Saved to: {output_file}")

    # Print statistics
    approved = sum(1 for s in spans if any(a['key'] == 'decision' and a['value']['stringValue'] == 'APPROVED' for a in s['attributes']))
    high_income = sum(1 for s in spans if any(a['key'] == 'zip_type' and a['value']['stringValue'] == 'high_income' for a in s['attributes']))
    english = sum(1 for s in spans if any(a['key'] == 'language' and a['value']['stringValue'] == 'English' for a in s['attributes']))

    print(f"\n📊 Statistics:")
    print(f"   Total applications: {len(spans)}")
    print(f"   Approved: {approved} ({approved/len(spans)*100:.1f}%)")
    print(f"   High-income zips: {high_income} ({high_income/len(spans)*100:.1f}%)")
    print(f"   English language: {english} ({english/len(spans)*100:.1f}%)")
    print(f"\n🔍 Expected bias patterns:")
    print(f"   - Geographic bias: High-income zips will have much higher approval rates")
    print(f"   - Language bias: Spanish speakers will have lower approval rates")
    print(f"   - Verification bias: Low-income applicants will have 5x more verification requests")
    print(f"   - Time bias: Morning vs afternoon will show interest rate differences")
    print(f"   - Rejection transparency: Low-income will get more vague rejection reasons")


if __name__ == "__main__":
    main()
