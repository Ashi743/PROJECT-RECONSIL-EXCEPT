"""
Test runner for Exception Triage Agent - tests all 12 exception scenarios.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from exception_triage_agent import ExceptionTriageAgent
from database import Database
from guardrails import Guardrails
from dotenv import load_dotenv


def load_test_scenario(filename: str) -> dict:
    """Load a test scenario from JSON file."""
    test_data_dir = Path(__file__).parent / "test_data"
    filepath = test_data_dir / filename

    with open(filepath, 'r') as f:
        return json.load(f)


def run_test_scenario(agent: ExceptionTriageAgent, scenario: dict) -> dict:
    """Run a single test scenario and return results."""

    exception_message = scenario["exception_message"]
    context = scenario.get("context")

    result = agent.detect_and_route(exception_message, context)

    expected = scenario.get("expected_output", {})

    # Check if result matches expected output
    passed = True
    issues = []

    if "exception_type" in expected:
        if result.get("exception_type") != expected["exception_type"]:
            passed = False
            issues.append(f"Exception type mismatch: expected {expected['exception_type']}, got {result.get('exception_type')}")

    if "urgency" in expected:
        if result.get("urgency") != expected["urgency"]:
            passed = False
            issues.append(f"Urgency mismatch: expected {expected['urgency']}, got {result.get('urgency')}")

    if "handler" in expected:
        if result.get("handler") != expected["handler"]:
            passed = False
            issues.append(f"Handler mismatch: expected {expected['handler']}, got {result.get('handler')}")

    if "classification_confidence" in expected:
        if abs(result.get("classification_confidence", 0) - expected["classification_confidence"]) > 5:
            passed = False
            issues.append(f"Confidence mismatch: expected ~{expected['classification_confidence']}, got {result.get('classification_confidence')}")

    return {
        "scenario_id": scenario["scenario_id"],
        "description": scenario["description"],
        "passed": passed,
        "issues": issues,
        "result": result,
        "expected": expected
    }


def main():
    """Run all exception triage test scenarios."""

    print("\n" + "="*80)
    print("🧪 EXCEPTION TRIAGE AGENT - TEST RUNNER")
    print("="*80 + "\n")

    # Initialize
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file")
        return

    db = Database()
    guardrails = Guardrails(db)
    agent = ExceptionTriageAgent(api_key, db, guardrails)

    # Load all test scenarios
    test_files = [
        "exception_01_shipment_delay.json",
        "exception_02_missing_document.json",
        "exception_03_lc_discrepancy.json",
        "exception_04_dd_risk.json",
        "exception_05_critical_delay.json",
        "exception_06_time_bar_approaching.json",
        "exception_07_multiple_issues.json",
        "exception_08_resolved_exception.json",
        "exception_09_false_alarm.json",
        "exception_10_urgent_escalation.json",
        "exception_11_routine_delay.json",
        "exception_12_edge_case.json",
    ]

    results = []
    passed_count = 0

    # Run each scenario
    for test_file in test_files:
        try:
            print(f"Running {test_file}...", end=" ")

            scenario = load_test_scenario(test_file)
            result = run_test_scenario(agent, scenario)

            results.append(result)

            if result["passed"]:
                passed_count += 1
                print("✅ PASS")
            else:
                print("❌ FAIL")
                for issue in result["issues"]:
                    print(f"  - {issue}")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                "scenario_id": test_file,
                "passed": False,
                "error": str(e)
            })

    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)

    total_tests = len(test_files)
    failed_count = total_tests - passed_count
    pass_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0

    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_count} ✅")
    print(f"Failed: {failed_count} ❌")
    print(f"Pass Rate: {pass_rate:.1f}%")

    # Detailed results by category
    print("\n" + "-"*80)
    print("RESULTS BY EXCEPTION TYPE")
    print("-"*80)

    exception_types = {}
    for result in results:
        exc_type = result.get("result", {}).get("exception_type", "UNKNOWN")
        if exc_type not in exception_types:
            exception_types[exc_type] = {"passed": 0, "total": 0}
        exception_types[exc_type]["total"] += 1
        if result["passed"]:
            exception_types[exc_type]["passed"] += 1

    for exc_type, counts in exception_types.items():
        print(f"{exc_type}: {counts['passed']}/{counts['total']} passed")

    # Export results to JSON
    output_file = "exception_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_count,
                "failed": failed_count,
                "pass_rate": pass_rate
            },
            "results": results
        }, f, indent=2)

    print(f"\n📁 Results exported to {output_file}")
    print("\n" + "="*80)

    return 0 if pass_rate == 100.0 else 1


if __name__ == "__main__":
    sys.exit(main())
