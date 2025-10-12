#!/usr/bin/env python3
"""
Streamlit UI for Interactive AI Agent Guards Testing

This provides a visual interface to:
- Define agent purpose and build conversations
- Test multiple security scanners (LlamaFirewall + NeMo GuardRails)
- Visualize scanner decisions and scores
- Compare different scenarios
"""

import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from multi_agent_demo.scanners import NEMO_GUARDRAILS_AVAILABLE, PRESIDIO_AVAILABLE
from multi_agent_demo.scenarios import load_saved_scenarios
from multi_agent_demo.ui import render_sidebar, render_conversation_builder, render_test_results
from multi_agent_demo.firewall import initialize_firewall

# Load environment variables from .env file only
load_dotenv()

# Configure environment for LlamaFirewall compatibility
# Set tokenizers parallelism to avoid warnings/errors
os.environ['TOKENIZERS_PARALLELISM'] = 'false'  # Set to false for Streamlit Cloud stability

# Disable torch.compile() which can cause syntax errors in Streamlit Cloud
os.environ['TORCH_COMPILE_DISABLE'] = '1'
os.environ['PYTORCH_JIT'] = '0'  # Disable JIT compilation
print("🔧 Disabled torch.compile() and JIT for Streamlit Cloud compatibility")

# Configure HuggingFace cache directory (writable in Streamlit Cloud)
if not os.getenv('HF_HOME'):
    os.environ['HF_HOME'] = '/tmp/.cache/huggingface'
    print(f"📂 Set HF_HOME to: {os.environ['HF_HOME']}")

# Ensure HF_TOKEN is available for transformers/huggingface_hub
hf_token = os.getenv('HF_TOKEN')
if hf_token:
    # Set both possible environment variables that HF libraries check
    os.environ['HF_TOKEN'] = hf_token
    os.environ['HUGGING_FACE_HUB_TOKEN'] = hf_token
    print(f"🔑 HF_TOKEN loaded from .env: {hf_token[:15]}...{hf_token[-15:]} (length: {len(hf_token)})")
else:
    print("❌ No HF_TOKEN found in .env file")

# Create cache directory if it doesn't exist
cache_dir = os.environ.get('HF_HOME', '/tmp/.cache/huggingface')
os.makedirs(cache_dir, exist_ok=True)
print(f"✅ Cache directory ready: {cache_dir}")

# Additional transformers configuration to prevent code generation
os.environ['TRANSFORMERS_OFFLINE'] = '0'  # Allow downloads but avoid code execution
os.environ['TRANSFORMERS_NO_TF'] = '1'    # Disable TensorFlow backend
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'  # Reduce logging

# CRITICAL: Prevent transformers from executing remote code
# This is likely the actual cause of the syntax error
os.environ['HF_HUB_DISABLE_EXPERIMENTAL_WARNING'] = '1'
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '0'  # Allow token usage
print("🔧 Configured transformers to prevent remote code execution")

# Attempt to disable torch dynamo/compile at import time
try:
    import torch
    # Disable all torch compilation features
    torch.jit._state.disable()
    print("🔧 Disabled torch.jit")

    if hasattr(torch, '_dynamo'):
        torch._dynamo.config.suppress_errors = True
        torch._dynamo.config.cache_size_limit = 0  # Disable dynamo cache
        print("🔧 Configured torch._dynamo to suppress errors")

    # Disable autograd profiling which can cause code generation
    if hasattr(torch, 'autograd'):
        torch.autograd.set_grad_enabled(False)
        torch.autograd.profiler.profile(enabled=False)
        print("🔧 Disabled autograd profiling")

except ImportError:
    pass  # Torch not installed yet, will be configured when loaded
except Exception as e:
    print(f"⚠️ Could not configure torch: {e}")


# Page configuration
st.set_page_config(
    page_title="AI Agent Guards Testing Application",
    page_icon="🛡️",
    layout="wide"
)


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "conversations" not in st.session_state:
        # Load saved scenarios from persistent storage
        st.session_state.conversations = load_saved_scenarios()

    if "current_conversation" not in st.session_state:
        st.session_state.current_conversation = {
            "purpose": "",
            "messages": []
        }

    if "test_results" not in st.session_state:
        st.session_state.test_results = []

    if "enabled_scanners" not in st.session_state:
        st.session_state.enabled_scanners = {
            "PromptGuard": True,
            "AlignmentCheck": True,
            "FactsChecker": NEMO_GUARDRAILS_AVAILABLE,
            "DataDisclosureGuard": PRESIDIO_AVAILABLE
        }

    # Initialize input field state for clearing after adding messages
    if "input_user_content" not in st.session_state:
        st.session_state.input_user_content = ""
    if "input_assistant_content" not in st.session_state:
        st.session_state.input_assistant_content = ""
    if "input_action_name" not in st.session_state:
        st.session_state.input_action_name = ""
    if "input_thought" not in st.session_state:
        st.session_state.input_thought = ""
    if "input_params" not in st.session_state:
        st.session_state.input_params = ""

    # Initialize editing state
    if "editing_message_index" not in st.session_state:
        st.session_state.editing_message_index = None


def main():
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()

    # Display title
    st.title("🛡️ AI Agent Guards Testing Application")
    st.markdown("Demo app to expose the behavior of AI Agent Guards")

    # Render sidebar with scanner configuration and scenario selection
    render_sidebar()

    # Main content area with two columns
    col1, col2 = st.columns([3, 2])

    with col1:
        # Render conversation builder (left panel)
        render_conversation_builder()

    with col2:
        # Render test results (right panel)
        render_test_results()


if __name__ == "__main__":
    main()