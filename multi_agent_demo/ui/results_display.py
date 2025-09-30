"""
Test results display UI components
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def render_test_results():
    """Render test results display"""
    if not st.session_state.test_results:
        return

    latest_result = st.session_state.test_results[-1]

    # AlignmentCheck Results
    _render_alignment_check_results(latest_result)

    # PromptGuard Results
    _render_prompt_guard_results(latest_result)

    # NeMo GuardRails Results
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

        # Score gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=ac_result["score"],
            number={"font": {"size": 24}},
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "axis": {"range": [0, 1], "tickwidth": 2, "tickcolor": "darkblue"},
                "bar": {"color": "green" if ac_result["score"] > 0.7 else "orange" if ac_result["score"] > 0.3 else "red", "thickness": 0.8},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "gray"
            }
        ))
        fig_gauge.update_layout(height=188, showlegend=False, margin={"l": 20, "r": 20, "t": 20, "b": 20})
        st.plotly_chart(fig_gauge, use_container_width=True, key="alignment_check_gauge")

        st.info(f"**Reason:** {ac_result['reason']}")
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
                    st.warning(f"⚠️ Risk detected: {pg_result['message']}")
                st.caption(f"Score: {pg_result.get('score', 'N/A')} | Decision: {pg_result.get('decision', 'N/A')}")
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

                # Score gauge - consistent with AlignmentCheck
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=scanner_result["score"],
                    number={"font": {"size": 24}},
                    domain={"x": [0, 1], "y": [0, 1]},
                    gauge={
                        "axis": {"range": [0, 1], "tickwidth": 2, "tickcolor": "darkblue"},
                        "bar": {"color": "green" if scanner_result["score"] > 0.7 else "orange" if scanner_result["score"] > 0.3 else "red", "thickness": 0.8},
                        "bgcolor": "white",
                        "borderwidth": 2,
                        "bordercolor": "gray"
                    }
                ))
                fig_gauge.update_layout(height=188, showlegend=False, margin={"l": 20, "r": 20, "t": 20, "b": 20})
                st.plotly_chart(fig_gauge, use_container_width=True, key=f"{scanner_name.lower()}_gauge")

                # Show analysis with expandable full response
                st.info(f"**Analysis:** {scanner_result['reason']}")

                # Add expandable section for full AI response
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