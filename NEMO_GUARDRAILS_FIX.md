# NeMo GuardRails - OpenAI SDK Compatibility Fix

## Problem

When running FactsChecker tests in GitHub Actions, you may see this error:

```
TypeError: AsyncCompletions.create() got an unexpected keyword argument 'stream_usage'
```

Full error trace:
```
WARNING! stream_usage is not default parameter.
stream_usage was transferred to model_kwargs.
Please confirm that stream_usage is what you intended.
Error invoking LLM (model=gpt-4o-mini): AsyncCompletions.create() got an unexpected keyword argument 'stream_usage'
```

## Root Cause

**Version incompatibility** between:
- `openai` (OpenAI Python SDK) version **1.58.0 or newer**
- `langchain-community` (used internally by NeMo GuardRails)

The OpenAI SDK version 1.58.0+ introduced breaking changes to the API, and `langchain-community` (which NeMo GuardRails depends on) hasn't been updated to handle these changes yet.

Specifically:
1. NeMo GuardRails uses `langchain-community` to call OpenAI's API
2. `langchain-community` tries to pass a `stream_usage` parameter
3. OpenAI SDK 1.58.0+ doesn't accept this parameter
4. Result: TypeError

## Solution

### Fix #1: Pin OpenAI SDK Version (APPLIED)

Constrain the OpenAI SDK to versions before 1.58.0:

```bash
pip install "openai<1.58.0"
```

This is applied in `.github/workflows/test.yml`:

```yaml
- name: Install dependencies
  run: |
    pip install "openai<1.58.0"  # Avoid stream_usage parameter error
    pip install nemoguardrails
```

### Fix #2: Wait for Upstream Updates

Alternatively, wait for:
- NeMo GuardRails to update to use newer langchain versions
- OR langchain-community to be updated for OpenAI SDK 1.58.0+

Monitor these repositories:
- https://github.com/NVIDIA/NeMo-Guardrails/issues
- https://github.com/langchain-ai/langchain/issues

### Fix #3: Use Alternative LLM Provider

If you don't want to pin versions, switch NeMo GuardRails to use a different LLM provider in `nemo_config/config.yml`:

```yaml
# Example: Use Anthropic Claude instead
models:
  - type: main
    engine: anthropic
    model: claude-3-5-sonnet-20241022
```

Then use `ANTHROPIC_API_KEY` instead of `OPENAI_API_KEY`.

## Verification

After applying the fix, the FactsChecker test should pass:

```bash
python test_facts_checker_scanner.py
```

Expected output:
```
✅ PASS: FactsChecker Available
✅ PASS: Self-Contradiction Detection
✅ PASS: RAG Ungroundedness - Fabricated API
...
✅ ALL TESTS PASSED (7/7)
```

## Related Issues

- OpenAI SDK breaking changes: https://github.com/openai/openai-python/releases
- NeMo GuardRails compatibility: https://github.com/NVIDIA/NeMo-Guardrails/issues
- Langchain OpenAI integration: https://github.com/langchain-ai/langchain/issues

## Timeline

- **Issue Discovered:** 2026-02-07
- **Fix Applied:** 2026-02-07
- **Status:** FIXED (pinned openai<1.58.0)

## Future Action

When NeMo GuardRails or langchain-community release updates that are compatible with OpenAI SDK 1.58.0+, remove the version constraint:

```diff
- pip install "openai<1.58.0"
+ pip install openai
```

Test thoroughly before removing the constraint!
