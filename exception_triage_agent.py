"""
Exception Triage Agent - Automatically detects, classifies, and routes operational problems.

Capabilities:
- Classify exceptions into 4 types (SHIPMENT_DELAY, MISSING_DOCUMENT, LC_DISCREPANCY, DD_RISK)
- Assess urgency (CRITICAL, HIGH, MEDIUM, LOW)
- Route to appropriate handler team
- Generate action plans
- Calculate financial impact
- Log all decisions to audit trail
"""

import json
from datetime import datetime, timedelta
from openai import OpenAI
import uuid

EXCEPTION_TYPES = {
    "SHIPMENT_DELAY": {
        "handler": "FREIGHT_TEAM",
        "owner": "freight_specialist@agro-company.com",
        "default_deadline_hours": 4,
        "keywords": ["delay", "late", "delayed", "behind schedule", "vessel", "carrier", "shipment"],
        "description": "Shipment is delayed or vessel is behind schedule"
    },

    "MISSING_DOCUMENT": {
        "handler": "DOCS_TEAM",
        "owner": "docs_specialist@agro-company.com",
        "default_deadline_hours": 2,
        "keywords": ["missing", "document", "bol", "bill of lading", "invoice", "certificate", "bl", "missing doc"],
        "description": "Required document is missing or not yet received"
    },

    "LC_DISCREPANCY": {
        "handler": "TRADE_FINANCE_TEAM",
        "owner": "lc_specialist@agro-company.com",
        "default_deadline_hours": 24,
        "keywords": ["lc", "discrepancy", "letter of credit", "amendment", "clause", "ucp 600", "credit"],
        "description": "LC has discrepancy vs contract or invoice"
    },

    "DD_RISK": {
        "handler": "OPERATIONS_TEAM",
        "owner": "operations_mgr@agro-company.com",
        "default_deadline_hours": 2,
        "keywords": ["demurrage", "detention", "laytime", "dd", "d&d", "port", "discharge", "free time"],
        "description": "Demurrage/detention risk detected - vessel is approaching laytime expiry"
    }
}


