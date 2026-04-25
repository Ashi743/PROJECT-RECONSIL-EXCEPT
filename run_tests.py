#!/usr/bin/env python3
"""
Comprehensive test runner for Reconciliation + LC Doc agents.
Tests all 15 reconciliation scenarios and 5 LC scenarios.
"""

import sys
import json
from datetime import datetime
from reconciliation_agent import ReconciliationAgent, MOCK_SCENARIOS
from doc_agent import LCDocAgent
from database import Database
from guardrails import Guardrails
import os
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

TEST_SCENARIOS = {
    "scenario_01_perfect_match": {
        "description": "All three documents match perfectly",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected": {
            "status": "AUTO_APPROVE",
            "confidence_min": 95,
            "fraud_score_max": 10,
            "anomalies_max": 0
        }
    },
    "scenario_02_minor_qty_variance": {
        "description": "Qty variance 0.5-2% (acceptable)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 101, "price_usd": 500, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100.5, "date": "2024-04-10"},
        "expected": {
            "status": "ROUTE_TO_SPECIALIST",
            "confidence_min": 80,
            "confidence_max": 95,
            "fraud_score_max": 20,
            "anomalies_max": 1
        }
    },
    "scenario_03_minor_price_variance": {
        "description": "Price variance 0.5-1% (acceptable)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100, "price_usd": 504, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected": {
            "status": "ROUTE_TO_SPECIALIST",
            "confidence_min": 80,
            "confidence_max": 95
        }
    },
    "scenario_04_combined_minor": {
        "description": "Both qty and price have minor variance",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 101, "price_usd": 504, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100.5, "date": "2024-04-10"},
        "expected": {
            "status": "ROUTE_TO_SPECIALIST",
            "confidence_min": 70,
            "confidence_max": 90,
            "fraud_score_max": 25
        }
    },
    "scenario_05_major_qty_variance": {
        "description": "Qty variance 2-5% (major)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 105, "price_usd": 500, "date": "2024-04-15"},
        "receipt": {"qty_mt": 103, "date": "2024-04-10"},
        "expected": {
            "status": "ESCALATE_TO_MANAGER",
            "confidence_max": 80,
            "fraud_score_min": 20,
            "anomalies_min": 1
        }
    },
    "scenario_06_major_price_variance": {
        "description": "Price variance > 2% (major)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100, "price_usd": 512, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected": {
            "status": "ESCALATE_TO_MANAGER",
            "confidence_max": 80,
            "fraud_score_min": 15
        }
    },
    "scenario_07_qty_mismatch_contract_invoice": {
        "description": "Contract qty ≠ Invoice qty (order changed)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 120, "price_usd": 500, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected": {
            "status": "ESCALATE_TO_MANAGER",
            "confidence_max": 80,
            "fraud_score_min": 30,
            "anomalies_min": 2
        }
    },
    "scenario_08_qty_mismatch_invoice_receipt": {
        "description": "Invoice qty ≠ Receipt qty (seller added extra)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 110, "price_usd": 500, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected": {
            "status": "ESCALATE_TO_MANAGER",
            "confidence_max": 70,
            "fraud_score_min": 40,
            "anomalies_min": 2
        }
    },
    "scenario_09_fraud_extra_qty_low_price": {
        "description": "FRAUD: Extra qty + lower price",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 115, "price_usd": 450, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected": {
            "status": "ESCALATE_TO_DIRECTOR",
            "confidence_max": 50,
            "fraud_score_min": 70
        }
    },
    "scenario_10_fraud_impossible_timeline": {
        "description": "FRAUD: Invoice before receipt (impossible)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-05"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected": {
            "status": "ESCALATE_TO_DIRECTOR",
            "confidence_max": 30,
            "fraud_score_min": 85
        }
    },
    "scenario_11_timeline_gap": {
        "description": "Receipt > 10 days after invoice (unusual delay)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-05"},
        "receipt": {"qty_mt": 100, "date": "2024-04-20"},
        "expected": {
            "status": "ROUTE_TO_SPECIALIST",
            "confidence_min": 60,
            "confidence_max": 85,
            "fraud_score_min": 20,
            "anomalies_min": 1
        }
    },
    "scenario_12_late_invoice": {
        "description": "Invoice submitted 25 days after receipt",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100, "price_usd": 500, "date": "2024-05-05"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected": {
            "status": "ROUTE_TO_SPECIALIST",
            "confidence_min": 55,
            "confidence_max": 80,
            "fraud_score_min": 25,
            "anomalies_min": 1
        }
    },
    "scenario_13_multiple_anomalies": {
        "description": "3+ anomalies together (very suspicious)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 115, "price_usd": 480, "date": "2024-03-28"},
        "receipt": {"qty_mt": 95, "date": "2024-04-10"},
        "expected": {
            "status": "ESCALATE_TO_DIRECTOR",
            "confidence_max": 50,
            "fraud_score_min": 70,
            "anomalies_min": 4
        }
    },
    "scenario_14_edge_case_boundary": {
        "description": "Variance exactly at 0.5% boundary",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100.5, "price_usd": 500, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"},
        "expected": {
            "status": "AUTO_APPROVE",
            "confidence_min": 95,
            "fraud_score_max": 10
        }
    },
    "scenario_15_extreme_variance": {
        "description": "Extreme variance > 10% (almost certainly fraud)",
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 150, "price_usd": 400, "date": "2024-04-15"},
        "receipt": {"qty_mt": 80, "date": "2024-04-10"},
        "expected": {
            "status": "ESCALATE_TO_DIRECTOR",
            "confidence_max": 30,
            "fraud_score_min": 85,
            "anomalies_min": 3
        }
    }
}


