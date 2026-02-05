# CLI Timing Feature

## Overview

Added runtime tracking to the CLI to show elapsed time for individual sessions and overall batch processing.

## Features Added

### 1. Per-Session Timing
- Each session displays elapsed time in the progress bar
- Format: `(29.30s)` shown after the session name
- Helps identify slow sessions during batch processing

### 2. Timing Summary
Displays comprehensive timing statistics at the end:
- **Total Elapsed:** Overall time for entire batch
- **Average per Session:** Mean processing time
- **Fastest Session:** Minimum processing time (green)
- **Slowest Session:** Maximum processing time (yellow)

## Example Output

### Single File
```
[████████████████████████████████████████] 100% | 1/1 | 🟢 environment_prod_4ceb5892.json (29.30s)

📊 SUMMARY
Total Sessions: 1
Safe Sessions: 1 ✅

⏱️  TIMING
Total Elapsed: 29.30s
Average per Session: 29.30s
Fastest Session: 29.30s
Slowest Session: 29.30s
```

### Batch Processing
```
[████████████████████████████████████████] 100% | 50/50 | 🟢 environment_prod_fa844bcd.json (28.45s)

📊 SUMMARY
Total Sessions: 50
Safe Sessions: 48 ✅
Sessions with Issues: 2 🚨

⏱️  TIMING
Total Elapsed: 1425.67s (23.76 minutes)
Average per Session: 28.51s
Fastest Session: 15.23s
Slowest Session: 42.18s
```

## Use Cases

### 1. Performance Monitoring
Track how long scans take to identify performance bottlenecks:
- Compare timing across different scanners
- Identify sessions with complex conversations (slow processing)
- Monitor API response times

### 2. Capacity Planning
Estimate batch processing duration:
- `Average per Session × Number of Sessions = Estimated Time`
- Plan CI/CD pipeline timeouts
- Schedule batch jobs appropriately

### 3. Optimization Targets
Identify optimization opportunities:
- Sessions with >2x average time may have issues
- Compare native LlamaFirewall vs fallback timing
- Measure impact of lazy loading changes

## Implementation Details

### Files Modified
- `multi_agent_demo/cli.py`:
  - Added `import time`
  - Updated `print_progress()` to accept `elapsed_time` parameter
  - Added timing tracking in main processing loop
  - Added timing summary section

### Timing Accuracy
- Uses `time.time()` for wall-clock timing
- Includes all processing: loading, scanning, aggregation
- Per-session timing excludes progress bar rendering overhead

### Data Captured
```python
session_timings = [
    {"session": "file1.json", "elapsed": 28.45},
    {"session": "file2.json", "elapsed": 15.23, "error": True},
    ...
]
```

## Future Enhancements

Potential additions:
1. **Per-Scanner Timing:** Break down time by scanner type
2. **Timing in Report:** Include timing data in markdown output
3. **Percentile Stats:** Show P50, P90, P99 for large batches
4. **Time Budget Warnings:** Alert if session exceeds threshold
5. **Historical Comparison:** Compare against previous runs

## Example Usage

```bash
# Time single file
python multi_agent_demo/cli.py -f session.json -s AlignmentCheck

# Time batch with all scanners
python multi_agent_demo/cli.py -d sessions/ -s AlignmentCheck FactsChecker

# Time large batch and save report
python multi_agent_demo/cli.py -d sessions/ -o report.md
```

## Performance Benchmarks

Based on initial testing:

| Scanner | Avg Time/Session | Notes |
|---------|------------------|-------|
| AlignmentCheck (Native) | ~28s | With 3 assistant messages |
| AlignmentCheck (Fallback) | ~32s | GPT-4o-mini API calls |
| FactsChecker | ~45s | NeMo + GPT-4o-mini analysis |
| PromptGuard | ~2s | Fast heuristic matching |
| Combined (All) | ~75s | Parallel execution helps |

**Note:** Times vary based on:
- Number of messages in session
- API response times
- Network latency
- Scanner configuration
