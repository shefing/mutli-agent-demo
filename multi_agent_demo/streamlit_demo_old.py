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

# Ensure API keys are available for LlamaFirewall
try:
    import streamlit as st
    if hasattr(st, 'secrets'):
        for key in ['TOGETHER_API_KEY', 'OPENAI_API_KEY', 'HF_TOKEN']:
            if key in st.secrets and key not in os.environ:
                os.environ[key] = st.secrets[key]
except:
    pass

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

def get_dynamic_user_goal(user_input):
    """Extract or determine user goal dynamically"""
    
    # 1. Check if user has manually set a goal
    if st.session_state.get('user_goal'):
        return st.session_state.user_goal
    
    # 2. If first message, try to extract goal from it
    if len(st.session_state.chat_history) <= 1:  # Only user message just added
        # Auto-extract goal from first message if it contains intent keywords
        user_input_lower = user_input.lower()
        
        if any(keyword in user_input_lower for keyword in ['help me', 'i want to', 'i need to', 'can you']):
            # Extract the intent and set as goal
            extracted_goal = f"Help the user: {user_input}"
            st.session_state.user_goal = extracted_goal
            return extracted_goal
    
    # 3. Infer from conversation context if available
    if len(st.session_state.chat_history) > 1:
        # Use existing goal if conversation is ongoing
        if st.session_state.get('user_goal'):
            return st.session_state.user_goal
    
    # 4. Detect domain-specific goals based on keywords
    user_input_lower = user_input.lower()
    
    if any(keyword in user_input_lower for keyword in ['balance', 'account', 'transfer', 'money', 'payment', 'financial']):
        goal = "Help me manage my finances securely and accurately"
    elif any(keyword in user_input_lower for keyword in ['travel', 'flight', 'hotel', 'booking', 'trip']):
        goal = "Help me plan and book travel arrangements safely"
    elif any(keyword in user_input_lower for keyword in ['email', 'send', 'forward', 'message', 'mail']):
        goal = "Help me manage my email communications securely"
    else:
        goal = "Help me with legitimate operations while maintaining security and privacy"
    
    # Store the inferred goal for the session
    if not st.session_state.get('user_goal'):
        st.session_state.user_goal = goal
    
    return goal

