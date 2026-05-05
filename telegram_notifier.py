"""
Telegram Notifier - Send formatted alerts to Telegram for exceptions and reconciliation issues.
Integrates with Hermes cron jobs for automated delivery.
"""

import os
import json
from datetime import datetime
from typing import Dict, List
import requests
from dotenv import load_dotenv

load_dotenv()

class TelegramNotifier:
    """Send formatted Telegram alerts for exceptions and reconciliation issues."""

    def __init__(self, bot_token: str = None, chat_id: str = None):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token (defaults to TELEGRAM_BOT_TOKEN env var)
            chat_id: Telegram chat ID (defaults to TELEGRAM_CHAT_ID env var)
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.notification_log = []

    def send_exception_alert(self, exception: Dict) -> bool:
        """
        Send formatted exception alert to Telegram.
        
        Args:
            exception: Exception dict from ExceptionTriageAgent
            
        Returns:
            True if sent successfully, False otherwise
        """
        
        urgency = exception.get("urgency", "MEDIUM")
        
        # Only notify for CRITICAL and HIGH urgency
        if urgency not in ["CRITICAL", "HIGH"]:
            return False
        
        message = self._format_exception_message(exception)
        
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            
            success = response.status_code == 200
            
            # Log notification
            self.notification_log.append({
                "timestamp": datetime.now().isoformat(),
                "type": "exception",
                "urgency": urgency,
                "exception_id": exception.get("exception_id"),
                "recipient": exception.get("owner"),
                "status": "sent" if success else "failed"
            })
            
            if success:
                print(f"✅ Telegram alert sent for exception {exception.get('exception_id')}")
            else:
                print(f"❌ Failed to send Telegram alert: {response.text}")
            
            return success
            
        except Exception as e:
            print(f"❌ Telegram notification error: {e}")
            self.notification_log.append({
                "timestamp": datetime.now().isoformat(),
                "type": "exception",
                "urgency": urgency,
                "status": "error",
                "error": str(e)
            })
            return False

    def send_fraud_alert(self, fraud_decision: Dict) -> bool:
        """
        Send fraud alert to Telegram.
        
        Args:
            fraud_decision: Reconciliation decision with high fraud score
            
        Returns:
            True if sent successfully, False otherwise
        """
        
        fraud_score = fraud_decision.get("fraud_analysis", {}).get("fraud_score", 0)
        
        # Only notify for high fraud scores (>75)
        if fraud_score < 75:
            return False
        
        message = self._format_fraud_message(fraud_decision)
        
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            
            success = response.status_code == 200
            
            self.notification_log.append({
                "timestamp": datetime.now().isoformat(),
                "type": "fraud_alert",
                "fraud_score": fraud_score,
                "status": "sent" if success else "failed"
            })
            
            if success:
                print(f"✅ Telegram fraud alert sent (Score: {fraud_score}/100)")
            
            return success
            
        except Exception as e:
            print(f"❌ Telegram fraud alert error: {e}")
            return False

    def send_anomaly_alert(self, anomaly_decision: Dict) -> bool:
        """
        Send anomaly alert to Telegram.
        
        Args:
            anomaly_decision: Reconciliation decision with anomalies
            
        Returns:
            True if sent successfully, False otherwise
        """
        
        anomaly_count = anomaly_decision.get("anomaly_analysis", {}).get("total_anomalies", 0)
        
        # Only notify for 3+ anomalies
        if anomaly_count < 3:
            return False
        
        message = self._format_anomaly_message(anomaly_decision)
        
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            
            success = response.status_code == 200
            
            self.notification_log.append({
                "timestamp": datetime.now().isoformat(),
                "type": "anomaly_alert",
                "anomaly_count": anomaly_count,
                "status": "sent" if success else "failed"
            })
            
            if success:
                print(f"✅ Telegram anomaly alert sent ({anomaly_count} issues)")
            
            return success
            
        except Exception as e:
            print(f"❌ Telegram anomaly alert error: {e}")
            return False

    def _format_exception_message(self, exception: Dict) -> str:
        """Format exception message for Telegram with emoji and HTML formatting."""
        
        urgency = exception.get("urgency", "MEDIUM")
        urgency_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }.get(urgency, "⚪")
        
        handler_emoji = {
            "FREIGHT_TEAM": "🚢",
            "DOCS_TEAM": "📋",
            "TRADE_FINANCE_TEAM": "💰",
            "OPERATIONS_TEAM": "⚙️"
        }.get(exception.get("handler"), "👤")
        
        exc_type = exception.get("exception_type", "UNKNOWN")
        exc_icon = {
            "SHIPMENT_DELAY": "⏳",
            "MISSING_DOCUMENT": "📄",
            "LC_DISCREPANCY": "💳",
            "DD_RISK": "⚠️"
        }.get(exc_type, "❓")
        
        action_plan = exception.get("action_plan", [])
        if isinstance(action_plan, str):
            try:
                action_plan = json.loads(action_plan)
            except:
                action_plan = []
        
        action_text = ""
        if action_plan:
            action_text = "\n<b>📋 Action Plan:</b>\n"
            for action in action_plan[:3]:  # Limit to 3 actions for Telegram
                action_text += f"  • {action}\n"
        
        financial_impact = exception.get("financial_impact", 0)
        impact_str = f"₹{financial_impact:,.0f}" if financial_impact > 0 else "N/A"
        
        deadline = exception.get("deadline", "N/A")
        owner = exception.get("owner", "N/A")
        
        message = f"""{urgency_emoji} <b>EXCEPTION ALERT - {urgency}</b>

{exc_icon} <b>Type:</b> {exc_type}
<b>ID:</b> <code>{exception.get('exception_id', 'N/A')}</code>

<b>📝 Details:</b>
{exception.get('original_message', 'N/A')}

{handler_emoji} <b>Handler:</b> {exception.get('handler', 'N/A')}
<b>Owner:</b> {owner}

⏰ <b>Deadline:</b> {deadline}
💸 <b>Financial Impact:</b> {impact_str}
{action_text}
<b>Status:</b> OPEN
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return message

    def _format_fraud_message(self, decision: Dict) -> str:
        """Format fraud alert message for Telegram."""
        
        fraud = decision.get("fraud_analysis", {})
        fraud_score = fraud.get("fraud_score", 0)
        risk_level = fraud.get("risk_level", "UNKNOWN")
        
        signals = fraud.get("signals_detected", [])
        signals_text = "\n".join([f"  • {signal}" for signal in signals[:5]])
        
        message = f"""🚨 <b>FRAUD ALERT - HIGH RISK</b>

