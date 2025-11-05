"""
Conversation builder UI components
"""

import streamlit as st
import json
from datetime import datetime


def render_conversation_builder():
    """Render the conversation builder UI"""

    # Agent Configuration
    st.subheader("🎯 Agent Purpose")
    purpose = st.text_area(
        "Agent Intended Purpose",
        value=st.session_state.current_conversation["purpose"],
        help="Define what the agent is supposed to do",
        placeholder="e.g., Check account balance and show transactions",
        height=60
    )
    st.session_state.current_conversation["purpose"] = purpose

    st.divider()
    st.subheader("💬 Conversation Builder")

    # Display current conversation
    for i, msg in enumerate(st.session_state.current_conversation["messages"]):
        if st.session_state.editing_message_index == i:
            # Editing mode for this message
            _render_message_editor(i, msg)
        else:
            # Normal display mode with edit/delete buttons
            _render_message_display(i, msg)

    # Add new message
    _render_message_adder()

    # Control buttons
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
                if st.button("✓ Update", key=f"update_{index}"):
                    st.session_state.current_conversation["messages"][index]["content"] = edited_content
                    st.session_state.editing_message_index = None
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key=f"cancel_{index}"):
                    st.session_state.editing_message_index = None
                    st.rerun()
        else:
            if msg.get("action"):
                # Editing assistant action
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
                    if st.button("✓ Update", key=f"update_{index}"):
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
                    if st.button("❌ Cancel", key=f"cancel_{index}"):
                        st.session_state.editing_message_index = None
                        st.rerun()
            else:
                # Editing regular assistant response
                edited_content = st.text_area(
                    "Edit assistant response:",
                    value=msg["content"],
                    height=80,
                    key=f"edit_assistant_{index}"
                )
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✓ Update", key=f"update_{index}"):
                        st.session_state.current_conversation["messages"][index]["content"] = edited_content
                        st.session_state.editing_message_index = None
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_{index}"):
                        st.session_state.editing_message_index = None
                        st.rerun()


def _render_message_display(index: int, msg: dict):
    """Render message display with edit/delete buttons"""
    if msg["type"] == "user":
        with st.chat_message("user"):
            col_msg, col_btns = st.columns([4, 1])
            with col_msg:
                # Use st.text() which doesn't interpret markdown at all
                st.text(msg["content"])
            with col_btns:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("✏️", key=f"edit_btn_{index}", help="Edit message"):
                        st.session_state.editing_message_index = index
                        st.rerun()
                with btn_col2:
                    if st.button("🗑️", key=f"delete_btn_{index}", help="Delete message"):
                        del st.session_state.current_conversation["messages"][index]
                        st.rerun()
    else:
        with st.chat_message("assistant"):
            col_msg, col_btns = st.columns([4, 1])
            with col_msg:
                if msg.get("action"):
                    st.write(f"**Action:** `{msg['action']}`")
                    st.write("**Thought:**")
                    st.text(msg["content"])
                    if msg.get("action_input"):
                        st.json(msg["action_input"])
                else:
                    # Use st.text() which doesn't interpret markdown at all
                    st.text(msg["content"])
            with col_btns:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("✏️", key=f"edit_btn_{index}", help="Edit message"):
                        st.session_state.editing_message_index = index
                        st.rerun()
                with btn_col2:
                    if st.button("🗑️", key=f"delete_btn_{index}", help="Delete message"):
                        del st.session_state.current_conversation["messages"][index]
                        st.rerun()


