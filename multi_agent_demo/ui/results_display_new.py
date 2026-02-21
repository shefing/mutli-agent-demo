"""
Test results display with count-based UI and visual linking to conversation messages
"""

import streamlit as st
import pandas as pd

# Map internal scanner keys to user-facing display names
SCANNER_DISPLAY_NAMES = {
    "PromptGuard": "Prompt Guard",
    "AlignmentCheck": "Alignment Checker",
    "FactsChecker": "Facts Checker",
    "DataDisclosureGuard": "Data Guard",
}


def _get_role_specific_number(messages: list, message_index: int, message_type: str) -> int:
    """Calculate role-specific message number (e.g., User #1, Agent #2)"""
    count = 0
    for i in range(message_index + 1):
        if i < len(messages) and messages[i].get("type") == message_type:
            count += 1
    return count


def _role_badge_html(role: str, number: int, decision: str) -> str:
    """Generate colored badge matching conversation panel"""
    colors = {"BLOCK": "#e74c3c", "WARNING": "#f39c12", "SAFE": "#27ae60"}
    color = colors.get(decision, "#555")
    prefix = "U" if role == "user" else "A"
    return f'<span style="background:{color}; color:white; padding:3px 10px; border-radius:4px; font-size:0.9rem; font-weight:bold;">{prefix}#{number}</span>'


def _compact_counts_html(counts: dict) -> str:
    """Render compact inline count bar"""
    safe = counts.get("safe", 0)
    warning = counts.get("warning", 0)
    block = counts.get("block", 0)
    parts = []
    if safe > 0:
        parts.append(f'<span style="color:#27ae60; font-size:1.05rem;">&#10003;{safe}</span>')
    if warning > 0:
        parts.append(f'<span style="color:#f39c12; font-size:1.05rem;">&#9888;{warning}</span>')
    if block > 0:
        parts.append(f'<span style="color:#e74c3c; font-size:1.05rem;">&#10007;{block}</span>')
    return " &nbsp; ".join(parts) if parts else '<span style="color:#888; font-size:1.05rem;">No data</span>'


def _render_results_summary(result: dict):
    """Render a clear overall results summary at top of results panel"""
    # Collect per-scanner decisions in display order
    scanner_decisions = []

    if result.get("prompt_guard") and "overall_decision" in result["prompt_guard"]:
        scanner_decisions.append(("PromptGuard", result["prompt_guard"]["overall_decision"]))

    if result.get("alignment_check") and "overall_decision" in result["alignment_check"]:
        scanner_decisions.append(("AlignmentCheck", result["alignment_check"]["overall_decision"]))

    for name, sr in result.get("nemo_results", {}).items():
        if "overall_decision" in sr:
            scanner_decisions.append((name, sr["overall_decision"]))

    # Determine overall
    all_decisions = [d for _, d in scanner_decisions]
    if "BLOCK" in all_decisions:
        overall, color = "BLOCK", "#e74c3c"
    elif "WARNING" in all_decisions:
        overall, color = "WARNING", "#f39c12"
    else:
        overall, color = "SAFE", "#27ae60"

    # Overall badge
    st.markdown(
        f'<div style="background:{color}; color:white; padding:12px 16px; border-radius:8px; '
        f'text-align:center; font-size:1.5rem; font-weight:bold; margin-bottom:8px;">'
        f'{overall}</div>',
        unsafe_allow_html=True
    )

    # Per-scanner summary line with nowrap to prevent icon/name splitting
    icons = {"BLOCK": "🔴", "WARNING": "🟡", "SAFE": "🟢"}
    summary_parts = []
    for name, decision in scanner_decisions:
        display = SCANNER_DISPLAY_NAMES.get(name, name)
        summary_parts.append(
            f'<span style="white-space:nowrap;">{icons.get(decision, "⚪")}&nbsp;{display}</span>'
        )
    st.markdown(
        f'<div style="text-align:center; font-size:1rem; color:#aaa; margin-bottom:8px;">'
        f'{" &nbsp;&bull;&nbsp; ".join(summary_parts)}</div>',
        unsafe_allow_html=True
    )


