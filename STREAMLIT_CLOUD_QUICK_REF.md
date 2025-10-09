# Streamlit Cloud Quick Reference

## Current Status

Your Streamlit Cloud deployment is experiencing a **PromptGuard compatibility issue**. This is expected and now handled gracefully.

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

## Immediate Solution

**Option 1: Disable PromptGuard (Recommended)**
1. In your deployed app sidebar
2. Uncheck "☑️ PromptGuard"
3. Use only AlignmentCheck + FactsChecker
4. Both of these work fine on Streamlit Cloud

**Option 2: Accept the Error**
- Leave PromptGuard enabled
- UI will show a user-friendly message explaining the Streamlit Cloud limitation
- Other scanners will continue to work

## Scanner Status on Streamlit Cloud

| Scanner | Status | Requirements | Notes |
|---------|--------|--------------|-------|
| **AlignmentCheck** | ✅ Works | TOGETHER_API_KEY in secrets | Fully functional |
| **PromptGuard** | ⚠️ May Fail | HF_TOKEN in secrets | Model loading issues |
| **FactsChecker** | ✅ Works | OPENAI_API_KEY in secrets | Fully functional |

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
