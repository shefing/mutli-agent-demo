# GitHub Actions Error Fixes

This document tracks errors encountered in GitHub Actions tests and their fixes.

## Error #1: NeMo GuardRails - stream_usage Parameter Error

### Error Message
```
TypeError: AsyncCompletions.create() got an unexpected keyword argument 'stream_usage'
WARNING! stream_usage is not default parameter.
Error invoking LLM (model=gpt-4o-mini): AsyncCompletions.create() got an unexpected keyword argument 'stream_usage'
```

### Affected Tests
- `test_facts_checker_scanner.py` (all 7 tests)

### Root Cause
Version incompatibility between:
- OpenAI SDK version 1.58.0+ (breaking changes)
- langchain-community (used by NeMo GuardRails, hasn't updated yet)

### Fix Applied
**Pinned OpenAI SDK version** in both:

1. `.github/workflows/test.yml`:
```yaml
pip install "openai<1.58.0"  # Avoid stream_usage parameter error
```

2. `requirements_minimal.txt`:
```python
openai<1.58.0  # Compatibility with NeMo GuardRails
```

### Status
✅ **FIXED** - Tests will now use OpenAI SDK < 1.58.0

### Future Action
When NeMo GuardRails/langchain-community updates for OpenAI 1.58.0+, remove the version pin.

---

## Error #2: AlignmentCheck Test - Missing 'counts' Key

### Error Message
```
❌ CRITICAL ERROR: Test execution failed: 'counts'
Error: Process completed with exit code 1.
Overall Decision: None
```

### Affected Tests
- `test_alignment_check.py` (all 4 tests)

### Root Cause
The test was accessing `result['counts']` directly without checking if the key exists. When the scan function returns an error (e.g., API key missing or API failure), the result dictionary only contains `{"error": "...", "scanner": "..."}` without the 'counts' key.

**Test code before fix:**
```python
result = scan_alignment_check_per_message(messages=messages, purpose=purpose)
print(f"Counts: Safe={result['counts']['safe']}, ...")  # KeyError if 'counts' missing!
```

### Fix Applied
**Added error checking** in `test_alignment_check.py` for all test functions:

```python
result = scan_alignment_check_per_message(messages=messages, purpose=purpose)

# Check for errors first
if "error" in result:
    print(f"\n❌ ERROR: {result.get('error')}")
    return False

print(f"\nOverall Decision: {result.get('overall_decision')}")
counts = result.get('counts', {})  # Safe access with default
print(f"Counts: Safe={counts.get('safe', 0)}, Warning={counts.get('warning', 0)}, Block={counts.get('block', 0)}")
```

### Changes Made
Fixed 3 test functions in `test_alignment_check.py`:
1. ✅ `test_aligned_conversation()`
2. ✅ `test_goal_hijacking()`
3. ✅ `test_off_topic_redirect()`

### Status
✅ **FIXED** - Tests now handle error cases gracefully

### Why This Happened
The `scan_alignment_check_per_message()` function returns different result formats:

**Success case:**
```python
{
    "scanner": "AlignmentCheck",
    "overall_decision": "SAFE",
    "counts": {"safe": 2, "warning": 0, "block": 0, "total": 2},
    "message_results": [...]
}
```

**Error case:**
```python
{
    "error": "OPENAI_API_KEY not configured",
    "scanner": "AlignmentCheck"
}
```

The test needs to handle both cases.

---

## Error #3: Slack Failure Notifications Not Sent

### Problem
When tests failed with exceptions (like KeyError), **only success notifications** were sent to Slack, never failure notifications.

### Root Cause
**Silent failure detection bug** in the workflow:

1. Test runs and crashes with exception (e.g., KeyError accessing `result['counts']`)
2. Python exits with code 1
3. Because `continue-on-error: true`, the workflow continues
4. BUT: The shell script never reaches `echo "outcome=failure" >> $GITHUB_OUTPUT`
5. The output variable is empty/undefined
6. "Collect test results" checks: `if [ "$OUTCOME" == "failure" ]`
7. Empty string != "failure", so FAILED counter is not incremented
8. FAILED = 0, so workflow succeeds ✅ (incorrectly!)
9. Only success notification sent, failures silently ignored ❌

**Example of the bug:**
```yaml
run: |
  python test_facts_checker_scanner.py  # Crashes with KeyError
  TEST_RESULT=$?  # Never reached!
  echo "outcome=failure" >> $GITHUB_OUTPUT  # Never reached!
```

### Fix Applied
**Check BOTH the output AND the step outcome** in the "Collect test results" step:

**Before:**
```bash
FACTS_CHECKER_OUTCOME="${{ steps.test_facts_checker.outputs.outcome }}"
if [ "$FACTS_CHECKER_OUTCOME" == "failure" ]; then
  FAILED=$((FAILED + 1))
fi
```

**After:**
```bash
FACTS_CHECKER_OUTCOME="${{ steps.test_facts_checker.outputs.outcome }}"
FACTS_CHECKER_STEP_OUTCOME="${{ steps.test_facts_checker.outcome }}"
if [ "$FACTS_CHECKER_OUTCOME" == "failure" ] || [ "$FACTS_CHECKER_STEP_OUTCOME" == "failure" ]; then
  FAILED=$((FAILED + 1))
fi
```

Now we check:
- ✅ The custom output (if test completed and set it)
- ✅ The actual step outcome (catches crashes and exceptions)

### Changes Made
Updated failure detection for all 5 optional tests:
1. ✅ test_alignment_dual_dimensions.py
2. ✅ test_alignment_vs_factchecker.py
3. ✅ test_alignment_check.py
4. ✅ test_native_llamafirewall_scanner.py
5. ✅ test_facts_checker_scanner.py

### Status
✅ **FIXED** - Failures will now be properly detected and reported to Slack

### Why This Is Critical
Without this fix:
- ❌ Tests could fail silently
- ❌ Broken code could be merged
- ❌ Team wouldn't know about failures
- ❌ Only saw success messages, creating false confidence

With this fix:
- ✅ All failures are detected
- ✅ Slack notifications sent for every failure
- ✅ Team can respond to issues immediately
- ✅ Proper CI/CD visibility

---

## Summary

All three critical errors are now fixed:

1. ✅ **NeMo GuardRails compatibility** - Pinned OpenAI SDK version to avoid `stream_usage` parameter error
2. ✅ **Test error handling** - Added proper error checking in tests to prevent KeyError crashes
3. ✅ **Slack failure notifications** - Fixed silent failure detection bug so ALL failures are reported

### What Changed
- **`.github/workflows/test.yml`**:
  - Added OpenAI SDK version pin
  - Fixed failure detection to check both output and step outcome
- **`test_alignment_check.py`**:
  - Added error handling for missing 'counts' key
- **`requirements_minimal.txt`**:
  - Added OpenAI SDK version constraint

### Expected Behavior Now
✅ Tests will run with compatible dependencies
✅ Tests will handle errors gracefully
✅ **ALL failures will send Slack notifications**
✅ **ALL successes will send Slack notifications**
✅ Full visibility into CI/CD pipeline health

**Next run should succeed AND properly report any issues!** 🎉

---

**Last Updated:** 2026-02-07
