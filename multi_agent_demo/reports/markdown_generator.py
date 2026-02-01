"""
Markdown report generator for CLI batch processing
"""

from typing import List, Dict


def generate_markdown_report(
    all_results: List[Dict],
    session_files: List[str],
    aggregated: Dict,
    show_safe_details: bool = False
) -> str:
    """
    Generate markdown report for batch scan results

    Args:
        all_results: List of scanner results per session
        session_files: List of session file paths
        aggregated: Aggregated statistics from aggregate_results()
        show_safe_details: Whether to show details for safe sessions

    Returns:
        Markdown formatted report string
    """
    lines = []

    # Header
    lines.append("# 🛡️ AI Agent Guards - Batch Scan Report")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Overall Statistics
    lines.append("## 📊 Overall Statistics")
    lines.append("")
    lines.append(f"- **Total Sessions Scanned:** {aggregated['total_sessions']}")
    lines.append(f"- **Safe Sessions:** {aggregated['safe_sessions']} ✅")
    lines.append(f"- **Sessions with Issues:** {aggregated['unsafe_sessions']} 🚨")
    lines.append("")
    lines.append(f"**Accumulated Counts:**")
    lines.append(f"- 🚫 **Blocks:** {aggregated['total_blocks']}")
    lines.append(f"- ⚠️ **Warnings:** {aggregated['total_warnings']}")
    lines.append(f"- ✅ **Safe:** {aggregated['total_safe']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Per-Scanner Statistics
    lines.append("## 🔍 Results by Scanner")
    lines.append("")

    for scanner_name, counts in aggregated['by_scanner'].items():
        lines.append(f"### {scanner_name}")
        lines.append("")
        lines.append(f"| Metric | Count |")
        lines.append(f"|--------|-------|")
        lines.append(f"| 🚫 Blocks | {counts['blocks']} |")
        lines.append(f"| ⚠️ Warnings | {counts['warnings']} |")
        lines.append(f"| ✅ Safe | {counts['safe']} |")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Summary Table (all sessions with scanner results)
    lines.append("## 📋 Sessions Summary")
    lines.append("")

    # Build table header
    scanner_names = list(aggregated['by_scanner'].keys())
    header = "| Session | " + " | ".join(scanner_names) + " |"
    separator = "|---------|" + "|".join(["---------"] * len(scanner_names)) + "|"

    lines.append(header)
    lines.append(separator)

    # Build table rows
    for i, (result, session_file) in enumerate(zip(all_results, session_files), 1):
        session_name = session_file.split('/')[-1]
        row = f"| {session_name} |"

        for scanner_name in scanner_names:
            # Get scanner result for this session
            scanner_result = None
            if scanner_name == "AlignmentCheck":
                scanner_result = result.get("alignment_check")
            elif scanner_name == "PromptGuard":
                scanner_result = result.get("prompt_guard")
            else:
                scanner_result = result.get("nemo_results", {}).get(scanner_name)

            # Extract blocks and warnings
            if scanner_result and "counts" in scanner_result and "error" not in scanner_result:
                blocks = scanner_result["counts"].get("block", 0)
                warnings = scanner_result["counts"].get("warning", 0)

                if blocks > 0 and warnings > 0:
                    cell = f" 🚫 {blocks} ⚠️ {warnings} |"
                elif blocks > 0:
                    cell = f" 🚫 {blocks} |"
                elif warnings > 0:
                    cell = f" ⚠️ {warnings} |"
                else:
                    cell = " ✅ |"
            else:
                cell = " - |"  # No data or error

            row += cell

        lines.append(row)

    lines.append("")
    lines.append("---")
    lines.append("")

    # Detailed Results (only sessions with issues, unless show_safe_details=True)
    lines.append("## 📋 Detailed Results per Session")
    lines.append("")

    if not show_safe_details:
        lines.append("_Note: Only showing sessions with issues. Safe sessions are omitted for brevity._")
        lines.append("")

    for i, (result, session_file) in enumerate(zip(all_results, session_files), 1):
        # Determine if session has issues
        session_has_issues = _session_has_issues(result)

        # Skip safe sessions if not showing details
        if not session_has_issues and not show_safe_details:
            continue

        # Session header
        session_name = session_file.split('/')[-1]  # Just filename
        lines.append(f"### Session {i}: `{session_name}`")
        lines.append("")

        # Overall session decision
        overall_decision = _get_session_overall_decision(result)
        if overall_decision == "SAFE":
            lines.append(f"**Overall Decision:** 🟢 {overall_decision}")
        elif overall_decision == "WARNING":
            lines.append(f"**Overall Decision:** 🟡 {overall_decision}")
        else:
            lines.append(f"**Overall Decision:** 🔴 {overall_decision}")
        lines.append("")

        # If session is safe, just mention it and move on
        if not session_has_issues:
            lines.append("_All scanners reported this session as safe._")
            lines.append("")
            lines.append("---")
            lines.append("")
            continue

        # Scanner results for this session
        lines.append("**Scanner Results:**")
        lines.append("")

        # AlignmentCheck
        if result.get("alignment_check"):
            _append_scanner_result(lines, "AlignmentCheck", result["alignment_check"])

        # PromptGuard
        if result.get("prompt_guard"):
            _append_scanner_result(lines, "PromptGuard", result["prompt_guard"])

        # NeMo scanners
        for scanner_name, scanner_result in result.get("nemo_results", {}).items():
            _append_scanner_result(lines, scanner_name, scanner_result)

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _session_has_issues(result: Dict) -> bool:
    """Check if session has any issues (blocks or warnings)"""
    # Check AlignmentCheck
    if result.get("alignment_check"):
        ac = result["alignment_check"]
        if ac.get("overall_decision") in ["BLOCK", "WARNING"]:
            return True

    # Check PromptGuard
    if result.get("prompt_guard"):
        pg = result["prompt_guard"]
        if pg.get("overall_decision") in ["BLOCK", "WARNING"]:
            return True

    # Check NeMo scanners
    for scanner_result in result.get("nemo_results", {}).values():
        if scanner_result.get("overall_decision") in ["BLOCK", "WARNING"]:
            return True

    return False


def _get_session_overall_decision(result: Dict) -> str:
    """Get overall decision for a session (BLOCK > WARNING > SAFE)"""
    all_decisions = []

    if result.get("alignment_check") and "overall_decision" in result["alignment_check"]:
        all_decisions.append(result["alignment_check"]["overall_decision"])

    if result.get("prompt_guard") and "overall_decision" in result["prompt_guard"]:
        all_decisions.append(result["prompt_guard"]["overall_decision"])

    for scanner_result in result.get("nemo_results", {}).values():
        if "overall_decision" in scanner_result:
            all_decisions.append(scanner_result["overall_decision"])

    if "BLOCK" in all_decisions:
        return "BLOCK"
    elif "WARNING" in all_decisions:
        return "WARNING"
    else:
        return "SAFE"


def _append_scanner_result(lines: List[str], scanner_name: str, scanner_result: Dict):
    """Append scanner result to markdown lines"""
    decision = scanner_result.get("overall_decision", "SAFE")
    counts = scanner_result.get("counts", {})

    # Only show if not safe
    if decision == "SAFE":
        return

    # Scanner header with decision
    if decision == "BLOCK":
        lines.append(f"- **{scanner_name}:** 🔴 {decision}")
    elif decision == "WARNING":
        lines.append(f"- **{scanner_name}:** 🟡 {decision}")
    else:
        lines.append(f"- **{scanner_name}:** 🟢 {decision}")

    # Counts
    if counts:
        lines.append(f"  - Total: {counts.get('total', 0)} | "
                    f"Safe: {counts.get('safe', 0)} | "
                    f"Warnings: {counts.get('warning', 0)} | "
                    f"Blocks: {counts.get('block', 0)}")

    # Reason (if available and not safe)
    if scanner_result.get("reason"):
        reason = scanner_result["reason"]
        # Truncate long reasons
        if len(reason) > 200:
            reason = reason[:200] + "..."
        lines.append(f"  - _Reason:_ {reason}")

    lines.append("")
