"""
Common UI components shared across pages
"""

import streamlit as st


def render_agent_configuration(expanded=True):
    """
    Render agent configuration section
    This is shared between Real-time and Deviations pages

    Args:
        expanded: Whether the expander should be open by default
    """
    with st.expander("🤖 Agent Configuration", expanded=expanded):
        st.markdown("### Define Agent Purpose and Scope")

        # Agent purpose
        agent_purpose = st.text_area(
            "Agent Purpose",
            value=st.session_state.get("agent_purpose", ""),
            placeholder="e.g., Process customer support requests, manage account operations",
            help="What is the intended purpose of this agent?",
            key="agent_purpose_input"
        )
        st.session_state.agent_purpose = agent_purpose

        # Agent description (optional)
        agent_description = st.text_area(
            "Agent Description (Optional)",
            value=st.session_state.get("agent_description", ""),
            placeholder="e.g., Customer service banking agent that helps with balance checks, transfers, and account management",
            help="Additional context about the agent's capabilities and constraints",
            key="agent_description_input"
        )
        st.session_state.agent_description = agent_description

        # Display current configuration summary
        if agent_purpose:
            st.success(f"✅ Agent purpose configured: {agent_purpose[:100]}{'...' if len(agent_purpose) > 100 else ''}")
        else:
            st.info("ℹ️ Configure agent purpose to enable alignment checking")


def render_page_header(title, description):
    """
    Render consistent page header

    Args:
        title: Page title
        description: Page description
    """
    st.title(title)
    st.markdown(description)
    st.divider()
