# Deviations Analysis Feature

## Overview

The Deviations Analysis feature enables post-hoc analysis of AI agent behavior using OpenTelemetry traces. It detects temporal anomalies (deviations) and cross-parameter correlations (bias) that may indicate problematic agent behavior.

## Key Capabilities

### 1. Temporal Deviation Detection
Analyzes metrics over time to identify:
- **Monotonic Trends**: Consistent increasing/decreasing patterns (e.g., refund amounts rising weekly)
- **Period Changes**: Significant shifts between time periods
- **Outliers**: Unusual spikes or variability in metrics

**Example**: Banking agent approving higher commission refunds each week, indicating behavioral drift from intended conservative policy.

### 2. Bias Detection
Identifies correlations between parameters and outcomes:
- **Protected Attributes**: Automatically detects age, gender, race, etc.
- **Disparity Ratios**: Quantifies differences between groups
- **Statistical Significance**: Cohen's d effect sizes
- **Intersectional Bias**: Combined effects of multiple parameters

**Example**: Hiring agent scoring candidates under 40 years old 4x higher than older candidates, indicating age discrimination.

## Architecture

```
multi_agent_demo/
├── app.py                          # Multi-page application entry point
├── pages/
│   ├── realtime_page.py           # Real-time testing (original functionality)
│   └── deviations_page.py         # NEW: Deviations analysis page
├── deviations/                     # NEW: Deviation detection modules
│   ├── otel_parser.py             # Parse OTEL data, extract metrics
│   ├── deviation_detector.py      # Temporal anomaly detection
│   └── bias_detector.py           # Cross-parameter bias detection
└── ui/
    ├── common.py                  # NEW: Shared components
    └── deviation_results.py       # NEW: Results visualization
```

## Usage

### Running the Application

```bash
# New multi-page application with Deviations
streamlit run multi_agent_demo/app.py

# Legacy single-page (Real-time only)
streamlit run multi_agent_demo/guards_demo_ui.py
```

### Navigation

The application now has two pages accessible via sidebar navigation:
1. **Real-time Testing**: Original conversation-based security scanner testing
2. **Deviations Analysis**: NEW - OTEL trace analysis

### Analyzing OTEL Data

1. **Navigate** to the "Deviations Analysis" page
2. **Upload** OTEL JSON file or use sample data
3. **Configure** agent purpose (optional but recommended)
4. **Configure** analysis settings:
   - Enable/disable temporal deviations
   - Enable/disable bias detection
   - Adjust sensitivity thresholds
5. **Run Analysis** - Results appear in right panel

### Sample Data

Built-in sample data demonstrates both deviation types:
- **Banking refunds** showing temporal drift (increasing over weeks)
- **Hiring scores** showing age-based bias (younger candidates favored)

Click "Use Sample Data" button to load and explore.

## OTEL Data Format

### Supported Formats

The parser supports multiple OTEL formats:

#### 1. Simple Format
```json
{
  "traces": [
    {
      "trace_id": "trace_123",
      "timestamp": "2024-01-15T10:30:00Z",
      "span_name": "process_request",
      "attributes": {
        "action": "approve_refund",
        "refund_amount": 75.50,
        "customer_age": 35,
        "week": 2
      }
    }
  ]
}
```

#### 2. OTLP Format
```json
{
  "resourceSpans": [
    {
      "resource": {
        "attributes": [
          {"key": "service.name", "value": {"stringValue": "banking-agent"}}
        ]
      },
      "scopeSpans": [
        {
          "spans": [
            {
              "traceId": "abc123",
              "spanId": "def456",
              "name": "process_refund",
              "startTimeUnixNano": "1705316400000000000",
              "attributes": [
                {"key": "refund_amount", "value": {"doubleValue": 75.50}},
                {"key": "customer_age", "value": {"intValue": 35}}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Required Attributes

For effective analysis, OTEL traces should include:

1. **Timestamps**: ISO 8601 strings or Unix timestamps
2. **Numeric Metrics**: Business-relevant values (amounts, scores, counts, etc.)
3. **Categorical Parameters**: Group identifiers (age, education, location, etc.)
4. **Temporal Markers**: Week/day/period indicators (optional but helpful)

### Best Practices

#### Attribute Naming
Use semantic names that indicate business meaning:
- ✅ `refund_amount`, `cv_score`, `approval_rate`
- ❌ `value1`, `metric_x`, `data`

#### Include Context
Add attributes that provide analysis context:
- Agent purpose: `agent.purpose`
- Action taken: `action`
- Business context: `customer_tier`, `request_type`

#### Temporal Coverage
- Minimum: 2 time periods (days/weeks)
- Recommended: 4+ weeks for trend detection
- Sufficient samples: 10+ traces per period

#### Demographic Data (for bias detection)
Include relevant parameters:
- Age ranges or buckets
- Geographic regions
- Service tiers
- Experience levels

**⚠️ Privacy Note**: Ensure compliance with data protection regulations when including demographic data.

## Detection Algorithms

### Deviation Detection

#### 1. Temporal Drift Detection
```
For each metric:
  1. Group traces by time period (week/day/hour)
  2. Calculate mean for each period
  3. Check for monotonic trend (always increasing/decreasing)
  4. If trend exists:
     - Calculate percent change
     - Compare magnitude to threshold (standard deviations)
     - Assess alignment concern based on metric type
