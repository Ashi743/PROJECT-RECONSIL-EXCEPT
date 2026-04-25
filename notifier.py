"""
Notifier - Email/Slack notification system for both agents.
Currently simulates notifications (prints to console).
Can be extended to send real emails/Slack messages.
"""

from datetime import datetime
from typing import Dict, List


class Notifier:
    """Notification system for alerts from both agents."""

    def __init__(self, email_enabled=False, slack_enabled=False):
        """
        Initialize notifier.

        Args:
            email_enabled: Send email notifications (not implemented)
            slack_enabled: Send Slack notifications (not implemented)
        """
        self.email_enabled = email_enabled
        self.slack_enabled = slack_enabled
        self.notification_log = []

    def send_exception_alert(self, exception: Dict) -> bool:
        """
        Send notification for exception (CRITICAL/HIGH only).

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

        # Log notification
        self.notification_log.append({
            "timestamp": datetime.now().isoformat(),
            "type": "exception",
            "urgency": urgency,
            "exception_id": exception.get("exception_id"),
            "recipient": exception.get("owner"),
            "message": message
        })

        # Console output (demo mode)
        self._print_console_notification(exception, message)

        # TODO: Send actual email/Slack
        # if self.email_enabled:
        #     self._send_email(exception["owner"], message)
        # if self.slack_enabled:
        #     self._send_slack(exception["handler"], message)

        return True

    def send_fraud_alert(self, fraud_decision: Dict) -> bool:
        """
        Send notification for high-fraud-score reconciliation.

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

        # Log notification
        self.notification_log.append({
            "timestamp": datetime.now().isoformat(),
            "type": "fraud_alert",
            "fraud_score": fraud_score,
            "audit_id": fraud_decision.get("audit_id"),
            "message": message
        })

        # Console output
        self._print_fraud_alert(fraud_decision, message)

        return True

    def send_anomaly_alert(self, anomaly_decision: Dict) -> bool:
        """
        Send notification for multiple anomalies detected.

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

        # Log notification
        self.notification_log.append({
            "timestamp": datetime.now().isoformat(),
            "type": "anomaly_alert",
            "anomaly_count": anomaly_count,
            "audit_id": anomaly_decision.get("audit_id"),
            "message": message
        })

        # Console output
        self._print_anomaly_alert(anomaly_decision, message)

        return True

    def _format_exception_message(self, exception: Dict) -> str:
        """Format exception notification message."""

        return f"""
EXCEPTION ALERT - {exception.get('urgency')}

Exception ID: {exception.get('exception_id')}
Type: {exception.get('exception_type')}
Message: {exception.get('original_message')}
Handler: {exception.get('handler')}
Owner: {exception.get('owner')}
Deadline: {exception.get('deadline')}
Financial Impact: ₹{exception.get('financial_impact', 0):,.0f}

Action Required: {exception.get('deadline')}

Action Plan:
"""

    def _format_fraud_message(self, decision: Dict) -> str:
        """Format fraud alert message."""

        fraud = decision.get("fraud_analysis", {})

        return f"""
FRAUD ALERT - HIGH RISK

Audit ID: {decision.get('audit_id')}
Fraud Score: {fraud.get('fraud_score')}/100
Risk Level: {fraud.get('risk_level')}

Signals Detected:
"""

    def _format_anomaly_message(self, decision: Dict) -> str:
        """Format anomaly alert message."""

        anomaly = decision.get("anomaly_analysis", {})

        return f"""
ANOMALY ALERT - MULTIPLE ISSUES

Audit ID: {decision.get('audit_id')}
Total Anomalies: {anomaly.get('total_anomalies')}
Critical Anomalies: {anomaly.get('critical_anomalies')}

Anomalies Detected:
"""

    def _print_console_notification(self, exception: Dict, message: str) -> None:
        """Print exception notification to console (demo mode)."""

        urgency = exception.get("urgency", "MEDIUM")

        if urgency == "CRITICAL":
            icon = "🔴"
        elif urgency == "HIGH":
            icon = "🟠"
        else:
            icon = "🟡"

        print(f"\n{icon} NOTIFICATION: {message}")

    def _print_fraud_alert(self, decision: Dict, message: str) -> None:
        """Print fraud alert to console (demo mode)."""

        fraud_score = decision.get("fraud_analysis", {}).get("fraud_score", 0)
        print(f"\n🚨 FRAUD ALERT (Score: {fraud_score}/100): {message}")

    def _print_anomaly_alert(self, decision: Dict, message: str) -> None:
        """Print anomaly alert to console (demo mode)."""

        count = decision.get("anomaly_analysis", {}).get("total_anomalies", 0)
        print(f"\n⚠️ ANOMALY ALERT ({count} issues): {message}")

    def get_notification_log(self, limit: int = 50) -> List[Dict]:
        """Get recent notifications."""

        return self.notification_log[-limit:]

    def clear_log(self) -> None:
        """Clear notification log."""

        self.notification_log = []
