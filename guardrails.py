import secrets
from datetime import datetime, timedelta
from typing import Dict, List


class Guardrails:
    """Implements 5 guardrails for safe agent operations."""

    SANCTIONS_LIST = ["Iran Inc", "Syria Corp", "North Korea Ltd", "Cuban Export"]

    def __init__(self, database):
        """Initialize guardrails."""
        self.database = database

    def route_by_confidence(self, confidence: int, decision_type: str) -> Dict:
        """Route decisions based on confidence score."""
        if confidence > 95:
            action = "AUTO_APPROVE"
            owner = None
            deadline = None
            urgency = "NONE"
        elif confidence >= 80:
            action = "ROUTE_TO_SPECIALIST"
            owner = self._get_specialist(decision_type)
            deadline = (datetime.now() + timedelta(hours=24)).isoformat()
            urgency = "MEDIUM"
        elif confidence >= 50:
            action = "ESCALATE_TO_MANAGER"
            owner = self._get_manager(decision_type)
            deadline = (datetime.now() + timedelta(hours=2)).isoformat()
            urgency = "HIGH"
        else:
            action = "ESCALATE_TO_DIRECTOR"
            owner = self._get_director(decision_type)
            deadline = (datetime.now() + timedelta(hours=1)).isoformat()
            urgency = "CRITICAL"

        return {
            "action": action,
            "owner": owner,
            "deadline": deadline,
            "urgency": urgency,
            "confidence_threshold": confidence
        }

    def log_agent_decision(self, agent_name: str, decision: dict, confidence: int, reasoning: str) -> str:
        """Log agent decision to audit trail."""
        return self.database.log_agent_decision(agent_name, decision, confidence, reasoning)

    def log_human_approval(self, audit_id: str, approver: str, decision: str, notes: str, confidence: int) -> None:
        """Log human approval decision."""
        self.database.log_human_approval(audit_id, approver, decision, notes, confidence)

    def mask_for_display(self, data: dict, user_role: str) -> dict:
        """Mask sensitive fields based on user role."""
        sensitive_fields = [
            "counterparty_name",
            "bank_details",
            "customer_contact",
            "invoice_line_items",
            "account_numbers",
            "applicant",
            "issuing_bank"
        ]

        masked = data.copy()

        if user_role == "viewer":
            for field in sensitive_fields:
                if field in masked:
                    masked[field] = "***REDACTED***"
        elif user_role == "analyst":
            for field in sensitive_fields:
                if field in masked:
                    if field == "counterparty_name" and isinstance(masked[field], str):
                        masked[field] = "***REDACTED***"
                    elif field in ["bank_details", "customer_contact", "account_numbers", "invoice_line_items"]:
                        masked[field] = "***REDACTED***"
        elif user_role == "manager":
            for field in sensitive_fields:
                if field == "counterparty_name" and isinstance(masked[field], str) and len(masked[field]) > 6:
                    name = masked[field]
                    masked[field] = f"{name[:3]}...{name[-3:]}"
                elif field in ["bank_details", "account_numbers"]:
                    masked[field] = "***REDACTED***"

        return masked

    def check_ucp600_compliance(self, lc_data: dict) -> Dict:
        """Check LC against UCP 600 standards."""
        violations = []
        warnings = []

        negotiability = lc_data.get("negotiability", "").upper()
        if negotiability == "NOT_NEGOTIABLE" and lc_data.get("requires_negotiation"):
            violations.append({
                "rule": "negotiability",
                "severity": "VIOLATION",
                "message": "LC is NOT_NEGOTIABLE but contract requires negotiation"
            })

        days_to_expiry = lc_data.get("days_to_expiry", 0)
        if days_to_expiry <= 0:
            violations.append({
                "rule": "expiry",
                "severity": "VIOLATION",
                "message": f"LC has expired ({days_to_expiry} days)"
            })
        elif days_to_expiry < 7:
            warnings.append({
                "rule": "expiry",
                "severity": "WARNING",
                "message": f"LC expires in {days_to_expiry} days (less than 7 days)"
            })

        invoice_amount = lc_data.get("invoice_amount", 0)
        lc_amount = lc_data.get("lc_amount", 0)
        if invoice_amount > lc_amount:
            violations.append({
                "rule": "amount",
                "severity": "VIOLATION",
                "message": f"Invoice amount ({invoice_amount}) exceeds LC amount ({lc_amount})"
            })

        counterparty = lc_data.get("counterparty", "")
        if not self.check_sanctions(counterparty):
            violations.append({
                "rule": "sanctions",
                "severity": "VIOLATION",
                "message": f"Counterparty '{counterparty}' is on sanctions list"
            })

        lc_incoterm = lc_data.get("incoterm", "").upper()
        contract_incoterm = lc_data.get("contract_incoterm", "").upper()
        if lc_incoterm and contract_incoterm and lc_incoterm != contract_incoterm:
            warnings.append({
                "rule": "incoterm",
                "severity": "WARNING",
                "message": f"LC incoterm ({lc_incoterm}) != contract incoterm ({contract_incoterm})"
            })

        compliant = len(violations) == 0
        status = "PASS" if compliant else "FAIL"

        return {
            "compliant": compliant,
            "violations": violations,
            "warnings": warnings,
            "status": status
        }

    def check_sanctions(self, counterparty: str) -> bool:
        """Check if counterparty is on sanctions list."""
        return counterparty not in self.SANCTIONS_LIST

    def check_time_bar(self, days_remaining: int) -> Dict:
        """Check if time-bar is approaching."""
        if days_remaining <= 0:
            alert_level = "CRITICAL"
            message = f"LC has expired ({days_remaining} days)"
        elif days_remaining < 7:
            alert_level = "CRITICAL"
            message = f"LC expires in {days_remaining} days - URGENT"
        elif days_remaining < 14:
            alert_level = "WARNING"
            message = f"LC expires in {days_remaining} days"
        else:
            alert_level = "OK"
            message = f"LC expires in {days_remaining} days"

        return {
            "alert_level": alert_level,
            "message": message,
            "days_remaining": days_remaining
        }

    def create_hitl_workflow(self, agent_recommendation: dict) -> Dict:
        """Create HITL approval workflow structure."""
        audit_id = self._generate_audit_id()
        deadline = self._calculate_deadline(agent_recommendation)

        return {
            "id": audit_id,
            "status": "awaiting_approval",
            "agent_recommendation": agent_recommendation,
            "created_at": datetime.now().isoformat(),
            "deadline": deadline,
            "approval_options": ["APPROVE", "REJECT", "REQUEST_INFO"],
            "requires_comment": agent_recommendation.get("status") in [
                "ESCALATE_TO_MANAGER",
                "ESCALATE_TO_DIRECTOR"
            ]
        }

    def create_hitl_display_data(self, agent_recommendation: dict, contract: dict = None, invoice: dict = None, receipt: dict = None) -> Dict:
        """Create data structure optimized for HITL UI display."""
        audit_id = agent_recommendation.get("audit_id", self._generate_audit_id())

        variance_analysis = agent_recommendation.get("variance_analysis", {})
        fraud_analysis = agent_recommendation.get("fraud_analysis", {})
        anomaly_analysis = agent_recommendation.get("anomaly_analysis", {})

        comparison_rows = []
        if contract and invoice and receipt:
            comparison_rows = [
                {
                    "field": "Quantity (MT)",
                    "contract": str(contract.get("qty_mt", "N/A")),
                    "invoice": str(invoice.get("qty_mt", "N/A")),
                    "receipt": str(receipt.get("qty_mt", "N/A")),
                    "status": "✅" if abs(invoice.get("qty_mt", 0) - contract.get("qty_mt", 0)) < contract.get("qty_mt", 1) * 0.005 else "⚠️",
                    "variance": f"{variance_analysis.get('qty_variance', {}).get('variance_contract_to_invoice_pct', 0):.2f}%"
                },
                {
                    "field": "Price (USD)",
                    "contract": f"${contract.get('price_usd', 'N/A')}",
                    "invoice": f"${invoice.get('price_usd', 'N/A')}",
                    "receipt": "N/A",
                    "status": "✅" if abs(invoice.get("price_usd", 0) - contract.get("price_usd", 0)) < contract.get("price_usd", 1) * 0.005 else "⚠️",
                    "variance": f"{variance_analysis.get('price_variance', {}).get('variance_pct', 0):.2f}%"
                },
                {
                    "field": "Date",
                    "contract": contract.get("date", "N/A"),
                    "invoice": invoice.get("date", "N/A"),
                    "receipt": receipt.get("date", "N/A"),
                    "status": "✅" if variance_analysis.get('timeline_variance', {}).get('severity') == 'GREEN' else "⚠️",
                    "variance": f"{variance_analysis.get('timeline_variance', {}).get('days_diff', 0)} days"
                }
            ]

        return {
            "audit_id": audit_id,
            "agent_recommendation": {
                "status": agent_recommendation.get("status", "UNKNOWN"),
                "confidence": agent_recommendation.get("confidence", 0),
                "confidence_bar": "█" * (agent_recommendation.get("confidence", 0) // 10) + "░" * ((100 - agent_recommendation.get("confidence", 0)) // 10)
            },
            "comparison_table": {
                "headers": ["Field", "Contract", "Invoice", "Receipt", "Status", "Variance"],
                "rows": comparison_rows
            },
            "variance_summary": {
                "qty_variance_pct": variance_analysis.get('qty_variance', {}).get('variance_contract_to_invoice_pct', 0),
                "price_variance_pct": variance_analysis.get('price_variance', {}).get('variance_pct', 0),
                "timeline_days": variance_analysis.get('timeline_variance', {}).get('days_diff', 0),
                "variance_severity": variance_analysis.get('qty_variance', {}).get('severity', 'UNKNOWN')
            },
            "risk_summary": {
                "fraud_score": fraud_analysis.get('fraud_score', 0),
                "fraud_level_display": self._get_fraud_level_display(fraud_analysis.get('fraud_score', 0)),
                "anomalies_count": anomaly_analysis.get('total_anomalies', 0),
                "total_signals": fraud_analysis.get('total_signals_detected', 0) + anomaly_analysis.get('total_anomalies', 0)
            },
            "issues_for_review": self._generate_issues_list(variance_analysis, fraud_analysis, anomaly_analysis),
            "approval_guidance": {
                "decision_options": ["APPROVE", "REJECT", "REQUEST_MORE_INFO", "ESCALATE"],
                "recommended_action": agent_recommendation.get("recommendation", "UNKNOWN"),
                "if_approve": "Shipment will proceed to payment processing",
                "if_reject": "Shipment will be escalated for investigation",
                "if_request_info": "Specialist will contact you for additional details",
                "escalation_reason": f"Fraud score {fraud_analysis.get('fraud_score', 0)}/100 detected" if fraud_analysis.get('fraud_score', 0) > 50 else None
            }
        }

    def process_human_decision(self, audit_id: str, agent_recommendation: Dict, human_decision: str, human_notes: str, human_confidence: int) -> Dict:
        """Process human's decision and calculate final status."""
        agent_confidence = agent_recommendation.get("confidence", 50)

        agreement = (human_decision == "APPROVE" and agent_recommendation.get("status") == "AUTO_APPROVE") or \
                   (human_decision == "REJECT" and agent_recommendation.get("status") == "ESCALATE_TO_DIRECTOR")

        final_confidence = self.calculate_blended_confidence(agent_confidence, human_confidence, agreement)

        if human_decision == "APPROVE":
            final_status = "APPROVED"
        elif human_decision == "REJECT":
            final_status = "REJECTED"
        else:
            final_status = "PENDING_INFO"

        override_reason = None
        if not agreement:
            override_reason = f"Human {human_decision} overrides agent {agent_recommendation.get('status')}"

        self.log_human_approval(audit_id, "user", human_decision, human_notes, human_confidence)

        return {
            "audit_id": audit_id,
            "agent_recommendation": agent_recommendation.get("status", "UNKNOWN"),
            "human_decision": human_decision,
            "human_notes": human_notes,
            "human_confidence": human_confidence,
            "final_status": final_status,
            "override_reason": override_reason,
            "final_confidence": final_confidence,
            "approval_chain": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "actor": "AGENT",
                    "decision": agent_recommendation.get("status", "UNKNOWN"),
                    "confidence": agent_confidence
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "actor": "HUMAN",
                    "decision": human_decision,
                    "confidence": human_confidence
                }
            ],
            "logged_at": datetime.now().isoformat()
        }

    def calculate_blended_confidence(self, agent_confidence: int, human_confidence: int, agreement: bool) -> int:
        """Blend agent and human confidence scores."""
        if agreement:
            blended = int(0.7 * agent_confidence + 0.3 * human_confidence)
        else:
            blended = int(0.5 * agent_confidence + 0.5 * human_confidence)

        return max(0, min(100, blended))

    def generate_approval_summary(self, decision_record: dict) -> str:
        """Generate human-readable summary of decision."""
        agent_status = decision_record.get("agent_recommendation", "UNKNOWN")
        agent_conf = decision_record.get("approval_chain", [{}])[0].get("confidence", 0)
        human_decision = decision_record.get("human_decision", "UNKNOWN")
        human_conf = decision_record.get("human_confidence", 0)
        final_status = decision_record.get("final_status", "UNKNOWN")
        final_conf = decision_record.get("final_confidence", 0)

        return f"""Agent recommended {agent_status} ({agent_conf}% confidence).
Human {human_decision} ({human_conf}% confidence).
Final Status: {final_status} ({final_conf}% blended confidence)."""

    def _generate_audit_id(self) -> str:
        """Generate unique audit ID."""
        return f"AUD-{secrets.token_hex(4).upper()}"

    def _get_specialist(self, decision_type: str) -> str:
        """Get specialist email for decision type."""
        specialists = {
            "reconciliation": "specialist-recon@company.com",
            "lc_validation": "specialist-lc@company.com"
        }
        return specialists.get(decision_type, "specialist@company.com")

    def _get_manager(self, decision_type: str) -> str:
        """Get manager email for decision type."""
        managers = {
            "reconciliation": "manager-recon@company.com",
            "lc_validation": "manager-lc@company.com"
        }
        return managers.get(decision_type, "manager@company.com")

    def _get_director(self, decision_type: str) -> str:
        """Get director email."""
        return "director@company.com"

    def _calculate_deadline(self, recommendation: dict) -> str:
        """Calculate deadline based on urgency."""
        urgency = recommendation.get("routing", {}).get("urgency", "MEDIUM")

        if urgency == "CRITICAL":
            deadline_dt = datetime.now() + timedelta(hours=1)
        elif urgency == "HIGH":
            deadline_dt = datetime.now() + timedelta(hours=2)
        elif urgency == "MEDIUM":
            deadline_dt = datetime.now() + timedelta(hours=24)
        else:
            deadline_dt = datetime.now() + timedelta(days=7)

        return deadline_dt.isoformat()

    def _get_fraud_level_display(self, fraud_score: int) -> str:
        """Get fraud level display with emoji."""
        if fraud_score < 25:
            return "🟢 LOW"
        elif fraud_score < 50:
            return "🟡 MEDIUM"
        elif fraud_score < 75:
            return "🟠 HIGH"
        else:
            return "🔴 CRITICAL"

    def _generate_issues_list(self, variance_analysis: Dict, fraud_analysis: Dict, anomaly_analysis: Dict) -> List[Dict]:
        """Generate list of issues for human review."""
        issues = []

        qty_var = variance_analysis.get('qty_variance', {})
        if qty_var.get('severity') in ['ORANGE', 'RED']:
            issues.append({
                "issue_title": "Quantity Variance",
                "issue_description": f"{qty_var.get('variance_contract_to_invoice_pct', 0):.2f}% variance between contract and invoice",
                "severity": qty_var.get('severity'),
                "impact": "Potential loss due to quantity discrepancy",
                "requires_action": True,
                "suggested_action": "Verify with warehouse or supplier"
            })

        if fraud_analysis.get('signals_detected'):
            for signal in fraud_analysis['signals_detected']:
                issues.append({
                    "issue_title": signal.get('signal_type', 'Unknown'),
                    "issue_description": signal.get('message', ''),
                    "severity": signal.get('severity'),
                    "impact": f"${signal.get('financial_exposure_usd', 0):,.2f} at risk",
                    "requires_action": True,
                    "suggested_action": "Investigate immediately"
                })

        if anomaly_analysis.get('anomalies_detected'):
            for anomaly in anomaly_analysis['anomalies_detected'][:3]:
                issues.append({
                    "issue_title": anomaly.get('anomaly_type', 'Unknown'),
                    "issue_description": anomaly.get('description', ''),
                    "severity": anomaly.get('severity'),
                    "impact": "Logical inconsistency detected",
                    "requires_action": anomaly.get('severity') in ['HIGH', 'CRITICAL'],
                    "suggested_action": "Request clarification from supplier"
                })

        return issues
