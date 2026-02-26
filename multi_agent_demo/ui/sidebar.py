"""
Sidebar UI components for scanner configuration and scenario selection
"""

import streamlit as st
import json
from multi_agent_demo.scenarios import get_predefined_scenarios, load_scenario_from_json
from multi_agent_demo.scanners import NEMO_GUARDRAILS_AVAILABLE, PRESIDIO_AVAILABLE
from multi_agent_demo.core.scanner_runner import validate_session_messages


def _load_scenario_data(purpose, messages, filename=None):
    """Load scenario data into session state and optionally auto-run tests"""
    st.session_state.current_conversation = {
        "purpose": purpose,
        "messages": messages
    }
    st.session_state.agent_purpose = purpose
    # Sync ALL widget keys that display the purpose — Streamlit widgets with
    # a `key` read from st.session_state[key] on subsequent renders, ignoring
    # the `value` param.
    st.session_state.agent_purpose_input = purpose      # common.py (deviations page)
    st.session_state.sticky_purpose_input = purpose     # realtime_page.py
    st.session_state.test_results = []
    st.session_state.loaded_scenario_filename = filename
    if st.session_state.get("auto_run_after_load", True):
        st.session_state.pending_auto_run = True
    st.rerun()


def render_sidebar():
    """Render the sidebar: scanners (primary), file upload (main usage), built-in scenarios (secondary)"""
    with st.sidebar:
        # Compact sidebar CSS
        st.markdown("""
            <style>
            [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
                gap: 0.3rem;
            }
            [data-testid="stSidebar"] .stMarkdown h3 {
                font-size: 1rem !important;
                margin-top: 0.2rem !important;
                margin-bottom: 0.2rem !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # --- 1. Scanner configuration (primary — core value) ---
        st.markdown("### Scanners")

        # Ordered: Prompt Guard, Alignment Checker, Facts Checker, Data Guard
        # Tuples: (internal_key, display_name, icon, description)
        scanner_list = [
            ("PromptGuard", "Prompt Guard", "🔍", "Detects malicious inputs"),
            ("AlignmentCheck", "Alignment Checker", "🎯", "Detects goal hijacking"),
            ("FactsChecker", "Facts Checker", "📊", "Self-contradictions & ungrounded claims"),
            ("DataDisclosureGuard", "Data Guard", "🔐", "PII disclosure & intent validation"),
        ]

        for scanner_name, display_name, icon, description in scanner_list:
            is_nemo_scanner = scanner_name in ["FactsChecker"]
            is_presidio_scanner = scanner_name in ["DataDisclosureGuard"]

            is_disabled = (is_nemo_scanner and not NEMO_GUARDRAILS_AVAILABLE) or \
                         (is_presidio_scanner and not PRESIDIO_AVAILABLE)

            if is_nemo_scanner:
                help_text = description + " (Requires NeMo GuardRails)"
            elif is_presidio_scanner:
                help_text = description + " (Requires Presidio)"
            else:
                help_text = description

            # Initialize widget key from enabled_scanners (no `value` + `key` anti-pattern)
            widget_key = f"enable_{scanner_name}"
            if widget_key not in st.session_state:
                st.session_state[widget_key] = (
                    st.session_state.enabled_scanners.get(scanner_name, False) and not is_disabled
                )

            enabled = st.checkbox(
                f"{icon} {display_name}",
                help=help_text,
                key=widget_key,
                disabled=is_disabled
            )
            st.session_state.enabled_scanners[scanner_name] = enabled

        # Compact status line
        enabled_scanners = st.session_state.enabled_scanners
        total = sum(1 for v in enabled_scanners.values() if v)
        if total == 0:
            st.warning("No scanners enabled")
        else:
            st.caption(f"{total} scanner{'s' if total != 1 else ''} active")

        st.divider()

        # --- 2. File upload (main usage) ---
        st.markdown("### Load Scenario")

        uploaded_file = st.file_uploader(
            "Load JSON scenario",
            type=["json", "txt"],
            help="Upload a JSON file (.json or .txt) with agent_purpose and messages fields",
            label_visibility="collapsed"
        )

        if uploaded_file is not None:
            try:
                file_content = uploaded_file.read()
                scenario_data = json.loads(file_content)

                if "messages" not in scenario_data:
                    st.error("Invalid JSON: 'messages' field required")
                elif "agent_purpose" not in scenario_data:
                    st.error("Invalid JSON: 'agent_purpose' field required")
                else:
                    ok, err = validate_session_messages(scenario_data["messages"])
                    if not ok:
                        st.error(f"Session too large: {err}")
                    else:
                        scenario_name = scenario_data.get("scenario_name", "Custom")
                        st.caption(f"Loaded: {scenario_name} ({len(scenario_data['messages'])} msgs)")
                        # Display full filename for copy-paste
                        st.code(uploaded_file.name, language=None)
                        if st.button("Load & Run", type="primary", use_container_width=True):
                            _load_scenario_data(
                                scenario_data.get("agent_purpose", ""),
                                scenario_data.get("messages", []),
                                filename=uploaded_file.name
                            )
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
            except Exception as e:
                st.error(f"Error: {e}")

        # Auto-run toggle — use key only (no `value`), init widget key in session state
        if "auto_run_after_load" not in st.session_state:
            st.session_state.auto_run_after_load = True
        if "auto_run_toggle" not in st.session_state:
            st.session_state.auto_run_toggle = st.session_state.auto_run_after_load

        st.checkbox(
            "Auto-run tests after load",
            key="auto_run_toggle",
            on_change=lambda: setattr(st.session_state, 'auto_run_after_load',
                                       st.session_state.auto_run_toggle)
        )

        st.divider()

        # --- 3. Built-in scenarios (secondary — collapsible) ---
        with st.expander("Built-in Scenarios", expanded=False):
            predefined_scenarios = get_predefined_scenarios()
            for name, data in predefined_scenarios.items():
                msg_count = len(data.get("messages", []))
                if st.button(
                    f"{name}",
                    key=f"scenario_{name}",
                    use_container_width=True,
                    help=f"{msg_count} messages"
                ):
                    _load_scenario_data(data["purpose"], data["messages"])
