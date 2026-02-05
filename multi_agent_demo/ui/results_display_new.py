"""
New simplified test results display with count-based UI
Removes scores, gauges, and plots - uses only counts
"""

import streamlit as st
import pandas as pd


def _get_role_specific_number(messages: list, message_index: int, message_type: str) -> int:
    """
    Calculate role-specific message number (e.g., User #1, Assistant #2)

    Args:
        messages: Full conversation message list
        message_index: Overall message index
        message_type: "user" or "assistant"

    Returns:
        Role-specific number (1-indexed)
    """
    count = 0
    for i in range(message_index + 1):
        if i < len(messages) and messages[i].get("type") == message_type:
            count += 1
    return count


def render_overall_decision(result: dict):
    """Render overall decision badge at top"""
    st.markdown("## 🎯 Overall Decision")

    # Aggregate all scanner decisions
    all_decisions = []

    # AlignmentCheck
    if result.get("alignment_check") and "overall_decision" in result["alignment_check"]:
        all_decisions.append(result["alignment_check"]["overall_decision"])

    # PromptGuard
    if result.get("prompt_guard") and "overall_decision" in result["prompt_guard"]:
        all_decisions.append(result["prompt_guard"]["overall_decision"])

    # NeMo results (FactsChecker, DataDisclosureGuard)
    for scanner_name, scanner_result in result.get("nemo_results", {}).items():
        if "overall_decision" in scanner_result:
            all_decisions.append(scanner_result["overall_decision"])

    # Determine overall: BLOCK > WARNING > SAFE
    if "BLOCK" in all_decisions:
        overall = "BLOCK"
        icon = "🔴"
        color = "red"
    elif "WARNING" in all_decisions:
        overall = "WARNING"
        icon = "🟡"
        color = "orange"
    else:
        overall = "SAFE"
        icon = "🟢"
        color = "green"

    # Display large badge
    st.markdown(
        f"""
        <div style="
            background-color: {color};
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 20px;
        ">
            {icon} {overall}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_scanner_counts(scanner_name: str, result: dict, messages: list = None):
    """Render counts for a single scanner with role-specific message numbering"""
    if not result or "error" in result:
        st.error(f"❌ {scanner_name}: Error - {result.get('error', 'Unknown error')}")
        return

    counts = result.get("counts", {})
    overall = result.get("overall_decision", "SAFE")

    # Header with overall decision
    if overall == "BLOCK":
        st.markdown(f"### 🔴 {scanner_name}: BLOCK")
    elif overall == "WARNING":
        st.markdown(f"### 🟡 {scanner_name}: WARNING")
    else:
        st.markdown(f"### 🟢 {scanner_name}: SAFE")

    # Count summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", counts.get("total", 0))
    with col2:
        st.metric("✅ Safe", counts.get("safe", 0))
    with col3:
        st.metric("⚠️ Warning", counts.get("warning", 0))
    with col4:
        st.metric("🚫 Block", counts.get("block", 0))

    # Overall Analysis/Reason (collapsed by default, only show if not SAFE)
    if overall != "SAFE" and "reason" in result and result["reason"]:
        with st.expander("🔍 View Overall Analysis", expanded=False):
            st.markdown(result["reason"])

    # Special handling for FactsChecker
    if scanner_name == "FactsChecker":
        _render_factchecker_details(result)

    # Special handling for DataDisclosureGuard
    elif scanner_name == "DataDisclosureGuard":
        _render_datadisclosure_details(result)

    # Per-message analysis (collapsed by default, only show messages with issues)
    message_results = result.get("message_results", [])
    if message_results:
        # Filter to only non-SAFE messages
        issues_only = [msg for msg in message_results if msg.get("decision", "SAFE") != "SAFE"]

        if issues_only:
            with st.expander(f"📋 View {len(issues_only)} Message(s) with Issues", expanded=False):
                for msg_result in issues_only:
                    decision_icon = {
                        "SAFE": "🟢",
                        "WARNING": "🟡",
                        "BLOCK": "🔴"
                    }.get(msg_result.get("decision", "SAFE"), "⚪")

                    msg_idx = msg_result.get("message_index", "?")
                    msg_type = msg_result.get("message_type", "?")
                    decision = msg_result.get("decision", "SAFE")
                    reason = msg_result.get("reason", "No details available")

                    # Get role-specific number (e.g., User #1, Assistant #2)
                    if messages and isinstance(msg_idx, int):
                        role_number = _get_role_specific_number(messages, msg_idx, msg_type)
                        role_label = f"{msg_type.capitalize()} #{role_number}"
                    else:
                        role_label = f"Message #{msg_idx} ({msg_type})"

                    st.markdown(f"**{role_label}:** {decision_icon} {decision}")
                    with st.expander(f"Details for {role_label}", expanded=False):
                        st.text(reason)
                    st.divider()


def _render_factchecker_details(result: dict):
    """Render detailed FactsChecker analysis"""
    issues = result.get("issues_detected", [])
    detailed_analysis = result.get("detailed_analysis", {})
    per_message_findings = result.get("per_message_findings", [])

    # Only show details if there are issues
    if not issues and not per_message_findings:
        return

    # Show detected issues with detailed analysis
    if issues:
        with st.expander(f"🚨 Issues Detected ({len(issues)})", expanded=False):
            for issue in issues:
                if issue == "Self-Contradiction":
                    st.error(f"**{issue}**: Agent contradicted previous statements")
                elif issue == "RAG Ungroundedness":
                    st.warning(f"**{issue}**: Claims made without evidence support")
                else:
                    st.warning(f"**{issue}**")

                # Show detailed analysis for this issue
                if issue in detailed_analysis:
                    with st.expander(f"📄 {issue} - Full Analysis", expanded=False):
                        st.text(detailed_analysis[issue])

    # Show per-message findings
    if per_message_findings:
        with st.expander(f"📋 Per-Message Findings ({len(per_message_findings)} messages)", expanded=False):
            # Group by message number
            findings_by_message = {}
            for finding in per_message_findings:
                msg_num = finding["message_number"]
                if msg_num not in findings_by_message:
                    findings_by_message[msg_num] = []
                findings_by_message[msg_num].append(finding)

            for msg_num in sorted(findings_by_message.keys()):
                findings = findings_by_message[msg_num]
                issues_list = [f["issue_type"] for f in findings]

                st.markdown(f"**Message {msg_num}:** {', '.join(issues_list)}")
                st.caption(f"_Preview:_ {findings[0]['message_preview'][:100]}...")

                for finding in findings:
                    with st.expander(f"🔍 Message {msg_num} - {finding['issue_type']}", expanded=False):
                        st.text(finding['details'])


def _render_datadisclosure_details(result: dict):
    """Render detailed DataDisclosureGuard analysis"""
    pii_findings = result.get("pii_findings", [])

    # Only show details if there are PII findings
    if not pii_findings:
        return

    if pii_findings:
        # Get overall alignment status
        overall_aligned = pii_findings[0].get('is_aligned', True) if pii_findings else True

        # Collect all unique PII types
        all_pii_types = set()
        for finding in pii_findings:
            for entity in finding.get('pii_entities', []):
                all_pii_types.add(entity['type'])

        # Show alignment status
        if overall_aligned:
            st.success(f"✅ **Alignment Check:** PII collection is appropriate for stated purpose")
        else:
            st.error(f"❌ **Alignment Check:** PII collection appears misaligned with stated purpose")

        # Show PII details
        with st.expander(f"🔍 PII Details ({len(pii_findings)} occurrence(s), {len(all_pii_types)} type(s))", expanded=False):
            st.markdown(f"**Detected PII Types:** {', '.join(sorted(all_pii_types))}")
            st.markdown(f"**Overall Alignment:** {'✅ Aligned' if overall_aligned else '❌ Misaligned'}")

            # Show alignment reasoning if misaligned
            if not overall_aligned and pii_findings:
                alignment_reason = pii_findings[0].get('alignment_check', {}).get('reason', 'N/A')
                with st.expander("📄 Alignment Reasoning", expanded=False):
                    st.text(alignment_reason)

            st.divider()
            st.markdown("**PII Occurrences by Message:**")

            for idx, finding in enumerate(pii_findings, 1):
                pii_list = ', '.join([f"{e['type']}" for e in finding.get('pii_entities', [])])
                msg_type = finding.get('message_type', 'unknown')
                st.write(f"{idx}. **{msg_type.capitalize()}** message: {pii_list}")


def render_test_results_new():
    """Render test results with new count-based UI"""
    if not st.session_state.test_results:
        st.info("No test results yet. Run a test to see results here.")
        return

    latest_result = st.session_state.test_results[-1]

    # Get messages for role-specific numbering
    messages = st.session_state.current_conversation.get("messages", [])

    # Overall Decision (big badge at top)
    render_overall_decision(latest_result)

    st.divider()

    # Individual Scanner Results
    st.markdown("## 📊 Scanner Results")

    # AlignmentCheck
    if latest_result.get("alignment_check"):
        render_scanner_counts("AlignmentCheck", latest_result["alignment_check"], messages)
        st.divider()

    # PromptGuard
    if latest_result.get("prompt_guard"):
        render_scanner_counts("PromptGuard", latest_result["prompt_guard"], messages)
        st.divider()

    # NeMo scanners
    for scanner_name, scanner_result in latest_result.get("nemo_results", {}).items():
        render_scanner_counts(scanner_name, scanner_result, messages)
        st.divider()

    # Test History Summary
    if len(st.session_state.test_results) > 1:
        st.markdown("## 📈 Test History")
        st.info(f"Total tests run: {len(st.session_state.test_results)}")

        # Show recent results
        with st.expander("View Recent Tests"):
            history_data = []
            for i, test in enumerate(reversed(st.session_state.test_results[-10:]), 1):
                # Get overall decision from test
                all_decisions = []
                if test.get("alignment_check") and "overall_decision" in test["alignment_check"]:
                    all_decisions.append(test["alignment_check"]["overall_decision"])
                if test.get("prompt_guard") and "overall_decision" in test["prompt_guard"]:
                    all_decisions.append(test["prompt_guard"]["overall_decision"])
                for scanner_result in test.get("nemo_results", {}).values():
                    if "overall_decision" in scanner_result:
                        all_decisions.append(scanner_result["overall_decision"])

                if "BLOCK" in all_decisions:
                    overall = "🔴 BLOCK"
                elif "WARNING" in all_decisions:
                    overall = "🟡 WARNING"
                else:
                    overall = "🟢 SAFE"

                history_data.append({
                    "Test #": len(st.session_state.test_results) - i + 1,
                    "Overall": overall,
                    "Messages": test.get("conversation_length", 0),
                    "Time": test.get("timestamp", "")[:19]
                })

            if history_data:
                df = pd.DataFrame(history_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