def run_reconciliation_tests():
    """Run all 15 reconciliation test scenarios."""
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not found in .env")
        return

    db = Database()
    guardrails = Guardrails(db)
    agent = ReconciliationAgent(openai_api_key, db, guardrails)

    results = {
        "total_tests": len(TEST_SCENARIOS),
        "passed": 0,
        "failed": 0,
        "test_results": [],
        "timestamp": datetime.now().isoformat()
    }

    for scenario_name, scenario in TEST_SCENARIOS.items():
        print(f"\n{'='*80}")
        print(f"Running: {scenario_name}")
        print(f"Description: {scenario['description']}")
        print(f"{'='*80}")

        try:
            result = agent.reconcile(
                scenario["contract"],
                scenario["invoice"],
                scenario["receipt"]
            )

            expected = scenario["expected"]
            discrepancies = []
            test_passed = True

            if result["status"] != expected.get("status"):
                discrepancies.append(f"Status: got {result['status']}, expected {expected['status']}")
                test_passed = False

            confidence = result["confidence"]
            if "confidence_min" in expected and confidence < expected["confidence_min"]:
                discrepancies.append(f"Confidence too low: {confidence} < {expected['confidence_min']}")
                test_passed = False

            if "confidence_max" in expected and confidence > expected["confidence_max"]:
                discrepancies.append(f"Confidence too high: {confidence} > {expected['confidence_max']}")
                test_passed = False

            fraud_score = result.get("fraud_analysis", {}).get("fraud_score", 0)
            if "fraud_score_min" in expected and fraud_score < expected["fraud_score_min"]:
                discrepancies.append(f"Fraud score too low: {fraud_score} < {expected['fraud_score_min']}")
                test_passed = False

            if "fraud_score_max" in expected and fraud_score > expected["fraud_score_max"]:
                discrepancies.append(f"Fraud score too high: {fraud_score} > {expected['fraud_score_max']}")
                test_passed = False

            anomalies = result.get("anomaly_analysis", {}).get("total_anomalies", 0)
            if "anomalies_min" in expected and anomalies < expected["anomalies_min"]:
                discrepancies.append(f"Too few anomalies: {anomalies} < {expected['anomalies_min']}")
                test_passed = False

            if "anomalies_max" in expected and anomalies > expected["anomalies_max"]:
                discrepancies.append(f"Too many anomalies: {anomalies} > {expected['anomalies_max']}")
                test_passed = False

            status_icon = "✅" if test_passed else "❌"
            print(f"\n{status_icon} Result: {result['status']}")
            print(f"   Confidence: {confidence}%")
            print(f"   Fraud Score: {fraud_score}/100")
            print(f"   Anomalies: {anomalies}")

            if discrepancies:
                print(f"\n❌ Discrepancies:")
                for disc in discrepancies:
                    print(f"   - {disc}")

            if test_passed:
                results["passed"] += 1
            else:
                results["failed"] += 1

            results["test_results"].append({
                "scenario": scenario_name,
                "description": scenario["description"],
                "passed": test_passed,
                "agent_output": {
                    "status": result["status"],
                    "confidence": confidence,
                    "fraud_score": fraud_score,
                    "anomalies": anomalies
                },
                "expected_output": expected,
                "discrepancies": discrepancies
            })

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results["test_results"].append({
                "scenario": scenario_name,
                "description": scenario["description"],
                "passed": False,
                "error": str(e)
            })
            results["failed"] += 1

    return results


def print_summary(results):
    """Print test summary."""
    print(f"\n\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Pass Rate: {results['passed'] / results['total_tests'] * 100:.1f}%")
    print(f"{'='*80}\n")


def save_results(results):
    """Save test results to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"✅ Test results saved to {filename}")


def main():
    """Run all tests and generate report."""
    print("🚀 Starting Reconciliation Agent Tests...")
    results = run_reconciliation_tests()

    if results:
        print_summary(results)
        save_results(results)
    else:
        print("❌ Tests did not run. Check your environment.")
        sys.exit(1)


if __name__ == "__main__":
    main()
