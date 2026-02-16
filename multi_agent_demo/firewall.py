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
    SystemMessage,
    Trace,
    UserMessage,
)

from multi_agent_demo.scanners import (
    FactCheckerScanner,
    NEMO_GUARDRAILS_AVAILABLE,
    DataDisclosureGuardScanner,
    PRESIDIO_AVAILABLE
)
from multi_agent_demo.direct_scanner_wrapper import (
    scan_alignment_check_direct,
    scan_prompt_guard_direct
)
from multi_agent_demo.alignment_check_new import (
    scan_alignment_check_per_message,
    scan_prompt_guard_per_message
)
from multi_agent_demo.core.scanner_runner import (
    ALIGNMENT_EVAL_CONTEXT,
    ALIGNMENT_PARALLEL_THRESHOLD,
    check_trace_for_large_messages,
    is_trivially_empty,
    scan_replay_with_timeout,
    _scan_single_message
)


def initialize_firewall():
    """
    Initialize LlamaFirewall with selected LlamaFirewall scanners only.

    BUG FIX: Returns None only if NO scanners are enabled at all.
    Previously returned None if no LlamaFirewall scanners were enabled,
    even when NeMo scanners were selected.
    """
    import os

    # Check for required API tokens BEFORE attempting initialization
    enabled_scanners = st.session_state.enabled_scanners
    llamafirewall_scanners = ["PromptGuard", "AlignmentCheck"]

    # Check if any LlamaFirewall scanner is enabled
    llamafirewall_enabled = any(enabled_scanners.get(name, False) for name in llamafirewall_scanners)

    if llamafirewall_enabled:
        # Verify required API tokens exist
        if enabled_scanners.get("AlignmentCheck", False):
            together_key = os.getenv("TOGETHER_API_KEY")
            if not together_key:
                st.error("⚠️ AlignmentCheck requires TOGETHER_API_KEY. Please configure it in Streamlit Cloud secrets.")
                return None

        if enabled_scanners.get("PromptGuard", False):
            hf_token = os.getenv("HF_TOKEN")
            if not hf_token:
                st.warning("⚠️ PromptGuard works best with HF_TOKEN. Configure it in Streamlit Cloud secrets if you encounter issues.")

    # Build scanner configuration for LlamaFirewall scanners only
    scanner_config = {}

    if enabled_scanners.get("PromptGuard", False):
        scanner_config[Role.USER] = scanner_config.get(Role.USER, []) + [ScannerType.PROMPT_GUARD]

    if enabled_scanners.get("AlignmentCheck", False):
        scanner_config[Role.ASSISTANT] = scanner_config.get(Role.ASSISTANT, []) + [ScannerType.AGENT_ALIGNMENT]

    # BUG FIX: Check if ANY scanner is enabled (LlamaFirewall or NeMo)
    total_enabled = sum(enabled_scanners.values())
    if total_enabled == 0:
        print("⚠️ No scanners enabled at all")
        return None

    # If no LlamaFirewall scanners but NeMo scanners are enabled, return None
    if not scanner_config:
        nemo_enabled = any(enabled_scanners.get(name, False) for name in ["FactsChecker"])
        if nemo_enabled:
            print("ℹ️ Only NeMo scanners enabled, LlamaFirewall not needed")
            return None
        else:
            print("⚠️ No LlamaFirewall scanners enabled")
            return None

    # Validate scanner configuration before passing to LlamaFirewall
    if not scanner_config or not any(scanner_config.values()):
        print("⚠️ Scanner configuration is empty, skipping LlamaFirewall initialization")
        return None

    try:
        llamafirewall_names = [name for name in llamafirewall_scanners if enabled_scanners.get(name, False)]
        print(f"🚀 Initializing LlamaFirewall with scanners: {llamafirewall_names}")
        print(f"🔧 Scanner config: {scanner_config}")

        # Initialize with explicit configuration
        firewall = LlamaFirewall(scanner_config)

        print(f"✅ LlamaFirewall initialized with {len(llamafirewall_names)} scanner(s): {llamafirewall_names}")
        return firewall

    except SyntaxError as e:
        print(f"❌ LlamaFirewall initialization failed with SyntaxError: {str(e)}")
        st.error(f"⚠️ LlamaFirewall configuration error: {str(e)}. This may be due to API token issues or environment differences.")
        return None
    except Exception as e:
        print(f"❌ LlamaFirewall initialization failed: {str(e)}")
        if "401" in str(e) or "Unauthorized" in str(e):
            st.error("⚠️ LlamaFirewall initialization failed due to authentication. Check your API tokens in Streamlit Cloud secrets.")
        elif "expected an indented block" in str(e):
            st.error("⚠️ LlamaFirewall configuration error. Please check your API tokens are properly configured in Streamlit Cloud secrets.")
        else:
            st.error(f"⚠️ LlamaFirewall initialization error: {str(e)}")
        return None


