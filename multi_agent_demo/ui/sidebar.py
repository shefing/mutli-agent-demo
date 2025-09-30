"""
Sidebar UI components for scanner configuration and scenario selection
"""

import streamlit as st
from multi_agent_demo.scenarios import get_predefined_scenarios
from multi_agent_demo.scanners import NEMO_GUARDRAILS_AVAILABLE


def _display_scanner_status():
    """Display dynamic scanner status summary"""
    enabled_scanners = st.session_state.enabled_scanners

    # Categorize scanners
    llamafirewall_scanners = ["PromptGuard", "AlignmentCheck"]
    nemo_scanners = ["SelfContradiction", "FactChecker", "HallucinationDetector"]

    # Count enabled scanners
    llamafirewall_enabled = sum(1 for name in llamafirewall_scanners if enabled_scanners.get(name, False))
    nemo_enabled = sum(1 for name in nemo_scanners if enabled_scanners.get(name, False))
    total_enabled = llamafirewall_enabled + nemo_enabled

    # Display status with appropriate styling
    if total_enabled == 0:
        st.warning("⚠️ No scanners enabled")
    else:
        status_msg = f"🛡️ **{total_enabled} scanner(s) enabled:**\n\n"
        if llamafirewall_enabled > 0:
            status_msg += f"• LlamaFirewall: {llamafirewall_enabled}\n\n"
        if nemo_enabled > 0:
            status_msg += f"• NeMo GuardRails: {nemo_enabled}"
        st.success(status_msg)


def render_sidebar():
    """Render the sidebar with scanner configuration and scenario selection"""
    with st.sidebar:
        st.header("🛡️ Scanner Configuration")

        # Scanner selection with checkboxes
        st.subheader("Enable Scanners")

        # Available scanners with descriptions
        scanner_info = {
            "PromptGuard": "🔍 Detects malicious user inputs",
            "AlignmentCheck": "🎯 Detects goal hijacking",
            "SelfContradiction": "🔄 Detects response inconsistencies",
            "FactChecker": "📊 Verifies factual accuracy",
            "HallucinationDetector": "🌟 Detects hallucinated content"
        }

        # Create checkboxes for each scanner
        for scanner_name, description in scanner_info.items():
            # Check if NeMo GuardRails scanners are available
            is_nemo_scanner = scanner_name in ["SelfContradiction", "FactChecker", "HallucinationDetector"]
            is_disabled = is_nemo_scanner and not NEMO_GUARDRAILS_AVAILABLE

            enabled = st.checkbox(
                f"{scanner_name}",
                value=st.session_state.enabled_scanners[scanner_name] and not is_disabled,
                help=description + (" (Requires NeMo GuardRails)" if is_nemo_scanner else ""),
                key=f"enable_{scanner_name}",
                disabled=is_disabled
            )
            st.session_state.enabled_scanners[scanner_name] = enabled
            st.caption(description + (" ⚠️ NeMo GuardRails required" if is_disabled else ""))

        # Display scanner status summary
        _display_scanner_status()

        st.divider()

        st.header("📚 Predefined Scenarios")

        # Get predefined scenarios
        predefined_scenarios = get_predefined_scenarios()
        scenario_names = [""] + list(predefined_scenarios.keys())

        # Predefined scenarios
        scenario = st.selectbox(
            "Choose scenario",
            scenario_names
        )

        if st.button("Load Scenario") and scenario:
            scenario_data = predefined_scenarios[scenario]
            st.session_state.current_conversation = {
                "purpose": scenario_data["purpose"],
                "messages": scenario_data["messages"]
            }
            # Clear test results when loading a new scenario
            st.session_state.test_results = []
            st.rerun()