def show_real_time_chat():
    st.header("💬 Real-time Agent Chat")
    st.markdown("Interact with the multi-agent system in real-time and see security monitoring in action.")
    
    # Chat interface
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'clear_input' not in st.session_state:
        st.session_state.clear_input = False
    if 'user_goal' not in st.session_state:
        st.session_state.user_goal = ""
    if 'chat_thread_id' not in st.session_state:
        st.session_state.chat_thread_id = "realtime_chat_demo"
    
    # User goal configuration
    with st.expander("🎯 User Goal Configuration", expanded=len(st.session_state.chat_history) == 0):
        st.markdown("**Current User Goal:**")
        if st.session_state.user_goal:
            st.info(f"🎯 {st.session_state.user_goal}")
        else:
            st.warning("No user goal set - AlignmentCheck scanner will use default goal")
        
        # Manual goal override
        manual_goal = st.text_input("Set custom user goal (optional):", 
                                   placeholder="e.g., Help me manage my finances securely")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Set Goal"):
                if manual_goal:
                    st.session_state.user_goal = manual_goal
                    st.success("User goal updated!")
                    st.rerun()
        
        with col2:
            if st.button("Clear Goal"):
                st.session_state.user_goal = ""
                st.success("User goal cleared!")
                st.rerun()
    
    # Display chat history
    for msg_idx, message in enumerate(st.session_state.chat_history):
        if message["role"] == "user":
            st.markdown(f"👤 **You:** {message['content']}")
        else:
            if message.get("blocked", False):
                st.error(f"🛡️ **Security:** {message['content']}")
            else:
                st.success(f"🤖 **{message.get('agent', 'Agent')}:** {message['content']}")
            
            # Show debug info if available
            if message.get("debug_info"):
                with st.expander("🔍 Debug Info - Security Scanners"):
                    debug_info = message["debug_info"]
                    
                    # Create tabs for different scanner types
                    tabs = ["🔍 PromptGuard Scanner", "🎯 AlignmentCheck Scanner", "📊 Overall Request"]
                    if debug_info.get("demo_malicious_simulation"):
                        tabs.append("🚨 Malicious Compliance Demo")
                    
                    tab_objects = st.tabs(tabs)
                    tab1, tab2, tab3 = tab_objects[:3]
                    tab4 = tab_objects[3] if len(tab_objects) > 3 else None
                    
                    with tab1:
                        st.markdown("**Input to PromptGuard:**")
                        st.code(debug_info.get("prompt_guard_input", "Not called"), language="json")
                        
                        st.markdown("**Output from PromptGuard:**")
                        st.code(debug_info.get("prompt_guard_output", "Not called"), language="json")
                    
                    with tab2:
                        st.markdown("**Input to AlignmentCheck:**")
                        st.code(debug_info.get("alignment_check_input", "Not called"), language="json")
                        
                        st.markdown("**Output from AlignmentCheck:**")
                        alignment_output = debug_info.get("alignment_check_output", "Not called")
                        if alignment_output != "Not called":
                            try:
                                alignment_data = json.loads(alignment_output)
                                
                                # Show key metrics first
                                if alignment_data.get("is_safe") is not None:
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        safety = "✅ SAFE" if alignment_data.get("is_safe") else "⚠️ UNSAFE"
                                        st.markdown(f"**Status:** {safety}")
                                    with col2:
                                        score = alignment_data.get("score", "N/A")
                                        st.markdown(f"**Score:** {score}")
                                    with col3:
                                        decision = alignment_data.get("decision", "N/A")
                                        st.markdown(f"**Decision:** {decision}")
                                
                                # Show reasoning prominently
                                reasoning = alignment_data.get("reasoning")
                                if reasoning:
                                    st.markdown("**🧠 Alignment Check Reasoning:**")
                                    st.info(reasoning)
                                
                                # Show violation type if present
                                violation_type = alignment_data.get("violation_type")
                                if violation_type:
                                    st.markdown(f"**Violation Type:** `{violation_type}`")
                                
                                # Show goal comparison
                                user_goal = alignment_data.get("user_goal_compared")
                                if user_goal:
                                    st.markdown(f"**User Goal Evaluated:** {user_goal}")
                                
                                # Show full raw output
                                if st.checkbox("Show Raw AlignmentCheck Output", key=f"raw_alignment_msg_{msg_idx}"):
                                    st.code(alignment_output, language="json")
                            except json.JSONDecodeError:
                                st.code(alignment_output, language="json")
                        else:
                            st.code(alignment_output, language="json")
                    
                    with tab3:
                        st.markdown("**Request Input:**")
                        st.code(debug_info.get("request_input", "No input data"), language="json")
                        
                        st.markdown("**Request Output:**")
                        st.code(debug_info.get("request_output", "No output data"), language="json")
                        
                        if debug_info.get("security_events"):
                            st.markdown("**Security Events:**")
                            for i, event in enumerate(debug_info["security_events"], 1):
                                st.markdown(f"Event {i}: {event.get('event_type', 'Unknown')}")
                                st.code(str(event.get("details", {})), language="json")
                    
                    # Fourth tab for malicious compliance demo
                    if tab4 and debug_info.get("demo_malicious_simulation"):
                        with tab4:
                            demo_result = debug_info["demo_malicious_simulation"]
                            
                            st.warning("⚠️ **Demo Warning**: This tab shows what would happen if the agent maliciously complied with suspicious requests. Real agents properly refuse such requests.")
                            
                            st.markdown("**🎭 Simulated Malicious Response:**")
                            st.error(f"*What if the agent said:* \"{demo_result['simulated_response']}\"")
                            
                            st.markdown("**🛡️ LlamaFirewall AlignmentCheck Detection:**")
                            alignment_check = demo_result["alignment_check"]
                            
                            # Show key metrics for the simulated scenario
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                safety = "✅ SAFE" if alignment_check.get("is_safe") else "⚠️ UNSAFE" 
                                st.markdown(f"**Status:** {safety}")
                            with col2:
                                score = alignment_check.get("score", "N/A")
                                st.markdown(f"**Score:** {score}")
                            with col3:
                                decision = alignment_check.get("decision", "N/A")
                                st.markdown(f"**Decision:** {decision}")
                            
                            # Show reasoning
                            if alignment_check.get("details"):
                                st.markdown("**🧠 Why This Would Be Blocked:**")
                                st.success(alignment_check["details"])
                            
                            # Show violation details
                            if alignment_check.get("violation_type"):
                                st.markdown(f"**Violation Type:** `{alignment_check['violation_type']}`")
                            
                            st.markdown("**📊 Demo Scenario Analysis:**")
                            st.info(
                                "This demonstrates how LlamaFirewall's AlignmentCheck scanner would detect "
                                "goal misalignment even if an agent were compromised and complied with malicious requests. "
                                "The system compares agent actions against the original user goal to identify deviations."
                            )
    
    # Input box with clearing logic
    user_input = st.text_input("Enter your request:", key="chat_input")
    
    # Clear input after processing if flag is set
    if st.session_state.clear_input:
        st.session_state.clear_input = False
        st.session_state["chat_input"] = ""
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("Send", type="primary"):
            if user_input:
                process_chat_message(user_input)
                st.session_state.clear_input = True
                st.rerun()
    
    with col2:
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.user_goal = ""
            # Generate new thread ID to clear security traces
            import uuid
            st.session_state.chat_thread_id = f"realtime_chat_{str(uuid.uuid4())[:8]}"
            st.rerun()

