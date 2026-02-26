"""
Conversation builder UI components
"""

import streamlit as st
import json
from datetime import datetime
from multi_agent_demo.core.scanner_runner import validate_session_messages


def _get_message_scan_decision(msg_index: int, msg_type: str) -> str | None:
    """Get the worst scan decision for a specific message across ALL scanners.

    Aggregates results from AlignmentCheck, PromptGuard, DataDisclosureGuard
    (which use message_results with message_index) and FactsChecker (which uses
    per_message_findings with 1-based assistant message_number).

    Returns: 'SAFE', 'WARNING', 'BLOCK', or None if not scanned.
    """
    if not st.session_state.test_results:
        return None

    latest = st.session_state.test_results[-1]
    has_any_results = False
    worst = "SAFE"

    def _escalate(current, new_decision):
        """Return the more severe decision"""
        severity = {"SAFE": 0, "WARNING": 1, "BLOCK": 2}
        if severity.get(new_decision, 0) > severity.get(current, 0):
            return new_decision
        return current

    # Check AlignmentCheck (assistant messages, uses message_index 0-based)
    if latest.get("alignment_check"):
        has_any_results = True
        for mr in latest["alignment_check"].get("message_results", []):
            if mr.get("message_index") == msg_index:
                worst = _escalate(worst, mr.get("decision", "SAFE"))

    # Check PromptGuard (user messages, uses message_index 0-based)
    if latest.get("prompt_guard"):
        has_any_results = True
        for mr in latest["prompt_guard"].get("message_results", []):
            if mr.get("message_index") == msg_index:
                worst = _escalate(worst, mr.get("decision", "SAFE"))

    # Check NeMo scanners
    for scanner_name, scanner_result in latest.get("nemo_results", {}).items():
        has_any_results = True

        # DataDisclosureGuard uses message_results with message_index (0-based)
        for mr in scanner_result.get("message_results", []):
            if mr.get("message_index") == msg_index:
                worst = _escalate(worst, mr.get("decision", "SAFE"))

        # FactsChecker uses per_message_findings with message_number (1-based assistant index)
        if scanner_name == "FactsChecker" and msg_type == "assistant":
            messages = st.session_state.current_conversation.get("messages", [])
            # Calculate 1-based assistant number for this message_index
            assistant_num = 0
            for i in range(msg_index + 1):
                if i < len(messages) and messages[i].get("type") == "assistant":
                    assistant_num += 1

            # Check per_message_findings
            for finding in scanner_result.get("per_message_findings", []):
                if finding.get("message_number") == assistant_num:
                    issue_type = finding.get("issue_type", "")
                    if "Contradiction" in issue_type:
                        worst = _escalate(worst, "BLOCK")
                    else:
                        worst = _escalate(worst, "WARNING")

            # Also check overall decision if there are issues detected
            if scanner_result.get("overall_decision") == "BLOCK" and msg_type == "assistant":
                # Self-contradiction applies to all assistant messages
                if "Self-Contradiction" in scanner_result.get("issues_detected", []):
                    worst = _escalate(worst, "WARNING")  # Mark all assistant msgs at least WARNING

    if has_any_results:
        return worst
    return None


def _decision_border_color(decision: str | None) -> str:
    """Return CSS border color for a scan decision"""
    if decision == "BLOCK":
        return "#e74c3c"
    elif decision == "WARNING":
        return "#f39c12"
    elif decision == "SAFE":
        return "#27ae60"
    return "#555"


def _role_badge_html(role: str, number: int, decision: str | None, index: int = None) -> str:
    """Generate an HTML badge for a message role with decision color"""
    color = _decision_border_color(decision)
    prefix = "U" if role == "user" else "A"
    badge = f'<span style="background:{color}; color:white; padding:3px 10px; border-radius:4px; font-size:0.9rem; font-weight:bold;">{prefix}#{number}</span>'
    if index is not None:
        badge += (
            f'<span class="msg-actions-inline">'
            f'<a href="?edit_msg={index}" target="_self" title="Edit">&#9998;</a>'
            f'<a href="?delete_msg={index}" target="_self" title="Delete">&#128465;</a>'
            f'</span>'
        )
    return badge


