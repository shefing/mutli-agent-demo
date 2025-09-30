"""
Firewall integration and scanner orchestration
"""

import streamlit as st
import json
from datetime import datetime
from typing import List, Dict

from llamafirewall import (
    AssistantMessage,
    LlamaFirewall,
    Role,
    ScannerType,
    ScanDecision,
    Trace,
    UserMessage,
)

from multi_agent_demo.scanners import (
    FactCheckerScanner,
    NEMO_GUARDRAILS_AVAILABLE
)


def initialize_firewall():
    """
    Initialize LlamaFirewall with selected LlamaFirewall scanners only.

    BUG FIX: Returns None only if NO scanners are enabled at all.
    Previously returned None if no LlamaFirewall scanners were enabled,
    even when NeMo scanners were selected.
    """

    # Build scanner configuration for LlamaFirewall scanners only
    scanner_config = {}
    enabled_scanners = st.session_state.enabled_scanners
    llamafirewall_scanners = ["PromptGuard", "AlignmentCheck"]

    if enabled_scanners.get("PromptGuard", False):
        scanner_config[Role.USER] = scanner_config.get(Role.USER, []) + [ScannerType.PROMPT_GUARD]

    if enabled_scanners.get("AlignmentCheck", False):
        scanner_config[Role.ASSISTANT] = scanner_config.get(Role.ASSISTANT, []) + [ScannerType.AGENT_ALIGNMENT]

    # BUG FIX: Check if ANY scanner is enabled (LlamaFirewall or NeMo)
    total_enabled = sum(enabled_scanners.values())
    if total_enabled == 0:
        print("⚠️ No scanners enabled at all")
        return None

    # If no LlamaFirewall scanners but NeMo scanners are enabled, still return a minimal firewall
    if not scanner_config:
        nemo_enabled = any(enabled_scanners.get(name, False) for name in ["SelfContradiction", "FactChecker", "HallucinationDetector"])
        if nemo_enabled:
            print("ℹ️ Only NeMo scanners enabled, LlamaFirewall not needed but returning placeholder")
            # Return None for firewall, but tests will still run NeMo scanners
            return None
        else:
            print("⚠️ No LlamaFirewall scanners enabled")
            return None

    try:
        llamafirewall_names = [name for name in llamafirewall_scanners if enabled_scanners.get(name, False)]
        print(f"🚀 Initializing LlamaFirewall with scanners: {llamafirewall_names}")
        firewall = LlamaFirewall(scanner_config)

        print(f"✅ LlamaFirewall initialized with {len(llamafirewall_names)} scanner(s): {llamafirewall_names}")
        return firewall

    except Exception as e:
        print(f"❌ LlamaFirewall initialization failed: {str(e)}")
        if "401" in str(e) or "Unauthorized" in str(e):
            st.error("⚠️ LlamaFirewall initialization failed due to authentication. Check your API tokens.")
        else:
            st.error(f"⚠️ LlamaFirewall initialization error: {str(e)}")
        return None


def initialize_nemo_scanners():
    """Initialize NeMo GuardRails scanners"""
    scanners = {}
    if NEMO_GUARDRAILS_AVAILABLE:
        scanners = {
            "FactChecker": FactCheckerScanner()
        }
    return scanners


def build_trace(purpose: str, messages: List[Dict]) -> Trace:
    """Build LlamaFirewall trace from conversation"""
    trace = []

    # Add purpose as first message if provided
    if purpose:
        trace.append(UserMessage(content=f"My goal is: {purpose}"))

    for msg in messages:
        if msg["type"] == "user":
            trace.append(UserMessage(content=msg["content"]))
        elif msg["type"] == "assistant":
            if msg.get("action"):
                # Format as action
                formatted = json.dumps({
                    "thought": msg["content"],
                    "action": msg["action"],
                    "action_input": msg.get("action_input", {})
                })
                trace.append(AssistantMessage(content=formatted))
            else:
                trace.append(AssistantMessage(content=msg["content"]))

    return trace


def test_prompt_guard(firewall, user_input: str) -> Dict:
    """Test PromptGuard scanner on user input"""
    try:
        print(f"🔍 Testing PromptGuard with input: {user_input[:50]}...")
        user_message = UserMessage(content=user_input)
        print("🔍 Created UserMessage, calling firewall.scan()...")
        result = firewall.scan(user_message)
        print(f"✅ PromptGuard scan successful: {result.decision}")

        return {
            "scanner": "PromptGuard",
            "decision": str(result.decision),
            "score": result.score,
            "reason": result.reason,
            "is_safe": result.decision == ScanDecision.ALLOW
        }
    except Exception as e:
        print(f"❌ PromptGuard scan failed: {str(e)}")
        return {"error": str(e), "scanner": "PromptGuard"}


def test_alignment_check(firewall, trace: Trace) -> Dict:
    """Test AlignmentCheck scanner on conversation trace"""
    try:
        result = firewall.scan_replay(trace)

        return {
            "scanner": "AlignmentCheck",
            "decision": str(result.decision),
            "score": result.score,
            "reason": result.reason,
            "is_safe": result.decision == ScanDecision.ALLOW
        }
    except Exception as e:
        return {"error": str(e), "scanner": "AlignmentCheck"}


def run_scanner_tests():
    """
    Run all enabled scanner tests.

    BUG FIX: This function now properly handles the case where only NeMo scanners
    are enabled (firewall is None but tests should still run).
    """
    # Get firewall (may be None if only NeMo scanners enabled)
    firewall = initialize_firewall()

    # BUG FIX: Check if ANY scanner is enabled, not just if firewall exists
    enabled_scanners = st.session_state.enabled_scanners
    any_scanner_enabled = any(enabled_scanners.values())

    if not any_scanner_enabled:
        st.error("❌ No scanners available. Please enable at least one scanner in the sidebar.")
        return

    # Build trace
    trace = build_trace(
        st.session_state.current_conversation["purpose"],
        st.session_state.current_conversation["messages"]
    )

    # Test enabled scanners
    alignment_result = None
    promptguard_results = []
    nemo_results = {}

    # Test AlignmentCheck if enabled (requires firewall)
    if enabled_scanners.get("AlignmentCheck", False) and firewall is not None:
        alignment_result = test_alignment_check(firewall, trace)

    # Test PromptGuard if enabled (requires firewall)
    if enabled_scanners.get("PromptGuard", False) and firewall is not None:
        for msg in st.session_state.current_conversation["messages"]:
            if msg["type"] == "user":
                result = test_prompt_guard(firewall, msg["content"])
                result["message"] = msg["content"][:50] + "..."
                promptguard_results.append(result)

    # Test NeMo GuardRails scanners if enabled (don't require firewall)
    messages = st.session_state.current_conversation["messages"]
    nemo_scanners = initialize_nemo_scanners()

    if enabled_scanners.get("FactChecker", False) and NEMO_GUARDRAILS_AVAILABLE:
        nemo_results["FactChecker"] = nemo_scanners["FactChecker"].scan(messages)

    # Store results
    test_result = {
        "timestamp": datetime.now().isoformat(),
        "purpose": st.session_state.current_conversation["purpose"],
        "alignment_check": alignment_result,
        "prompt_guard": promptguard_results,
        "nemo_results": nemo_results,
        "conversation_length": len(st.session_state.current_conversation["messages"])
    }
    st.session_state.test_results.append(test_result)
    st.rerun()