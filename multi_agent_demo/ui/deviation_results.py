"""
Deviation Results Display Components - Simplified Version
Clean, focused visualization of deviation and bias detection results
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any


def render_deviation_results(
    deviation_results: List[Dict[str, Any]],
    bias_results: List[Dict[str, Any]]
):
    """
    Render simplified deviation and bias analysis results

    Args:
        deviation_results: List of temporal deviation findings
        bias_results: List of bias findings
    """
    total_issues = len(deviation_results) + len(bias_results)

    if total_issues == 0:
        st.info("✅ No significant deviations or bias patterns detected")
        return

    st.subheader(f"📊 Found {total_issues} Issue{'s' if total_issues != 1 else ''}")

    # Show critical bias findings first (protected attributes)
    critical_bias = [b for b in bias_results if b.get("is_protected_attribute", False)]

    if critical_bias:
        st.error(f"🚨 **{len(critical_bias)} Critical Bias Finding{'s' if len(critical_bias) != 1 else ''} (Protected Attributes)**")
        for bias in critical_bias:
            _render_simple_bias_card(bias)

    # Show other bias findings
    other_bias = [b for b in bias_results if not b.get("is_protected_attribute", False)]
    if other_bias:
        st.warning(f"⚠️ **{len(other_bias)} Bias Pattern{'s' if len(other_bias) != 1 else ''}**")
        for bias in other_bias:
            _render_simple_bias_card(bias)

    # Show deviation findings
    if deviation_results:
        st.info(f"📈 **{len(deviation_results)} Temporal Deviation{'s' if len(deviation_results) != 1 else ''}**")
        for deviation in deviation_results:
            _render_simple_deviation_card(deviation)


def _render_simple_bias_card(bias: Dict[str, Any]):
    """Render a simplified bias finding card"""
    with st.container():
        # Main description
        st.markdown(f"**{bias['description']}**")

        details = bias.get('details', {})

        # Key metrics in columns
        col1, col2, col3 = st.columns(3)

        with col1:
            if 'advantaged_group' in details:
                st.metric(
                    "Advantaged Group",
                    str(details['advantaged_group'])[:20],
                    f"{details.get('advantaged_mean', 0):.2f}"
                )

        with col2:
            if 'disadvantaged_group' in details:
                st.metric(
                    "Disadvantaged Group",
                    str(details['disadvantaged_group'])[:20],
                    f"{details.get('disadvantaged_mean', 0):.2f}"
                )

        with col3:
            if 'disparity_ratio' in details:
                ratio = details['disparity_ratio']
                st.metric(
                    "Disparity",
                    f"{ratio:.2f}x",
                    delta="Critical" if ratio > 2 else "Significant" if ratio > 1.5 else None,
                    delta_color="inverse"
                )

        # Show concern if exists
        if 'fairness_concern' in bias:
            with st.expander("💡 Why This Matters"):
                concerns = bias['fairness_concern'].split(" | ")
                for concern in concerns[:2]:  # Show first 2 concerns
                    st.markdown(f"• {concern}")

        st.divider()


def _render_simple_deviation_card(deviation: Dict[str, Any]):
    """Render a simplified deviation finding card"""
    with st.container():
        # Main description
        st.markdown(f"**{deviation['description']}**")

        details = deviation.get('details', {})

        # Show key change metrics
        if 'percent_change' in details:
            col1, col2, col3 = st.columns(3)

            with col1:
                if 'first_mean' in details:
                    st.metric("Starting Value", f"{details['first_mean']:.2f}")

            with col2:
                if 'last_mean' in details:
                    st.metric(
                        "Current Value",
                        f"{details['last_mean']:.2f}",
                        f"{details['percent_change']:.1f}%"
                    )

            with col3:
                direction = details.get('direction', '').title()
                if direction:
                    st.metric("Trend", direction)

        # Show alignment concern with detailed analysis
        if 'alignment_concern' in deviation:
            with st.expander("💡 Why This Matters"):
                st.markdown(f"**Alignment Concern:**")
                st.markdown(f"• {deviation['alignment_concern']}")

                # Add detailed statistical information
                if details:
                    st.markdown("")
                    st.markdown("**Deviation Details:**")

                    # Time period information
                    if 'first_period' in details and 'last_period' in details:
                        st.markdown(f"• **Time Period**: {details['first_period']} → {details['last_period']}")

                    if 'periods_analyzed' in details:
                        st.markdown(f"• **Periods Analyzed**: {details['periods_analyzed']}")

                    # Change magnitude
                    if 'first_mean' in details and 'last_mean' in details:
                        change_amount = details['last_mean'] - details['first_mean']
                        st.markdown(f"• **Absolute Change**: {change_amount:+.2f} ({details['first_mean']:.2f} → {details['last_mean']:.2f})")

                    # Show evidence from period stats if available
                    evidence = deviation.get('evidence', {})
                    if evidence and len(evidence) > 0:
                        st.markdown("")
                        st.markdown("**Period-by-Period Breakdown:**")

                        # Create a simple table showing trend
                        period_data = []
                        for period_key in sorted(evidence.keys()):
                            stats = evidence[period_key]
                            period_data.append({
                                "Period": period_key,
                                "Average": f"{stats['mean']:.2f}",
                                "Samples": stats['count']
                            })

                        # Show as dataframe (limited to first/last few periods if many)
                        if len(period_data) <= 6:
                            df = pd.DataFrame(period_data)
                            st.dataframe(df, hide_index=True, use_container_width=True)
                        else:
                            # Show first 3 and last 3 periods
                            df_first = pd.DataFrame(period_data[:3])
                            df_last = pd.DataFrame(period_data[-3:])
                            st.dataframe(df_first, hide_index=True, use_container_width=True)
                            st.markdown("*... (intermediate periods omitted) ...*")
                            st.dataframe(df_last, hide_index=True, use_container_width=True)

        st.divider()