def render_conversation_builder():
    """Render the conversation builder UI"""

    # CSS for hover-only edit/delete icons inside message headers
    st.markdown("""
        <style>
        .msg-actions-inline {
            opacity: 0;
            transition: opacity 0.15s;
            margin-left: 8px;
            display: inline;
        }
        .msg-wrapper:hover .msg-actions-inline {
            opacity: 1;
        }
        .msg-actions-inline a {
            color: #888;
            text-decoration: none;
            font-size: 0.85rem;
            margin-left: 6px;
            cursor: pointer;
        }
        .msg-actions-inline a:hover {
            color: #ccc;
        }
        </style>
    """, unsafe_allow_html=True)

    # Handle edit/delete via query params (set by inline HTML links)
    params = st.query_params
    if "edit_msg" in params:
        try:
            st.session_state.editing_message_index = int(params["edit_msg"])
        except (ValueError, TypeError):
            pass
        st.query_params.clear()
        st.rerun()
    if "delete_msg" in params:
        try:
            idx = int(params["delete_msg"])
            msgs = st.session_state.current_conversation["messages"]
            if 0 <= idx < len(msgs):
                del msgs[idx]
        except (ValueError, TypeError):
            pass
        st.query_params.clear()
        st.rerun()

    messages = st.session_state.current_conversation["messages"]
    msg_count = len(messages)
    conv_cols = st.columns([3, 1])
    with conv_cols[0]:
        st.subheader("Conversation")
    with conv_cols[1]:
        st.markdown(
            f"<div style='padding-top:10px; color:#888; font-size:0.95rem; text-align:right;'>"
            f"{msg_count} message{'s' if msg_count != 1 else ''}</div>",
            unsafe_allow_html=True
        )
    user_count = 0
    assistant_count = 0

    if not messages:
        st.caption("No messages yet. Add messages below or load a scenario from the sidebar.")

    for i, msg in enumerate(messages):
        if msg["type"] == "user":
            user_count += 1
            role_number = user_count
        else:
            assistant_count += 1
            role_number = assistant_count

        if st.session_state.editing_message_index == i:
            _render_message_editor(i, msg)
        else:
            decision = _get_message_scan_decision(i, msg["type"])
            _render_message_display(i, msg, role_number, decision)

    # Add new message (collapsible)
    with st.expander("Add message", expanded=len(messages) == 0):
        _render_message_adder()

    # Control buttons (export + clear only — Run Tests is in sticky bar)
    _render_control_buttons()


