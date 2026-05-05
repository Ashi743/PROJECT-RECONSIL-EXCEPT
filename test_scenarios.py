"""
Test Scenarios for AgroCompany Exception Detection System
Run different test scenarios to trigger exceptions and test Telegram alerts.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add project directory to path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from exception_triage_agent import ExceptionTriageAgent
from database import Database
from guardrails import Guardrails
from telegram_notifier import TelegramNotifier
from dotenv import load_dotenv
import json

load_dotenv()

# Test scenarios
TEST_SCENARIOS = {
    "CRITICAL_SHIPMENT_DELAY": {
        "name": "Critical Shipment Delay (10 days)",
        "message": "Vessel MV CriticalDelay delayed 10 days from Mumbai to Singapore",
        "context": {
            "shipment_id": "TEST-SHIP-001",
            "vessel_name": "MV CriticalDelay",
            "days_delayed": 10,
            "daily_dd_rate": 75000
        },
        "expected_urgency": "CRITICAL"
    },
    
    "HIGH_SHIPMENT_DELAY": {
        "name": "High Priority Shipment Delay (5 days)",
        "message": "Vessel MV DelayedShip delayed 5 days approaching port",
        "context": {
            "shipment_id": "TEST-SHIP-002",
            "vessel_name": "MV DelayedShip",
            "days_delayed": 5,
            "daily_dd_rate": 60000
        },
        "expected_urgency": "HIGH"
    },
    
    "CRITICAL_MISSING_DOC": {
        "name": "Critical Missing Document (2 days to deadline)",
        "message": "Certificate of Origin missing, only 2 days until LC deadline expires",
        "context": {
            "lc_id": "TEST-LC-001",
            "document_type": "Certificate of Origin",
            "days_to_lc_deadline": 2,
            "lc_amount": 8000000
        },
        "expected_urgency": "CRITICAL"
    },
    
    "HIGH_MISSING_DOC": {
        "name": "High Priority Missing Document (5 days)",
        "message": "Bill of Lading not received, LC deadline in 5 days",
        "context": {
            "lc_id": "TEST-LC-002",
            "document_type": "Bill of Lading",
            "days_to_lc_deadline": 5,
            "lc_amount": 5000000
        },
        "expected_urgency": "HIGH"
    },
    
    "CRITICAL_DEMURRAGE": {
        "name": "Critical Demurrage Risk (2 days)",
        "message": "Vessel MV CriticalPort laytime expires in 2 days - urgent discharge needed",
        "context": {
            "vessel_name": "MV CriticalPort",
            "port": "Singapore",
            "days_to_laytime_expiry": 2,
            "daily_dd_rate": 85000
        },
        "expected_urgency": "CRITICAL"
    },
    
    "HIGH_DEMURRAGE": {
        "name": "High Priority Demurrage Risk (5 days)",
        "message": "Vessel approaching laytime expiry at port - 5 days remaining",
        "context": {
            "vessel_name": "MV HighDD",
            "port": "Mumbai",
            "days_to_laytime_expiry": 5,
            "daily_dd_rate": 65000
        },
        "expected_urgency": "HIGH"
    },
    
    "LC_DISCREPANCY": {
        "name": "LC Discrepancy - Amount Mismatch",
        "message": "LC amount USD 50,000 vs Invoice USD 52,000 - discrepancy detected",
        "context": {
            "lc_id": "TEST-LC-003",
            "lc_amount": 50000000,
            "invoice_amount": 52000000
        },
        "expected_urgency": "MEDIUM"
    },
    
    "MULTIPLE_ISSUES": {
        "name": "Multiple Critical Issues",
        "message": "MV MultiIssue delayed 8 days, BOL missing, laytime expires in 3 days - URGENT",
        "context": {
            "shipment_id": "TEST-SHIP-003",
            "vessel_name": "MV MultiIssue",
            "days_delayed": 8,
            "days_to_lc_deadline": 7,
            "days_to_laytime_expiry": 3,
            "daily_dd_rate": 70000
        },
        "expected_urgency": "CRITICAL"
    }
}


def test_single_scenario(scenario_key: str, send_telegram: bool = True):
    """
    Run a single test scenario.
    
    Args:
        scenario_key: Key from TEST_SCENARIOS
        send_telegram: Whether to send Telegram alert
    """
    
    if scenario_key not in TEST_SCENARIOS:
        print(f"❌ Scenario '{scenario_key}' not found")
        print(f"\nAvailable scenarios:")
        for key, scenario in TEST_SCENARIOS.items():
            print(f"  • {key}: {scenario['name']}")
        return False
    
    scenario = TEST_SCENARIOS[scenario_key]
    
    print(f"\n{'='*70}")
    print(f"🧪 TEST SCENARIO: {scenario['name']}")
    print(f"{'='*70}\n")
    
    try:
        # Initialize components
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("❌ OPENAI_API_KEY not found in .env")
            return False
        
        db = Database()
        guardrails = Guardrails(db)
        exception_agent = ExceptionTriageAgent(openai_api_key, db, guardrails)
        telegram_notifier = TelegramNotifier()
        
        # Run detection
        print(f"📝 Exception Message: {scenario['message']}\n")
        print(f"📊 Context: {json.dumps(scenario['context'], indent=2)}\n")
        
        print("🔄 Running exception detection...\n")
        result = exception_agent.detect_and_route(scenario['message'], scenario['context'])
        
        # Display results
        print(f"{'='*70}")
        print(f"✅ DETECTION RESULTS")
        print(f"{'='*70}\n")
        
        print(f"Exception ID:    {result.get('exception_id')}")
        print(f"Type:            {result.get('exception_type')}")
        print(f"Urgency:         {result.get('urgency')} (Expected: {scenario['expected_urgency']})")
        print(f"Confidence:      {result.get('classification_confidence')}%")
        print(f"Urgency Score:   {result.get('urgency_score')}/100")
        print(f"Handler:         {result.get('handler')}")
        print(f"Owner:           {result.get('owner')}")
        print(f"Deadline:        {result.get('deadline')}")
        print(f"Financial Impact: ₹{result.get('financial_impact', 0):,.0f}\n")
        
        # Show action plan
        print("📋 Action Plan:")
        action_plan = result.get('action_plan', [])
        if isinstance(action_plan, str):
            try:
                action_plan = json.loads(action_plan)
            except:
                action_plan = []
        
        for action in action_plan:
            print(f"  {action}")
        
        print(f"\n{'='*70}")
        
        # Send Telegram alert if requested
        if send_telegram:
            print("\n📱 Sending Telegram alert...")
            if result.get('urgency') in ['CRITICAL', 'HIGH']:
                success = telegram_notifier.send_exception_alert(result)
                if success:
                    print("✅ Telegram alert sent successfully!\n")
                else:
                    print("⚠️  Failed to send Telegram alert (check credentials)\n")
            else:
                print("ℹ️  Telegram alert not sent (urgency not CRITICAL/HIGH)\n")
        
        # Save to database
        print(f"💾 Exception saved to audit_logs.db")
        print(f"{'='*70}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Test scenario error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_scenarios(send_telegram: bool = False):
    """
    Run all test scenarios.
    
    Args:
        send_telegram: Whether to send Telegram alerts
    """
    
    print(f"\n{'='*70}")
    print(f"🧪 RUNNING ALL TEST SCENARIOS")
    print(f"{'='*70}\n")
    
    results = {}
    
    for scenario_key, scenario in TEST_SCENARIOS.items():
        print(f"\n[{scenario_key}] {scenario['name']}...")
        
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                print("❌ OPENAI_API_KEY not found")
                return
            
            db = Database()
            guardrails = Guardrails(db)
            exception_agent = ExceptionTriageAgent(openai_api_key, db, guardrails)
            telegram_notifier = TelegramNotifier()
            
            result = exception_agent.detect_and_route(scenario['message'], scenario['context'])
            
            results[scenario_key] = {
                "status": "SUCCESS",
                "exception_id": result.get('exception_id'),
                "urgency": result.get('urgency'),
                "expected": scenario['expected_urgency'],
                "match": result.get('urgency') == scenario['expected_urgency']
            }
            
            # Send alert if urgency is CRITICAL or HIGH
            if send_telegram and result.get('urgency') in ['CRITICAL', 'HIGH']:
                telegram_notifier.send_exception_alert(result)
            
            print(f"  ✅ Type: {result.get('exception_type')}")
            print(f"  ✅ Urgency: {result.get('urgency')} (Expected: {scenario['expected_urgency']})")
            
        except Exception as e:
            results[scenario_key] = {
                "status": "FAILED",
                "error": str(e)
            }
            print(f"  ❌ Error: {e}")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*70}\n")
    
    passed = sum(1 for r in results.values() if r.get('status') == 'SUCCESS' and r.get('match'))
    total = len(results)
    
    print(f"Total Scenarios: {total}")
    print(f"Passed:          {passed}")
    print(f"Failed:          {total - passed}\n")
    
    for scenario_key, result in results.items():
        status_icon = "✅" if result.get('match') else "❌"
        print(f"{status_icon} {scenario_key}: {result.get('urgency', 'N/A')}")


def test_telegram_connection():
    """Test Telegram connection with a test message."""
    
    print(f"\n{'='*70}")
    print(f"📱 TELEGRAM CONNECTION TEST")
    print(f"{'='*70}\n")
    
    try:
        telegram_notifier = TelegramNotifier()
        
        print("Sending test message to Telegram...\n")
        success = telegram_notifier.send_test_message("CONNECTION")
        
        if success:
            print("\n✅ Telegram connection is working!")
            print("   You should have received a test message on your Telegram chat.")
        else:
            print("\n❌ Failed to send test message.")
            print("   Check your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        
        print(f"{'='*70}\n")
        return success
        
    except Exception as e:
        print(f"❌ Telegram test error: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test AgroCompany exception detection scenarios")
    parser.add_argument("--scenario", help="Run specific scenario (key from TEST_SCENARIOS)")
    parser.add_argument("--all", action="store_true", help="Run all scenarios")
    parser.add_argument("--telegram", action="store_true", help="Send Telegram alerts")
    parser.add_argument("--test-telegram", action="store_true", help="Test Telegram connection only")
    parser.add_argument("--list", action="store_true", help="List all available scenarios")
    
    args = parser.parse_args()
    
    if args.list:
        print("\n📋 Available Test Scenarios:\n")
        for key, scenario in TEST_SCENARIOS.items():
            print(f"  {key}")
            print(f"    {scenario['name']}")
            print(f"    Expected Urgency: {scenario['expected_urgency']}\n")
    
    elif args.test_telegram:
        test_telegram_connection()
    
    elif args.all:
        test_all_scenarios(send_telegram=args.telegram)
    
    elif args.scenario:
        test_single_scenario(args.scenario, send_telegram=args.telegram)
    
    else:
        print("\n❌ Please specify an action:")
        print("   --scenario KEY     Run specific scenario")
        print("   --all              Run all scenarios")
        print("   --list             List available scenarios")
        print("   --test-telegram    Test Telegram connection")
        print("   --telegram         Send Telegram alerts\n")
        print("Example: python test_scenarios.py --scenario CRITICAL_SHIPMENT_DELAY --telegram\n")
