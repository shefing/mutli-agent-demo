# Streamlit Cloud Deployment Fix

## Issue
When deployed on Streamlit Cloud, you may see this error:
```
Error: expected an indented block after function definition on line 3 (<unknown>, line 3)
```

## Root Causes

### 1. Missing API Tokens (Primary Issue)
This error occurs when **API tokens are not configured in Streamlit Cloud secrets**. LlamaFirewall makes API calls during initialization, and without proper authentication, it receives malformed responses that cause syntax errors.

### 2. PromptGuard Model Compatibility (Secondary Issue)
Even with proper API tokens, **PromptGuard may fail on Streamlit Cloud** due to model loading issues. The error occurs when the scanner tries to load the `meta-llama/Llama-Prompt-Guard-2-86M` model in Streamlit Cloud's environment.

**Observed behavior:**
- ✅ PromptGuard downloads successfully
- ✅ LlamaFirewall initializes successfully
- ❌ PromptGuard fails when actually scanning messages

**Workaround:** Disable PromptGuard on Streamlit Cloud and use only AlignmentCheck and FactsChecker scanners.

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

### 2. Environment Configuration for Streamlit Cloud

Added critical environment variables in `guards_demo_ui.py` to prevent torch compilation errors:

```python
# Disable torch.compile() which can cause syntax errors in Streamlit Cloud
os.environ['TORCH_COMPILE_DISABLE'] = '1'
os.environ['PYTORCH_JIT'] = '0'  # Disable JIT compilation
os.environ['TOKENIZERS_PARALLELISM'] = 'false'  # Stability

# Configure writable cache directory
os.environ['HF_HOME'] = '/tmp/.cache/huggingface'

# Disable torch dynamo errors
import torch
if hasattr(torch, '_dynamo'):
    torch._dynamo.config.suppress_errors = True
```

**Why this matters:**
- The "expected an indented block" error is caused by PyTorch's dynamic code compilation (`torch.compile()` or JIT)
- Streamlit Cloud's restricted environment doesn't support dynamic code generation
- Disabling these features forces eager execution mode

### 3. Code Improvements Made

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
- ✅ No initialization errors
- ✅ LlamaFirewall initializes properly
- ✅ Clear error messages if tokens are still missing
- ⚠️ **PromptGuard may fail on Streamlit Cloud** (see workaround below)
- ✅ AlignmentCheck works properly
- ✅ FactsChecker works properly

### 5. PromptGuard Workaround for Streamlit Cloud

If PromptGuard fails with the syntax error on Streamlit Cloud:

**Option A: Disable PromptGuard** (Recommended for Streamlit Cloud)
1. In the sidebar, uncheck "PromptGuard"
2. Use AlignmentCheck and FactsChecker only
3. Deploy locally if PromptGuard testing is critical

**Option B: Default to Disabled** (Code change)
Edit `guards_demo_ui.py` to disable PromptGuard by default:
```python
if "enabled_scanners" not in st.session_state:
    st.session_state.enabled_scanners = {
        "PromptGuard": False,  # Disabled by default for Streamlit Cloud
        "AlignmentCheck": True,
        "FactsChecker": NEMO_GUARDRAILS_AVAILABLE
    }
```

The UI now shows a clear message when PromptGuard fails:
```
⚠️ Streamlit Cloud Compatibility Issue
PromptGuard scanner uses models that may not be compatible with
Streamlit Cloud's environment. This scanner works on local deployments.
```

### 6. Fallback Behavior

The application gracefully handles scanner failures:

**Missing API Tokens:**
- **AlignmentCheck**: Shows clear error message, returns None (test won't run)
- **PromptGuard**: Shows warning, attempts to run (may fail)
- **FactsChecker**: Shows error when attempting to use (requires OpenAI)

**PromptGuard Model Loading Issues (Streamlit Cloud):**
- Shows user-friendly error: "⚠️ Streamlit Cloud Compatibility Issue"
- Provides guidance: "This scanner works on local deployments"
- Other scanners continue to work normally
- Application remains functional with remaining scanners

## Files Modified

1. **`multi_agent_demo/firewall.py`**
   - Added pre-initialization API token validation
   - Enhanced error handling for SyntaxError in PromptGuard
   - Added specific Streamlit Cloud compatibility notes

2. **`multi_agent_demo/ui/results_display.py`**
   - Added user-friendly error display for PromptGuard Streamlit Cloud issues
   - Shows expandable technical details
   - Guides users to use local deployment for PromptGuard

3. **`INSTALL.md`**
   - Added complete Streamlit Cloud deployment section
   - Documented API token requirements
   - Added troubleshooting guidance

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

**Problem:**
- Syntax error on Streamlit Cloud: "expected an indented block after function definition on line 3"
- Affects LlamaFirewall scanners (PromptGuard, AlignmentCheck)

**Root Causes:**
1. Missing API tokens in Streamlit Cloud secrets
2. PromptGuard model loading incompatibility with Streamlit Cloud environment

**Solution:**
1. Configure API tokens in Streamlit Cloud secrets (TOGETHER_API_KEY, HF_TOKEN, OPENAI_API_KEY)
2. Enhanced error handling to catch and explain Streamlit Cloud issues
3. Graceful fallback with clear user guidance

**Result:**
- ✅ Clear error messages guide users to fix configuration
- ✅ AlignmentCheck works on Streamlit Cloud (with TOGETHER_API_KEY)
- ✅ FactsChecker works on Streamlit Cloud (with OPENAI_API_KEY)
- ⚠️ PromptGuard may need to be disabled on Streamlit Cloud
- ✅ Application remains functional with available scanners

**Recommended Streamlit Cloud Configuration:**
- ✅ Enable: AlignmentCheck + PromptGuard + FactsChecker (with new torch.compile fix)
- ⚠️ If issues persist: Disable PromptGuard, keep AlignmentCheck + FactsChecker
- 📌 Use local deployment for guaranteed compatibility with all scanners

**Latest Fix (2025-10-09):**
Added environment variables to disable PyTorch dynamic compilation which was causing the syntax error. This should allow both AlignmentCheck and PromptGuard to work on Streamlit Cloud.