def _render_message_editor(index: int, msg: dict):
    """Render message editor UI"""
    with st.container():
        if msg["type"] == "user":
            edited_content = st.text_area(
                "Edit user message:",
                value=msg["content"],
                height=80,
                key=f"edit_user_{index}"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update", key=f"update_{index}"):
                    st.session_state.current_conversation["messages"][index]["content"] = edited_content
                    st.session_state.editing_message_index = None
                    st.rerun()
            with col2:
                if st.button("Cancel", key=f"cancel_{index}"):
                    st.session_state.editing_message_index = None
                    st.rerun()
        else:
            if msg.get("action"):
                edited_action = st.text_input(
                    "Edit action name:",
                    value=msg.get("action", ""),
                    key=f"edit_action_{index}"
                )
                edited_content = st.text_area(
                    "Edit thought:",
                    value=msg["content"],
                    height=60,
                    key=f"edit_thought_{index}"
                )
                edited_params = st.text_area(
                    "Edit parameters (JSON):",
                    value=json.dumps(msg.get("action_input", {}), indent=2),
                    height=60,
                    key=f"edit_params_{index}"
                )
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update", key=f"update_{index}"):
                        try:
                            action_input = json.loads(edited_params) if edited_params else {}
                            st.session_state.current_conversation["messages"][index].update({
                                "content": edited_content,
                                "action": edited_action,
                                "action_input": action_input
                            })
                            st.session_state.editing_message_index = None
                            st.rerun()
                        except json.JSONDecodeError:
                            st.error("Invalid JSON in parameters")
                with col2:
                    if st.button("Cancel", key=f"cancel_{index}"):
                        st.session_state.editing_message_index = None
                        st.rerun()
            else:
                edited_content = st.text_area(
                    "Edit agent response:",
                    value=msg["content"],
                    height=80,
                    key=f"edit_assistant_{index}"
                )
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update", key=f"update_{index}"):
                        st.session_state.current_conversation["messages"][index]["content"] = edited_content
                        st.session_state.editing_message_index = None
                        st.rerun()
                with col2:
                    if st.button("Cancel", key=f"cancel_{index}"):
                        st.session_state.editing_message_index = None
                        st.rerun()


def _render_message_display(index: int, msg: dict, role_number: int, decision: str | None):
    """Render message display with colored border and visual differentiation between user/agent"""
    border_color = _decision_border_color(decision)
    badge = _role_badge_html(msg["type"], role_number, decision, index=index)

    # Visual differentiation: user messages have lighter bg, agent messages have slightly different bg
    if msg["type"] == "user":
        bg_color = "rgba(100, 149, 237, 0.06)"  # subtle blue tint for user
        role_label = "User"
    else:
        bg_color = "rgba(255, 255, 255, 0.03)"  # neutral for agent
        role_label = "Agent"

    if msg["type"] == "user":
        content_text = msg["content"].replace("\n", "<br>")
        msg_html = f"""
        <div class="msg-wrapper" id="msg-{index}">
            <div style="border-left: 4px solid {border_color}; padding: 10px 14px; margin: 4px 0; border-radius: 0 6px 6px 0; background: {bg_color};">
                <div style="margin-bottom:4px;">
                    {badge} <span style="color:#6495ED; font-size:0.95rem; margin-left:4px; font-weight:500;">{role_label}</span>
                </div>
                <div style="font-size:1rem; line-height:1.5;">{content_text}</div>
            </div>
        </div>
        """
        st.markdown(msg_html, unsafe_allow_html=True)
    else:
        if msg.get("action"):
            thought_text = msg["content"].replace("\n", "<br>")
            params_text = json.dumps(msg.get("action_input", {}), indent=2)
            msg_html = f"""
            <div class="msg-wrapper" id="msg-{index}">
                <div style="border-left: 4px solid {border_color}; padding: 10px 14px; margin: 4px 0; border-radius: 0 6px 6px 0; background: {bg_color};">
                    <div style="margin-bottom:4px;">
                        {badge} <span style="color:#aaa; font-size:0.95rem; margin-left:4px;">{role_label} &middot; <code>{msg['action']}</code></span>
                    </div>
                    <div style="font-size:0.95rem; color:#aaa; margin-bottom:2px;">{thought_text}</div>
                    <pre style="font-size:0.9rem; background:rgba(0,0,0,0.2); padding:6px; border-radius:4px; margin:4px 0 0 0; overflow-x:auto;">{params_text}</pre>
                </div>
            </div>
            """
            st.markdown(msg_html, unsafe_allow_html=True)
        else:
            content_text = msg["content"].replace("\n", "<br>")
            msg_html = f"""
            <div class="msg-wrapper" id="msg-{index}">
                <div style="border-left: 4px solid {border_color}; padding: 10px 14px; margin: 4px 0; border-radius: 0 6px 6px 0; background: {bg_color};">
                    <div style="margin-bottom:4px;">
                        {badge} <span style="color:#aaa; font-size:0.95rem; margin-left:4px; font-weight:500;">{role_label}</span>
                    </div>
                    <div style="font-size:1rem; line-height:1.5;">{content_text}</div>
                </div>
            </div>
            """
            st.markdown(msg_html, unsafe_allow_html=True)


def _render_message_adder():
    """Render UI for adding new messages"""
    message_type = st.radio("Type", ["User", "Agent", "Agent Action"], horizontal=True, label_visibility="collapsed")

    # Note: widgets use `key` without `value` — Streamlit reads the widget's
    # current value from st.session_state[key].  Passing both `value` and `key`
    # causes `value` to be ignored after first render and emits browser warnings.

    if message_type == "User":
        user_content = st.text_area(
            "User message",
            height=80,
            placeholder="Enter user message...",
            label_visibility="collapsed",
            key="user_message_input"
        )
        st.session_state.input_user_content = user_content

        if st.button("Add User Message") and user_content:
            st.session_state.current_conversation["messages"].append({
                "type": "user",
                "content": user_content
            })
            st.session_state.input_user_content = ""
            st.session_state.user_message_input = ""
            st.rerun()

    elif message_type == "Agent":
        assistant_content = st.text_area(
            "Agent response",
            height=80,
            placeholder="Enter agent response...",
            label_visibility="collapsed",
            key="assistant_message_input"
        )
        st.session_state.input_assistant_content = assistant_content

        if st.button("Add Agent Response") and assistant_content:
            st.session_state.current_conversation["messages"].append({
                "type": "assistant",
                "content": assistant_content
            })
            st.session_state.input_assistant_content = ""
            st.session_state.assistant_message_input = ""
            st.rerun()

    else:  # Agent Action
        col_a, col_b = st.columns(2)
        with col_a:
            action_name = st.text_input(
                "Action name",
                placeholder="e.g., transfer_funds",
                key="action_name_input"
            )
            st.session_state.input_action_name = action_name

            thought = st.text_area(
                "Thought",
                height=60,
                placeholder="What the agent is thinking...",
                key="thought_input"
            )
            st.session_state.input_thought = thought

        with col_b:
            params = st.text_area(
                "Parameters (JSON)",
                height=60,
                placeholder='{"to": "account", "amount": 100}',
                key="params_input"
            )
            st.session_state.input_params = params

        if st.button("Add Agent Action") and action_name and thought:
            try:
                action_input = json.loads(params) if params else {}
                st.session_state.current_conversation["messages"].append({
                    "type": "assistant",
                    "content": thought,
                    "action": action_name,
                    "action_input": action_input
                })
                st.session_state.input_action_name = ""
                st.session_state.action_name_input = ""
                st.session_state.input_thought = ""
                st.session_state.thought_input = ""
                st.session_state.input_params = ""
                st.session_state.params_input = ""
                st.rerun()
            except json.JSONDecodeError:
                st.error("Invalid JSON in parameters")


def _render_control_buttons():
    """Render control buttons — export and clear only (Run Tests is in sticky bar)"""
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("Clear Conversation", use_container_width=True):
            st.session_state.current_conversation = {"purpose": "", "messages": []}
            st.session_state.test_results = []
            st.session_state.loaded_scenario_filename = None
            st.rerun()

    with col_btn2:
        with st.popover("Export Scenario", use_container_width=True):
            if st.session_state.current_conversation["messages"]:
                export_data = {
                    "scenario_name": "Exported Scenario",
                    "agent_purpose": st.session_state.current_conversation["purpose"],
                    "messages": st.session_state.current_conversation["messages"],
                    "exported_at": datetime.now().isoformat(),
                    "format_version": "1.0"
                }

                export_json = json.dumps(export_data, indent=2, ensure_ascii=False)

                st.download_button(
                    label="Download JSON",
                    data=export_json,
                    file_name=f"ai_guards_scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )

                st.text_area(
                    "Copy JSON:",
                    value=export_json,
                    height=150
                )
            else:
                st.info("Create a conversation first to export it")
