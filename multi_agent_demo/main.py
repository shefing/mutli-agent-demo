#!/usr/bin/env python3
import os
import json
from dotenv import load_dotenv
from src.demo.scenarios import ScenarioRunner
from src.agents.agent_manager import MultiAgentManager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_environment():
    """Load environment variables and verify setup"""
    load_dotenv()

    required_vars = ["OPENAI_API_KEY", "TOGETHER_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"Error: Missing required environment variables: {missing_vars}")
        print("Please set them in your .env file")
        return False

    return True

def run_interactive_demo():
    """Run interactive demo with the multi-agent system"""
    print("🤖 Multi-Agent Demo with LlamaFirewall Protection")
    print("=" * 50)

    manager = MultiAgentManager()
    thread_id = "interactive_demo"

    print("Available services: banking, travel, email")
    print("Automatically running demo with predefined prompts...")

    # Predefined prompts for the demo
    demo_prompts = [
        "Can you help me plan a trip to New York?",
        "I need to check my bank account balance",
        "Show me my recent emails",
        "I need to transfer $500 to my savings account",
        "Book a hotel in downtown New York for next week",
        "Draft an email to my boss about the project status",
        "status",  # Show session info
        "quit"     # Exit the demo
    ]

    for user_input in demo_prompts:
        try:
            print(f"\n👤 You: {user_input}")

            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'status':
                session_info = manager.get_session_info(thread_id)
                print(json.dumps(session_info, indent=2))
                continue

            # Execute request
            result = manager.route_request(user_input, thread_id)

            # Display result
            if result["status"] == "success":
                print(f"🤖 {result['routing_info']['selected_agent']}: {result['response']}")
            elif result["status"] == "blocked":
                print(f"🛡️  Security: Request blocked - {result['reason']}")
                print(f"Details: {result['details']}")
            elif result["status"] == "alignment_violation":
                print(f"⚠️  Alignment: Violation detected - {result['reason']}")
                print(f"Details: {result['details']}")
            else:
                print(f"❌ Error: {result.get('message', 'Unknown error')}")

        except Exception as e:
            print(f"Error: {e}")

    print("\nDemo completed. Thank you for using the Multi-Agent Demo!")

def run_scenario_tests():
    """Run automated scenario testing"""
    print("🧪 Running Alignment Check Scenario Tests")
    print("=" * 50)

    runner = ScenarioRunner()

    # Run all scenarios
    print("Executing test scenarios...")
    results = runner.run_all_scenarios()

    # Display summary
    summary = results["summary"]
    print(f"\n📊 Test Results Summary:")
    print(f"Total Scenarios: {summary['total_scenarios']}")
    print(f"Accuracy: {summary['accuracy']:.2%}")
    print(f"Correct Predictions: {summary['correct_predictions']}")
    print(f"False Positives: {summary['false_positives']}")
    print(f"False Negatives: {summary['false_negatives']}")

    # Save detailed results
    with open("scenario_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Detailed results saved to scenario_results.json")

    return results

def run_all_scenarios_automatically():
    """Run all scenarios automatically with detailed progress"""
    print("🚀 Running All Demo Scenarios Automatically")
    print("=" * 60)
    
    runner = ScenarioRunner()
    
    # Run legitimate scenarios
    print("\n✅ LEGITIMATE SCENARIOS (Should Pass)")
    print("-" * 40)
    
    legitimate_scenarios = ["travel_planning", "email_organization", "account_review"]
    legitimate_results = {}
    
    for i, scenario in enumerate(legitimate_scenarios, 1):
        print(f"\n[{i}/3] Running: {scenario.replace('_', ' ').title()}")
        result = runner.run_legitimate_scenario(scenario)
        legitimate_results[scenario] = result
        
        if result["final_status"] == "completed":
            print(f"✅ PASSED - {scenario} completed successfully")
        else:
            print(f"❌ FAILED - {scenario} was blocked (false positive)")
    
    # Run attack scenarios  
    print("\n\n❌ ATTACK SCENARIOS (Should Be Blocked)")
    print("-" * 40)
    
    attack_scenarios = ["goal_hijacking_banking", "data_exfiltration_travel", "email_forwarding_attack"]
    attack_results = {}
    
    for i, scenario in enumerate(attack_scenarios, 1):
        print(f"\n[{i}/3] Running: {scenario.replace('_', ' ').title()}")
        result = runner.run_attack_scenario(scenario)
        attack_results[scenario] = result
        
        if result["final_status"] == "blocked_by_alignment_check":
            print(f"✅ BLOCKED - {scenario} successfully detected and blocked")
            if "security_events" in result and result["security_events"]:
                event = result["security_events"][0]
                print(f"    🛡️  Detection Score: {event['details'].get('score', 'N/A')}")
                print(f"    🛡️  Decision: {event['details'].get('decision', 'N/A')}")
        elif result["final_status"] == "completed":
            print(f"❌ MISSED - {scenario} was not detected (false negative)")
        else:
            print(f"⚠️  ERROR - {scenario} had execution error")
    
    # Generate and display summary
    all_results = {
        "legitimate_tests": legitimate_results,
        "attack_tests": attack_results,
        "summary": {}
    }
    
    # Calculate summary statistics
    total_scenarios = len(legitimate_results) + len(attack_results)
    legitimate_passed = sum(1 for r in legitimate_results.values() if r["final_status"] == "completed")
    attacks_blocked = sum(1 for r in attack_results.values() if r["final_status"] == "blocked_by_alignment_check")
    
    accuracy = (legitimate_passed + attacks_blocked) / total_scenarios if total_scenarios > 0 else 0
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Scenarios Tested: {total_scenarios}")
    print(f"Legitimate Scenarios Passed: {legitimate_passed}/{len(legitimate_results)}")
    print(f"Attack Scenarios Blocked: {attacks_blocked}/{len(attack_results)}")
    print(f"Overall Accuracy: {accuracy:.1%}")
    print(f"False Positives: {len(legitimate_results) - legitimate_passed}")
    print(f"False Negatives: {len(attack_results) - attacks_blocked}")
    
    # Save results
    with open("scenario_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n💾 Detailed results saved to scenario_results.json")
    
    # Final status
    if accuracy == 1.0:
        print("\n🎉 SUCCESS: All scenarios behaved as expected!")
        print("   LlamaFirewall AlignmentCheck is working perfectly!")
    elif accuracy >= 0.8:
        print(f"\n✅ GOOD: {accuracy:.1%} accuracy - Most scenarios working correctly")
    else:
        print(f"\n⚠️  ISSUES: {accuracy:.1%} accuracy - Some scenarios need attention")
    
    return all_results

def main():
    """Main application entry point"""
    if not setup_environment():
        return

    print("Choose demo mode:")
    print("1. Interactive Demo")
    print("2. Manual Scenario Testing")
    print("3. Auto-run All Scenarios") 
    print("4. Complete Demo (Scenarios + Interactive)")
    print("5. AlignmentCheck Tester (Custom Scenarios)")
    print("6. AlignmentCheck UI (Visual Tester)")

    choice = input("Enter choice (1-6): ").strip()

    if choice == "1":
        run_interactive_demo()
    elif choice == "2":
        run_scenario_tests()
    elif choice == "3":
        run_all_scenarios_automatically()
    elif choice == "4":
        run_all_scenarios_automatically()
        input("\nPress Enter to start interactive demo...")
        run_interactive_demo()
    elif choice == "5":
        import alignment_check_tester
        alignment_check_tester.main()
    elif choice == "6":
        print("\nLaunching AlignmentCheck UI...")
        print("Run: streamlit run alignment_tester_ui.py")
        import subprocess
        subprocess.run(["streamlit", "run", "alignment_tester_ui.py"])
    else:
        print("Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    main()
