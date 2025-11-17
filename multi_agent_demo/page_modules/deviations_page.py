"""
Deviations Analysis Page
Analyze OpenTelemetry traces to detect behavioral deviations and bias
"""

import streamlit as st
import json
from typing import Dict, Any
from multi_agent_demo.ui.common import render_page_header, render_agent_configuration
from multi_agent_demo.deviations import parse_otel_data, detect_deviations, detect_bias
from multi_agent_demo.ui.deviation_results import render_deviation_results


def render_otel_upload():
    """Render OTEL file upload section"""
    st.subheader("📁 Upload OpenTelemetry Data")

    uploaded_file = st.file_uploader(
        "Upload OTEL JSON file",
        type=['json'],
        help="Upload OpenTelemetry trace data in JSON format"
    )

    if uploaded_file is not None:
        try:
            # Read and parse the uploaded file
            otel_content = uploaded_file.read().decode('utf-8')
            otel_data = json.loads(otel_content)

            # Check if this is a new file (clear previous analysis)
            if 'current_otel_file' not in st.session_state or st.session_state.current_otel_file != uploaded_file.name:
                st.session_state.current_otel_file = uploaded_file.name
                # Clear previous analysis results
                st.session_state.deviation_results = []
                st.session_state.bias_results = []

            # Store in session state
            st.session_state.otel_data = otel_data

            # Display basic statistics
            st.success(f"✅ OTEL data loaded successfully")

            return otel_data

        except json.JSONDecodeError as e:
            st.error(f"❌ Error parsing JSON file: {e}")
            st.session_state.otel_data = None
            return None
        except Exception as e:
            st.error(f"❌ Error loading file: {e}")
            st.session_state.otel_data = None
            return None

    # Show sample data option if no file uploaded
    if st.session_state.otel_data is None:
        st.info("ℹ️ Upload an OTEL JSON file to begin analysis")

        if st.button("📝 Use Sample Data"):
            # Load sample OTEL data
            sample_data = _generate_sample_otel_data()
            st.session_state.otel_data = sample_data
            st.session_state.current_otel_file = "sample_data"
            # Clear previous analysis results
            st.session_state.deviation_results = []
            st.session_state.bias_results = []
            st.rerun()

    return st.session_state.otel_data


def _generate_sample_otel_data():
    """Generate sample OTEL data for demonstration"""
    import random
    from datetime import datetime, timedelta

    base_time = datetime.now() - timedelta(days=30)
    traces = []

    # Banking commission refund example (showing deviation over time)
    for week in range(4):
        for day in range(7):
            for i in range(random.randint(5, 15)):
                timestamp = base_time + timedelta(weeks=week, days=day, hours=random.randint(0, 23))

                # Average refund increases over weeks (deviation pattern)
                base_refund = 50 + (week * 15)  # $50 -> $95 over 4 weeks
                refund_amount = base_refund + random.uniform(-10, 10)

                trace = {
                    "trace_id": f"trace_{week}_{day}_{i}",
                    "timestamp": timestamp.isoformat(),
                    "span_name": "process_refund_request",
                    "attributes": {
                        "agent.purpose": "Banking customer service - handle refund requests",
                        "action": "approve_commission_refund",
                        "refund_amount": round(refund_amount, 2),
                        "week": week + 1,
                        "customer_age": random.randint(25, 65),
                        "customer_tenure_years": random.randint(1, 20)
                    }
                }
                traces.append(trace)

    # Hiring CV scoring example (showing bias pattern)
    for i in range(100):
        age = random.randint(22, 60)
        # Bias: people under 40 get higher scores
        if age < 40:
            base_score = random.uniform(70, 95)
        else:
            base_score = random.uniform(40, 70)

        timestamp = base_time + timedelta(days=random.randint(0, 28))

        trace = {
            "trace_id": f"hiring_trace_{i}",
            "timestamp": timestamp.isoformat(),
            "span_name": "score_candidate",
            "attributes": {
                "agent.purpose": "HR screening agent - score candidate CVs",
                "action": "calculate_cv_score",
                "cv_score": round(base_score, 2),
                "candidate_age": age,
                "years_experience": random.randint(0, 30),
                "education_level": random.choice(["Bachelor", "Master", "PhD"])
            }
        }
        traces.append(trace)

    return {"traces": traces}


