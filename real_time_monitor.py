"""
Real-Time Monitoring Engine - Periodically checks for exceptions in shipments, documents, LCs, and laytime.

Monitors:
1. Shipment tracking (delays)
2. Document status (missing docs)
3. LC deadlines (time-bars)
4. Laytime/demurrage (DD risk)
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time


class RealTimeMonitor:
    """Real-time monitoring engine that periodically checks for exceptions."""

    def __init__(self, exception_agent, database, check_interval_minutes=5):
        """
        Initialize real-time monitor.

        Args:
            exception_agent: ExceptionTriageAgent instance
            database: Database instance
            check_interval_minutes: How often to run checks (default 5 min)
        """
        self.exception_agent = exception_agent
        self.database = database
        self.check_interval_minutes = check_interval_minutes
        self.scheduler = BackgroundScheduler()
        self.is_running = False

    def start(self):
        """Start the monitoring scheduler"""
        if not self.is_running:
            try:
                self.scheduler.add_job(
                    self.run_all_checks,
                    'interval',
                    minutes=self.check_interval_minutes,
                    id='exception_monitor'
                )

                self.scheduler.start()
                self.is_running = True
                print(f"✅ Real-time monitor started (checking every {self.check_interval_minutes} min)")
            except Exception as e:
                print(f"Error starting monitor: {e}")

    def stop(self):
        """Stop the monitoring scheduler"""
        if self.is_running:
            try:
                self.scheduler.shutdown()
                self.is_running = False
                print("⏹️ Real-time monitor stopped")
            except Exception as e:
                print(f"Error stopping monitor: {e}")

    def run_all_checks(self):
        """Run all monitoring checks"""
        print(f"\n🔍 Running exception checks at {datetime.now().strftime('%H:%M:%S')}...")

        # Check 1: Shipment delays
        self.check_shipment_delays()

        # Check 2: Missing documents
        self.check_missing_documents()

        # Check 3: LC deadlines
        self.check_lc_deadlines()

        # Check 4: Demurrage risk
        self.check_demurrage_risk()

        print("✅ All checks complete\n")

    def check_shipment_delays(self):
        """Check for shipment delays"""
        try:
            shipments = self.database.get_shipments_in_transit()

            for shipment in shipments:
                from datetime import datetime as dt
                expected_arrival = dt.fromisoformat(shipment["expected_arrival"])
                now = dt.now()

                if now > expected_arrival:
                    days_delayed = (now - expected_arrival).days

                    if not self.database.exception_exists(shipment["shipment_id"], "SHIPMENT_DELAY"):
                        exception_message = f"Vessel {shipment['vessel_name']} delayed {days_delayed} days"

                        context = {
                            "shipment_id": shipment["shipment_id"],
                            "vessel_name": shipment["vessel_name"],
                            "days_delayed": days_delayed,
                            "daily_dd_rate": shipment.get("daily_dd_rate", 50000)
                        }

                        result = self.exception_agent.detect_and_route(exception_message, context)
                        print(f"🚨 SHIPMENT_DELAY detected: {shipment['vessel_name']} ({days_delayed} days)")
        except Exception as e:
            print(f"Error in check_shipment_delays: {e}")

    def check_missing_documents(self):
        """Check for missing documents approaching LC deadline"""
        try:
            lcs = self.database.get_active_lcs()

            for lc in lcs:
                from datetime import datetime as dt
                required_docs = lc.get("required_documents", [])
                received_docs = lc.get("received_documents", [])

                missing_docs = [doc for doc in required_docs if doc not in received_docs]

                if missing_docs:
                    lc_expiry = dt.fromisoformat(lc["expiry_date"])
                    days_to_expiry = (lc_expiry - dt.now()).days

                    if not self.database.exception_exists(lc["lc_id"], "MISSING_DOCUMENT"):
                        for doc in missing_docs:
                            exception_message = f"{doc} not received yet, LC expires in {days_to_expiry} days"

                            context = {
                                "lc_id": lc["lc_id"],
                                "document_type": doc,
                                "days_to_lc_deadline": days_to_expiry,
                                "lc_amount": lc.get("lc_amount", 5000000)
                            }

                            result = self.exception_agent.detect_and_route(exception_message, context)
                            print(f"🚨 MISSING_DOCUMENT detected: {doc} (deadline in {days_to_expiry} days)")
        except Exception as e:
            print(f"Error in check_missing_documents: {e}")

    def check_lc_deadlines(self):
        """Check for approaching LC deadlines"""
        try:
            lcs = self.database.get_active_lcs()

            for lc in lcs:
                from datetime import datetime as dt
                lc_expiry = dt.fromisoformat(lc["expiry_date"])
                days_to_expiry = (lc_expiry - dt.now()).days

                if days_to_expiry <= 3 and days_to_expiry >= 0:
                    if not self.database.exception_exists(lc["lc_id"], "LC_DISCREPANCY"):
                        exception_message = f"LC {lc['lc_number']} time-bar approaching - expires in {days_to_expiry} days"

                        context = {
                            "lc_id": lc["lc_id"],
                            "lc_number": lc["lc_number"],
                            "days_to_lc_deadline": days_to_expiry,
                            "lc_amount": lc.get("lc_amount", 5000000)
                        }

                        result = self.exception_agent.detect_and_route(exception_message, context)
                        print(f"🚨 LC_DEADLINE approaching: {lc['lc_number']} ({days_to_expiry} days)")
        except Exception as e:
            print(f"Error in check_lc_deadlines: {e}")

    def check_demurrage_risk(self):
        """Check for vessels approaching laytime expiry"""
        try:
            vessels = self.database.get_vessels_discharging()

            for vessel in vessels:
                from datetime import datetime as dt
                laytime_expiry = dt.fromisoformat(vessel["laytime_expiry"])
                days_to_expiry = (laytime_expiry - dt.now()).days

                if days_to_expiry <= 10:
                    if not self.database.exception_exists(vessel["vessel_name"], "DD_RISK"):
                        exception_message = f"Laytime expires in {days_to_expiry} days for {vessel['vessel_name']}"

                        context = {
                            "vessel_name": vessel["vessel_name"],
                            "port": vessel.get("port"),
                            "days_to_laytime_expiry": days_to_expiry,
                            "daily_dd_rate": vessel.get("daily_dd_rate", 50000)
                        }

                        result = self.exception_agent.detect_and_route(exception_message, context)
                        print(f"🚨 DD_RISK detected: {vessel['vessel_name']} ({days_to_expiry} days to expiry)")
        except Exception as e:
            print(f"Error in check_demurrage_risk: {e}")
