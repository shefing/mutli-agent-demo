"""
Real-time Testing Page
Original functionality for testing agent conversations with security scanners
"""

import streamlit as st
from multi_agent_demo.ui import render_sidebar, render_conversation_builder, render_test_results_new
from multi_agent_demo.ui.common import render_page_header


def render():
    """Render the real-time testing page"""
    # Page header
    render_page_header(
        "🛡️ Real-Time",
        "Test AI agent conversations with security scanners in real-time"
    )

    # Render sidebar with scanner configuration and scenario selection
    render_sidebar()

    # Prevent wide content (tables, JSON, code blocks) in the conversation panel
    # from overflowing into the results panel — clip with horizontal scrollbar
    st.markdown("""
        <style>
        /* Left column: clip overflow so wide tables/code get a scrollbar */
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
            overflow-x: auto;
        }
        /* Right column: render above any residual overflow */
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
            position: relative;
            z-index: 10;
        }
        </style>
    """, unsafe_allow_html=True)

    # Main content area with two columns
    col1, col2 = st.columns([3, 2])

    with col1:
        # Render conversation builder (left panel)
        render_conversation_builder()

    with col2:
        # Render test results (right panel)
        render_test_results_new()
