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
import time
import warnings
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_agent_demo.core import run_scanners_on_session, aggregate_results
from multi_agent_demo.reports import generate_markdown_report


# ANSI color codes for terminal output (disabled when stdout is not a terminal)
class Colors:
    RESET = '\033[0m' if sys.stdout.isatty() else ''
    GREEN = '\033[92m' if sys.stdout.isatty() else ''
    YELLOW = '\033[93m' if sys.stdout.isatty() else ''
    RED = '\033[91m' if sys.stdout.isatty() else ''
    BLUE = '\033[94m' if sys.stdout.isatty() else ''
    CYAN = '\033[96m' if sys.stdout.isatty() else ''
    BOLD = '\033[1m' if sys.stdout.isatty() else ''


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


def print_progress(current: int, total: int, session_name: str, decision: str, elapsed_time: float = None):
    """Print progress bar and current status"""
    percentage = int((current / total) * 100)
    bar_length = 40
    filled = int((current / total) * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)

    # Decision icon
    icon = "🟢" if decision == "SAFE" else "🟡" if decision == "WARNING" else "🔴"

    # Format timing if provided
    timing_str = ""
    if elapsed_time is not None:
        timing_str = f" ({elapsed_time:.2f}s)"

    print(f"\r[{bar}] {percentage}% | {current}/{total} | {icon} {session_name[:40]:<40}{timing_str}", end='', flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Batch scan session files with AI Agent Guards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan all JSON files in directory with all scanners
  python -m multi_agent_demo.cli -d ./sessions

  # Scan single session file
  python -m multi_agent_demo.cli -f ./sessions/environment_prod_1234.json

  # Scan with specific scanners
  python -m multi_agent_demo.cli -d ./sessions -s AlignmentCheck FactsChecker

  # Scan single file with specific scanner
  python -m multi_agent_demo.cli -f ./session.json -s AlignmentCheck

  # Include safe session details in report
  python -m multi_agent_demo.cli -d ./sessions --show-safe

Available Scanners:
  - PromptGuard: Detects malicious prompts and injections
  - AlignmentCheck: Detects goal hijacking and behavioral drift
  - FactsChecker: Detects contradictions and ungrounded claims
  - DataDisclosureGuard: Detects PII disclosure issues
        """
    )

    # Create mutually exclusive group for directory vs file
    input_group = parser.add_mutually_exclusive_group(required=True)

    input_group.add_argument(
        "-d", "--directory",
        help="Directory containing session JSON files"
    )

    input_group.add_argument(
        "-f", "--file",
        help="Single session JSON file to scan"
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

    # Find session files (directory or single file)
    if args.directory:
        print_colored(f"📂 Scanning directory: {args.directory}", Colors.BLUE)
        session_files = find_session_files(args.directory)

        if not session_files:
            print_colored(f"❌ No JSON files found in {args.directory}", Colors.RED)
            sys.exit(1)

        print_colored(f"✅ Found {len(session_files)} session file(s)", Colors.GREEN)
    else:
        # Single file mode
        print_colored(f"📄 Scanning single file: {args.file}", Colors.BLUE)

        file_path = Path(args.file)
        if not file_path.exists():
            print_colored(f"❌ File not found: {args.file}", Colors.RED)
            sys.exit(1)

        if not file_path.is_file():
            print_colored(f"❌ Not a file: {args.file}", Colors.RED)
            sys.exit(1)

        if not str(file_path).endswith('.json'):
            print_colored(f"⚠️  Warning: File does not have .json extension", Colors.YELLOW)

        session_files = [str(file_path)]
        print_colored(f"✅ File loaded successfully", Colors.GREEN)

    print()

    # Print enabled scanners
    print_colored(f"🔍 Enabled scanners: {', '.join(args.scanners)}", Colors.BLUE)
    print()

    # Process each session
    print_colored("⚙️  Processing sessions...", Colors.BLUE)
    print()

    # Track timing
    start_time = time.time()
    all_results = []
    valid_sessions = []
    session_data_list = []  # Store session data for report generation
    session_timings = []

    for i, session_file in enumerate(session_files, 1):
        session_name = Path(session_file).name

        # Load session
        session_data = load_session_file(session_file)
        if not session_data:
            print_progress(i, len(session_files), session_name, "ERROR")
            continue

        # Run scanners with timing
        session_start = time.time()
        try:
            result = run_scanners_on_session(
                session_data=session_data,
                enabled_scanners=args.scanners
            )
            session_elapsed = time.time() - session_start
            session_timings.append({"session": session_name, "elapsed": session_elapsed})

            all_results.append(result)
            valid_sessions.append(session_file)
            session_data_list.append(session_data)  # Store session data for report

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

            print_progress(i, len(session_files), session_name, decision, session_elapsed)

        except Exception as e:
            session_elapsed = time.time() - session_start
            session_timings.append({"session": session_name, "elapsed": session_elapsed, "error": True})
            print_colored(f"\n⚠️ Error processing {session_name}: {e}", Colors.YELLOW)
            print_progress(i, len(session_files), session_name, "ERROR", session_elapsed)
            continue

    # Calculate total elapsed time
    total_elapsed = time.time() - start_time

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
        session_data_list=session_data_list,
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
        # Print to console (markdown only, no color codes)
        print()
        print("=" * 80)
        print("📄 MARKDOWN REPORT (copy and paste)")
        print("=" * 80)
        print()
        print(report)  # Just the markdown, no color codes

    # Check for scanner errors
    scanner_errors = {}
    for result in all_results:
        if result.get("alignment_check") and "error" in result["alignment_check"]:
            scanner_errors["AlignmentCheck"] = result["alignment_check"]["error"]
        if result.get("prompt_guard") and "error" in result["prompt_guard"]:
            scanner_errors["PromptGuard"] = result["prompt_guard"]["error"]
        for scanner_name, scanner_result in result.get("nemo_results", {}).items():
            if "error" in scanner_result:
                scanner_errors[scanner_name] = scanner_result["error"]

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

    # Print timing information
    print_colored("⏱️  TIMING", Colors.BLUE)
    print()
    print_colored(f"Total Elapsed: {total_elapsed:.2f}s", Colors.BLUE)
    if session_timings:
        avg_time = sum(t["elapsed"] for t in session_timings) / len(session_timings)
        min_time = min(t["elapsed"] for t in session_timings)
        max_time = max(t["elapsed"] for t in session_timings)
        print_colored(f"Average per Session: {avg_time:.2f}s", Colors.BLUE)
        print_colored(f"Fastest Session: {min_time:.2f}s", Colors.GREEN)
        print_colored(f"Slowest Session: {max_time:.2f}s", Colors.YELLOW)
    print()

    # Show scanner errors if any
    if scanner_errors:
        print_colored("⚠️  SCANNER ERRORS", Colors.YELLOW)
        print()
        for scanner_name, error in scanner_errors.items():
            print_colored(f"  • {scanner_name}: {error}", Colors.YELLOW)
        print()

    print_colored("=" * 80, Colors.CYAN)

    # Cleanup: Close any pending async tasks to avoid "Event loop is closed" errors
    # This happens because some libraries (httpx, openai) create async clients that
    # need cleanup, but we're running in a synchronous context
    try:
        # Get the current event loop if it exists
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            # Cancel all pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            # Give tasks a chance to complete cancellation
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except RuntimeError:
        # No event loop or already closed - that's fine
        pass


if __name__ == "__main__":
    # Suppress asyncio warnings about unclosed resources
    # These occur when async libraries (httpx, openai SDK) create async clients
    # but we're running in a synchronous CLI context
    warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*coroutine.*was never awaited")
    warnings.filterwarnings("ignore", message=".*Event loop is closed.*")

    # Also suppress asyncio errors logged to stderr
    import logging
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)

    try:
        main()
    finally:
        # Final cleanup: ensure all async resources are properly closed
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.close()
        except RuntimeError:
            pass
