import json
from typing import Dict, List
from openai import OpenAI


MOCK_SCENARIOS = {
    "perfect_match": {
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"}
    },
    "minor_variance": {
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 101, "price_usd": 498, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"}
    },
    "major_variance": {
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 105, "price_usd": 480, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"}
    },
    "fraud_signal": {
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 110, "price_usd": 450, "date": "2024-04-15"},
        "receipt": {"qty_mt": 100, "date": "2024-04-10"}
    },
    "qty_mismatch": {
        "contract": {"qty_mt": 100, "price_usd": 500, "date": "2024-04-01"},
        "invoice": {"qty_mt": 102, "price_usd": 500, "date": "2024-04-15"},
        "receipt": {"qty_mt": 98, "date": "2024-04-10"}
    }
}


class ReconciliationAgent:
    """3-way reconciliation agent (contract ↔ invoice ↔ receipt) with fraud detection."""

    def __init__(self, openai_api_key: str, database, guardrails):
        """
        Initialize Reconciliation Agent.

        Args:
            openai_api_key: OpenAI API key
            database: Database instance
            guardrails: Guardrails instance
        """
        self.openai_api_key = openai_api_key
        self.database = database
        self.guardrails = guardrails
        self.client = OpenAI(api_key=openai_api_key)

    def reconcile(self, contract: dict, invoice: dict, receipt: dict) -> Dict:
        """
        Perform 3-way reconciliation with fraud detection.

        Args:
            contract: Contract data
            invoice: Invoice data
            receipt: Receipt data

        Returns:
            Dict with reconciliation results, confidence, routing, and audit_id
        """
        matches = {}
        matches["qty_match"] = self.check_qty_match(contract, invoice, receipt)
        matches["price_match"] = self.check_price_match(contract, invoice)
        matches["timeline_match"] = self.check_timeline(invoice, receipt)

        anomalies = self.detect_anomalies(contract, invoice, receipt)
        confidence = self.calculate_confidence(matches, anomalies)

        routing = self.guardrails.route_by_confidence(confidence, "reconciliation")

        reasoning = self._build_reasoning(matches, anomalies)

        decision = {
            "status": routing["action"],
            "confidence": confidence,
            "matches": matches,
            "anomalies": anomalies,
            "routing": routing
        }

        audit_id = self.guardrails.log_agent_decision(
            agent_name="reconciliation_agent",
            decision=decision,
            confidence=confidence,
            reasoning=reasoning
        )

        financial_impact = self._calculate_financial_impact(contract, invoice, receipt)

        return {
            "status": routing["action"],
            "confidence": confidence,
            "matches": matches,
            "anomalies": anomalies,
            "routing": routing,
            "audit_id": audit_id,
            "reasoning": reasoning,
            "financial_impact": financial_impact
        }

    def check_qty_match(self, contract: dict, invoice: dict, receipt: dict) -> Dict:
        """
        Check quantity matching across 3 documents.

        Variance Rules:
        - < 0.5%: GREEN (perfect)
        - 0.5-2%: YELLOW (acceptable, -15 confidence)
        - > 2%: RED (review, -40 confidence)

        Args:
            contract: Contract data
            invoice: Invoice data
            receipt: Receipt data

        Returns:
            Dict with match status and confidence penalty
        """
        contract_qty = contract.get("qty_mt", 0)
        invoice_qty = invoice.get("qty_mt", 0)
        receipt_qty = receipt.get("qty_mt", 0)

        if contract_qty == 0:
            return {
                "status": "RED",
                "contract_qty": contract_qty,
                "invoice_qty": invoice_qty,
                "receipt_qty": receipt_qty,
                "variance_pct": 0,
                "message": "Contract qty is 0",
                "confidence_penalty": 100
            }

        variance_pct = abs(invoice_qty - contract_qty) / contract_qty * 100

        if variance_pct < 0.5:
            status = "GREEN"
            penalty = 0
            message = "Perfect qty match"
        elif variance_pct <= 2:
            status = "YELLOW"
            penalty = 15
            message = f"Qty variance {variance_pct:.2f}% (acceptable)"
        else:
            status = "RED"
            penalty = 40
            message = f"Qty variance {variance_pct:.2f}% (exceeds 2%)"

        return {
            "status": status,
            "contract_qty": contract_qty,
            "invoice_qty": invoice_qty,
            "receipt_qty": receipt_qty,
            "variance_pct": variance_pct,
            "message": message,
            "confidence_penalty": penalty
        }

    def check_price_match(self, contract: dict, invoice: dict) -> Dict:
        """
        Check price matching.

        Variance Rules:
        - < 0.5%: GREEN
        - 0.5-1%: YELLOW (-15 confidence)
        - > 1%: RED (-40 confidence)

        Args:
            contract: Contract data
            invoice: Invoice data

        Returns:
            Dict with match status and confidence penalty
        """
        contract_price = contract.get("price_usd", 0)
        invoice_price = invoice.get("price_usd", 0)

        if contract_price == 0:
            return {
                "status": "RED",
                "contract_price": contract_price,
                "invoice_price": invoice_price,
                "variance_pct": 0,
                "message": "Contract price is 0",
                "confidence_penalty": 100
            }

        variance_pct = abs(invoice_price - contract_price) / contract_price * 100

        if variance_pct < 0.5:
            status = "GREEN"
            penalty = 0
            message = "Perfect price match"
        elif variance_pct <= 1:
            status = "YELLOW"
            penalty = 15
            message = f"Price variance {variance_pct:.2f}% (acceptable)"
        else:
            status = "RED"
            penalty = 40
            message = f"Price variance {variance_pct:.2f}% (exceeds 1%)"

        return {
            "status": status,
            "contract_price": contract_price,
            "invoice_price": invoice_price,
            "variance_pct": variance_pct,
            "message": message,
            "confidence_penalty": penalty
        }

    def check_timeline(self, invoice: dict, receipt: dict) -> Dict:
        """
        Check timeline (invoice should be after receipt).

        Rules:
        - Invoice date <= 5 days after receipt: GREEN
        - 5-10 days: YELLOW (-10 confidence)
        - > 10 days: RED (-20 confidence)

        Args:
            invoice: Invoice data
            receipt: Receipt data

        Returns:
            Dict with timeline status and penalty
        """
        from datetime import datetime

        invoice_date_str = invoice.get("date", "")
        receipt_date_str = receipt.get("date", "")

        try:
            invoice_date = datetime.strptime(invoice_date_str, "%Y-%m-%d")
            receipt_date = datetime.strptime(receipt_date_str, "%Y-%m-%d")
            days_diff = (invoice_date - receipt_date).days
        except ValueError:
            return {
                "status": "RED",
                "invoice_date": invoice_date_str,
                "receipt_date": receipt_date_str,
                "days_diff": 0,
                "message": "Invalid date format",
                "confidence_penalty": 20
            }

        if days_diff < 0:
            return {
                "status": "RED",
                "invoice_date": invoice_date_str,
                "receipt_date": receipt_date_str,
                "days_diff": days_diff,
                "message": "Invoice date is before receipt date (impossible)",
                "confidence_penalty": 40
            }

        if days_diff <= 5:
            status = "GREEN"
            penalty = 0
            message = f"Invoice {days_diff} days after receipt (normal)"
        elif days_diff <= 10:
            status = "YELLOW"
            penalty = 10
            message = f"Invoice {days_diff} days after receipt (acceptable)"
        else:
            status = "RED"
            penalty = 20
            message = f"Invoice {days_diff} days after receipt (delayed)"

        return {
            "status": status,
            "invoice_date": invoice_date_str,
            "receipt_date": receipt_date_str,
            "days_diff": days_diff,
            "message": message,
            "confidence_penalty": penalty
        }

    def detect_anomalies(self, contract: dict, invoice: dict, receipt: dict) -> List[Dict]:
        """
        Detect fraud signals and anomalies.

        Anomalies:
        1. QTY_MISMATCH: Invoice qty != receipt qty
        2. PRICE_REDUCTION: Invoice price < contract price
        3. QTY_INCREASE: Invoice qty > contract qty
        4. SUSPICIOUS_COMBO: Price reduction + extra qty (fraud signal)
        5. TIMELINE_GAP: Invoice > 10 days after receipt

        Args:
            contract: Contract data
            invoice: Invoice data
            receipt: Receipt data

        Returns:
            List of detected anomalies
        """
        anomalies = []

        contract_qty = contract.get("qty_mt", 0)
        invoice_qty = invoice.get("qty_mt", 0)
        receipt_qty = receipt.get("qty_mt", 0)
        contract_price = contract.get("price_usd", 0)
        invoice_price = invoice.get("price_usd", 0)

        if invoice_qty != receipt_qty:
            anomalies.append({
                "type": "QTY_MISMATCH",
                "severity": "HIGH",
                "message": f"Invoice qty ({invoice_qty}) != receipt qty ({receipt_qty})",
                "confidence_penalty": 20,
                "financial_impact": abs(invoice_qty - receipt_qty) * invoice_price
            })

        if invoice_price < contract_price:
            price_reduction_pct = (contract_price - invoice_price) / contract_price * 100
            anomalies.append({
                "type": "PRICE_REDUCTION",
                "severity": "MEDIUM",
                "message": f"Invoice price reduced by {price_reduction_pct:.2f}%",
                "confidence_penalty": 10,
                "financial_impact": (contract_price - invoice_price) * invoice_qty
            })

        if invoice_qty > contract_qty:
            qty_increase = invoice_qty - contract_qty
            anomalies.append({
                "type": "QTY_INCREASE",
                "severity": "MEDIUM",
                "message": f"Invoice qty ({invoice_qty}) exceeds contract ({contract_qty}) by {qty_increase}",
                "confidence_penalty": 15,
                "financial_impact": qty_increase * invoice_price
            })

        if invoice_price < contract_price and invoice_qty > contract_qty:
            anomalies.append({
                "type": "SUSPICIOUS_COMBO",
                "severity": "CRITICAL",
                "message": "Price reduction + extra qty together (fraud signal)",
                "confidence_penalty": 30,
                "financial_impact": (contract_price - invoice_price) * invoice_qty + (invoice_qty - contract_qty) * invoice_price
            })

        from datetime import datetime
        try:
            invoice_date = datetime.strptime(invoice.get("date", ""), "%Y-%m-%d")
            receipt_date = datetime.strptime(receipt.get("date", ""), "%Y-%m-%d")
            days_diff = (invoice_date - receipt_date).days
            if days_diff > 10:
                anomalies.append({
                    "type": "TIMELINE_GAP",
                    "severity": "MEDIUM",
                    "message": f"Invoice {days_diff} days after receipt (delayed)",
                    "confidence_penalty": 10,
                    "financial_impact": 0
                })
        except ValueError:
            pass

        return anomalies

    def calculate_confidence(self, matches: dict, anomalies: list) -> int:
        """
        Calculate overall confidence score.

        Scoring:
        - Start at 100
        - Apply penalties from matches
        - Apply penalties from anomalies
        - Floor at 0, ceiling at 100

        Args:
            matches: Match results dict
            anomalies: Anomalies list

        Returns:
            Confidence score (0-100)
        """
        confidence = 100

        for match_type, match_data in matches.items():
            confidence -= match_data.get("confidence_penalty", 0)

        for anomaly in anomalies:
            confidence -= anomaly.get("confidence_penalty", 0)

        return max(0, min(100, confidence))

    def use_gpt_for_edge_case(self, contract: dict, invoice: dict, receipt: dict, anomalies: list) -> str:
        """
        Use GPT-4o for complex reasoning on edge cases.

        Only call GPT if:
        - Confidence is 60-80%
        - Multiple anomalies
        - Unusual patterns

        Args:
            contract: Contract data
            invoice: Invoice data
            receipt: Receipt data
            anomalies: Detected anomalies

        Returns:
            GPT's reasoning
        """
        try:
            prompt = f"""You are a trade finance expert. Analyze this reconciliation edge case and provide a brief recommendation.

Contract: {json.dumps(contract, indent=2)}
Invoice: {json.dumps(invoice, indent=2)}
Receipt: {json.dumps(receipt, indent=2)}
Anomalies Detected: {json.dumps(anomalies, indent=2)}

Provide a JSON response with:
- "assessment": brief assessment
- "risk_level": LOW | MEDIUM | HIGH | CRITICAL
- "recommendation": APPROVE | ROUTE_TO_SPECIALIST | ESCALATE | REJECT
"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a trade finance expert. Analyze reconciliation data."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("assessment", "Unable to generate assessment")
        except Exception as e:
            return f"Error generating GPT assessment: {str(e)}"

    def _build_reasoning(self, matches: dict, anomalies: list) -> str:
        """Build human-readable reasoning string."""
        parts = []

        qty_match = matches.get("qty_match", {})
        if qty_match.get("status") == "GREEN":
            parts.append("✓ Quantity match OK")
        else:
            parts.append(f"⚠ Qty issue: {qty_match.get('message')}")

        price_match = matches.get("price_match", {})
        if price_match.get("status") == "GREEN":
            parts.append("✓ Price match OK")
        else:
            parts.append(f"⚠ Price issue: {price_match.get('message')}")

        timeline_match = matches.get("timeline_match", {})
        if timeline_match.get("status") == "GREEN":
            parts.append("✓ Timeline OK")
        else:
            parts.append(f"⚠ Timeline issue: {timeline_match.get('message')}")

        if anomalies:
            parts.append(f"⚠ {len(anomalies)} anomaly/anomalies detected")
            for anomaly in anomalies:
                parts.append(f"  - {anomaly['type']}: {anomaly['message']}")

        return "; ".join(parts)

    def _calculate_financial_impact(self, contract: dict, invoice: dict, receipt: dict) -> float:
        """Calculate financial impact of discrepancies."""
        impact = 0

        contract_qty = contract.get("qty_mt", 0)
        invoice_qty = invoice.get("qty_mt", 0)
        contract_price = contract.get("price_usd", 0)
        invoice_price = invoice.get("price_usd", 0)

        if invoice_qty != contract_qty:
            impact += abs(invoice_qty - contract_qty) * invoice_price

        if invoice_price != contract_price:
            impact += abs(invoice_price - contract_price) * invoice_qty

        return impact