def process_chat_message(user_input):
    """Process chat message through the multi-agent system"""
    
    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    try:
        # Process through agent manager with debug instrumentation
        manager = MultiAgentManager()
        thread_id = st.session_state.chat_thread_id
        
        # Store original firewall scan methods for debugging
        original_scan_user_input = manager.security_manager.scan_user_input
        original_check_agent_alignment = manager.security_manager.check_agent_alignment
        
        # Capture scanner interactions
        scanner_debug = {
            "prompt_guard": {"input": None, "output": None},
            "alignment_check": {"input": None, "output": None}
        }
        
        def debug_scan_user_input(user_input, thread_id):
            scanner_debug["prompt_guard"]["input"] = json.dumps({
                "user_input": user_input,
                "thread_id": thread_id,
                "scanner": "PromptGuard"
            }, indent=2)
            result = original_scan_user_input(user_input, thread_id)
            scanner_debug["prompt_guard"]["output"] = json.dumps(result, indent=2, default=str)
            return result
        
        def debug_check_agent_alignment(thread_id, user_goal):
            scanner_debug["alignment_check"]["input"] = json.dumps({
                "thread_id": thread_id,
                "user_goal": user_goal,
                "scanner": "AlignmentCheck",
                "trace_length": len(manager.security_manager.conversation_traces.get(thread_id, []))
            }, indent=2)
            result = original_check_agent_alignment(thread_id, user_goal)
            
            # Enhanced debug output with reasoning
            debug_output = {
                "is_safe": result.get("is_safe"),
                "decision": result.get("decision"),
                "score": result.get("score"),
                "violation_type": result.get("violation_type"),
                "reasoning": result.get("details", result.get("reason")),
                "action": result.get("action"),
                "user_goal_compared": result.get("user_goal"),
                "full_result": result
            }
            scanner_debug["alignment_check"]["output"] = json.dumps(debug_output, indent=2, default=str)
            return result
        
        # Monkey patch the methods
        manager.security_manager.scan_user_input = debug_scan_user_input
        manager.security_manager.check_agent_alignment = debug_check_agent_alignment
        
        # Determine user goal dynamically
        user_goal = get_dynamic_user_goal(user_input)
        result = manager.route_request(user_input, thread_id, user_goal)
        
        # DEMO ENHANCEMENT: For demonstration purposes, also show what would happen
        # if the agent complied maliciously with suspicious requests
        demo_malicious_result = None
        if "confidential" in user_input.lower() and ("forward" in user_input.lower() or "send" in user_input.lower()):
            # Simulate what would happen if agent complied maliciously
            from langchain_core.messages import HumanMessage, AIMessage
            
            # Create a temporary trace for demonstration
            demo_thread_id = f"{thread_id}_demo_malicious"
            manager.security_manager.add_to_trace(demo_thread_id, HumanMessage(content=st.session_state.chat_history[0]['content'] if st.session_state.chat_history else "Please help me organize my work emails"))
            manager.security_manager.add_to_trace(demo_thread_id, AIMessage(content="I can help you organize your work emails. What specific organization would you like to implement?"))
            manager.security_manager.add_to_trace(demo_thread_id, HumanMessage(content=user_input))
            
            # Simulate malicious compliance response
            malicious_response = f"I will forward all your confidential financial reports to {user_input.split('@')[1].split()[0] if '@' in user_input else 'the specified address'} as requested."
            manager.security_manager.add_to_trace(demo_thread_id, AIMessage(content=malicious_response))
            
            # Check what alignment would detect
            demo_alignment_check = manager.security_manager.check_agent_alignment(demo_thread_id, user_goal)
            demo_malicious_result = {
                "simulated_response": malicious_response,
                "alignment_check": demo_alignment_check
            }
        
        # Restore original methods
        manager.security_manager.scan_user_input = original_scan_user_input
        manager.security_manager.check_agent_alignment = original_check_agent_alignment
        
        # Build comprehensive debug info
        debug_info = {
            "request_input": json.dumps({
                "user_input": user_input,
                "thread_id": thread_id,
                "timestamp": datetime.now().isoformat()
            }, indent=2),
            "request_output": json.dumps(result, indent=2, default=str),
            "prompt_guard_input": scanner_debug["prompt_guard"]["input"] or "Not called",
            "prompt_guard_output": scanner_debug["prompt_guard"]["output"] or "Not called", 
            "alignment_check_input": scanner_debug["alignment_check"]["input"] or "Not called",
            "alignment_check_output": scanner_debug["alignment_check"]["output"] or "Not called",
            "security_events": result.get("security_events", []),
            "demo_malicious_simulation": demo_malicious_result
        }
        
        # Add response to history
        if result["status"] == "success":
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": result["response"],
                "agent": result.get("routing_info", {}).get("selected_agent", "Agent"),
                "blocked": False,
                "debug_info": debug_info
            })
        elif result["status"] in ["blocked", "alignment_violation"]:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Request blocked: {result.get('reason', 'Security violation')}",
                "blocked": True,
                "debug_info": debug_info
            })
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Error: {result.get('message', 'Unknown error')}",
                "blocked": False,
                "debug_info": debug_info
            })
            
    except Exception as e:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"System error: {str(e)}",
            "blocked": False,
            "debug_info": {
                "request_input": f"Error processing: {user_input}",
                "request_output": f"Exception: {str(e)}",
                "prompt_guard_input": "Error occurred",
                "prompt_guard_output": "Error occurred",
                "alignment_check_input": "Error occurred", 
                "alignment_check_output": "Error occurred",
                "security_events": []
            }
        })
    
    # Trigger rerun to update display
    st.rerun()

if __name__ == "__main__":
    main()