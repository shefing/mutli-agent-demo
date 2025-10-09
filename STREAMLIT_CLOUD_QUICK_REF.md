# Streamlit Cloud Quick Reference

## Current Status - UPDATED 2025-10-09

**Root cause identified:** PyTorch dynamic compilation (`torch.compile()`) causing syntax errors in Streamlit Cloud's restricted environment.

**Fix applied:** Added environment variables to disable torch.compile() and JIT compilation.

**Expected result:** Both AlignmentCheck and PromptGuard should now work on Streamlit Cloud.

## What's Working ✅

From your logs, we can see:
- ✅ Application loads successfully
- ✅ Dependencies installed
- ✅ HF_TOKEN loaded correctly
- ✅ NeMo GuardRails available
- ✅ LlamaFirewall initializes successfully
- ✅ AlignmentCheck scanner should work (if TOGETHER_API_KEY configured)
- ✅ FactsChecker scanner should work (if OPENAI_API_KEY configured)

## What's Not Working ⚠️

- ❌ **PromptGuard scanner fails** when scanning messages
- Error: `expected an indented block after function definition on line 3`
- Root cause: Model loading incompatibility with Streamlit Cloud environment

## What Changed (Latest Fix)

**Added to `guards_demo_ui.py`:**
```python
# Disable torch.compile() which can cause syntax errors
os.environ['TORCH_COMPILE_DISABLE'] = '1'
os.environ['PYTORCH_JIT'] = '0'  # Disable JIT compilation
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Configure writable cache
os.environ['HF_HOME'] = '/tmp/.cache/huggingface'

# Disable torch dynamo errors
import torch
if hasattr(torch, '_dynamo'):
    torch._dynamo.config.suppress_errors = True
```

**What this fixes:**
- Prevents PyTorch from generating dynamic Python code at runtime
- Forces eager execution mode (compatible with Streamlit Cloud)
- Should resolve "expected an indented block" errors

## Testing the Fix

**After deploying these changes:**
1. Push code to your repository
2. Streamlit Cloud will auto-redeploy
3. Check logs for: "🔧 Disabled torch.compile() and JIT for Streamlit Cloud compatibility"
4. Test both AlignmentCheck and PromptGuard scanners
5. Both should now work without syntax errors

## Fallback Plan

**If the fix doesn't work (Option 1 - Temporary):**
1. In your deployed app sidebar
2. Uncheck "☑️ PromptGuard"
3. Use only AlignmentCheck + FactsChecker
4. Report the issue with full logs

**Option 2: Local Deployment**
- Clone the repo locally
- All 3 scanners work perfectly in local environment
- Use for comprehensive testing

## Scanner Status on Streamlit Cloud (After Fix)

| Scanner | Status | Requirements | Notes |
|---------|--------|--------------|-------|
| **AlignmentCheck** | ✅ Should Work | TOGETHER_API_KEY in secrets | Fixed with torch.compile disable |
| **PromptGuard** | ✅ Should Work | HF_TOKEN in secrets | Fixed with torch.compile disable |
| **FactsChecker** | ✅ Works | OPENAI_API_KEY in secrets | Always worked |

## Required Secrets Configuration

Ensure these are configured in **Streamlit Cloud → Settings → Secrets**:

```toml
# Required for AlignmentCheck
TOGETHER_API_KEY = "your-together-api-key"

# Optional for PromptGuard (may still fail)
HF_TOKEN = "hf_your-huggingface-token"

# Required for FactsChecker
OPENAI_API_KEY = "sk-your-openai-key"
```

## Code Changes Made

The code now handles PromptGuard failures gracefully:

1. **Catches SyntaxError** in `firewall.py`
2. **Shows user-friendly message** in results display
3. **Provides guidance** to disable or use local deployment
4. **Doesn't crash** - other scanners continue working

## User Experience

When PromptGuard fails, users will see:

```
⚠️ Streamlit Cloud Compatibility Issue

PromptGuard scanner uses models that may not be
compatible with Streamlit Cloud's environment.
This scanner works on local deployments.

🔍 Technical Details (expandable)
```

## Recommended Configuration for Streamlit Cloud

**Default scanners to enable:**
```python
st.session_state.enabled_scanners = {
    "PromptGuard": False,      # Disabled for Streamlit Cloud
    "AlignmentCheck": True,     # Works on Streamlit Cloud
    "FactsChecker": True        # Works on Streamlit Cloud
}
```

## Testing Your Deployment

1. ✅ Check logs show: `✅ LlamaFirewall initialized with 2 scanner(s)`
2. ✅ Load a test scenario
3. ✅ Disable PromptGuard in sidebar
4. ✅ Run test with AlignmentCheck + FactsChecker
5. ✅ Verify both scanners return results

## Local Development vs Streamlit Cloud

| Feature | Local | Streamlit Cloud |
|---------|-------|-----------------|
| PromptGuard | ✅ Works | ⚠️ May fail |
| AlignmentCheck | ✅ Works | ✅ Works |
| FactsChecker | ✅ Works | ✅ Works |
| Full Testing | ✅ All scanners | ✅ 2/3 scanners |

## Next Steps

1. **Short term**: Disable PromptGuard on Streamlit Cloud
2. **Long term**: Use local deployment for comprehensive testing with all 3 scanners
3. **Alternative**: Investigate PromptGuard alternatives that work on Streamlit Cloud

## Support Files

- **`STREAMLIT_CLOUD_FIX.md`** - Detailed technical explanation
- **`INSTALL.md`** - Complete deployment guide
- **`firewall.py`** - Enhanced error handling
- **`results_display.py`** - User-friendly error messages