def initialize_nemo_scanners():
    """Initialize NeMo GuardRails and other custom scanners"""
    scanners = {}
    if NEMO_GUARDRAILS_AVAILABLE:
        scanners["FactsChecker"] = FactCheckerScanner()

    if PRESIDIO_AVAILABLE:
        scanners["DataDisclosureGuard"] = DataDisclosureGuardScanner()

    return scanners


def build_trace(purpose: str, messages: List[Dict]) -> Trace:
    """Build LlamaFirewall trace from conversation"""
    trace = []

    # Add purpose as system context so that AlignmentCheck picks
    # the first real UserMessage as the goal to evaluate against
    system_content = f"{ALIGNMENT_EVAL_CONTEXT}\n\n{purpose}" if purpose else ALIGNMENT_EVAL_CONTEXT
    trace.append(SystemMessage(content=system_content))

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
    """Test PromptGuard scanner on user input with fallback to direct API"""
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
        # Try direct HF Inference API fallback
        print(f"⚠️ LlamaFirewall PromptGuard failed: {str(e)}, trying direct API fallback...")
        return scan_prompt_guard_direct(user_input)


def test_alignment_check(firewall, trace: Trace, messages: List[Dict] = None, purpose: str = "") -> Dict:
    """Test AlignmentCheck scanner on conversation trace with fallback to direct API"""
    try:
        result = firewall.scan_replay(trace)

        return {
            "scanner": "AlignmentCheck",
            "decision": str(result.decision),
            "score": result.score,
            "reason": result.reason,
            "is_safe": result.decision == ScanDecision.ALLOW
        }
    except SyntaxError as e:
        # Syntax error - try direct API fallback (use NEW per-message scanner)
        print(f"⚠️ LlamaFirewall AlignmentCheck failed with SyntaxError, trying direct API fallback...")
        if messages is not None:
            return scan_alignment_check_per_message(messages, purpose)
        return {"error": f"SyntaxError and no messages for fallback: {str(e)}", "scanner": "AlignmentCheck"}
    except Exception as e:
        # Other errors - try direct API fallback if available (use NEW per-message scanner)
        print(f"⚠️ LlamaFirewall AlignmentCheck failed: {str(e)}, trying direct API fallback...")
        if messages is not None:
            return scan_alignment_check_per_message(messages, purpose)
        return {"error": str(e), "scanner": "AlignmentCheck"}


def _ui_run_alignment_check(messages, purpose):
    """Run AlignmentCheck for UI path (thread-safe, no Streamlit calls).

    Delegates to the shared _scan_single_message helper. For sessions with
    >= ALIGNMENT_PARALLEL_THRESHOLD assistant messages, scans run in parallel.
    """
    try:
        import os
        import logging
        from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
        logging.getLogger("llamafirewall").setLevel(logging.ERROR)

        together_key = os.getenv("TOGETHER_API_KEY")
        if not together_key:
            raise Exception("TOGETHER_API_KEY not configured")

        assistant_messages = [(i, msg) for i, msg in enumerate(messages) if msg.get("type") == "assistant"]
        if not assistant_messages:
            return {
                "scanner": "AlignmentCheck",
                "overall_decision": "SAFE",
                "counts": {"safe": 0, "warning": 0, "block": 0, "total": 0},
                "message_results": [],
                "method": "native_llamafirewall"
            }

        if len(assistant_messages) >= ALIGNMENT_PARALLEL_THRESHOLD:
            message_results = []
            futures = {}
            with ThreadPoolExecutor(max_workers=3) as executor:
                for msg_idx, msg in assistant_messages:
                    future = executor.submit(_scan_single_message, messages, msg_idx, purpose)
                    futures[future] = msg_idx

                try:
                    for future in as_completed(futures, timeout=600):
                        try:
                            message_results.append(future.result())
                        except Exception as e:
                            msg_idx = futures[future]
                            message_results.append({
                                "message_index": msg_idx,
                                "message_type": "assistant",
                                "decision": "WARNING",
                                "reason": str(e),
                                "skipped": True,
                                "skip_severity": "error"
                            })
                except FuturesTimeout:
                    for future, msg_idx in futures.items():
                        if not future.done():
                            message_results.append({
                                "message_index": msg_idx,
                                "message_type": "assistant",
                                "decision": "WARNING",
                                "reason": "AlignmentCheck per-message scan timed out (600s)",
                                "skipped": True,
                                "skip_severity": "timeout"
                            })

            message_results.sort(key=lambda r: r["message_index"])
        else:
            message_results = []
            for msg_idx, msg in assistant_messages:
                message_results.append(_scan_single_message(messages, msg_idx, purpose))

        counts = {
            "safe": sum(1 for r in message_results if r["decision"] == "SAFE"),
            "warning": sum(1 for r in message_results if r["decision"] == "WARNING"),
            "block": sum(1 for r in message_results if r["decision"] == "BLOCK"),
            "total": len(message_results)
        }
        overall = "BLOCK" if counts["block"] > 0 else "WARNING" if counts["warning"] > 0 else "SAFE"
        print(f"✅ Native LlamaFirewall AlignmentCheck: {overall}")
        return {
            "scanner": "AlignmentCheck",
            "overall_decision": overall,
            "counts": counts,
            "message_results": message_results,
            "method": "native_llamafirewall"
        }
    except Exception as e:
        print(f"⚠️ Native LlamaFirewall failed: {str(e)}, using GPT-4o-mini fallback...")
        result = scan_alignment_check_per_message(messages, purpose)
        if isinstance(result, dict):
            result["method"] = "gpt4o_mini_fallback"
        return result


