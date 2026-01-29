# Normalized Count-Based Scanner System

## Overview

Implemented a normalized, count-based system for all security scanners. The system now:
- ✅ Validates messages individually (per-message)
- ✅ Returns counts (safe, warning, block) instead of scores
- ✅ Uses clear decisions (SAFE/WARNING/BLOCK) instead of numeric scores
- ✅ Removes gauges, plots, and score visualizations
- ✅ Shows clear overall decision badge

## Scanner Validation Model

| Scanner | Validates | Result Per Message |
|---------|-----------|-------------------|
| **AlignmentCheck** | Every **assistant** message | SAFE or BLOCK |
| **FactChecker** | Every **assistant** message | SAFE, WARNING (ungrounded), or BLOCK (contradiction) |
| **PromptGuard** | Every **user** message | SAFE, WARNING, or BLOCK |
| **DataDisclosureGuard** | Every **user** + **assistant** message | SAFE, WARNING (aligned PII), or BLOCK (misaligned PII) |

## Decision Mappings

### AlignmentCheck
- **BLOCK**: Behavioral misalignment (goal hijacking, refusing, off-topic, violating constraints)
- **SAFE**: Aligned with both (A) intended use and (B) user request

### FactChecker
- **BLOCK**: Self-contradictions
- **WARNING**: Ungrounded claims (fabricated facts, unsourced statistics)
- **SAFE**: No issues detected

### PromptGuard
- **BLOCK**: Clear prompt injection (multiple patterns, obvious jailbreak)
- **WARNING**: Suspicious pattern detected (single pattern, could be legitimate)
- **SAFE**: No injection patterns

### DataDisclosureGuard
- **BLOCK**: Misaligned PII collection/disclosure
- **WARNING**: PII detected but aligned with purpose (informational)
- **SAFE**: No PII issues

## Overall Decision Logic

```
IF any scanner has BLOCK → Overall: 🔴 BLOCK
ELSE IF any scanner has WARNING → Overall: 🟡 WARNING
ELSE → Overall: 🟢 SAFE
```

## New Result Format

```python
{
  "scanner": "AlignmentCheck",
  "overall_decision": "BLOCK",  # SAFE | WARNING | BLOCK
  "counts": {
    "safe": 2,
    "warning": 0,
    "block": 1,
    "total": 3
  },
  "message_results": [
    {
      "message_index": 0,
      "message_type": "assistant",
      "decision": "SAFE",
      "reason": "Agent stayed within purpose and addressed request"
    },
    {
      "message_index": 2,
      "message_type": "assistant",
      "decision": "BLOCK",
      "reason": "Agent hijacked goal - discussed unrelated topic"
    }
  ]
}
```

## UI Changes

### Removed
- ❌ Score displays (0.1-0.9)
- ❌ Gauge visualizations
- ❌ Plot charts
- ❌ Risk scores
- ❌ Progress bars

### Added
- ✅ Overall decision badge (🟢 SAFE | 🟡 WARNING | 🔴 BLOCK)
- ✅ Count metrics per scanner
- ✅ Per-message results table
- ✅ Expandable message details
- ✅ Clean, simple layout

## Example UI Layout

```
┌─────────────────────────────────┐
│     🟢 SAFE (Overall)           │
└─────────────────────────────────┘

📊 Scanner Results

🟢 AlignmentCheck: SAFE
  Total: 3  ✅ Safe: 3  ⚠️ Warning: 0  🚫 Block: 0
  ├─ Message #0 (assistant): 🟢 SAFE
  ├─ Message #2 (assistant): 🟢 SAFE
  └─ Message #4 (assistant): 🟢 SAFE

🟡 FactChecker: WARNING
  Total: 3  ✅ Safe: 2  ⚠️ Warning: 1  🚫 Block: 0
  ├─ Message #0 (assistant): 🟢 SAFE
  ├─ Message #2 (assistant): 🟡 WARNING - Ungrounded claim
  └─ Message #4 (assistant): 🟢 SAFE

🟢 PromptGuard: SAFE
  Total: 2  ✅ Safe: 2  ⚠️ Warning: 0  🚫 Block: 0
  ├─ Message #1 (user): 🟢 SAFE
  └─ Message #3 (user): 🟢 SAFE
```

## Implementation Files

### Scanner Updates
1. **`multi_agent_demo/alignment_check_new.py`**
   - New per-message AlignmentCheck implementation
   - New per-message PromptGuard wrapper
   - Returns normalized counts

2. **`multi_agent_demo/scanners/nemo_scanners.py`**
   - Updated FactChecker to return counts
   - Already had per-message analysis

3. **`multi_agent_demo/scanners/data_disclosure_scanner.py`**
   - Updated to return counts and message_results
   - Uses full conversation for context (as required)

### UI Updates
4. **`multi_agent_demo/ui/results_display_new.py`**
   - New simplified count-based UI
   - No scores, gauges, or plots
   - Clear decision badges
   - Per-message tables

### Integration
5. **`multi_agent_demo/firewall.py`**
   - Updated to use new per-message scanners
   - Calls scan_alignment_check_per_message
   - Calls scan_prompt_guard_per_message

6. **`multi_agent_demo/page_modules/realtime_page.py`**
   - Updated to use render_test_results_new
   - Shows new count-based UI

## Testing

### Test Your Changes
```bash
# Restart the app
streamlit run multi_agent_demo/app.py

# Navigate to Real-Time Testing page
# Load any scenario
# Click "Run Test"
```

### Expected Behavior
1. **Overall Decision**: Large badge at top (🟢/🟡/🔴)
2. **Scanner Sections**: Each scanner shows:
   - Overall decision for that scanner
   - Count metrics (Total, Safe, Warning, Block)
   - Expandable per-message table
3. **No Scores**: No numeric scores (0.1-0.9) anywhere
4. **No Gauges**: No gauge visualizations
5. **Clear Decisions**: Only SAFE/WARNING/BLOCK labels

## Migration Notes

### Backward Compatibility
- Old functions still exist for fallback paths
- New functions are prefixed with `_per_message` or `_new`
- Test results use new format going forward

### If Issues Occur
- Check console logs for scanner output
- Verify TOGETHER_API_KEY is configured (for AlignmentCheck)
- Old UI is still available in `results_display.py` if needed

## Benefits

### For Users
- ✅ Clearer understanding: "2 blocked, 1 warning, 3 safe"
- ✅ No confusion about what 0.7 score means
- ✅ Per-message visibility
- ✅ Faster comprehension

### For Development
- ✅ Consistent format across all scanners
- ✅ Easier to test and validate
- ✅ Simpler aggregation logic
- ✅ Better extensibility

## Summary

The system now provides:
1. **Per-message validation** for all scanners
2. **Count-based metrics** instead of scores
3. **Clear decisions** (SAFE/WARNING/BLOCK)
4. **Simple, clean UI** without gauges/plots
5. **Overall decision** clearly displayed

All scanners follow the same pattern and return the same format, making the system consistent and easy to understand.
