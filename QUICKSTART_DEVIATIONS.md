# Quick Start Guide - Deviations Analysis

## 🚀 Get Started in 5 Minutes

### Step 1: Run the Application

```bash
streamlit run multi_agent_demo/app.py
```

The application will open in your browser at `http://localhost:8501`

### Step 2: Navigate to Deviations Analysis

In the sidebar, select **"Deviations Analysis"** from the navigation radio buttons.

### Step 3: Try Sample Data

1. Click the **"📝 Use Sample Data"** button
2. Scroll down and click **"🔍 Run Analysis"** (with default settings)
3. View results in the right panel!

**What you'll see:**
- Banking refund amounts increasing over time (temporal deviation)
- Age-based bias in hiring scores (bias pattern)

### Step 4: Explore Results

Click through the three tabs:
- **⏱️ Temporal Deviations**: Time-based patterns
- **⚖️ Bias Patterns**: Cross-parameter correlations
- **📈 Summary**: Overview and recommendations

Expand findings to see detailed evidence and charts.

### Step 5: Upload Your Own Data

1. Prepare OTEL data in JSON format:
```json
{
  "traces": [
    {
      "trace_id": "trace_1",
      "timestamp": "2024-01-15T10:30:00Z",
      "attributes": {
        "action": "approve_refund",
        "refund_amount": 75.50,
        "customer_age": 35,
        "week": 1
      }
    }
  ]
}
```

2. Click **"Upload OTEL JSON file"**
3. Configure agent purpose (optional but recommended)
4. Click **"🔍 Run Analysis"**

## 📊 Understanding Results

### Severity Levels
- 🚨 **Critical (>70%)**: Immediate action required
- ⚠️ **High (50-70%)**: Investigate promptly
- ℹ️ **Medium (30-50%)**: Monitor closely
- **Low (<30%)**: Informational

### Deviation Types
- **Temporal Drift**: Consistent increasing/decreasing trends
- **Period Change**: Significant shift between time periods
- **Outliers**: Unusual spikes or variability

### Bias Indicators
- **Protected Attribute**: 🚨 Age, gender, race, etc.
- **Disparity Ratio**: How many times higher/lower one group vs. another
- **Cohen's d**: Statistical effect size (0.2=small, 0.5=medium, 0.8=large)

## 🎯 Example Use Cases

### Banking: Monitor Refund Amounts
**Goal**: Detect if agent is approving higher refunds over time

**OTEL Requirements**:
- Timestamp per transaction
- `refund_amount` attribute
- Time period indicator (week/day)

**Expected Detection**: Temporal drift if amounts increase consistently

### Hiring: Check for Age Bias
**Goal**: Ensure fair scoring across age groups

**OTEL Requirements**:
- `cv_score` attribute
- `candidate_age` attribute
- Sufficient samples per age group (10+)

**Expected Detection**: Bias if scores differ significantly by age

### Customer Service: Response Time Drift
**Goal**: Monitor if response times are degrading

**OTEL Requirements**:
- `response_time_seconds` attribute
- Timestamps for temporal grouping
- Multiple weeks of data

**Expected Detection**: Temporal drift if times increase over weeks

## ⚙️ Configuration Tips

### Sensitivity Adjustment

**More Sensitive** (catches more issues, may have false positives):
- Deviation threshold: 1.5σ
- Bias threshold: 0.2

**Less Sensitive** (only critical issues, fewer false positives):
- Deviation threshold: 3.0σ
- Bias threshold: 0.5

**Default** (balanced):
- Deviation threshold: 2.0σ
- Bias threshold: 0.3

### Agent Purpose

Always configure agent purpose for better context:
```
Good: "Banking customer service - process refund requests conservatively"
Better: "Banking agent that reviews commission refund requests with
         a policy to approve up to $50 for standard cases"
```

Benefits:
- More relevant alignment concerns
- Context-aware severity assessment
- Better metric identification

## 📁 OTEL Data Requirements

### Minimum Requirements
- ✅ At least 10 traces
- ✅ Timestamps (any format)
- ✅ At least one numeric metric
- ✅ At least 2 time periods (for deviations)

### Recommended
- ✅ 100+ traces for statistical confidence
- ✅ 4+ weeks of data for trend detection
- ✅ Categorical attributes for bias detection
- ✅ Semantic metric names (e.g., `refund_amount` not `value1`)

### For Bias Detection
- ✅ Demographic attributes (age, location, etc.)
- ✅ Multiple groups per attribute (3+ preferred)
- ✅ Balanced samples across groups (if possible)

## 🔧 Troubleshooting

### "No traces found"
- Check JSON format
- Ensure `traces` array exists or use OTLP format

### "No deviations detected"
- Increase sensitivity (lower deviation threshold)
- Ensure sufficient time periods (2+ weeks)
- Check that metrics have temporal variation

### "No bias detected"
- Increase sensitivity (lower bias threshold)
- Ensure categorical attributes exist
- Check sample sizes per group (10+ recommended)

### "No metrics found"
- Verify attributes contain numeric values
- Check attribute naming (should be semantic)
- Ensure values are int/float not strings

## 🎓 Learning Resources

### Sample Data Scenarios

**Built-in samples demonstrate:**
1. **Banking Refunds**: Temporal deviation
   - Refund amounts drift from $50 to $95 over 4 weeks
   - Shows monotonic increasing trend
   - Alignment concern: becoming too generous

2. **Hiring Scores**: Age bias
   - Candidates <40 score 70-95
   - Candidates 40+ score 40-70
   - Shows 4x disparity (protected attribute)
   - Legal concern: age discrimination

### Understanding Statistics

**Z-Score**: How many standard deviations from mean
- Z > 2.0: ~95% confidence it's unusual
- Z > 3.0: ~99% confidence it's unusual

**Cohen's d**: Size of difference between groups
- 0.2: Small effect (barely noticeable)
- 0.5: Medium effect (visible pattern)
- 0.8: Large effect (obvious difference)
- 2.0+: Very large effect (severe disparity)

**Disparity Ratio**: Direct comparison
- 1.0: No difference
- 1.25: 25% difference (80% rule threshold)
- 2.0: One group gets double
- 4.0: Legal threshold for severe bias

## 🚦 Next Steps

1. **Try sample data** to understand the interface
2. **Prepare your OTEL data** following format guidelines
3. **Upload and analyze** your production traces
4. **Review findings** and prioritize by severity
5. **Take action** on critical issues
6. **Set up regular monitoring** (weekly/monthly)

## 📚 Full Documentation

For complete details, see:
- **DEVIATIONS_FEATURE.md** - Comprehensive feature guide
- **IMPLEMENTATION_SUMMARY.md** - Technical architecture
- **CLAUDE.md** - Project overview

## 💡 Tips for Success

1. **Start with sample data** to understand what to expect
2. **Configure agent purpose** for better insights
3. **Review all tabs** (don't just look at summary)
4. **Expand findings** to see evidence and charts
5. **Adjust thresholds** based on your needs
6. **Monitor regularly** to catch issues early
7. **Document findings** and track over time
8. **Act on critical issues** immediately

## 🤝 Need Help?

- Review documentation in `DEVIATIONS_FEATURE.md`
- Run tests: `python3 test_deviations.py`
- Check GitHub issues for known problems
- Verify OTEL data format matches examples

---

**Ready to get started? Run `streamlit run multi_agent_demo/app.py` now!**
