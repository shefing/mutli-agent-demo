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

    # Count results
    blocked_count = 0
    safe_count = 0
    warning_count = 0
    error_count = 0

    # Check AlignmentCheck
    if result["alignment_check"] and "error" not in result["alignment_check"]:
        if not result["alignment_check"]["is_safe"]:
            blocked_count += 1
        else:
            safe_count += 1
    elif result["alignment_check"] and "error" in result["alignment_check"]:
        error_count += 1

    # Check PromptGuard
    for pg in result.get("prompt_guard", []):
        if "error" not in pg:
            if not pg["is_safe"]:
                blocked_count += 1  # Changed from warning_count to blocked_count
            else:
                safe_count += 1
        else:
            error_count += 1

    # Check NeMo results
    for scanner_result in result.get("nemo_results", {}).values():
        if "error" not in scanner_result:
            if not scanner_result["is_safe"]:
                blocked_count += 1
            else:
                safe_count += 1
        else:
            error_count += 1

    # Display summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🚫 Blocked", blocked_count)
    with col2:
        st.metric("⚠️ Warnings", warning_count)
    with col3:
        st.metric("✅ Safe", safe_count)
    with col4:
        st.metric("❌ Errors", error_count)

    # Overall verdict
    if blocked_count > 0:
        st.error("🚨 **OVERALL: BLOCKED** - One or more scanners detected threats")
    elif warning_count > 0:
        st.warning("⚠️ **OVERALL: WARNING** - Potential risks detected")
    elif error_count > 0:
        st.info("ℹ️ **OVERALL: ERRORS** - Some scanners encountered errors")
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
        # Decision indicator
        if ac_result["is_safe"]:
            st.success(f"✅ {ac_result['decision']}")
        else:
            st.error(f"🚫 {ac_result['decision']}")

        # Risk gauge - FULL gauge = DANGER, EMPTY gauge = SAFE
        # Always red, fill level indicates risk
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

        # Determine analysis type and display compactly
        reason = ac_result['reason']
        reason_lower = reason.lower()

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
        st.error(f"Error: {ac_result['error']}")


def _render_prompt_guard_results(result: dict):
    """Render PromptGuard scanner results"""
    st.subheader("PromptGuard Scanner")
    if result["prompt_guard"]:
        for pg_result in result["prompt_guard"]:
            if "error" not in pg_result:
                if pg_result["is_safe"]:
                    st.success(f"✅ Safe: {pg_result['message']}")
                else:
                    # Show the reason (what was detected) instead of just the message
                    reason = pg_result.get('reason', 'Prompt injection detected')
                    st.error(f"🚫 Blocked: {reason}")
                    # Show the truncated message as additional context
                    st.caption(f"Input: {pg_result['message']}")
                st.caption(f"Score: {pg_result.get('score', 'N/A')} | Decision: {pg_result.get('decision', 'N/A')}")
            else:
                # Check if this is a Streamlit Cloud compatibility issue
                if "streamlit_cloud_note" in pg_result:
                    st.error(f"⚠️ **Streamlit Cloud Compatibility Issue**")
                    st.warning("PromptGuard scanner uses models that may not be compatible with Streamlit Cloud's environment. This scanner works on local deployments.")
                    with st.expander("🔍 Technical Details"):
                        st.code(pg_result['error'])
                else:
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
                # Decision indicator
                if scanner_result["is_safe"]:
                    st.success(f"✅ {scanner_result['decision']}")
                else:
                    st.error(f"🚫 {scanner_result['decision']}")

                # Risk gauge - FULL gauge = DANGER, EMPTY gauge = SAFE
                # Always red, fill level indicates risk
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

                # Show analysis with expandable full response
                st.info(f"**Analysis:** {scanner_result['reason']}")

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
                st.error(f"Error: {scanner_result['error']}")


def _render_history_chart():
    """Render test history chart"""
    if len(st.session_state.test_results) > 1:
        st.subheader("📊 Test History")

        history_data = []
        for i, result in enumerate(st.session_state.test_results):
            if result["alignment_check"] and "error" not in result["alignment_check"]:
                history_data.append({
                    "Test": i + 1,
                    "Score": result["alignment_check"]["score"],
                    "Decision": result["alignment_check"]["decision"],
                    "Safe": result["alignment_check"]["is_safe"]
                })

        if history_data:
            df = pd.DataFrame(history_data)
            fig_line = px.line(df, x="Test", y="Score",
                              color="Safe",
                              markers=True,
                              title="Alignment Scores Over Tests")
            fig_line.add_hline(y=0.5, line_dash="dash", line_color="red",
                              annotation_text="Threshold")
            st.plotly_chart(fig_line, use_container_width=True)