def _ui_run_prompt_guard(messages):
    """Run PromptGuard for UI path (thread-safe, no Streamlit calls)."""
    return scan_prompt_guard_per_message(messages)


def _ui_run_facts_checker(messages, purpose, nemo_scanners_dict):
    """Run FactsChecker for UI path (thread-safe, no Streamlit calls)."""
    current_date = datetime.now().strftime("%B %d, %Y")
    return nemo_scanners_dict["FactsChecker"].scan(messages, context=purpose, current_date=current_date)


def _ui_run_data_disclosure_guard(messages, purpose, nemo_scanners_dict):
    """Run DataDisclosureGuard for UI path (thread-safe, no Streamlit calls)."""
    return nemo_scanners_dict["DataDisclosureGuard"].scan(messages, purpose)


def run_scanner_tests():
    """
    Run all enabled scanner tests in parallel.

    All scanners are independent (no data dependencies), so they run concurrently
    via ThreadPoolExecutor for ~4x speedup. Session state reads happen on the main
    thread before launching workers; session state writes and st.rerun() happen on
    the main thread after all workers complete.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

    # Get firewall (may be None if only NeMo scanners enabled)
    firewall = initialize_firewall()

    # Check if ANY scanner is enabled
    enabled_scanners = st.session_state.enabled_scanners
    any_scanner_enabled = any(enabled_scanners.values())

    if not any_scanner_enabled:
        st.error("❌ No scanners available. Please enable at least one scanner in the sidebar.")
        return

    # Read all needed data from session state on the main thread
    messages = st.session_state.current_conversation["messages"]
    purpose = st.session_state.current_conversation["purpose"]

    # Initialize NeMo scanners on main thread (one-time setup)
    nemo_scanners_dict = initialize_nemo_scanners()

    # Submit all enabled scanners to run in parallel
    alignment_result = None
    promptguard_result = None
    nemo_results = {}

    futures = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        if enabled_scanners.get("AlignmentCheck", False):
            print("✅ Running AlignmentCheck scanner...")
            futures[executor.submit(_ui_run_alignment_check, messages, purpose)] = "alignment_check"

        if enabled_scanners.get("PromptGuard", False):
            print("✅ Running PromptGuard scanner...")
            futures[executor.submit(_ui_run_prompt_guard, messages)] = "prompt_guard"

        if enabled_scanners.get("FactsChecker", False) and NEMO_GUARDRAILS_AVAILABLE:
            print("✅ Running FactsChecker scanner...")
            futures[executor.submit(_ui_run_facts_checker, messages, purpose, nemo_scanners_dict)] = "FactsChecker"

        if enabled_scanners.get("DataDisclosureGuard", False) and PRESIDIO_AVAILABLE:
            print("✅ Running DataDisclosureGuard scanner...")
            futures[executor.submit(_ui_run_data_disclosure_guard, messages, purpose, nemo_scanners_dict)] = "DataDisclosureGuard"

        # Collect results as they complete (wait up to 10 min for all scanners)
        try:
            for future in as_completed(futures, timeout=600):
                key = futures[future]
                try:
                    result = future.result()
                    if key == "alignment_check":
                        alignment_result = result
                    elif key == "prompt_guard":
                        promptguard_result = result
                    else:
                        nemo_results[key] = result
                except Exception as e:
                    if key == "alignment_check":
                        alignment_result = {"error": str(e)}
                    elif key == "prompt_guard":
                        promptguard_result = {"error": str(e)}
                    else:
                        nemo_results[key] = {"error": str(e)}
        except FuturesTimeoutError:
            # Some scanners didn't finish — report timeout for unfinished ones
            for future, key in futures.items():
                if not future.done():
                    error = {"error": "Scanner timed out (600s)"}
                    if key == "alignment_check":
                        alignment_result = error
                    elif key == "prompt_guard":
                        promptguard_result = error
                    else:
                        nemo_results[key] = error

    # Store results on main thread (session state writes must be main-thread)
    test_result = {
        "timestamp": datetime.now().isoformat(),
        "purpose": purpose,
        "alignment_check": alignment_result,
        "prompt_guard": promptguard_result,
        "nemo_results": nemo_results,
        "conversation_length": len(messages)
    }
    st.session_state.test_results.append(test_result)
    st.rerun()