def render_scanner_counts(scanner_name: str, result: dict, messages: list = None):
    """Render counts for a single scanner with compact layout and colored badges"""
    if not result or "error" in result:
        st.error(f"{scanner_name}: Error - {result.get('error', 'Unknown error')}")
        return

    counts = result.get("counts", {})
    overall = result.get("overall_decision", "SAFE")

    # Header with decision icon and compact counts
    display_name = SCANNER_DISPLAY_NAMES.get(scanner_name, scanner_name)
    icons = {"BLOCK": "&#x1F534;", "WARNING": "&#x1F7E1;", "SAFE": "&#x1F7E2;"}
    icon = icons.get(overall, "")
    counts_html = _compact_counts_html(counts)

    st.markdown(
        f'<div style="display:flex; align-items:center; gap:12px; margin:4px 0; flex-wrap:nowrap;">'
        f'<span style="font-weight:bold; font-size:1.25rem; white-space:nowrap;">{icon} {display_name}</span>'
        f'<span style="font-size:1.1rem;">{counts_html}</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Overall analysis (expanded if not SAFE)
    if overall != "SAFE" and "reason" in result and result["reason"]:
        with st.expander("View Analysis", expanded=True):
            st.markdown(result["reason"])

    # Special handling for FactsChecker
    if scanner_name == "FactsChecker":
        _render_factchecker_details(result)
    elif scanner_name == "DataDisclosureGuard":
        _render_datadisclosure_details(result)

    # Per-message issues (expanded by default when there are issues)
    message_results = result.get("message_results", [])
    if message_results:
        issues_only = [msg for msg in message_results if msg.get("decision", "SAFE") != "SAFE"]

        if issues_only:
            with st.expander(f"{len(issues_only)} message(s) with issues", expanded=True):
                for msg_result in issues_only:
                    msg_idx = msg_result.get("message_index", "?")
                    msg_type = msg_result.get("message_type", "?")
                    decision = msg_result.get("decision", "SAFE")
                    reason = msg_result.get("reason", "No details available")

                    # Use "Agent" instead of "assistant" for display
                    display_type = "Agent" if msg_type == "assistant" else msg_type.capitalize()

                    if messages and isinstance(msg_idx, int):
                        role_number = _get_role_specific_number(messages, msg_idx, msg_type)
                        badge = _role_badge_html(msg_type, role_number, decision)
                    else:
                        badge = f'<span style="background:#e74c3c; color:white; padding:3px 10px; border-radius:4px; font-size:0.9rem;">Msg {msg_idx}</span>'

                    # Message preview
                    preview = ""
                    if messages and isinstance(msg_idx, int) and msg_idx < len(messages):
                        msg_content = messages[msg_idx].get("content", "")
                        preview = msg_content[:80] + ("..." if len(msg_content) > 80 else "")

                    st.markdown(
                        f'{badge} &nbsp; <span style="color:#ccc; font-size:0.95rem;">{preview}</span>',
                        unsafe_allow_html=True
                    )
                    st.text(reason)
                    st.divider()


def _render_factchecker_details(result: dict):
    """Render detailed FactsChecker analysis"""
    issues = result.get("issues_detected", [])
    detailed_analysis = result.get("detailed_analysis", {})
    per_message_findings = result.get("per_message_findings", [])

    if not issues and not per_message_findings:
        return

    if issues:
        with st.expander(f"Issues Detected ({len(issues)})", expanded=True):
            for issue in issues:
                if issue == "Self-Contradiction":
                    st.error(f"**{issue}**: Agent contradicted previous statements")
                elif issue == "RAG Ungroundedness":
                    st.warning(f"**{issue}**: Claims made without evidence support")
                else:
                    st.warning(f"**{issue}**")

                if issue in detailed_analysis:
                    with st.expander(f"{issue} - Full Analysis", expanded=False):
                        st.markdown(detailed_analysis[issue])

    if per_message_findings:
        with st.expander(f"Per-Message Findings ({len(per_message_findings)} messages)", expanded=True):
            findings_by_message = {}
            for finding in per_message_findings:
                msg_num = finding["message_number"]
                if msg_num not in findings_by_message:
                    findings_by_message[msg_num] = []
                findings_by_message[msg_num].append(finding)

            for msg_num in sorted(findings_by_message.keys()):
                findings = findings_by_message[msg_num]
                issues_list = [f["issue_type"] for f in findings]

                st.markdown(f"**Agent Message {msg_num}:** {', '.join(issues_list)}")
                st.caption(f"_Preview:_ {findings[0]['message_preview'][:100]}...")

                for finding in findings:
                    with st.expander(f"Agent Msg {msg_num} - {finding['issue_type']}", expanded=False):
                        st.markdown(finding['details'])


def _render_datadisclosure_details(result: dict):
    """Render detailed DataDisclosureGuard analysis"""
    pii_findings = result.get("pii_findings", [])

    if not pii_findings:
        return

    overall_aligned = pii_findings[0].get('is_aligned', True) if pii_findings else True
    all_pii_types = set()
    for finding in pii_findings:
        for entity in finding.get('pii_entities', []):
            all_pii_types.add(entity['type'])

    if overall_aligned:
        st.success(f"PII collection is appropriate for stated purpose")
    else:
        st.error(f"PII collection appears misaligned with stated purpose")

    with st.expander(f"PII Details ({len(pii_findings)} occurrence(s), {len(all_pii_types)} type(s))", expanded=not overall_aligned):
        st.markdown(f"**Detected PII Types:** {', '.join(sorted(all_pii_types))}")

        if not overall_aligned and pii_findings:
            alignment_reason = pii_findings[0].get('alignment_check', {}).get('reason', 'N/A')
            with st.expander("Alignment Reasoning", expanded=False):
                st.text(alignment_reason)

        st.divider()
        st.markdown("**PII by Message:**")
        for idx, finding in enumerate(pii_findings, 1):
            pii_list = ', '.join([f"{e['type']}" for e in finding.get('pii_entities', [])])
            msg_type = finding.get('message_type', 'unknown')
            display_type = "Agent" if msg_type == "assistant" else msg_type.capitalize()
            st.write(f"{idx}. **{display_type}**: {pii_list}")


def render_test_results_new():
    """Render test results with compact count-based UI"""
    if not st.session_state.test_results:
        st.info("No test results yet. Load a scenario and run tests.")
        return

    latest_result = st.session_state.test_results[-1]
    messages = st.session_state.current_conversation.get("messages", [])

    # Clear results summary
    _render_results_summary(latest_result)

    st.divider()

    # Scanner results detail — ordered: Prompt Guard, Alignment Checker, Facts Checker, Data Guard
    st.markdown("### Scanner Details")

    if latest_result.get("prompt_guard"):
        render_scanner_counts("PromptGuard", latest_result["prompt_guard"], messages)
        st.divider()

    if latest_result.get("alignment_check"):
        render_scanner_counts("AlignmentCheck", latest_result["alignment_check"], messages)
        st.divider()

    # NeMo scanners in order: FactsChecker then DataDisclosureGuard
    nemo = latest_result.get("nemo_results", {})
    for key in ["FactsChecker", "DataDisclosureGuard"]:
        if key in nemo:
            render_scanner_counts(key, nemo[key], messages)
            st.divider()
    # Any remaining nemo scanners
    for key, scanner_result in nemo.items():
        if key not in ["FactsChecker", "DataDisclosureGuard"]:
            render_scanner_counts(key, scanner_result, messages)
            st.divider()

    # Test History
    if len(st.session_state.test_results) > 1:
        with st.expander(f"Test History ({len(st.session_state.test_results)} runs)"):
            history_data = []
            for i, test in enumerate(reversed(st.session_state.test_results[-10:]), 1):
                all_decisions = []
                if test.get("alignment_check") and "overall_decision" in test["alignment_check"]:
                    all_decisions.append(test["alignment_check"]["overall_decision"])
                if test.get("prompt_guard") and "overall_decision" in test["prompt_guard"]:
                    all_decisions.append(test["prompt_guard"]["overall_decision"])
                for scanner_result in test.get("nemo_results", {}).values():
                    if "overall_decision" in scanner_result:
                        all_decisions.append(scanner_result["overall_decision"])

                if "BLOCK" in all_decisions:
                    overall = "BLOCK"
                elif "WARNING" in all_decisions:
                    overall = "WARNING"
                else:
                    overall = "SAFE"

                history_data.append({
                    "#": len(st.session_state.test_results) - i + 1,
                    "Result": overall,
                    "Msgs": test.get("conversation_length", 0),
                    "Time": test.get("timestamp", "")[:19]
                })

            if history_data:
                df = pd.DataFrame(history_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
