"""
Shared scanner execution logic
Used by both UI and CLI to run scanners on sessions
"""

from typing import Dict, List, Optional
import json


def run_scanners_on_session(
    session_data: dict,
    enabled_scanners: List[str],
    agent_config: Optional[dict] = None
) -> dict:
    """
    Run enabled scanners on a single session (CLI-compatible, no Streamlit dependency)

    Args:
        session_data: Session JSON with messages and purpose/agent_purpose
        enabled_scanners: List of scanner names to run
        agent_config: Optional agent configuration (name, role, purpose)

    Returns:
        dict with scanner results

    Supported session formats:
        Format 1 (Langfuse export):
        {
          "scenario_name": "...",
          "agent_purpose": "...",
          "messages": [...]
        }

        Format 2 (Simple):
        {
          "session_id": "...",
          "purpose": "...",
          "messages": [...]
        }
    """
    # Extract conversation and purpose from session data
    # Support both "agent_purpose" (Langfuse) and "purpose" (simple format)
    messages = session_data.get("messages", [])
    purpose = session_data.get("agent_purpose") or session_data.get("purpose", "")

    # Build agent config
    if not agent_config:
        agent_config = {
            "name": session_data.get("agent_name", "Agent"),
            "role": session_data.get("agent_role", "Assistant"),
            "purpose": purpose
        }

    # Initialize results
    results = {
        "alignment_check": None,
        "prompt_guard": None,
        "nemo_results": {}
    }

    # Run AlignmentCheck (try native LlamaFirewall first, fallback to GPT-4o-mini)
    if "AlignmentCheck" in enabled_scanners:
        try:
            # Try native LlamaFirewall first
            from llamafirewall import (
                LlamaFirewall,
                Role,
                ScannerType,
                UserMessage,
                AssistantMessage,
                ScanDecision
            )
            import os

            # Check if TOGETHER_API_KEY is configured
            together_key = os.getenv("TOGETHER_API_KEY")
            if not together_key:
                raise Exception("TOGETHER_API_KEY not configured, will use fallback")

            # Initialize native LlamaFirewall
            scanner_config = {Role.ASSISTANT: [ScannerType.AGENT_ALIGNMENT]}
            firewall = LlamaFirewall(scanner_config)

            # Build trace from messages
            trace = []
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

            # Validate each assistant message individually for granular results
            assistant_messages = [(i, msg) for i, msg in enumerate(messages) if msg.get("type") == "assistant"]

            if not assistant_messages:
                results["alignment_check"] = {
                    "scanner": "AlignmentCheck",
                    "overall_decision": "SAFE",
                    "counts": {"safe": 0, "warning": 0, "block": 0, "total": 0},
                    "message_results": [],
                    "reason": "No assistant messages to validate",
                    "method": "native_llamafirewall"
                }
            else:
                # Per-message validation using native LlamaFirewall
                message_results = []

                for msg_idx, msg in assistant_messages:
                    # Build trace up to and including this message
                    msg_trace = []
                    if purpose:
                        msg_trace.append(UserMessage(content=f"My goal is: {purpose}"))

                    for i, m in enumerate(messages[:msg_idx + 1]):
                        if m["type"] == "user":
                            msg_trace.append(UserMessage(content=m["content"]))
                        elif m["type"] == "assistant":
                            if m.get("action"):
                                formatted = json.dumps({
                                    "thought": m["content"],
                                    "action": m["action"],
                                    "action_input": m.get("action_input", {})
                                })
                                msg_trace.append(AssistantMessage(content=formatted))
                            else:
                                msg_trace.append(AssistantMessage(content=m["content"]))

                    # Scan this message
                    result = firewall.scan_replay(msg_trace)

                    # Convert to normalized format
                    decision = "SAFE" if result.decision == ScanDecision.ALLOW else "BLOCK"
                    message_results.append({
                        "message_index": msg_idx,
                        "message_type": "assistant",
                        "decision": decision,
                        "reason": result.reason
                    })

                # Calculate counts
                counts = {
                    "safe": sum(1 for r in message_results if r["decision"] == "SAFE"),
                    "warning": sum(1 for r in message_results if r["decision"] == "WARNING"),
                    "block": sum(1 for r in message_results if r["decision"] == "BLOCK"),
                    "total": len(message_results)
                }

                # Determine overall decision
                if counts["block"] > 0:
                    overall_decision = "BLOCK"
                elif counts["warning"] > 0:
                    overall_decision = "WARNING"
                else:
                    overall_decision = "SAFE"

                results["alignment_check"] = {
                    "scanner": "AlignmentCheck",
                    "overall_decision": overall_decision,
                    "counts": counts,
                    "message_results": message_results,
                    "method": "native_llamafirewall"
                }

        except Exception as e:
            # Fall back to GPT-4o-mini implementation
            print(f"⚠️ Native LlamaFirewall failed: {str(e)}, using GPT-4o-mini fallback...")
            try:
                from multi_agent_demo.alignment_check_new import scan_alignment_check_per_message
                results["alignment_check"] = scan_alignment_check_per_message(
                    messages=messages,
                    purpose=purpose
                )
                # Mark as fallback
                if isinstance(results["alignment_check"], dict):
                    results["alignment_check"]["method"] = "gpt4o_mini_fallback"
            except Exception as fallback_error:
                results["alignment_check"] = {"error": f"Native failed: {str(e)}, Fallback failed: {str(fallback_error)}"}

    # Run PromptGuard
    if "PromptGuard" in enabled_scanners:
        try:
            from multi_agent_demo.alignment_check_new import scan_prompt_guard_per_message
            results["prompt_guard"] = scan_prompt_guard_per_message(
                messages=messages
            )
        except Exception as e:
            results["prompt_guard"] = {"error": str(e)}

    # Run FactsChecker
    if "FactsChecker" in enabled_scanners or "FactChecker" in enabled_scanners:
        try:
            # Lazy import - only load NeMo when needed
            from multi_agent_demo.scanners import FactCheckerScanner, NEMO_GUARDRAILS_AVAILABLE

            if NEMO_GUARDRAILS_AVAILABLE:
                scanner = FactCheckerScanner()
                # Pass today's date for temporal context
                from datetime import datetime
                current_date = datetime.now().strftime("%B %d, %Y")  # e.g., "February 07, 2026"
                # Use explicit keyword arg 'context' to match method signature
                result = scanner.scan(messages, context=purpose, current_date=current_date)
                results["nemo_results"]["FactsChecker"] = result
            else:
                results["nemo_results"]["FactsChecker"] = {
                    "error": "NeMo GuardRails not available"
                }
        except Exception as e:
            results["nemo_results"]["FactsChecker"] = {"error": str(e)}

    # Run DataDisclosureGuard
    if "DataDisclosureGuard" in enabled_scanners:
        try:
            # Lazy import - only load Presidio when needed
            from multi_agent_demo.scanners import DataDisclosureGuardScanner, PRESIDIO_AVAILABLE

            if PRESIDIO_AVAILABLE:
                scanner = DataDisclosureGuardScanner()
                result = scanner.scan(messages, purpose)
                results["nemo_results"]["DataDisclosureGuard"] = result
            else:
                results["nemo_results"]["DataDisclosureGuard"] = {
                    "error": "Presidio not available"
                }
        except Exception as e:
            results["nemo_results"]["DataDisclosureGuard"] = {"error": str(e)}

    return results