def render_analysis_controls():
    """Render analysis configuration and execution controls"""
    st.subheader("⚙️ Analysis Configuration")

    col1, col2 = st.columns(2)

    with col1:
        detect_temporal_deviations = st.checkbox(
            "Detect Temporal Deviations",
            value=True,
            help="Detect metrics that change significantly over time"
        )

    with col2:
        detect_parameter_bias = st.checkbox(
            "Detect Parameter Bias",
            value=True,
            help="Detect correlations between parameters that indicate bias"
        )

    # Sensitivity settings
    with st.expander("🎚️ Sensitivity Settings"):
        deviation_threshold = st.slider(
            "Deviation Threshold (Standard Deviations)",
            min_value=1.0,
            max_value=4.0,
            value=2.0,
            step=0.5,
            help="How many standard deviations to consider as anomalous"
        )

        bias_threshold = st.slider(
            "Bias Significance Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.05,
            help="Minimum effect size to report as significant bias (0-1)"
        )

    return {
        "detect_temporal_deviations": detect_temporal_deviations,
        "detect_parameter_bias": detect_parameter_bias,
        "deviation_threshold": deviation_threshold,
        "bias_threshold": bias_threshold
    }


def render():
    """Render the deviations analysis page"""
    # Page header
    render_page_header(
        "📊 Deviation",
        "Analyze OpenTelemetry traces to detect behavioral deviations and bias over time"
    )

    # Render agent configuration (collapsed by default on this page)
    render_agent_configuration(expanded=False)

    st.divider()

    # Layout: Left column for upload/config, Right column for results
    col1, col2 = st.columns([1, 1])

    with col1:
        # OTEL file upload
        otel_data = render_otel_upload()

        st.divider()

        # Analysis configuration
        if otel_data:
            analysis_config = render_analysis_controls()

            # Control buttons (matching realtime page design)
            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                if st.button("🔍 Run Analysis", type="primary", use_container_width=True):
                    with st.spinner("Analyzing telemetry data..."):
                        try:
                            # Parse OTEL data to extract metrics
                            parsed_data = parse_otel_data(otel_data)

                            # Run deviation detection
                            deviation_results = []
                            bias_results = []

                            if analysis_config["detect_temporal_deviations"]:
                                deviation_results = detect_deviations(
                                    parsed_data,
                                    threshold=analysis_config["deviation_threshold"],
                                    agent_purpose=st.session_state.agent_purpose
                                )

                            if analysis_config["detect_parameter_bias"]:
                                bias_results = detect_bias(
                                    parsed_data,
                                    threshold=analysis_config["bias_threshold"],
                                    agent_purpose=st.session_state.agent_purpose
                                )

                            # Store results in session state
                            st.session_state.deviation_results = deviation_results
                            st.session_state.bias_results = bias_results

                            st.success(f"✅ Analysis complete! Found {len(deviation_results)} deviations and {len(bias_results)} bias patterns")
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Analysis error: {e}")
                            import traceback
                            st.code(traceback.format_exc())

            with col_btn2:
                if st.button("🗑️ Clear Analysis", use_container_width=True):
                    st.session_state.deviation_results = []
                    st.session_state.bias_results = []
                    st.rerun()

    with col2:
        # Results display
        if st.session_state.deviation_results or st.session_state.bias_results:
            render_deviation_results(
                st.session_state.deviation_results,
                st.session_state.bias_results
            )
        else:
            st.info("ℹ️ Upload OTEL data and run analysis to see results")
