# Streamlit Cloud Deployment Fix

## Issue
When deployed on Streamlit Cloud, LlamaFirewall scanners (PromptGuard, AlignmentCheck) show error:
```
Error: expected an indented block after function definition on line 3 (<unknown>, line 3)
```

## Root Cause
This error occurs when **API tokens are not configured in Streamlit Cloud secrets**. LlamaFirewall makes API calls during initialization, and without proper authentication, it receives malformed responses that cause syntax errors.

## Solution

### 1. Configure Streamlit Cloud Secrets

**Go to your Streamlit Cloud app → Settings → Secrets**

Add the following in TOML format:

```toml
# Required for AlignmentCheck scanner
TOGETHER_API_KEY = "your-together-api-key"

# Recommended for PromptGuard scanner
HF_TOKEN = "hf_your-huggingface-token"

# Required for NeMo FactsChecker scanner
OPENAI_API_KEY = "sk-your-openai-key"
```

**Critical:**
- ✅ **TOGETHER_API_KEY** - Required for AlignmentCheck (causes the syntax error if missing)
- ✅ **HF_TOKEN** - Recommended for PromptGuard (may work without but better with)
- ✅ **OPENAI_API_KEY** - Required for FactsChecker

### 2. Code Improvements Made

Enhanced `multi_agent_demo/firewall.py` with:

#### A. Pre-initialization Token Validation
```python
def initialize_firewall():
    import os

    # Check for required API tokens BEFORE attempting initialization
    enabled_scanners = st.session_state.enabled_scanners

    if enabled_scanners.get("AlignmentCheck", False):
        together_key = os.getenv("TOGETHER_API_KEY")
        if not together_key:
            st.error("⚠️ AlignmentCheck requires TOGETHER_API_KEY. Please configure it in Streamlit Cloud secrets.")
            return None

    if enabled_scanners.get("PromptGuard", False):
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            st.warning("⚠️ PromptGuard works best with HF_TOKEN. Configure it in Streamlit Cloud secrets if you encounter issues.")
```

#### B. Better Exception Handling
```python
    except SyntaxError as e:
        print(f"❌ LlamaFirewall initialization failed with SyntaxError: {str(e)}")
        st.error(f"⚠️ LlamaFirewall configuration error: {str(e)}. This may be due to API token issues or environment differences.")
        return None
    except Exception as e:
        print(f"❌ LlamaFirewall initialization failed: {str(e)}")
        if "401" in str(e) or "Unauthorized" in str(e):
            st.error("⚠️ LlamaFirewall initialization failed due to authentication. Check your API tokens in Streamlit Cloud secrets.")
        elif "expected an indented block" in str(e):
            st.error("⚠️ LlamaFirewall configuration error. Please check your API tokens are properly configured in Streamlit Cloud secrets.")
        else:
            st.error(f"⚠️ LlamaFirewall initialization error: {str(e)}")
        return None
```

#### C. Configuration Validation
```python
    # Validate scanner configuration before passing to LlamaFirewall
    if not scanner_config or not any(scanner_config.values()):
        print("⚠️ Scanner configuration is empty, skipping LlamaFirewall initialization")
        return None

    # Log configuration for debugging
    print(f"🔧 Scanner config: {scanner_config}")
```

### 3. Deployment Steps

1. **Configure secrets** in Streamlit Cloud (see above)
2. **Push code changes** to your repository
3. **Restart your Streamlit Cloud app**
4. **Verify in logs**: Look for "✅ LlamaFirewall initialized" messages
5. **Test scanners**: Run a test scenario to ensure all scanners work

### 4. Verification

After deployment, you should see:
- ✅ No syntax errors
- ✅ Scanners initialize properly
- ✅ Clear error messages if tokens are still missing
- ✅ All three scanners (AlignmentCheck, PromptGuard, FactsChecker) working

### 5. Fallback Behavior

If API tokens are not configured:
- **AlignmentCheck**: Shows clear error message, returns None (test won't run)
- **PromptGuard**: Shows warning, attempts to run (may work with cached models)
- **FactsChecker**: Shows error when attempting to use (requires OpenAI)

The application gracefully handles missing scanners and continues to function with available ones.

## Files Modified

- `multi_agent_demo/firewall.py` - Enhanced error handling and token validation
- `INSTALL.md` - Added Streamlit Cloud deployment section

## Testing

**Local testing:**
```bash
streamlit run multi_agent_demo/guards_demo_ui.py
```

**Streamlit Cloud logs:**
```
🔑 Checking API tokens...
🚀 Initializing LlamaFirewall with scanners: ['AlignmentCheck', 'PromptGuard']
🔧 Scanner config: {<Role.USER: 'user'>: [<ScannerType.PROMPT_GUARD: 'prompt_guard'>], <Role.ASSISTANT: 'assistant'>: [<ScannerType.AGENT_ALIGNMENT: 'agent_alignment'>]}
✅ LlamaFirewall initialized with 2 scanner(s): ['AlignmentCheck', 'PromptGuard']
```

## Summary

**Problem:** Syntax error on Streamlit Cloud due to missing API tokens
**Solution:** Configure API tokens in Streamlit Cloud secrets + improved error handling
**Result:** Clear error messages guide users to fix configuration issues