def _render_message_adder():
    """Render UI for adding new messages"""
    message_type = st.radio("Add message", ["User", "Assistant", "Assistant Action"], horizontal=True)

    if message_type == "User":
        user_content = st.text_area(
            "User message",
            value=st.session_state.input_user_content,
            height=80,
            placeholder="Enter user message... (supports multi-line text)",
            help="Type the user's message. The text area will expand as you type.",
            key="user_message_input"
        )
        # Update session state when input changes
        st.session_state.input_user_content = user_content

        if st.button("Add User Message") and user_content:
            st.session_state.current_conversation["messages"].append({
                "type": "user",
                "content": user_content
            })
            # Clear the input field
            st.session_state.input_user_content = ""
            st.rerun()

    elif message_type == "Assistant":
        assistant_content = st.text_area(
            "Assistant response",
            value=st.session_state.input_assistant_content,
            height=80,
            placeholder="Enter assistant response... (supports multi-line text)",
            help="Type the assistant's response. The text area will expand as you type.",
            key="assistant_message_input"
        )
        # Update session state when input changes
        st.session_state.input_assistant_content = assistant_content

        if st.button("Add Assistant Response") and assistant_content:
            st.session_state.current_conversation["messages"].append({
                "type": "assistant",
                "content": assistant_content
            })
            # Clear the input field
            st.session_state.input_assistant_content = ""
            st.rerun()

    else:  # Assistant Action
        col_a, col_b = st.columns(2)
        with col_a:
            action_name = st.text_input(
                "Action name",
                value=st.session_state.input_action_name,
                placeholder="e.g., transfer_funds",
                key="action_name_input"
            )
            # Update session state
            st.session_state.input_action_name = action_name

            thought = st.text_area(
                "Thought",
                value=st.session_state.input_thought,
                height=60,
                placeholder="What the assistant is thinking...",
                help="Describe the assistant's reasoning for this action",
                key="thought_input"
            )
            # Update session state
            st.session_state.input_thought = thought

        with col_b:
            params = st.text_area(
                "Parameters (JSON)",
                value=st.session_state.input_params,
                height=60,
                placeholder='{"to": "account", "amount": 100}',
                help="JSON parameters for the action",
                key="params_input"
            )
            # Update session state
            st.session_state.input_params = params

        if st.button("Add Assistant Action") and action_name and thought:
            try:
                action_input = json.loads(params) if params else {}
                st.session_state.current_conversation["messages"].append({
                    "type": "assistant",
                    "content": thought,
                    "action": action_name,
                    "action_input": action_input
                })
                # Clear all action input fields
                st.session_state.input_action_name = ""
                st.session_state.input_thought = ""
                st.session_state.input_params = ""
                st.rerun()
            except json.JSONDecodeError:
                st.error("Invalid JSON in parameters")


def _render_control_buttons():
    """Render control buttons for the conversation"""
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

    with col_btn1:
        if st.button("🧪 Run Tests", type="primary", use_container_width=True):
            # Import here to avoid circular imports
            from multi_agent_demo.firewall import run_scanner_tests
            run_scanner_tests()

    with col_btn2:
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.current_conversation = {"purpose": "", "messages": []}
            # Clear test results when clearing conversation
            st.session_state.test_results = []
            st.rerun()

    with col_btn3:
        # Export current scenario
        with st.popover("📤 Export Scenario", use_container_width=True):
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
                    label="📥 Download JSON",
                    data=export_json,
                    file_name=f"ai_guards_scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )

                st.text_area(
                    "Copy this JSON (shareable via email/Slack):",
                    value=export_json,
                    height=150,
                    help="Copy this text and share it with others"
                )
            else:
                st.info("💡 Create a conversation first to export it")

    with col_btn4:
        # Import scenario
        with st.popover("📥 Import Scenario", use_container_width=True):
            uploaded_file = st.file_uploader(
                "Choose scenario file (.json or .txt)",
                type=['json', 'txt'],
                help="Upload a .json or .txt file exported from AI Guards Testing",
                key="scenario_file_uploader"
            )

            if uploaded_file is not None:
                try:
                    # Check file extension
                    file_name = uploaded_file.name.lower()
                    if file_name.endswith('.txt'):
                        # Read as text and parse as JSON
                        content = uploaded_file.read().decode('utf-8')
                        imported_data = json.loads(content)
                    else:
                        # Read as JSON directly
                        imported_data = json.load(uploaded_file)
                    st.success("✓ File loaded successfully")

                    # Validate the imported data
                    required_fields = ['agent_purpose', 'messages']
                    if all(field in imported_data for field in required_fields):
                        st.write("**Preview:**")
                        purpose_preview = imported_data['agent_purpose'][:100]
                        if len(imported_data['agent_purpose']) > 100:
                            purpose_preview += "..."
                        st.write(f"**Purpose:** {purpose_preview}")
                        st.write(f"**Messages:** {len(imported_data['messages'])}")

                        if st.button("✓ Import Scenario", type="primary", use_container_width=True):
                            # Load the scenario into current conversation
                            st.session_state.current_conversation = {
                                "purpose": imported_data['agent_purpose'],
                                "messages": imported_data['messages']
                            }
                            # Clear any existing test results
                            st.session_state.test_results = []
                            st.success("✓ Scenario imported successfully!")
                            st.rerun()
                    else:
                        st.error("❌ Invalid scenario format. Missing required fields: agent_purpose, messages")
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON file: {str(e)}")
            else:
                st.info("📁 Upload a JSON file to import a scenario")