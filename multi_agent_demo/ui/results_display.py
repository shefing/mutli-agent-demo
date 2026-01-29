"""
Test results display UI components
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def _render_result_summary(result: dict):
    """Render overall test result summary at the top"""
    st.subheader("📊 Test Results Summary")

    # Count results (3 categories: Blocked, Warnings, Safe)
    blocked_count = 0
    safe_count = 0
    warning_count = 0

    # Check AlignmentCheck
    if result["alignment_check"] and "error" not in result["alignment_check"]:
        ac = result["alignment_check"]
        # Support both old and new formats
        if "overall_decision" in ac:
            # New count-based format
            if ac["overall_decision"] == "BLOCK":
                blocked_count += 1
            elif ac["overall_decision"] == "WARNING":
                warning_count += 1
            else:
                safe_count += 1
        elif "is_safe" in ac:
            # Old format
            if not ac["is_safe"]:
                blocked_count += 1
            else:
                safe_count += 1
    elif result["alignment_check"] and "error" in result["alignment_check"]:
        blocked_count += 1  # Errors are treated as blocked

    # Check PromptGuard
    for pg in result.get("prompt_guard", []):
        if "error" not in pg:
            # Support both old and new formats
            if "decision" in pg:
                # New format
                if pg["decision"] == "BLOCK":
                    blocked_count += 1
                elif pg["decision"] == "WARNING":
                    warning_count += 1
                else:
                    safe_count += 1
            elif "is_safe" in pg:
                # Old format
                if not pg["is_safe"]:
                    blocked_count += 1
                else:
                    safe_count += 1
        else:
            blocked_count += 1  # Errors are treated as blocked

    # Check NeMo results
    # Special handling for FactsChecker - count both blocking issues AND warnings separately
    for scanner_name, scanner_result in result.get("nemo_results", {}).items():
        if "error" not in scanner_result:
            if scanner_name == "FactsChecker" and "issues_detected" in scanner_result:
                # Count specific issue types for FactsChecker
                issues = scanner_result.get("issues_detected", [])
                has_blocking = "Self-Contradiction" in issues
                has_warning = "RAG Ungroundedness" in issues

                if has_blocking:
                    blocked_count += 1
                if has_warning:
                    warning_count += 1
                if not has_blocking and not has_warning:
                    safe_count += 1
            else:
                # Other scanners - use decision field
                decision = scanner_result.get("decision", "")
                if decision == "BLOCK":
                    blocked_count += 1
                elif decision == "WARNING":
                    warning_count += 1
                elif decision in ["SAFE", "ALLOW"]:
                    safe_count += 1
                elif "is_safe" in scanner_result:
                    # Fallback to old format
                    if scanner_result["is_safe"]:
                        safe_count += 1
                    else:
                        blocked_count += 1
                else:
                    blocked_count += 1
        else:
            blocked_count += 1  # Errors are treated as blocked

    # Display summary (3 columns only)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🚫 Blocked", blocked_count)
    with col2:
        st.metric("⚠️ Warnings", warning_count)
    with col3:
        st.metric("✅ Safe", safe_count)

    # Overall verdict (3 states only)
    if blocked_count > 0:
        st.error("🚨 **OVERALL: BLOCKED** - One or more scanners detected threats or errors")
    elif warning_count > 0:
        st.warning("⚠️ **OVERALL: WARNING** - Potential risks detected")
    else:
        st.success("✅ **OVERALL: SAFE** - All scanners passed")


def render_test_results():
    """Render test results display"""
    if not st.session_state.test_results:
        return

    latest_result = st.session_state.test_results[-1]

    # Result Summary at top
    _render_result_summary(latest_result)

    st.divider()

    # AlignmentCheck Results
    _render_alignment_check_results(latest_result)

    # PromptGuard Results
    _render_prompt_guard_results(latest_result)

    # NeMo GuardRails Results (includes DataDisclosureGuard)
    _render_nemo_results(latest_result)

    # History chart
    _render_history_chart()


def _render_alignment_check_results(result: dict):
    """Render AlignmentCheck scanner results"""
    st.subheader("AlignmentCheck Scanner")
    ac_result = result["alignment_check"]

    if ac_result is None:
        st.info("🔒 AlignmentCheck scanner was disabled for this test")
    elif "error" not in ac_result:
        # Support both old and new formats
        if "overall_decision" in ac_result:
            # New count-based format
            decision = ac_result["overall_decision"]
            if decision == "SAFE":
                st.success(f"✅ {decision}")
            elif decision == "WARNING":
                st.warning(f"⚠️ {decision}")
            else:
                st.error(f"🚫 {decision}")

            # Show counts if available
            if "counts" in ac_result:
                counts = ac_result["counts"]
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Messages", counts["total"])
                with col2:
                    st.metric("✅ Safe", counts["safe"])
                with col3:
                    st.metric("⚠️ Warning", counts.get("warning", 0))
                with col4:
                    st.metric("🚫 Blocked", counts["block"])
        else:
            # Old format with score
            if ac_result.get("is_safe"):
                st.success(f"✅ {ac_result.get('decision', 'SAFE')}")
            else:
                st.error(f"🚫 {ac_result.get('decision', 'BLOCK')}")

            # Risk gauge - only for old format
            if "score" in ac_result:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=ac_result["score"],
                    number={"font": {"size": 24}, "suffix": " Risk"},
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Risk Level", "font": {"size": 16}},
                    gauge={
                        "axis": {"range": [0, 1], "tickwidth": 2, "tickcolor": "darkred"},
                        "bar": {"color": "red", "thickness": 0.8},  # Always red
                        "bgcolor": "lightgray",
                        "borderwidth": 2,
                        "bordercolor": "darkred",
                        "steps": [
                            {"range": [0, 0.3], "color": "rgba(144, 238, 144, 0.3)"},  # Light green zone (safe)
                            {"range": [0.3, 0.7], "color": "rgba(255, 255, 0, 0.3)"},  # Light yellow zone (warning)
                            {"range": [0.7, 1], "color": "rgba(255, 0, 0, 0.2)"}       # Light red zone (danger)
                        ]
                    }
                ))
                fig_gauge.update_layout(height=188, showlegend=False, margin={"l": 20, "r": 20, "t": 20, "b": 20})
                st.plotly_chart(fig_gauge, use_container_width=True, key="alignment_check_gauge")

                # Explain what the score means
                st.caption("📊 **Risk Score:** 0.0-0.3 = Safe (green) | 0.3-0.7 = Warning (yellow) | 0.7-1.0 = Danger (red)")
                st.caption(f"🔍 **This score ({ac_result['score']:.1f}):** {'Low risk - agent behavior is aligned' if ac_result['score'] < 0.3 else 'Medium risk - potential concerns detected' if ac_result['score'] < 0.7 else 'High risk - significant misalignment detected'}")

        # Determine analysis type and display compactly
        reason = ac_result.get('reason', 'No detailed reason provided')
        reason_lower = reason.lower() if reason else ''

        # Check for quantitative misalignment
        if any(word in reason_lower for word in ['numeric', 'quantity', 'discrepancy', 'orders', 'items', 'requested']):
            # Quantitative misalignment - show with specific title
            with st.expander("📊 Quantitative Misalignment Analysis", expanded=not ac_result["is_safe"]):
                st.markdown(f"<small>{reason}</small>", unsafe_allow_html=True)
        elif any(word in reason_lower for word in ['policy', 'consistent', 'equal', 'treatment']):
            # Policy consistency issue
            with st.expander("⚖️ Policy Consistency Analysis", expanded=not ac_result["is_safe"]):
                st.markdown(f"<small>{reason}</small>", unsafe_allow_html=True)
        elif any(word in reason_lower for word in ['pii', 'personal', 'disclosure', 'collecting']):
            # PII alignment issue
            with st.expander("🔒 Data Privacy Analysis", expanded=not ac_result["is_safe"]):
                st.markdown(f"<small>{reason}</small>", unsafe_allow_html=True)
        else:
            # General alignment analysis
            with st.expander("🔍 Alignment Analysis", expanded=not ac_result["is_safe"]):
                st.markdown(f"<small>{reason}</small>", unsafe_allow_html=True)
    else:
        st.error(f"❌ AlignmentCheck Error")
        st.markdown(ac_result['error'])
        if 'retry_hint' in ac_result:
            st.info(f"💡 **Tip:** {ac_result['retry_hint']}")


def _render_prompt_guard_results(result: dict):
    """Render PromptGuard scanner results"""
    st.subheader("PromptGuard Scanner")
    if result["prompt_guard"]:
        # Analyze results to create summary
        blocked_messages = []
        safe_messages = []
        error_messages = []

        for idx, pg_result in enumerate(result["prompt_guard"], 1):
            if "error" in pg_result:
                error_messages.append(idx)
            else:
                # Support both old and new formats
                if "decision" in pg_result:
                    # New format
                    if pg_result["decision"] in ["BLOCK"]:
                        blocked_messages.append(idx)
                    else:
                        safe_messages.append(idx)
                elif "is_safe" in pg_result:
                    # Old format
                    if not pg_result["is_safe"]:
                        blocked_messages.append(idx)
                    else:
                        safe_messages.append(idx)

        # Show overall decision
        if error_messages:
            st.error("🚫 BLOCKED (Scanner Error)")
        elif blocked_messages:
            st.error("🚫 BLOCKED")
        else:
            st.success("✅ ALLOW")

        # Show summary message
        total_messages = len(result["prompt_guard"])
        if blocked_messages:
            blocked_str = ', '.join(map(str, blocked_messages))
            st.info(f"**Analysis:** Messages {blocked_str} contain malicious patterns or prompt injection attempts. See per-message analysis below.")
        elif error_messages:
            error_str = ', '.join(map(str, error_messages))
            st.info(f"**Analysis:** Scanner encountered errors on messages {error_str}. See details below.")
        else:
            st.info(f"**Analysis:** All {total_messages} user message(s) are safe - no malicious patterns detected.")

        # Show per-message details only if there are issues (blocked or errors)
        if blocked_messages or error_messages:
            st.markdown("---")
            st.markdown("**📋 Per-Message Analysis:**")
            st.caption("Only showing messages with issues")

            for idx, pg_result in enumerate(result["prompt_guard"], 1):
                # Only show if this message has an issue
                if idx in blocked_messages or idx in error_messages:
                    if "error" not in pg_result:
                        # Blocked message
                        reason = pg_result.get('reason', 'Prompt injection detected')
                        st.markdown(f"**Message {idx}:** 🚫 Blocked")
                        with st.expander(f"🔍 View Message {idx} Details"):
                            st.error(f"**Detection:** {reason}")
                            st.caption(f"**Input Preview:** {pg_result['message']}")
                            st.caption(f"**Score:** {pg_result.get('score', 'N/A')} | **Decision:** {pg_result.get('decision', 'N/A')}")
                    else:
                        # Error message
                        st.markdown(f"**Message {idx}:** ❌ Error")
                        # Check if this is a Streamlit Cloud compatibility issue
                        if "streamlit_cloud_note" in pg_result:
                            with st.expander(f"🔍 View Message {idx} Error Details"):
                                st.error(f"⚠️ **Streamlit Cloud Compatibility Issue**")
                                st.warning("PromptGuard scanner uses models that may not be compatible with Streamlit Cloud's environment. This scanner works on local deployments.")
                                st.code(pg_result['error'])
                        else:
                            with st.expander(f"🔍 View Message {idx} Error Details"):
                                st.error(f"Error: {pg_result['error']}")
    else:
        st.info("🔒 No user messages to scan with PromptGuard")


def _render_nemo_results(result: dict):
    """Render NeMo GuardRails scanner results"""
    nemo_results = result.get("nemo_results", {})
    if nemo_results:
        for scanner_name, scanner_result in nemo_results.items():
            st.subheader(f"{scanner_name} Scanner")
            if "error" not in scanner_result:
                # Decision indicator with severity levels
                decision = scanner_result.get('decision', scanner_result.get('overall_decision', 'UNKNOWN'))
                if decision == "BLOCK":
                    st.error(f"🚫 {decision}")
                elif decision == "WARNING":
                    st.warning(f"⚠️ {decision}")
                elif decision in ["SAFE", "ALLOW"]:
                    st.success(f"✅ {decision}")
                elif "is_safe" in scanner_result and scanner_result["is_safe"]:
                    st.success(f"✅ {decision}")
                else:
                    st.error(f"🚫 {decision}")

                # Show counts if available (new format)
                if "counts" in scanner_result:
                    counts = scanner_result["counts"]
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Messages", counts["total"])
                    with col2:
                        st.metric("✅ Safe", counts["safe"])
                    with col3:
                        st.metric("⚠️ Warning", counts.get("warning", 0))
                    with col4:
                        st.metric("🚫 Blocked", counts["block"])

                # Risk gauge - only for old format with score
                if "score" in scanner_result:
                    fig_gauge = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=scanner_result["score"],
                        number={"font": {"size": 24}, "suffix": " Risk"},
                        domain={"x": [0, 1], "y": [0, 1]},
                        title={"text": "Risk Level", "font": {"size": 16}},
                        gauge={
                            "axis": {"range": [0, 1], "tickwidth": 2, "tickcolor": "darkred"},
                            "bar": {"color": "red", "thickness": 0.8},  # Always red
                            "bgcolor": "lightgray",
                            "borderwidth": 2,
                            "bordercolor": "darkred",
                            "steps": [
                                {"range": [0, 0.3], "color": "rgba(144, 238, 144, 0.3)"},  # Light green zone (safe)
                                {"range": [0.3, 0.7], "color": "rgba(255, 255, 0, 0.3)"},  # Light yellow zone (warning)
                                {"range": [0.7, 1], "color": "rgba(255, 0, 0, 0.2)"}       # Light red zone (danger)
                            ]
                        }
                    ))
                    fig_gauge.update_layout(height=188, showlegend=False, margin={"l": 20, "r": 20, "t": 20, "b": 20})
                    st.plotly_chart(fig_gauge, use_container_width=True, key=f"{scanner_name.lower()}_gauge")

                    # Explain what the score means
                    st.caption("📊 **Risk Score:** 0.0-0.3 = Safe (green) | 0.3-0.7 = Warning (yellow) | 0.7-1.0 = Danger (red)")
                    score_explanation = ""
                    if scanner_result['score'] < 0.3:
                        score_explanation = "Low risk - content appears safe"
                    elif scanner_result['score'] < 0.7:
                        score_explanation = "Medium risk - potential issues detected"
                    else:
                        score_explanation = "High risk - significant concerns detected"
                    st.caption(f"🔍 **This score ({scanner_result['score']:.1f}):** {score_explanation}")

                # Show analysis with expandable full response
                if "reason" in scanner_result:
                    st.info(f"**Analysis:** {scanner_result['reason']}")

                # Special handling for FactsChecker comprehensive checks
                if scanner_name == "FactsChecker" and "checks_performed" in scanner_result:
                    checks = scanner_result["checks_performed"]
                    issues = scanner_result.get("issues_detected", [])
                    detailed_analysis = scanner_result.get("detailed_analysis", {})
                    per_message_findings = scanner_result.get("per_message_findings", [])

                    # Show which checks were performed
                    st.markdown("**Checks Performed:**")
                    check_cols = st.columns(2)
                    with check_cols[0]:
                        if checks.get("self_contradiction"):
                            st.markdown("✅ Self-Contradiction")
                        else:
                            st.markdown("➖ Self-Contradiction")
                    with check_cols[1]:
                        if checks.get("rag_ungroundedness"):
                            st.markdown("✅ RAG Ungroundedness")
                        else:
                            st.markdown("➖ RAG Ungroundedness")

                    # Show detected issues summary
                    if issues:
                        st.markdown("**Issues Detected:**")
                        for issue in issues:
                            if issue == "Self-Contradiction":
                                st.error(f"⚠️ **{issue}**: Agent contradicted previous statements")
                            elif issue == "RAG Ungroundedness":
                                st.error(f"⚠️ **{issue}**: Claims made without evidence support (includes potentially fabricated details, unverified APIs, procedures, or features)")
                            else:
                                st.error(f"⚠️ {issue}")

                            # Show overall analysis for this issue type
                            if issue in detailed_analysis:
                                with st.expander(f"🔍 View {issue} Overall Summary"):
                                    st.text(detailed_analysis[issue])

                        # Show per-message findings (for RAG Ungroundedness and Fabrication)
                        if per_message_findings:
                            st.markdown("---")
                            with st.expander("📋 Per-Message Analysis", expanded=True):
                                st.caption("Each assistant message was analyzed individually")

                                # Group findings by message number
                                findings_by_message = {}
                                for finding in per_message_findings:
                                    msg_num = finding["message_number"]
                                    if msg_num not in findings_by_message:
                                        findings_by_message[msg_num] = []
                                    findings_by_message[msg_num].append(finding)

                                # Display findings per message
                                for msg_num in sorted(findings_by_message.keys()):
                                    findings = findings_by_message[msg_num]
                                    issues_list = [f["issue_type"] for f in findings]

                                    st.markdown(f"**Message {msg_num}:** {', '.join(issues_list)}")
                                    st.caption(f"_Preview:_ {findings[0]['message_preview']}")

                                    # Show detailed analysis for each issue type in this message
                                    for finding in findings:
                                        with st.expander(f"🔍 Message {msg_num} - {finding['issue_type']} Details"):
                                            st.text(finding['details'])

                # Special handling for DataDisclosureGuard PII findings
                if scanner_name == "DataDisclosureGuard" and "pii_findings" in scanner_result:
                    pii_findings = scanner_result["pii_findings"]
                    if pii_findings:
                        # Get overall alignment status (all findings share same alignment)
                        overall_aligned = pii_findings[0]['is_aligned'] if pii_findings else True
                        alignment_reason = pii_findings[0]['alignment_check'].get('reason', 'N/A') if pii_findings else 'N/A'

                        # Collect all unique PII types
                        all_pii_types = set()
                        for finding in pii_findings:
                            for entity in finding['pii_entities']:
                                all_pii_types.add(entity['type'])

                        # Show overall alignment assessment
                        if overall_aligned:
                            st.success(f"✅ **Alignment Check:** PII collection is appropriate for the stated purpose")
                        else:
                            st.error(f"❌ **Alignment Check:** PII collection appears misaligned with stated purpose")

                        with st.expander(f"🔍 View PII Details ({len(pii_findings)} occurrence(s), {len(all_pii_types)} type(s))"):
                            st.markdown(f"**Detected PII Types:** {', '.join(sorted(all_pii_types))}")
                            st.markdown(f"**Overall Alignment:** {'✅ Aligned' if overall_aligned else '❌ Misaligned'}")

                            if not overall_aligned:
                                with st.expander("📄 View Alignment Reasoning"):
                                    st.text(alignment_reason)

                            st.divider()
                            st.markdown("**PII Occurrences by Message:**")

                            for idx, finding in enumerate(pii_findings, 1):
                                pii_list = ', '.join([f"{e['type']}" for e in finding['pii_entities']])
                                st.write(f"{idx}. **{finding['message_type'].capitalize()}** message: {pii_list}")

                # Add expandable section for full AI response (for NeMo scanners)
                if "ai_response" in scanner_result and scanner_result["ai_response"]:
                    with st.expander("🔍 View Full NeMo Analysis"):
                        st.text(scanner_result['ai_response'])
            else:
                st.error(f"❌ {scanner_name} Scanner Error")
                st.markdown(scanner_result['error'])
                if 'retry_hint' in scanner_result:
                    st.info(f"💡 **Tip:** {scanner_result['retry_hint']}")


def _render_history_chart():
    """Render test history chart"""
    if len(st.session_state.test_results) > 1:
        st.subheader("📊 Test History")

        history_data = []
        for i, result in enumerate(st.session_state.test_results):
            if result["alignment_check"] and "error" not in result["alignment_check"]:
                ac = result["alignment_check"]
                # Support both old and new formats
                if "score" in ac:
                    # Old format with scores
                    history_data.append({
                        "Test": i + 1,
                        "Score": ac["score"],
                        "Decision": ac.get("decision", "UNKNOWN"),
                        "Safe": ac.get("is_safe", True)
                    })
                elif "overall_decision" in ac:
                    # New format - use counts to approximate a score
                    counts = ac.get("counts", {})
                    total = counts.get("total", 1)
                    blocked = counts.get("block", 0)
                    # Approximate score: 0 = all safe, 1 = all blocked
                    approx_score = blocked / total if total > 0 else 0
                    history_data.append({
                        "Test": i + 1,
                        "Score": approx_score,
                        "Decision": ac["overall_decision"],
                        "Safe": ac["overall_decision"] == "SAFE"
                    })

        if history_data:
            df = pd.DataFrame(history_data)
            fig_line = px.line(df, x="Test", y="Score",
                              color="Safe",
                              markers=True,
                              title="Test Results Over Time (Score = Blocked Messages / Total)")
            fig_line.add_hline(y=0.5, line_dash="dash", line_color="red",
                              annotation_text="Threshold")
            st.plotly_chart(fig_line, use_container_width=True)