class ExceptionTriageAgent:
    """Exception triage agent that classifies problems and routes to appropriate handlers."""

    def __init__(self, openai_api_key: str, database, guardrails):
        """Initialize Exception Triage Agent."""
        self.openai_api_key = openai_api_key
        self.database = database
        self.guardrails = guardrails
        self.client = OpenAI(api_key=openai_api_key)

    def detect_and_route(self, exception_message: str, context: dict = None) -> dict:
        """
        Main entry point: Detect exception type, assess urgency, route to handler.

        Args:
            exception_message: Natural language description of the exception
            context: Optional additional context with business details

        Returns:
            dict with exception_id, type, urgency, handler, action plan, financial impact, etc.
        """

        # STEP 1: Classify exception type
        exception_type, confidence = self.classify_exception(exception_message, context)

        # STEP 2: Assess urgency
        urgency, urgency_score = self.assess_urgency(exception_type, exception_message, context)

        # STEP 3: Route to handler
        handler_info = EXCEPTION_TYPES[exception_type]

        # STEP 4: Generate action plan
        action_plan = self.generate_action_plan(exception_type, context)

        # STEP 5: Calculate financial impact
        financial_impact = self.calculate_financial_impact(exception_type, context)

        # STEP 6: Determine deadline
        deadline_hours = self.calculate_deadline_hours(exception_type, urgency, context)
        deadline_timestamp = (datetime.now() + timedelta(hours=deadline_hours)).isoformat()

        # STEP 7: Create exception record
        exception_id = self._generate_exception_id()

        result = {
            "exception_id": exception_id,
            "exception_type": exception_type,
            "original_message": exception_message,
            "classification_confidence": confidence,
            "urgency": urgency,
            "urgency_score": urgency_score,
            "handler": handler_info["handler"],
            "owner": handler_info["owner"],
            "deadline": f"{deadline_hours} hours",
            "deadline_timestamp": deadline_timestamp,
            "action_plan": action_plan,
            "financial_impact": financial_impact,
            "notification_sent": False,
            "created_at": datetime.now().isoformat(),
            "status": "OPEN",
            "context": context or {}
        }

        # STEP 8: Log to audit trail
        audit_id = self.guardrails.log_agent_decision(
            agent_name="ExceptionTriageAgent",
            decision=result,
            confidence=confidence,
            reasoning=f"Classified as {exception_type} with {urgency} urgency. Routed to {handler_info['handler']}."
        )

        result["audit_id"] = audit_id

        # STEP 9: Save to exceptions database
        if self.database:
            self.database.save_exception(result)

        return result

    def classify_exception(self, exception_message: str, context: dict = None) -> tuple:
        """
        Classify exception into one of 4 types using keyword matching + GPT-4o.

        Returns: (exception_type: str, confidence: int)
        """

        # STEP 1: Keyword-based classification
        message_lower = exception_message.lower()

        type_scores = {}
        for exc_type, info in EXCEPTION_TYPES.items():
            matches = sum(1 for keyword in info["keywords"] if keyword in message_lower)
            type_scores[exc_type] = matches

        best_type = max(type_scores, key=type_scores.get)
        max_matches = type_scores[best_type]

        # Calculate confidence based on matches
        if max_matches >= 2:
            confidence = 90
        elif max_matches == 1:
            confidence = 65
        else:
            confidence = 40

        # STEP 2: If confidence low, use GPT-4o
        if confidence < 70:
            best_type, confidence = self._classify_with_gpt(exception_message, context)

        return best_type, confidence

    def _classify_with_gpt(self, exception_message: str, context: dict = None) -> tuple:
        """Use GPT-4o to classify exception when keywords are ambiguous."""

        prompt = f"""You are an expert trade finance operations specialist. Classify this exception into ONE of these 4 types:

1. SHIPMENT_DELAY - Vessel delayed, shipment late, carrier issues
2. MISSING_DOCUMENT - Document not received (BL, invoice, certificate)
3. LC_DISCREPANCY - Letter of Credit has discrepancy vs contract or invoice
4. DD_RISK - Demurrage/detention risk (vessel approaching laytime expiry)

Exception Message: "{exception_message}"

Additional Context: {json.dumps(context or {})}

Respond ONLY with valid JSON:
{{
    "exception_type": "SHIPMENT_DELAY" | "MISSING_DOCUMENT" | "LC_DISCREPANCY" | "DD_RISK",
    "confidence": <int 0-100>,
    "reasoning": "<brief explanation>"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert trade finance classifier. Respond ONLY with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            result = json.loads(response.choices[0].message.content)
            return result["exception_type"], result["confidence"]
        except Exception as e:
            print(f"GPT classification failed: {e}. Defaulting to SHIPMENT_DELAY")
            return "SHIPMENT_DELAY", 50

    def assess_urgency(self, exception_type: str, exception_message: str, context: dict = None) -> tuple:
        """
        Assess urgency level (CRITICAL, HIGH, MEDIUM, LOW) and urgency score (0-100).

        Returns: (urgency: str, urgency_score: int)
        """

        if exception_type == "SHIPMENT_DELAY":
            days_delayed = context.get("days_delayed", 0) if context else 0

            if days_delayed > 7:
                return "CRITICAL", 95
            elif days_delayed >= 3:
                return "HIGH", 75
            elif days_delayed >= 1:
                return "MEDIUM", 50
            else:
                return "LOW", 25

        elif exception_type == "MISSING_DOCUMENT":
            days_to_deadline = context.get("days_to_lc_deadline", 30) if context else 30

            if days_to_deadline < 3:
                return "CRITICAL", 95
            elif days_to_deadline < 7:
                return "HIGH", 75
            elif days_to_deadline < 14:
                return "MEDIUM", 50
            else:
                return "LOW", 25

        elif exception_type == "LC_DISCREPANCY":
            return "MEDIUM", 50

        elif exception_type == "DD_RISK":
            days_to_expiry = context.get("days_to_laytime_expiry", 10) if context else 10

            if days_to_expiry <= 2:
                return "CRITICAL", 95
            elif days_to_expiry <= 5:
                return "HIGH", 75
            elif days_to_expiry <= 10:
                return "MEDIUM", 50
            else:
                return "LOW", 25

        return "MEDIUM", 50

    def generate_action_plan(self, exception_type: str, context: dict = None) -> list:
        """Generate 3-5 action items based on exception type."""

        if exception_type == "SHIPMENT_DELAY":
            return [
                "1. Contact carrier immediately for updated ETA",
                "2. Calculate demurrage exposure if vessel is delayed further",
                "3. Notify customer of delay and provide revised delivery date",
                "4. Assess if laytime extension is needed",
                "5. Check if penalty clauses apply in contract"
            ]

        elif exception_type == "MISSING_DOCUMENT":
            doc_type = context.get("document_type", "document") if context else "document"
            days_to_deadline = context.get("days_to_lc_deadline", "unknown") if context else "unknown"

            return [
                f"1. Contact shipper/supplier immediately to request {doc_type}",
                "2. If urgent, arrange air courier or digital transmission",
                f"3. Notify LC issuing bank of potential delay (deadline in {days_to_deadline} days)",
                "4. Check if LC allows for electronic presentation",
                "5. Prepare amendment request if document cannot be obtained in time"
            ]

        elif exception_type == "LC_DISCREPANCY":
            return [
                "1. Review LC vs invoice/BL to identify exact discrepancy",
                "2. Contact supplier to discuss amendment or correction",
                "3. Calculate cost of LC amendment (typically $200-500)",
                "4. Assess if discrepancy can be waived by buyer",
                "5. Notify trade finance team of discrepancy and recommended action"
            ]

        elif exception_type == "DD_RISK":
            days_remaining = context.get("days_to_laytime_expiry", "unknown") if context else "unknown"
            daily_rate = context.get("daily_dd_rate", 50000) if context else 50000

            return [
                "1. Expedite discharge operations immediately",
                f"2. Monitor laytime hourly (only {days_remaining} days remaining)",
                f"3. Calculate demurrage exposure: ₹{daily_rate:,.0f}/day",
                "4. Negotiate laytime extension with counterparty if needed",
                "5. Document all delays and reasons (weather, port congestion, equipment failure)"
            ]

        return ["1. Investigate issue", "2. Take corrective action", "3. Monitor resolution"]

    def calculate_financial_impact(self, exception_type: str, context: dict = None) -> float:
        """Calculate potential financial impact (₹) of this exception if not resolved."""

        if exception_type == "SHIPMENT_DELAY":
            days_delayed = context.get("days_delayed", 0) if context else 0
            daily_dd_rate = context.get("daily_dd_rate", 50000) if context else 50000

            total_days = days_delayed + 3
            exposure = total_days * daily_dd_rate

            return exposure

        elif exception_type == "MISSING_DOCUMENT":
            lc_amount = context.get("lc_amount", 5000000) if context else 5000000
            days_to_deadline = context.get("days_to_lc_deadline", 30) if context else 30

            if days_to_deadline < 3:
                risk_factor = 0.5
            elif days_to_deadline < 7:
                risk_factor = 0.2
            else:
                risk_factor = 0.05

            exposure = lc_amount * risk_factor
            return exposure

        elif exception_type == "LC_DISCREPANCY":
            amendment_cost = 50000
            lc_amount = context.get("lc_amount", 5000000) if context else 5000000

            exposure = amendment_cost + (lc_amount * 0.1)
            return exposure

        elif exception_type == "DD_RISK":
            days_to_expiry = context.get("days_to_laytime_expiry", 10) if context else 10
            daily_dd_rate = context.get("daily_dd_rate", 50000) if context else 50000

            potential_detention_days = max(0, 5 - days_to_expiry)
            exposure = potential_detention_days * daily_dd_rate

            return exposure

        return 0.0

    def calculate_deadline_hours(self, exception_type: str, urgency: str, context: dict = None) -> int:
        """Calculate deadline in hours based on exception type and urgency."""

        default_hours = EXCEPTION_TYPES[exception_type]["default_deadline_hours"]

        if urgency == "CRITICAL":
            return max(1, default_hours // 2)
        elif urgency == "HIGH":
            return default_hours
        elif urgency == "MEDIUM":
            return int(default_hours * 1.5)
        elif urgency == "LOW":
            return default_hours * 2

        return default_hours

    def _generate_exception_id(self) -> str:
        """Generate unique exception ID."""
        return f"EXC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
