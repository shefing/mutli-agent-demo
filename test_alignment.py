#!/usr/bin/env python3
"""
Simple launcher for AlignmentCheck testing tools
This doesn't require LangChain dependencies
"""

import sys
import os
import subprocess

def main():
    print("🛡️  AlignmentCheck Testing Tools")
    print("=" * 50)
    print("1. CLI Tester (Interactive)")
    print("2. Standalone Tester (No LangChain needed)")
    print("3. Visual UI (Streamlit)")
    print("4. Exit")
    
    choice = input("\nChoice (1-4): ").strip()
    
    if choice == "1":
        # Try the full-featured tester first
        tester_path = "multi_agent_demo/alignment_check_tester.py"
        if os.path.exists(tester_path):
            try:
                subprocess.run([sys.executable, tester_path])
            except Exception as e:
                print(f"Error running CLI tester: {e}")
                print("Try the standalone version (option 2) instead")
        else:
            print(f"CLI tester not found at {tester_path}")
            
    elif choice == "2":
        # Run the standalone version
        standalone_path = "multi_agent_demo/alignment_check_standalone.py"
        if os.path.exists(standalone_path):
            subprocess.run([sys.executable, standalone_path])
        else:
            print(f"Standalone tester not found at {standalone_path}")
            
    elif choice == "3":
        # Run the Streamlit UI
        ui_path = "multi_agent_demo/alignment_tester_ui.py"
        if os.path.exists(ui_path):
            print(f"Launching Streamlit UI...")
            print(f"If browser doesn't open, visit: http://localhost:8501")
            subprocess.run(["streamlit", "run", ui_path])
        else:
            print(f"UI tester not found at {ui_path}")
            
    elif choice == "4":
        print("Goodbye!")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()