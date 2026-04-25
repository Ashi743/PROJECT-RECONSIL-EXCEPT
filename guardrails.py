import secrets
from datetime import datetime, timedelta
from typing import Dict, List


class Guardrails:
    """Implements 5 guardrails for safe agent operations."""

    SANCTIONS_LIST = ["Iran Inc", "Syria Corp", "North Korea Ltd", "Cuban Export"]

    def __init__(self, database):
        """
        Initialize guardrails.

        Args:
            database: Database instance for audit logging
        """
        self.database = database

    def route_by_confidence(self, confidence: int, decision_type: str) -> Dict:
        """
        Route decisions based on confidence score (Guardrail 1).

        Args:
            confidence: Confidence score (0-100)
            decision_type: Type of decision (reconciliation | lc_validation)

        Returns:
            Dict with routing action, owner, deadline, and urgency
        """
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
        """
        Log agent decision to audit trail (delegates to database).

        Args:
            agent_name: Name of agent
            decision: Decision dict
            confidence: Confidence score
            reasoning: Reasoning text

        Returns:
            audit_id
        """
        return self.database.log_agent_decision(agent_name, decision, confidence, reasoning)

    def log_human_approval(self, audit_id: str, approver: str, decision: str, notes: str, confidence: int) -> None:
        """
        Log human approval decision.

        Args:
            audit_id: Reference to agent decision
            approver: Approver name
            decision: APPROVE | REJECT | REQUEST_INFO
            notes: Human notes
            confidence: Human confidence (0-100)
        """
        self.database.log_human_approval(audit_id, approver, decision, notes, confidence)

    def mask_for_display(self, data: dict, user_role: str) -> dict:
        """
        Mask sensitive fields based on user role (Guardrail 3).

        Roles:
        - viewer: minimal info
        - analyst: essentials, masked details
        - manager: most fields, partial masking
        - compliance: full access

        Args:
            data: Data dict to mask
            user_role: User's role

        Returns:
            Masked data dict
        """
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
                    elif isinstance(masked.get("lc_amount"), (int, float)):
                        masked["lc_amount"] = f"₹{masked['lc_amount'] / 10_000_000:.2f}Cr"
        elif user_role == "manager":
            for field in sensitive_fields:
                if field == "counterparty_name" and isinstance(masked[field], str) and len(masked[field]) > 6:
                    name = masked[field]
                    masked[field] = f"{name[:3]}...{name[-3:]}"
                elif field in ["bank_details", "account_numbers"]:
                    masked[field] = "***REDACTED***"
        elif user_role == "compliance":
            pass
        else:
            pass

        return masked

    def check_ucp600_compliance(self, lc_data: dict) -> Dict:
        """
        Check LC against UCP 600 standards (Guardrail 4).

        Checks:
        1. Negotiability
        2. Time-bar (expiry)
        3. Amount
        4. Sanctions
        5. Incoterm alignment

        Args:
            lc_data: LC data dict

        Returns:
            Dict with compliance status, violations, and warnings
        """
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
        """
        Check if counterparty is on sanctions list.

        Args:
            counterparty: Counterparty name

        Returns:
            True if safe, False if sanctioned
        """
        return counterparty not in self.SANCTIONS_LIST

    def check_time_bar(self, days_remaining: int) -> Dict:
        """
        Check if time-bar is approaching.

        Args:
            days_remaining: Days until expiry

        Returns:
            Dict with alert level and message
        """
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
        """
        Create HITL approval workflow structure (Guardrail 5).

        Args:
            agent_recommendation: Agent's recommendation dict

        Returns:
            HITL workflow structure
        """
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

    def _generate_audit_id(self) -> str:
        """Generate unique audit ID (AUD-{8_char_hex})."""
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
