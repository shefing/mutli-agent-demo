#!/usr/bin/env python3
"""
CLI for batch processing session files with AI Agent Guards
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_agent_demo.core import run_scanners_on_session, aggregate_results
from multi_agent_demo.reports import generate_markdown_report


# ANSI color codes for terminal output
class Colors:
    RESET = '\033[0m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'


def print_colored(text: str, color: str = Colors.RESET):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.RESET}")


def find_session_files(directory: str) -> List[str]:
    """Find all JSON files in directory"""
    json_files = []
    path = Path(directory)

    if not path.exists():
        print_colored(f"❌ Directory not found: {directory}", Colors.RED)
        sys.exit(1)

    if not path.is_dir():
        print_colored(f"❌ Not a directory: {directory}", Colors.RED)
        sys.exit(1)

    for file in path.glob("**/*.json"):
        json_files.append(str(file))

    return sorted(json_files)


def load_session_file(file_path: str) -> dict:
    """Load session JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print_colored(f"⚠️ Error loading {file_path}: {e}", Colors.YELLOW)
        return None


def print_progress(current: int, total: int, session_name: str, decision: str):
    """Print progress bar and current status"""
    percentage = int((current / total) * 100)
    bar_length = 40
    filled = int((current / total) * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)

    # Decision icon
    icon = "🟢" if decision == "SAFE" else "🟡" if decision == "WARNING" else "🔴"

    print(f"\r[{bar}] {percentage}% | {current}/{total} | {icon} {session_name[:40]:<40}", end='', flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Batch scan session files with AI Agent Guards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan all JSON files in directory with all scanners
  python -m multi_agent_demo.cli -d ./sessions

  # Scan with specific scanners
  python -m multi_agent_demo.cli -d ./sessions -s AlignmentCheck FactsChecker

  # Include safe session details in report
  python -m multi_agent_demo.cli -d ./sessions --show-safe

Available Scanners:
  - PromptGuard: Detects malicious prompts and injections
  - AlignmentCheck: Detects goal hijacking and behavioral drift
  - FactsChecker: Detects contradictions and ungrounded claims
  - DataDisclosureGuard: Detects PII disclosure issues
        """
    )

    parser.add_argument(
        "-d", "--directory",
        required=True,
        help="Directory containing session JSON files"
    )

    parser.add_argument(
        "-s", "--scanners",
        nargs="+",
        choices=["PromptGuard", "AlignmentCheck", "FactsChecker", "DataDisclosureGuard"],
        default=["PromptGuard", "AlignmentCheck", "FactsChecker", "DataDisclosureGuard"],
        help="Scanners to run (default: all)"
    )

    parser.add_argument(
        "--show-safe",
        action="store_true",
        help="Show details for safe sessions in report (default: only show sessions with issues)"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output markdown report to file (default: print to console)"
    )

    args = parser.parse_args()

    # Print banner
    print_colored("=" * 80, Colors.CYAN)
    print_colored("🛡️  AI AGENT GUARDS - BATCH SCANNER", Colors.BOLD + Colors.CYAN)
    print_colored("=" * 80, Colors.CYAN)
    print()

    # Find session files
    print_colored(f"📂 Scanning directory: {args.directory}", Colors.BLUE)
    session_files = find_session_files(args.directory)

    if not session_files:
        print_colored(f"❌ No JSON files found in {args.directory}", Colors.RED)
        sys.exit(1)

    print_colored(f"✅ Found {len(session_files)} session file(s)", Colors.GREEN)
    print()

    # Print enabled scanners
    print_colored(f"🔍 Enabled scanners: {', '.join(args.scanners)}", Colors.BLUE)
    print()

    # Process each session
    print_colored("⚙️  Processing sessions...", Colors.BLUE)
    print()

    all_results = []
    valid_sessions = []

    for i, session_file in enumerate(session_files, 1):
        session_name = Path(session_file).name

        # Load session
        session_data = load_session_file(session_file)
        if not session_data:
            print_progress(i, len(session_files), session_name, "ERROR")
            continue

        # Run scanners
        try:
            result = run_scanners_on_session(
                session_data=session_data,
                enabled_scanners=args.scanners
            )
            all_results.append(result)
            valid_sessions.append(session_file)

            # Determine overall decision for progress display
            all_decisions = []
            if result.get("alignment_check") and "overall_decision" in result["alignment_check"]:
                all_decisions.append(result["alignment_check"]["overall_decision"])
            if result.get("prompt_guard") and "overall_decision" in result["prompt_guard"]:
                all_decisions.append(result["prompt_guard"]["overall_decision"])
            for scanner_result in result.get("nemo_results", {}).values():
                if "overall_decision" in scanner_result:
                    all_decisions.append(scanner_result["overall_decision"])

            if "BLOCK" in all_decisions:
                decision = "BLOCK"
            elif "WARNING" in all_decisions:
                decision = "WARNING"
            else:
                decision = "SAFE"

            print_progress(i, len(session_files), session_name, decision)

        except Exception as e:
            print_colored(f"\n⚠️ Error processing {session_name}: {e}", Colors.YELLOW)
            print_progress(i, len(session_files), session_name, "ERROR")
            continue

    print()  # New line after progress bar
    print()

    # Check if any sessions were processed
    if not all_results:
        print_colored("❌ No sessions were successfully processed", Colors.RED)
        sys.exit(1)

    print_colored("✅ Processing complete!", Colors.GREEN)
    print()

    # Aggregate results
    print_colored("📊 Aggregating results...", Colors.BLUE)
    aggregated = aggregate_results(all_results)
    print()

    # Generate markdown report
    print_colored("📝 Generating report...", Colors.BLUE)
    report = generate_markdown_report(
        all_results=all_results,
        session_files=valid_sessions,
        aggregated=aggregated,
        show_safe_details=args.show_safe
    )
    print()

    # Output report
    if args.output:
        # Write to file
        with open(args.output, 'w') as f:
            f.write(report)
        print_colored(f"✅ Report saved to: {args.output}", Colors.GREEN)
    else:
        # Print to console
        print_colored("=" * 80, Colors.CYAN)
        print_colored("📄 MARKDOWN REPORT (copy and paste)", Colors.BOLD + Colors.CYAN)
        print_colored("=" * 80, Colors.CYAN)
        print()
        print(report)

    # Print summary
    print()
    print_colored("=" * 80, Colors.CYAN)
    print_colored("📊 SUMMARY", Colors.BOLD + Colors.CYAN)
    print_colored("=" * 80, Colors.CYAN)
    print()
    print_colored(f"Total Sessions: {aggregated['total_sessions']}", Colors.BLUE)
    print_colored(f"Safe Sessions: {aggregated['safe_sessions']} ✅", Colors.GREEN)
    print_colored(f"Sessions with Issues: {aggregated['unsafe_sessions']} 🚨", Colors.RED if aggregated['unsafe_sessions'] > 0 else Colors.GREEN)
    print()
    print_colored(f"Total Blocks: {aggregated['total_blocks']} 🚫", Colors.RED if aggregated['total_blocks'] > 0 else Colors.GREEN)
    print_colored(f"Total Warnings: {aggregated['total_warnings']} ⚠️", Colors.YELLOW if aggregated['total_warnings'] > 0 else Colors.GREEN)
    print_colored(f"Total Safe: {aggregated['total_safe']} ✅", Colors.GREEN)
    print()
    print_colored("=" * 80, Colors.CYAN)


if __name__ == "__main__":
    main()