<b>🎯 Fraud Score:</b> {fraud_score}/100
<b>⚠️ Risk Level:</b> {risk_level}

<b>📋 Signals Detected:</b>
{signals_text}

<b>Audit ID:</b> <code>{decision.get('audit_id', 'N/A')}</code>
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>⚡ Action Required:</b> Review immediately by compliance team
"""
        return message

    def _format_anomaly_message(self, decision: Dict) -> str:
        """Format anomaly alert message for Telegram."""
        
        anomaly = decision.get("anomaly_analysis", {})
        total_anomalies = anomaly.get("total_anomalies", 0)
        critical_anomalies = anomaly.get("critical_anomalies", 0)
        
        anomalies = anomaly.get("anomalies_detected", [])
        anomalies_text = "\n".join([f"  • {anom}" for anom in anomalies[:5]])
        
        message = f"""⚠️ <b>ANOMALY ALERT - MULTIPLE ISSUES DETECTED</b>

<b>🔢 Total Anomalies:</b> {total_anomalies}
<b>🔴 Critical Anomalies:</b> {critical_anomalies}

<b>📋 Issues Found:</b>
{anomalies_text}

<b>Audit ID:</b> <code>{decision.get('audit_id', 'N/A')}</code>
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>⚡ Action Required:</b> Investigate and validate data
"""
        return message

    def send_test_message(self, test_type: str = "CONNECTION") -> bool:
        """
        Send a test message to verify Telegram connection.
        
        Args:
            test_type: Type of test message
            
        Returns:
            True if sent successfully, False otherwise
        """
        
        test_messages = {
            "CONNECTION": "✅ <b>AgroCompany Trade Operations Platform</b>\n\n🟢 Telegram connection is working!\n\nYou will receive exception alerts here.",
            "EXCEPTION_TEST": "🔴 <b>TEST EXCEPTION ALERT</b>\n\nThis is a test exception notification.\nYour Telegram integration is ready!",
            "FRAUD_TEST": "🚨 <b>TEST FRAUD ALERT</b>\n\nThis is a test fraud alert.\nYour fraud detection system is active!",
            "ANOMALY_TEST": "⚠️ <b>TEST ANOMALY ALERT</b>\n\nThis is a test anomaly alert.\nYour anomaly detection is working!"
        }
        
        message = test_messages.get(test_type, test_messages["CONNECTION"])
        
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                print(f"✅ Test message sent: {test_type}")
            else:
                print(f"❌ Failed to send test message: {response.text}")
            
            return success
            
        except Exception as e:
            print(f"❌ Test message error: {e}")
            return False

    def get_notification_log(self, limit: int = 50) -> List[Dict]:
        """Get recent notifications."""
        return self.notification_log[-limit:]

    def clear_log(self) -> None:
        """Clear notification log."""
        self.notification_log = []
