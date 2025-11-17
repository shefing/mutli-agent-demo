#!/usr/bin/env python3
"""
Multi-page Streamlit Application for AI Agent Guards
Main entry point with page routing and common components
"""

import time
start_time = time.time()

# Safe print function that ignores broken pipe errors
def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except (BrokenPipeError, IOError):
        pass

safe_print("="*80)
safe_print("AI AGENT GUARDS - STARTING APPLICATION")
safe_print("="*80)

import streamlit as st
safe_print(f"✅ Streamlit imported ({time.time() - start_time:.2f}s)")

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
safe_print(f"✅ Core libraries imported ({time.time() - start_time:.2f}s)")

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load environment variables
load_dotenv()

# Environment configuration (same as guards_demo_ui.py)
os.environ['SPACY_WARNING_IGNORE'] = 'W008'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['TORCH_COMPILE_DISABLE'] = '1'
os.environ['PYTORCH_JIT'] = '0'
safe_print("🔧 Configured environment for compatibility")

# HuggingFace configuration
if not os.getenv('HF_HOME'):
    os.environ['HF_HOME'] = '/tmp/.cache/huggingface'
    safe_print(f"📂 Set HF_HOME to: {os.environ['HF_HOME']}")

hf_token = os.getenv('HF_TOKEN')
if hf_token:
    os.environ['HF_TOKEN'] = hf_token
    os.environ['HUGGING_FACE_HUB_TOKEN'] = hf_token
    safe_print(f"🔑 HF_TOKEN configured")

cache_dir = os.environ.get('HF_HOME', '/tmp/.cache/huggingface')
os.makedirs(cache_dir, exist_ok=True)

# Additional transformers configuration
os.environ['TRANSFORMERS_OFFLINE'] = '0'
os.environ['TRANSFORMERS_NO_TF'] = '1'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['HF_HUB_DISABLE_EXPERIMENTAL_WARNING'] = '1'
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '0'

# Torch configuration
try:
    import torch
    torch.jit._state.disable()
    if hasattr(torch, '_dynamo'):
        torch._dynamo.config.suppress_errors = True
        torch._dynamo.config.cache_size_limit = 0
    if hasattr(torch, 'autograd'):
        torch.autograd.set_grad_enabled(False)
        torch.autograd.profiler.profile(enabled=False)
    safe_print("🔧 Torch configured")
except ImportError:
    pass
except Exception as e:
    safe_print(f"⚠️ Could not configure torch: {e}")

# Page configuration
st.set_page_config(
    page_title="Omniguard - AI Agent Guards",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import page modules (after environment setup)
safe_print(f"📦 Importing page modules... ({time.time() - start_time:.2f}s)")
from multi_agent_demo.page_modules import realtime_page, deviations_page
from multi_agent_demo.ui.common import render_agent_configuration
safe_print(f"✅ Page modules imported ({time.time() - start_time:.2f}s)")


def initialize_session_state():
    """Initialize common session state variables"""
    # Page navigation
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Real-Time"

    # Agent configuration (shared across pages)
    if "agent_purpose" not in st.session_state:
        st.session_state.agent_purpose = ""

    if "agent_description" not in st.session_state:
        st.session_state.agent_description = ""

    # Real-time page state
    if "conversations" not in st.session_state:
        from multi_agent_demo.scenarios import load_saved_scenarios
        st.session_state.conversations = load_saved_scenarios()

    if "current_conversation" not in st.session_state:
        st.session_state.current_conversation = {
            "purpose": "",
            "messages": []
        }

    if "test_results" not in st.session_state:
        st.session_state.test_results = []

    if "enabled_scanners" not in st.session_state:
        from multi_agent_demo.scanners import NEMO_GUARDRAILS_AVAILABLE, PRESIDIO_AVAILABLE
        st.session_state.enabled_scanners = {
            "PromptGuard": True,
            "AlignmentCheck": True,
            "FactsChecker": NEMO_GUARDRAILS_AVAILABLE,
            "DataDisclosureGuard": PRESIDIO_AVAILABLE
        }

    # Real-time input fields
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
    if "editing_message_index" not in st.session_state:
        st.session_state.editing_message_index = None

    # Deviations page state
    if "otel_data" not in st.session_state:
        st.session_state.otel_data = None

    if "deviation_results" not in st.session_state:
        st.session_state.deviation_results = None

    if "bias_results" not in st.session_state:
        st.session_state.bias_results = None


def render_page_navigation():
    """Render page navigation in sidebar"""
    st.sidebar.title("🛡️ Omniguard")

    # Page selection
    pages = ["Real-Time", "Deviation"]

    # Use radio buttons for page selection
    selected_page = st.sidebar.radio(
        "Navigation",
        pages,
        index=pages.index(st.session_state.current_page),
        key="page_selector",
        label_visibility="collapsed"  # Hide the "Navigation" label
    )

    # Update current page if changed
    if selected_page != st.session_state.current_page:
        st.session_state.current_page = selected_page
        st.rerun()

    st.sidebar.divider()


def main():
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()

    # Render page navigation
    render_page_navigation()

    # Render selected page
    if st.session_state.current_page == "Real-Time":
        realtime_page.render()
    elif st.session_state.current_page == "Deviation":
        deviations_page.render()


if __name__ == "__main__":
    safe_print(f"="*80)
    safe_print(f"🚀 STARTING MAIN APPLICATION ({time.time() - start_time:.2f}s)")
    safe_print(f"="*80)

    main()

    safe_print(f"="*80)
    safe_print(f"✅ APPLICATION READY ({time.time() - start_time:.2f}s)")
    safe_print(f"="*80)
