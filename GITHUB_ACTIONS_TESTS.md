# GitHub Actions Test Suite

## Overview
The test suite runs automatically on every push to `main` and on pull requests.

## Test Count: 10 Tests Total

### Core Tests (5) - Always Run
These tests run without requiring API keys:
1. ✅ `test_data_disclosure_fix.py` - DataDisclosureGuard false positive test
2. ✅ `test_alignment_fix.py` - DataDisclosureGuard alignment test
3. ✅ `test_user_provided_notification_contact.py` - User-provided notification contact test
4. ✅ `test_deviations.py` - Deviation/bias detection test
5. ✅ `test_prompt_guard_scanner.py` - PromptGuard scanner pattern-based detection (no API key needed)

### Optional Tests (5) - Require API Keys
These tests only run when the required API keys are configured in GitHub Secrets:

**Requires TOGETHER_API_KEY:**
6. ⚙️ `test_alignment_dual_dimensions.py` - AlignmentCheck dual dimensions test
7. ⚙️ `test_alignment_vs_factchecker.py` - AlignmentCheck vs FactChecker separation test
8. ⚙️ `test_native_llamafirewall_scanner.py` - Native LlamaFirewall scanner test

**Requires OPENAI_API_KEY:**
9. ⚙️ `test_alignment_check.py` - AlignmentCheck scanner test (GPT-4o-mini fallback implementation)
10. ⚙️ `test_facts_checker_scanner.py` - FactsChecker scanner test (7 subtests including temporal awareness)

## Known Issues

### NeMo GuardRails - OpenAI SDK Compatibility

**Issue:** NeMo GuardRails may fail with:
```
TypeError: AsyncCompletions.create() got an unexpected keyword argument 'stream_usage'
```

**Fix:** The workflow pins `openai<1.58.0` to avoid this issue. See `NEMO_GUARDRAILS_FIX.md` for details.

**Status:** ✅ FIXED (version constraint applied in workflow)

## Required GitHub Secrets

To run all 10 tests, configure these secrets in your repository:

### 1. TOGETHER_API_KEY ⚠️ REQUIRED FOR 3 TESTS
- Used by: AlignmentCheck tests (6, 7) and Native LlamaFirewall test (8)
- Provider: [Together AI](https://api.together.xyz/)
- Purpose: Powers native LlamaFirewall for behavioral drift detection

### 2. OPENAI_API_KEY ⚠️ REQUIRED FOR 2 TESTS
- Used by: AlignmentCheck GPT-4o-mini fallback test (9) and FactsChecker test (10)
- Provider: [OpenAI](https://platform.openai.com/)
- Purpose: Powers GPT-4o-mini based tests (AlignmentCheck fallback and NeMo GuardRails fact-checking)

## How to Add Secrets

1. Go to your GitHub repository
2. Navigate to: **Settings → Secrets and variables → Actions**
3. Click **"New repository secret"**
4. Add each secret:
   - Name: `TOGETHER_API_KEY`
   - Value: Your Together AI API key
   - Click "Add secret"

   - Name: `OPENAI_API_KEY`
   - Value: Your OpenAI API key
   - Click "Add secret"

## Test Results

The workflow will:
- ✅ **Pass**: If all running tests succeed (skipped tests don't cause failure)
- ❌ **Fail**: If any running test fails
- ⏭️ **Skip**: Optional tests without required API keys

### Slack Notifications

Both success and failure notifications are sent to Slack with:
- Total tests: X/10
- Tests passed, failed, and skipped
- Detailed per-test status with outcomes
- Links to workflow run and commit

## Adding New Tests

When adding a new test file, follow these steps:

1. **Create the test file** (e.g., `test_new_scanner.py`)

2. **Update `.github/workflows/test.yml`:**
   - Add test execution step (with or without API key check)
   - Update "Collect test results" section to count the new test
   - Update Slack notification to list the new test
   - Update `TOTAL=X` count if it's a core test

3. **Update this document:**
   - Add test to the appropriate section (Core or Optional)
   - Document any new required secrets
   - Update the test count in the title

4. **Notify the team:**
   - If new secrets are required, inform repository admins
   - Document which provider and why the secret is needed

## Example: Adding a Test That Requires a New Secret

If you add a test requiring `ANTHROPIC_API_KEY`:

```yaml
- name: Run Claude scanner test (optional)
  id: test_claude_scanner
  continue-on-error: true
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    if [ -z "$ANTHROPIC_API_KEY" ]; then
      echo "⏭️ Skipping Claude scanner test (ANTHROPIC_API_KEY not configured)"
      echo "outcome=skipped" >> $GITHUB_OUTPUT
      exit 0
    fi
    python test_claude_scanner.py
    TEST_RESULT=$?
    if [ $TEST_RESULT -eq 0 ]; then
      echo "outcome=success" >> $GITHUB_OUTPUT
    else
      echo "outcome=failure" >> $GITHUB_OUTPUT
      exit $TEST_RESULT
    fi
```

Then notify: "⚠️ New test added requiring `ANTHROPIC_API_KEY` from Claude AI"

---

**Last Updated:** 2026-02-07
**Total Tests:** 10 (5 core + 5 optional)
**Required Secrets:** 2 (TOGETHER_API_KEY, OPENAI_API_KEY)
