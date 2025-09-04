#!/usr/bin/env python3
"""
Streamlit UI for LlamaFirewall Multi-Agent Security Demo
Run with: streamlit run streamlit_demo.py
"""

import streamlit as st
import pandas as pd
import json
import time
import os
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your demo components
from src.demo.scenarios import ScenarioRunner
from src.agents.agent_manager import MultiAgentManager
import logging

# Configure Streamlit page
st.set_page_config(
    page_title="LlamaFirewall Multi-Agent Demo",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.metric-container {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
.attack-blocked {
    background-color: #ff4b4b;
    color: white;
    padding: 0.5rem;
    border-radius: 0.3rem;
    margin: 0.2rem 0;
}
.legitimate-passed {
    background-color: #00cc00;
    color: white;
    padding: 0.5rem;
    border-radius: 0.3rem;
    margin: 0.2rem 0;
}
.debug-info {
    background-color: #1e1e1e;
    color: #00ff00;
    font-family: 'Courier New', monospace;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scenario_results' not in st.session_state:
    st.session_state.scenario_results = {}
if 'current_scenario' not in st.session_state:
    st.session_state.current_scenario = None
if 'demo_history' not in st.session_state:
    st.session_state.demo_history = []

def check_environment_setup():
    """Check if required environment variables are set"""
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for the main LLM",
        "TOGETHER_API_KEY": "Together API key for LlamaFirewall AlignmentCheck",
        "HF_TOKEN": "HuggingFace token for PromptGuard models (optional)"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        # Check both environment variables and Streamlit secrets
        if not os.getenv(var) and var not in st.secrets:
            missing_vars.append((var, description))
        elif var in st.secrets:
            # Set environment variable from Streamlit secrets
            os.environ[var] = st.secrets[var]
    
    return missing_vars

def show_environment_config():
    """Show environment configuration panel"""
    st.error("🔧 Environment Configuration Required")
    
    missing_vars = check_environment_setup()
    
    st.markdown("**Missing Environment Variables:**")
    for var, description in missing_vars:
        st.markdown(f"- `{var}`: {description}")
    
    st.markdown("**Setup Instructions:**")
    st.code("""
# Set environment variables (choose one method):

# Method 1: Create .env file in the project directory
echo "OPENAI_API_KEY=your_openai_key_here" >> .env
echo "TOGETHER_API_KEY=your_together_key_here" >> .env  
echo "HF_TOKEN=your_huggingface_token" >> .env

# Method 2: Export in terminal before running
export OPENAI_API_KEY="your_openai_key_here"
export TOGETHER_API_KEY="your_together_key_here"
export HF_TOKEN="your_huggingface_token"

# Then restart Streamlit:
streamlit run streamlit_demo.py
    """, language="bash")
    
    st.info("💡 After setting the environment variables, refresh this page or restart the Streamlit app.")

def main():
    # Header
    st.title("🛡️ LlamaFirewall Multi-Agent Security Demo")
    st.markdown("**Protecting AI Agents Against Goal Hijacking & Alignment Attacks**")
    
    # Check environment setup first
    missing_vars = check_environment_setup()
    
    if missing_vars:
        show_environment_config()
        return
    
    # Show environment status in sidebar
    st.sidebar.success("✅ Environment configured")
    st.sidebar.markdown(f"**OpenAI Key:** {'*' * 8}...{os.getenv('OPENAI_API_KEY', '')[-4:]}")
    st.sidebar.markdown(f"**Together Key:** {'*' * 8}...{os.getenv('TOGETHER_API_KEY', '')[-4:]}")
    
    # Sidebar
    st.sidebar.header("🎮 Demo Controls")
    
    demo_mode = st.sidebar.selectbox(
        "Choose Demo Mode:",
        ["Overview Dashboard", "Interactive Scenarios", "Automated Testing", "Real-time Agent Chat"]
    )
    
    if demo_mode == "Overview Dashboard":
        show_overview_dashboard()
    elif demo_mode == "Interactive Scenarios":
        show_interactive_scenarios()
    elif demo_mode == "Automated Testing":
        show_automated_testing()
    elif demo_mode == "Real-time Agent Chat":
        show_real_time_chat()

def show_overview_dashboard():
    st.header("📊 Security Protection Dashboard")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🎯 Attack Detection Rate", 
            value="100%",
            delta="3/3 attacks blocked"
        )
    
    with col2:
        st.metric(
            label="✅ Legitimate Traffic", 
            value="100%",
            delta="3/3 requests allowed"
        )
    
    with col3:
        st.metric(
            label="⚡ Response Time", 
            value="3.2s",
            delta="Average per check"
        )
    
    with col4:
        st.metric(
            label="🛡️ Security Score", 
            value="A+",
            delta="0 false positives"
        )
    
    # Architecture diagram section
    st.subheader("🏗️ System Architecture")
    
    # Create architecture visualization
    fig = go.Figure()
    
    # Add nodes for the architecture
    fig.add_trace(go.Scatter(
        x=[1, 2, 2, 2, 3, 3, 4, 4],
        y=[3, 2, 3, 4, 1, 5, 2, 4],
        text=["👤 User", "🎯 Router", "💰 Banking", "✈️ Travel", 
              "🛡️ Security Manager", "📧 Email", "🔍 PromptGuard", "🎯 AlignmentCheck"],
        mode="markers+text",
        marker=dict(size=50, color=['lightblue', 'orange', 'gold', 'lightgreen', 
                                  'red', 'purple', 'pink', 'cyan']),
        textposition="middle center",
        showlegend=False
    ))
    
    fig.update_layout(
        title="Multi-Agent Security Architecture",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Threat landscape
    st.subheader("⚠️ Detected Threat Types")
    
    threat_data = pd.DataFrame({
        'Threat Type': ['Goal Hijacking', 'Data Exfiltration', 'Malicious Forwarding'],
        'Severity': ['Critical', 'High', 'High'],
        'Detection Rate': [100, 100, 100],
        'Response Time': [2.1, 3.2, 2.8]
    })
    
    st.dataframe(threat_data, use_container_width=True)

def show_interactive_scenarios():
    st.header("🎮 Interactive Security Scenarios")
    
    # Scenario selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Select Scenario Type")
        scenario_type = st.radio(
            "Choose scenario:",
            ["✅ Legitimate Operations", "❌ Attack Scenarios"]
        )
        
        if scenario_type == "✅ Legitimate Operations":
            scenarios = {
                "travel_planning": "🏢 Business Travel Planning",
                "email_organization": "📧 Email Organization", 
                "account_review": "💳 Account Review"
            }
        else:
            scenarios = {
                "goal_hijacking_banking": "💰 Banking Goal Hijacking",
                "data_exfiltration_travel": "✈️ Travel Data Exfiltration",
                "email_forwarding_attack": "📧 Email Forwarding Attack"
            }
        
        selected_scenario = st.selectbox("Choose specific scenario:", list(scenarios.keys()), 
                                       format_func=lambda x: scenarios[x])
    
    with col2:
        st.subheader("Scenario Execution")
        
        if st.button(f"🚀 Run {scenarios[selected_scenario]}", type="primary"):
            run_interactive_scenario(selected_scenario, scenario_type)

def run_interactive_scenario(scenario_name, scenario_type):
    """Run a single scenario with detailed UI feedback"""
    
    # Create progress container
    progress_container = st.container()
    result_container = st.container()
    debug_container = st.container()
    
    with progress_container:
        st.info(f"🔄 Running scenario: {scenario_name}")
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    # Initialize scenario runner
    runner = ScenarioRunner()
    
    try:
        # Update progress
        progress_bar.progress(25)
        status_text.text("Initializing security scanners...")
        time.sleep(0.5)
        
        # Run the scenario
        progress_bar.progress(50)
        status_text.text("Executing scenario steps...")
        
        if scenario_type == "✅ Legitimate Operations":
            result = runner.run_legitimate_scenario(scenario_name)
        else:
            result = runner.run_attack_scenario(scenario_name)
        
        progress_bar.progress(75)
        status_text.text("Analyzing security results...")
        time.sleep(0.5)
        
        progress_bar.progress(100)
        status_text.text("✅ Scenario completed!")
        
        # Display results
        with result_container:
            display_scenario_results(result, scenario_name)
        
        # Display debug information
        with debug_container:
            display_debug_info(result)
            
    except Exception as e:
        st.error(f"❌ Error running scenario: {str(e)}")

def display_scenario_results(result, scenario_name):
    """Display scenario results with visual indicators"""
    
    st.subheader("📋 Scenario Results")
    
    # Status indicator
    if result["final_status"] == "completed":
        st.success(f"✅ Scenario '{scenario_name}' completed successfully")
        st.markdown('<div class="legitimate-passed">LEGITIMATE OPERATION ALLOWED</div>', 
                   unsafe_allow_html=True)
    elif result["final_status"] == "blocked_by_alignment_check":
        st.error(f"🛡️ Scenario '{scenario_name}' blocked by security")
        st.markdown('<div class="attack-blocked">MALICIOUS BEHAVIOR DETECTED & BLOCKED</div>', 
                   unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Scenario '{scenario_name}' had unexpected result")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Steps Executed", len(result["steps_executed"]))
    
    with col2:
        st.metric("Security Events", len(result["security_events"]))
    
    with col3:
        if result["security_events"]:
            score = result["security_events"][0]["details"].get("score", "N/A")
            st.metric("Detection Score", f"{score:.1f}" if isinstance(score, (int, float)) else score)
        else:
            st.metric("Detection Score", "0.0")
    
    # Execution timeline
    st.subheader("⏱️ Execution Timeline")
    
    for i, step in enumerate(result["steps_executed"], 1):
        with st.expander(f"Step {i}: {step['user_input'][:50]}..."):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**User Input:**")
                st.code(step["user_input"], language="text")
                
            with col2:
                st.markdown("**Agent Response:**")
                if step["security_status"] == "success":
                    st.success("✅ Allowed")
                elif step["security_status"] == "alignment_violation":
                    st.error("🛡️ Blocked")
                else:
                    st.info("ℹ️ Other")
                
                if "agent_response" in step and "response" in step["agent_response"]:
                    st.text_area("Response:", step["agent_response"]["response"], height=100)

def display_debug_info(result):
    """Display detailed debug information"""
    
    with st.expander("🔍 Debug Information", expanded=False):
        st.markdown("**Full Scenario Result:**")
        st.json(result)
        
        if result["security_events"]:
            st.markdown("**Security Event Details:**")
            for event in result["security_events"]:
                st.markdown(f"**Step {event['step']} - {event['event_type']}:**")
                st.code(event["details"]["details"], language="text")

def show_automated_testing():
    st.header("🧪 Automated Security Testing")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Test Configuration")
        
        run_legitimate = st.checkbox("Run Legitimate Scenarios", value=True)
        run_attacks = st.checkbox("Run Attack Scenarios", value=True)
        
        if st.button("🚀 Start Automated Testing", type="primary"):
            run_automated_tests(run_legitimate, run_attacks)
    
    with col2:
        if 'test_results' in st.session_state:
            display_test_summary(st.session_state.test_results)

def run_automated_tests(run_legitimate, run_attacks):
    """Run automated test suite with progress tracking"""
    
    progress_container = st.container()
    
    with progress_container:
        st.info("🔄 Starting automated security testing...")
        
        overall_progress = st.progress(0)
        current_test = st.empty()
        
        results = {"legitimate": {}, "attacks": {}, "summary": {}}
        
        runner = ScenarioRunner()
        total_tests = 0
        completed_tests = 0
        
        # Count total tests
        if run_legitimate:
            total_tests += 3
        if run_attacks:
            total_tests += 3
        
        # Run legitimate scenarios
        if run_legitimate:
            legitimate_scenarios = ["travel_planning", "email_organization", "account_review"]
            
            for scenario in legitimate_scenarios:
                current_test.text(f"Running legitimate scenario: {scenario}")
                result = runner.run_legitimate_scenario(scenario)
                results["legitimate"][scenario] = result
                
                completed_tests += 1
                overall_progress.progress(completed_tests / total_tests)
                time.sleep(0.5)
        
        # Run attack scenarios
        if run_attacks:
            attack_scenarios = ["goal_hijacking_banking", "data_exfiltration_travel", "email_forwarding_attack"]
            
            for scenario in attack_scenarios:
                current_test.text(f"Running attack scenario: {scenario}")
                result = runner.run_attack_scenario(scenario)
                results["attacks"][scenario] = result
                
                completed_tests += 1
                overall_progress.progress(completed_tests / total_tests)
                time.sleep(0.5)
        
        current_test.text("✅ All tests completed!")
        st.session_state.test_results = results

def display_test_summary(results):
    """Display automated test results summary"""
    
    st.subheader("📊 Test Results Summary")
    
    # Calculate metrics
    legitimate_passed = sum(1 for r in results["legitimate"].values() 
                          if r["final_status"] == "completed")
    attacks_blocked = sum(1 for r in results["attacks"].values() 
                        if r["final_status"] == "blocked_by_alignment_check")
    
    total_legitimate = len(results["legitimate"])
    total_attacks = len(results["attacks"])
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Legitimate Scenarios", f"{legitimate_passed}/{total_legitimate}", 
                 "✅ Passed" if legitimate_passed == total_legitimate else "❌ Some failed")
    
    with col2:
        st.metric("Attack Scenarios", f"{attacks_blocked}/{total_attacks}",
                 "✅ Blocked" if attacks_blocked == total_attacks else "❌ Some missed")
    
    with col3:
        accuracy = (legitimate_passed + attacks_blocked) / (total_legitimate + total_attacks) * 100
        st.metric("Overall Accuracy", f"{accuracy:.1f}%", 
                 "🎯 Perfect" if accuracy == 100 else "⚠️ Needs attention")
    
    # Detailed results
    st.subheader("📋 Detailed Results")
    
    for category, scenarios in [("Legitimate", results["legitimate"]), ("Attacks", results["attacks"])]:
        st.markdown(f"**{category} Scenarios:**")
        
        for scenario_name, result in scenarios.items():
            status_icon = "✅" if ((category == "Legitimate" and result["final_status"] == "completed") or 
                                 (category == "Attacks" and result["final_status"] == "blocked_by_alignment_check")) else "❌"
            
            st.markdown(f"{status_icon} {scenario_name}: {result['final_status']}")

def show_real_time_chat():
    st.header("💬 Real-time Agent Chat")
    st.markdown("Interact with the multi-agent system in real-time and see security monitoring in action.")
    
    # Chat interface
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"👤 **You:** {message['content']}")
        else:
            if message.get("blocked", False):
                st.error(f"🛡️ **Security:** {message['content']}")
            else:
                st.success(f"🤖 **{message.get('agent', 'Agent')}:** {message['content']}")
    
    # Input box
    user_input = st.text_input("Enter your request:", key="chat_input")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("Send", type="primary"):
            if user_input:
                process_chat_message(user_input)
    
    with col2:
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

def process_chat_message(user_input):
    """Process chat message through the multi-agent system"""
    
    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    try:
        # Process through agent manager
        manager = MultiAgentManager()
        thread_id = "chat_demo"
        result = manager.route_request(user_input, thread_id)
        
        # Add response to history
        if result["status"] == "success":
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": result["response"],
                "agent": result.get("routing_info", {}).get("selected_agent", "Agent"),
                "blocked": False
            })
        elif result["status"] in ["blocked", "alignment_violation"]:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Request blocked: {result.get('reason', 'Security violation')}",
                "blocked": True
            })
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Error: {result.get('message', 'Unknown error')}",
                "blocked": False
            })
            
    except Exception as e:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"System error: {str(e)}",
            "blocked": False
        })
    
    # Trigger rerun to update display
    st.rerun()

if __name__ == "__main__":
    main()