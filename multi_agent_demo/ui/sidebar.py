"""
Sidebar UI components for scanner configuration and scenario selection
"""

import streamlit as st
import json
from multi_agent_demo.scenarios import get_predefined_scenarios, load_scenario_from_json
from multi_agent_demo.scanners import NEMO_GUARDRAILS_AVAILABLE, PRESIDIO_AVAILABLE


def _display_scanner_status():
    """Display dynamic scanner status summary"""
    enabled_scanners = st.session_state.enabled_scanners

    # Categorize scanners
    llamafirewall_scanners = ["PromptGuard", "AlignmentCheck"]
    nemo_scanners = ["FactsChecker"]
    custom_scanners = ["DataDisclosureGuard"]

    # Count enabled scanners
    llamafirewall_enabled = sum(1 for name in llamafirewall_scanners if enabled_scanners.get(name, False))
    nemo_enabled = sum(1 for name in nemo_scanners if enabled_scanners.get(name, False))
    custom_enabled = sum(1 for name in custom_scanners if enabled_scanners.get(name, False))
    total_enabled = llamafirewall_enabled + nemo_enabled + custom_enabled

    # Display status with appropriate styling
    if total_enabled == 0:
        st.warning("⚠️ No scanners enabled")
    else:
        status_msg = f"🛡️ **{total_enabled} scanner(s) enabled:**\n\n"
        if llamafirewall_enabled > 0:
            status_msg += f"• LlamaFirewall: {llamafirewall_enabled}\n\n"
        if nemo_enabled > 0:
            status_msg += f"• NeMo GuardRails: {nemo_enabled}\n\n"
        if custom_enabled > 0:
            status_msg += f"• Custom Scanners: {custom_enabled}"
        st.success(status_msg)


def render_sidebar():
    """Render the sidebar with scanner configuration and scenario selection"""
    with st.sidebar:
        st.header("🛡️ Scanner Configuration")

        # Scanner selection with checkboxes
        st.subheader("Enable Scanners")

        # Available scanners with descriptions (ordered to match results display)
        scanner_info = {
            "AlignmentCheck": "🎯 Detects goal hijacking",
            "PromptGuard": "🔍 Detects malicious user inputs",
            "FactsChecker": "📊 Detects self-contradictions & ungrounded claims (fabricated details without evidence)",
            "DataDisclosureGuard": "🔐 Detects PII disclosure & validates intent"
        }

        # Create checkboxes for each scanner
        for scanner_name, description in scanner_info.items():
            # Check scanner availability
            is_nemo_scanner = scanner_name in ["FactsChecker"]
            is_presidio_scanner = scanner_name in ["DataDisclosureGuard"]

            is_disabled = (is_nemo_scanner and not NEMO_GUARDRAILS_AVAILABLE) or \
                         (is_presidio_scanner and not PRESIDIO_AVAILABLE)

            # Determine help text
            if is_nemo_scanner:
                help_text = description + " (Requires NeMo GuardRails)"
            elif is_presidio_scanner:
                help_text = description + " (Requires Microsoft Presidio)"
            else:
                help_text = description

            enabled = st.checkbox(
                f"{scanner_name}",
                value=st.session_state.enabled_scanners.get(scanner_name, False) and not is_disabled,
                help=help_text,
                key=f"enable_{scanner_name}",
                disabled=is_disabled
            )
            st.session_state.enabled_scanners[scanner_name] = enabled

            # Caption with availability warning
            caption_text = description
            if is_disabled:
                if is_nemo_scanner:
                    caption_text += " ⚠️ NeMo GuardRails required"
                elif is_presidio_scanner:
                    caption_text += " ⚠️ Presidio required"
            st.caption(caption_text)

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

        st.divider()

        st.header("📁 Load Custom Scenario")

        # File uploader for JSON scenarios
        uploaded_file = st.file_uploader(
            "Upload JSON scenario file",
            type=["json"],
            help="Upload a JSON file with scenario_name, agent_purpose, and messages fields"
        )

        if uploaded_file is not None:
            try:
                # Read the uploaded file
                file_content = uploaded_file.read()
                scenario_data = json.loads(file_content)

                # Validate required fields
                if "messages" not in scenario_data:
                    st.error("❌ Invalid JSON: 'messages' field is required")
                elif "agent_purpose" not in scenario_data:
                    st.error("❌ Invalid JSON: 'agent_purpose' field is required")
                else:
                    # Display scenario info
                    scenario_name = scenario_data.get("scenario_name", "Custom Scenario")
                    st.success(f"✅ Loaded: {scenario_name}")
                    st.caption(f"Messages: {len(scenario_data['messages'])}")

                    # Load button
                    if st.button("Load Custom Scenario"):
                        st.session_state.current_conversation = {
                            "purpose": scenario_data.get("agent_purpose", ""),
                            "messages": scenario_data.get("messages", [])
                        }
                        # Clear test results when loading a new scenario
                        st.session_state.test_results = []
                        st.rerun()

            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON file: {e}")
            except Exception as e:
                st.error(f"❌ Error loading file: {e}")