def aggregate_results(all_results: List[dict]) -> dict:
    """
    Aggregate results from multiple sessions

    Args:
        all_results: List of result dicts from multiple sessions

    Returns:
        dict with aggregated statistics:
        {
            "total_sessions": int,
            "safe_sessions": int,
            "unsafe_sessions": int,
            "total_blocks": int,
            "total_warnings": int,
            "total_safe": int,
            "by_scanner": {
                "AlignmentCheck": {"blocks": int, "warnings": int, "safe": int},
                ...
            }
        }
    """
    total_sessions = len(all_results)
    safe_sessions = 0
    unsafe_sessions = 0
    total_blocks = 0
    total_warnings = 0
    total_safe = 0

    by_scanner = {}

    for result in all_results:
        session_is_safe = True

        # Check AlignmentCheck
        if result.get("alignment_check"):
            ac = result["alignment_check"]
            scanner_name = "AlignmentCheck"
            if scanner_name not in by_scanner:
                by_scanner[scanner_name] = {"blocks": 0, "warnings": 0, "safe": 0}

            if "overall_decision" in ac:
                # Add ALL counts (a scanner can have both blocks and warnings)
                if "counts" in ac:
                    counts = ac["counts"]
                    total_blocks += counts.get("block", 0)
                    total_warnings += counts.get("warning", 0)
                    total_safe += counts.get("safe", 0)

                    # Also add to per-scanner counts (actual message counts, not session counts)
                    by_scanner[scanner_name]["blocks"] += counts.get("block", 0)
                    by_scanner[scanner_name]["warnings"] += counts.get("warning", 0)
                    by_scanner[scanner_name]["safe"] += counts.get("safe", 0)

                # Check if session is safe
                if ac["overall_decision"] in ["BLOCK", "WARNING"]:
                    session_is_safe = False

        # Check PromptGuard
        if result.get("prompt_guard"):
            pg = result["prompt_guard"]
            scanner_name = "PromptGuard"
            if scanner_name not in by_scanner:
                by_scanner[scanner_name] = {"blocks": 0, "warnings": 0, "safe": 0}

            if "overall_decision" in pg:
                # Add ALL counts (a scanner can have both blocks and warnings)
                if "counts" in pg:
                    counts = pg["counts"]
                    total_blocks += counts.get("block", 0)
                    total_warnings += counts.get("warning", 0)
                    total_safe += counts.get("safe", 0)

                    # Also add to per-scanner counts (actual message counts, not session counts)
                    by_scanner[scanner_name]["blocks"] += counts.get("block", 0)
                    by_scanner[scanner_name]["warnings"] += counts.get("warning", 0)
                    by_scanner[scanner_name]["safe"] += counts.get("safe", 0)

                # Check if session is safe
                if pg["overall_decision"] in ["BLOCK", "WARNING"]:
                    session_is_safe = False

        # Check NeMo scanners (FactsChecker, DataDisclosureGuard)
        for scanner_name, scanner_result in result.get("nemo_results", {}).items():
            # Skip scanners with errors (not installed, etc.)
            if "error" in scanner_result:
                continue

            if scanner_name not in by_scanner:
                by_scanner[scanner_name] = {"blocks": 0, "warnings": 0, "safe": 0}

            if "overall_decision" in scanner_result:
                decision = scanner_result["overall_decision"]

                # Add ALL counts (a scanner can have both blocks and warnings, like FactsChecker)
                if "counts" in scanner_result:
                    counts = scanner_result["counts"]
                    total_blocks += counts.get("block", 0)
                    total_warnings += counts.get("warning", 0)
                    total_safe += counts.get("safe", 0)

                    # Also add to per-scanner counts (actual message counts, not session counts)
                    by_scanner[scanner_name]["blocks"] += counts.get("block", 0)
                    by_scanner[scanner_name]["warnings"] += counts.get("warning", 0)
                    by_scanner[scanner_name]["safe"] += counts.get("safe", 0)

                # Check if session is safe
                if decision in ["BLOCK", "WARNING"]:
                    session_is_safe = False

        if session_is_safe:
            safe_sessions += 1
        else:
            unsafe_sessions += 1

    return {
        "total_sessions": total_sessions,
        "safe_sessions": safe_sessions,
        "unsafe_sessions": unsafe_sessions,
        "total_blocks": total_blocks,
        "total_warnings": total_warnings,
        "total_safe": total_safe,
        "by_scanner": by_scanner
    }