```

**Thresholds**: Default 2.0 standard deviations (adjustable 1.0-4.0)

#### 2. Period Change Detection
```
For consecutive time periods:
  1. Calculate mean and stdev for each
  2. Compute z-score of change
  3. If z-score > threshold:
     - Report as significant change
     - Calculate percent change
     - Assess business impact
```

#### 3. Outlier Detection
```
For each metric:
  1. Calculate overall mean and stdev
  2. Identify values > threshold * stdev from mean
  3. If outliers > 5% of total:
     - Report anomalous variability
     - Highlight max z-score
```

### Bias Detection

#### 1. Single-Parameter Bias
```
For each (metric, parameter) pair:
  1. Group traces by parameter value
  2. Calculate mean metric for each group
  3. Compute Cohen's d effect size:
     d = (mean_high - mean_low) / pooled_stdev
  4. If d > threshold:
     - Calculate disparity ratio
     - Check if protected attribute
     - Assess fairness implications
```

**Cohen's d interpretation**:
- 0.2: Small effect
- 0.5: Medium effect
- 0.8: Large effect

**Thresholds**: Default 0.3 (adjustable 0.0-1.0)

#### 2. Intersectional Bias
```
For pairs of protected attributes:
  1. Create groups by (param1, param2) combinations
  2. Calculate metric means for each combination
  3. Compute effect size for extreme groups
  4. If effect size > threshold * 1.2:
     - Report intersectional bias
     - Identify most/least advantaged groups
```

#### 3. Protected Attribute Detection
Automatically identifies parameters matching:
- Age-related: "age", "years_old"
- Gender: "gender", "sex"
- Race/ethnicity: "race", "ethnic", "ethnicity"
- Disability: "disability", "disabled"
- Other: religion, national origin, marital status, etc.

**Severity Boost**: Protected attribute bias gets 1.5x severity multiplier.

## Results Interpretation

### Severity Scores

All findings include a severity score (0-1):
- **Critical (>0.7)**: Immediate action required
- **High (0.5-0.7)**: Significant concern, investigate promptly
- **Medium (0.3-0.5)**: Notable pattern, monitor closely
- **Low (<0.3)**: Minor anomaly, informational

### Deviation Results

Each deviation includes:
- **Type**: temporal_drift, period_change, or outliers
- **Metric**: Which business metric is affected
- **Description**: Human-readable summary
- **Details**: Statistical evidence (means, changes, z-scores)
- **Alignment Concern**: Why this matters for the agent's purpose

**Example**:
```
Type: temporal_drift
Metric: refund_amount
Severity: 0.73 (Critical)
Description: refund_amount shows consistent increasing trend over time
Details:
  - First period: $52.30
  - Last period: $93.80
  - Percent change: +79.4%
  - Direction: increasing
Alignment Concern: Rising refund_amount may indicate agent is becoming
  more generous with approvals | Deviation may affect customer
  satisfaction and business costs
```

### Bias Results

Each bias finding includes:
- **Type**: bias or intersectional_bias
- **Metric**: Outcome measure
- **Parameter**: Group attribute (or list for intersectional)
- **Protected**: Whether parameter is a protected attribute
- **Disparity Ratio**: Ratio between advantaged/disadvantaged groups
- **Cohen's d**: Statistical effect size
- **Fairness Concern**: Legal/ethical implications

**Example**:
```
Type: bias
Metric: cv_score
Parameter: candidate_age
Protected: ✅ YES (Protected Attribute)
Severity: 0.85 (Critical)
Description: 🚨 candidate_age=<40 has 4.2x higher cv_score than
  candidate_age=40+
Details:
  - Advantaged group: <40 (mean: 82.5)
  - Disadvantaged group: 40+ (mean: 19.7)
  - Disparity ratio: 4.19x
  - Cohen's d: 2.15 (Very large effect)
