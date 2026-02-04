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
    # Import scanners module (always needed for availability flags)
    from multi_agent_demo.scanners import (
        FactCheckerScanner,
        NEMO_GUARDRAILS_AVAILABLE,
        DataDisclosureGuardScanner,
        PRESIDIO_AVAILABLE
    )

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

    # Run AlignmentCheck
    if "AlignmentCheck" in enabled_scanners:
        try:
            from multi_agent_demo.alignment_check_new import scan_alignment_check_per_message
            results["alignment_check"] = scan_alignment_check_per_message(
                messages=messages,
                purpose=purpose
            )
        except Exception as e:
            results["alignment_check"] = {"error": str(e)}

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
        if NEMO_GUARDRAILS_AVAILABLE:
            try:
                scanner = FactCheckerScanner()
                # Use explicit keyword arg 'context' to match method signature
                result = scanner.scan(messages, context=purpose)
                results["nemo_results"]["FactsChecker"] = result
            except Exception as e:
                results["nemo_results"]["FactsChecker"] = {"error": str(e)}
        else:
            results["nemo_results"]["FactsChecker"] = {
                "error": "NeMo GuardRails not available"
            }

    # Run DataDisclosureGuard
    if "DataDisclosureGuard" in enabled_scanners:
        if PRESIDIO_AVAILABLE:
            try:
                scanner = DataDisclosureGuardScanner()
                result = scanner.scan(messages, purpose)
                results["nemo_results"]["DataDisclosureGuard"] = result
            except Exception as e:
                results["nemo_results"]["DataDisclosureGuard"] = {"error": str(e)}
        else:
            results["nemo_results"]["DataDisclosureGuard"] = {
                "error": "Presidio not available"
            }

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
