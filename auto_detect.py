"""
Automated Exception Detection Script - Runs via Hermes cron job
Detects exceptions and sends Telegram alerts every 5 minutes.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add project directory to path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from exception_triage_agent import ExceptionTriageAgent
from real_time_monitor import RealTimeMonitor
from database import Database
from guardrails import Guardrails
from telegram_notifier import TelegramNotifier
from dotenv import load_dotenv

load_dotenv()

def run_auto_detection():
    """
    Main auto-detection routine - detects exceptions and sends Telegram alerts.
    Designed to run via Hermes cron job every 5 minutes.
    """
    
    print(f"\n{'='*70}")
    print(f"🔍 AGRO-COMPANY AUTO-DETECTION RUN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    try:
        # Initialize components
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("❌ OPENAI_API_KEY not found in .env")
            return False
        
        # Initialize database and agents
        db = Database()
        guardrails = Guardrails(db)
        exception_agent = ExceptionTriageAgent(openai_api_key, db, guardrails)
        telegram_notifier = TelegramNotifier()
        
        # Run all monitoring checks
        print("📊 Running exception detection checks...\n")
        
        # Check 1: Shipment delays
        print("1️⃣  Checking for shipment delays...")
        shipment_exceptions = check_shipment_delays(db, exception_agent, telegram_notifier)
        
        # Check 2: Missing documents
        print("2️⃣  Checking for missing documents...")
        doc_exceptions = check_missing_documents(db, exception_agent, telegram_notifier)
        
        # Check 3: LC deadlines
        print("3️⃣  Checking for LC deadline issues...")
        lc_exceptions = check_lc_deadlines(db, exception_agent, telegram_notifier)
        
        # Check 4: Demurrage risk
        print("4️⃣  Checking for demurrage/laytime risks...")
        dd_exceptions = check_demurrage_risk(db, exception_agent, telegram_notifier)
        
        total_exceptions = shipment_exceptions + doc_exceptions + lc_exceptions + dd_exceptions
        
        print(f"\n{'='*70}")
        print(f"✅ DETECTION COMPLETE")
        print(f"   Total new exceptions detected: {total_exceptions}")
        print(f"   Telegram alerts sent: {total_exceptions}")
        print(f"{'='*70}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Auto-detection error: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_shipment_delays(db, exception_agent, telegram_notifier) -> int:
    """Check for shipment delays and send alerts."""
    
    count = 0
    try:
        shipments = db.get_shipments_in_transit()
        
        for shipment in shipments:
            from datetime import datetime as dt
            expected_arrival = dt.fromisoformat(shipment["expected_arrival"])
            now = dt.now()
            
            if now > expected_arrival:
                days_delayed = (now - expected_arrival).days
                
                if not db.exception_exists(shipment["shipment_id"], "SHIPMENT_DELAY"):
                    exception_message = f"Vessel {shipment['vessel_name']} delayed {days_delayed} days"
                    
                    context = {
                        "shipment_id": shipment["shipment_id"],
                        "vessel_name": shipment["vessel_name"],
                        "days_delayed": days_delayed,
                        "daily_dd_rate": shipment.get("daily_dd_rate", 50000)
                    }
                    
                    result = exception_agent.detect_and_route(exception_message, context)
                    
                    # Send Telegram alert
                    if result.get("urgency") in ["CRITICAL", "HIGH"]:
                        telegram_notifier.send_exception_alert(result)
                        count += 1
                        print(f"   🚢 SHIPMENT_DELAY: {shipment['vessel_name']} ({days_delayed} days)")
    
    except Exception as e:
        print(f"   ⚠️  Error checking shipment delays: {e}")
    
    return count


def check_missing_documents(db, exception_agent, telegram_notifier) -> int:
    """Check for missing documents and send alerts."""
    
    count = 0
    try:
        lcs = db.get_active_lcs()
        
        for lc in lcs:
            from datetime import datetime as dt
            required_docs = lc.get("required_documents", [])
            received_docs = lc.get("received_documents", [])
            
            missing_docs = [doc for doc in required_docs if doc not in received_docs]
            
            if missing_docs:
                lc_expiry = dt.fromisoformat(lc["expiry_date"])
                days_to_expiry = (lc_expiry - dt.now()).days
                
                if not db.exception_exists(lc["lc_id"], "MISSING_DOCUMENT"):
                    for doc in missing_docs:
                        exception_message = f"{doc} not received yet, LC expires in {days_to_expiry} days"
                        
                        context = {
                            "lc_id": lc["lc_id"],
                            "document_type": doc,
                            "days_to_lc_deadline": days_to_expiry,
                            "lc_amount": lc.get("lc_amount", 5000000)
                        }
                        
                        result = exception_agent.detect_and_route(exception_message, context)
                        
                        # Send Telegram alert
                        if result.get("urgency") in ["CRITICAL", "HIGH"]:
                            telegram_notifier.send_exception_alert(result)
                            count += 1
                            print(f"   📄 MISSING_DOCUMENT: {doc} (deadline in {days_to_expiry} days)")
    
    except Exception as e:
        print(f"   ⚠️  Error checking missing documents: {e}")
    
    return count


def check_lc_deadlines(db, exception_agent, telegram_notifier) -> int:
    """Check for approaching LC deadlines and send alerts."""
    
    count = 0
    try:
        lcs = db.get_active_lcs()
        
        for lc in lcs:
            from datetime import datetime as dt
            lc_expiry = dt.fromisoformat(lc["expiry_date"])
            days_to_expiry = (lc_expiry - dt.now()).days
            
            if days_to_expiry <= 3 and days_to_expiry >= 0:
                if not db.exception_exists(lc["lc_id"], "LC_DISCREPANCY"):
                    exception_message = f"LC {lc['lc_number']} time-bar approaching - expires in {days_to_expiry} days"
                    
                    context = {
                        "lc_id": lc["lc_id"],
                        "lc_number": lc["lc_number"],
                        "days_to_lc_deadline": days_to_expiry,
                        "lc_amount": lc.get("lc_amount", 5000000)
                    }
                    
                    result = exception_agent.detect_and_route(exception_message, context)
                    
                    # Send Telegram alert
                    if result.get("urgency") in ["CRITICAL", "HIGH"]:
                        telegram_notifier.send_exception_alert(result)
                        count += 1
                        print(f"   💳 LC_DEADLINE: {lc['lc_number']} (expires in {days_to_expiry} days)")
    
    except Exception as e:
        print(f"   ⚠️  Error checking LC deadlines: {e}")
    
    return count


def check_demurrage_risk(db, exception_agent, telegram_notifier) -> int:
    """Check for demurrage/laytime risks and send alerts."""
    
    count = 0
    try:
        vessels = db.get_vessels_discharging()
        
        for vessel in vessels:
            from datetime import datetime as dt
            laytime_expiry = dt.fromisoformat(vessel["laytime_expiry"])
            days_to_expiry = (laytime_expiry - dt.now()).days
            
            if days_to_expiry <= 10:
                if not db.exception_exists(vessel["vessel_name"], "DD_RISK"):
                    exception_message = f"Laytime expires in {days_to_expiry} days for {vessel['vessel_name']}"
                    
                    context = {
                        "vessel_name": vessel["vessel_name"],
                        "port": vessel.get("port"),
                        "days_to_laytime_expiry": days_to_expiry,
                        "daily_dd_rate": vessel.get("daily_dd_rate", 50000)
                    }
                    
                    result = exception_agent.detect_and_route(exception_message, context)
                    
                    # Send Telegram alert
                    if result.get("urgency") in ["CRITICAL", "HIGH"]:
                        telegram_notifier.send_exception_alert(result)
                        count += 1
                        print(f"   ⚠️  DD_RISK: {vessel['vessel_name']} ({days_to_expiry} days to expiry)")
    
    except Exception as e:
        print(f"   ⚠️  Error checking demurrage risk: {e}")
    
    return count


if __name__ == "__main__":
    success = run_auto_detection()
    sys.exit(0 if success else 1)