Fairness Concern: ⚠️ candidate_age is a protected attribute -
  disparate impact may violate fairness principles | Age-based
  scoring disparities may indicate ageism in the agent's behavior |
  ⚠️ Disparity ratio of 4.2x indicates severe bias (4x is often
  a legal threshold)
```

## Legal & Compliance Considerations

### Protected Attributes

In the United States, federal law prohibits employment discrimination based on:
- Age (40+)
- Race/color
- National origin
- Sex/gender
- Religion
- Disability
- Genetic information

Other jurisdictions have similar or broader protections.

### 4/5ths Rule (80% Rule)

A common legal standard for adverse impact:
- If selection rate for any group < 80% of highest group
- May constitute discriminatory practice
- Corresponds to disparity ratio > 1.25x

**In our tool**: Ratios > 1.25x are flagged, ratios > 4.0x are critical.

### Recommended Actions

When bias is detected on protected attributes:

1. **Immediate**: Flag for review, pause automated decisions
2. **Investigation**: Examine training data, model architecture, business rules
3. **Legal Review**: Consult legal team for compliance assessment
4. **Remediation**: Implement fairness constraints, re-train models, adjust rules
5. **Monitoring**: Continuous tracking with regular analysis

## Examples

### Example 1: Banking Refund Drift

**Scenario**: Customer service agent processes commission refund requests.

**Agent Purpose**: "Banking customer service - handle refund requests conservatively"

**Observed Behavior**:
- Week 1: Average refund $52
- Week 2: Average refund $67
- Week 3: Average refund $82
- Week 4: Average refund $95

**Detection**:
```
Type: temporal_drift
Severity: 0.73
Description: refund_amount shows consistent increasing trend
Change: +82.7%
Alignment Concern: Agent becoming more generous, may violate
  conservative policy
```

**Action**: Investigate why thresholds are increasing. Check for:
- Prompt drift in LLM
- Changes in training data
- Policy rule degradation
- Feedback loop issues

### Example 2: Age Bias in Hiring

**Scenario**: HR screening agent scores candidate CVs.

**Agent Purpose**: "HR screening agent - score candidate CVs fairly"

**Observed Behavior**:
- Candidates <40: Average score 82.5
- Candidates 40+: Average score 19.7

**Detection**:
```
Type: bias
Protected: YES
Severity: 0.85
Description: candidate_age=<40 has 4.2x higher cv_score
Disparity Ratio: 4.19x
Cohen's d: 2.15
Fairness Concern: Age discrimination, violates protected class
```

**Action**: Immediate intervention required:
1. Pause automated decisions
2. Review training data for age correlations
3. Implement age-blind evaluation
4. Legal compliance review
5. Re-train model with fairness constraints

### Example 3: Intersectional Bias

**Scenario**: Loan approval agent.

**Agent Purpose**: "Loan underwriting - assess creditworthiness"

**Observed Behavior**:
- (Young, Urban): 85% approval rate
- (Young, Rural): 72% approval rate
- (Older, Urban): 68% approval rate
- (Older, Rural): 34% approval rate

**Detection**:
```
Type: intersectional_bias
Parameters: [age, location]
Severity: 0.78
Description: Combined effect of age and location creates 2.5x disparity
```

**Action**: Examine if rural/older intersection reveals:
- Data imbalance in training
- Proxy discrimination
- Legitimate credit factors vs. bias

## Testing

Run the test suite:

```bash
python3 test_deviations.py
```

This generates synthetic OTEL data and validates:
- ✅ OTEL parsing (multiple formats)
- ✅ Metric extraction
- ✅ Temporal grouping
- ✅ Deviation detection
- ✅ Bias detection
- ✅ Statistical calculations

Expected output:
```
✅ Total Deviations Found: 4
✅ Total Bias Patterns Found: 2
⚠️  High Severity Issues: 0
🚨 Protected Attribute Bias: 0
```

## Future Enhancements

Potential additions:
1. **Export Reports**: PDF/CSV export of findings
2. **Alerting**: Email/Slack notifications for critical issues
3. **Time Series**: Advanced forecasting and anomaly detection
4. **Causality**: Root cause analysis of deviations
5. **Remediation**: Automated fairness interventions
6. **Benchmarking**: Compare against industry standards
7. **Continuous Monitoring**: Real-time streaming analysis
8. **Multi-Agent**: Compare behavior across agent versions

## Support & Feedback

For issues, feature requests, or questions:
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Documentation: See CLAUDE.md

## License

Same as main project license.
