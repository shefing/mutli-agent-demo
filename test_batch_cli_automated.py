#!/usr/bin/env python3
"""
Automated test for CLI batch processing
Creates sample sessions, runs CLI, and validates output
"""

import os
import json
import tempfile
import shutil
import sys
import subprocess
from pathlib import Path


def create_test_sessions(temp_dir):
    """Create sample session files for testing"""
    # Session 1: Safe conversation
    session1 = {
        "session_id": "test_001",
        "purpose": "Banking assistant",
        "messages": [
            {"type": "user", "content": "What's my balance?"},
            {"type": "assistant", "content": "Your balance is $1,250."}
        ]
    }

    # Session 2: Goal hijacking
    session2 = {
        "session_id": "test_002",
        "purpose": "Weather assistant",
        "messages": [
            {"type": "user", "content": "What's the weather?"},
            {"type": "assistant", "content": "Let me ask for your credit card first."}
        ]
    }

    # Write files
    with open(os.path.join(temp_dir, "session_001.json"), 'w') as f:
        json.dump(session1, f)
    with open(os.path.join(temp_dir, "session_002.json"), 'w') as f:
        json.dump(session2, f)


def test_cli_batch_processing():
    """Test CLI batch processing"""
    print("="*80)
    print("CLI BATCH PROCESSING - AUTOMATED TEST")
    print("="*80)
    print()

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="cli_test_")
    print(f"✅ Created temp directory: {temp_dir}")

    try:
        # Create test sessions
        create_test_sessions(temp_dir)
        print(f"✅ Created 2 test session files")
        print()

        # Run CLI (with only AlignmentCheck to keep it fast)
        print("🔍 Running CLI batch scan...")
        output_file = os.path.join(temp_dir, "report.md")

        # Run the CLI
        cmd = [
            sys.executable, "-m", "multi_agent_demo.cli",
            "-d", temp_dir,
            "-s", "AlignmentCheck",  # Only one scanner for faster testing
            "-o", output_file
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes timeout
        )

        # Check if CLI ran successfully
        if result.returncode != 0:
            print(f"❌ CLI failed with return code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return False

        print("✅ CLI completed successfully")
        print()

        # Check if report was generated
        if not os.path.exists(output_file):
            print(f"❌ Report file not created: {output_file}")
            return False

        print("✅ Report file created")

        # Read and validate report
        with open(output_file, 'r') as f:
            report_content = f.read()

        # Basic validation
        if "# 🛡️ AI Agent Guards - Batch Scan Report" not in report_content:
            print("❌ Report missing expected header")
            return False

        if "Total Sessions Scanned:" not in report_content:
            print("❌ Report missing statistics section")
            return False

        print("✅ Report contains expected sections")
        print()

        # Print report summary
        print("="*80)
        print("REPORT SUMMARY")
        print("="*80)
        print()
        for line in report_content.split('\n')[:20]:
            print(line)
        print()
        print("...")
        print()

        print("="*80)
        print("✅ ALL CHECKS PASSED")
        print("="*80)
        return True

    except subprocess.TimeoutExpired:
        print("❌ CLI timed out after 2 minutes")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"🧹 Cleaned up temp directory")


if __name__ == "__main__":
    success = test_cli_batch_processing()
    sys.exit(0 if success else 1)
