"""
Real-time Testing Page
Original functionality for testing agent conversations with security scanners
"""

import streamlit as st
from multi_agent_demo.ui import render_sidebar, render_test_results_new
from multi_agent_demo.ui.conversation_builder import render_conversation_builder


def render():
    """Render the real-time testing page"""

    # Global CSS
    st.markdown("""
        <style>
        /* Dense top: enough clearance for Streamlit toolbar, but compact */
        [data-testid="stMainBlockContainer"] {
            padding-top: 2.5rem !important;
            font-size: 1rem;
        }

        /* Compact page header */
        .page-header {
            margin-bottom: 0.3rem;
        }
        .page-header h1 {
            font-size: 1.4rem;
            margin: 0 0 0.1rem 0;
            line-height: 1.2;
        }
        .page-header p {
            font-size: 0.95rem;
            color: #999;
            margin: 0;
        }

        /* Heading sizes */
        .stMarkdown h2 {
            font-size: 1.3rem !important;
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        .stMarkdown h3 {
            font-size: 1.2rem !important;
            margin-top: 0.4rem !important;
            margin-bottom: 0.4rem !important;
        }

        /* Left column: clip overflow so wide tables/code get a scrollbar */
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
            overflow-x: auto;
        }
        /* Right column: render above any residual overflow */
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
            position: relative;
            z-index: 10;
        }

        /* Override primary button color to blue for Run CTA */
        [data-testid="stColumn"]:last-child button[kind="primary"] {
            background-color: #2563eb;
            border-color: #2563eb;
        }
        [data-testid="stColumn"]:last-child button[kind="primary"]:hover {
            background-color: #1d4ed8;
            border-color: #1d4ed8;
        }

        /* Larger Agent Purpose label */
        [data-testid="stTextArea"] label p {
            font-size: 1.05rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Compact page header (dense)
    st.markdown(
        '<div class="page-header">'
        '<h1>Omniguard: AI Agent Behavioral Governance</h1>'
        '<p>Monitor Agent conversations with dedicated scanners</p>'
        '</div>',
        unsafe_allow_html=True
    )

    # Render sidebar
    render_sidebar()

    # Handle auto-run after scenario load
    run_clicked = False
    if st.session_state.get("pending_auto_run"):
        st.session_state.pending_auto_run = False
        run_clicked = True

    # Two-column layout: purpose + conversation (left), run + results (right)
    col1, col2 = st.columns([3, 2])

    with col1:
        # Scenario filename + Agent Purpose in left column only
        with st.container(border=True):
            loaded_file = st.session_state.get("loaded_scenario_filename")
            if loaded_file:
                st.markdown(
                    f'<div style="color:#aaa; font-size:1rem; margin-bottom:4px;">'
                    f'Scenario: <code style="user-select:all; cursor:text; font-size:1rem;">{loaded_file}</code></div>',
                    unsafe_allow_html=True
                )

            # Sync widget key from conversation state (widget reads from
            # session_state[key], not from `value` param after first render)
            purpose_val = st.session_state.current_conversation["purpose"]
            if "sticky_purpose_input" not in st.session_state:
                st.session_state.sticky_purpose_input = purpose_val
            line_count = purpose_val.count('\n') + 1
            char_lines = max(1, len(purpose_val) // 70)
            effective_lines = max(line_count, char_lines)
            height = max(38, min(200, 18 + 20 * effective_lines))
            purpose = st.text_area(
                "Agent Purpose",
                placeholder="e.g., Check account balance and show transactions",
                height=height,
                key="sticky_purpose_input"
            )
            st.session_state.current_conversation["purpose"] = purpose

        render_conversation_builder()

    with col2:
        # Run button at top of results column
        run_clicked = st.button("Run", type="primary", use_container_width=True, key="sticky_run_tests") or run_clicked

        # Run tests if triggered
        if run_clicked:
            from multi_agent_demo.firewall import run_scanner_tests
            with st.status("Running scanners...", expanded=False):
                run_scanner_tests()

        render_test_results_new()
