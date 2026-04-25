import json
from typing import Dict, List
from datetime import datetime
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


class VarianceCalculator:
    """Calculate variance between documents with detailed breakdown."""

    @staticmethod
    def calculate_qty_variance(contract_qty: float, invoice_qty: float, receipt_qty: float) -> Dict:
        """Calculate quantity variance with 3D analysis."""
        if contract_qty == 0:
            return {
                "contract_qty": contract_qty,
                "invoice_qty": invoice_qty,
                "receipt_qty": receipt_qty,
                "variance_contract_to_invoice_pct": 0,
                "variance_invoice_to_receipt_pct": 0,
                "variance_contract_to_receipt_pct": 0,
                "qty_matches": {"contract_vs_invoice": False, "invoice_vs_receipt": False, "contract_vs_receipt": False},
                "severity": "RED",
                "variance_classification": {"contract_to_invoice": "MAJOR", "invoice_to_receipt": "MAJOR", "contract_to_receipt": "MAJOR"}
            }

        c_to_i = (invoice_qty - contract_qty) / contract_qty * 100 if contract_qty != 0 else 0
        i_to_r = (receipt_qty - invoice_qty) / invoice_qty * 100 if invoice_qty != 0 else 0
        c_to_r = (receipt_qty - contract_qty) / contract_qty * 100 if contract_qty != 0 else 0

        def classify(variance_pct):
            if abs(variance_pct) < 0.5:
                return "PERFECT"
            elif abs(variance_pct) <= 2:
                return "MINOR"
            else:
                return "MAJOR"

        matches = {
            "contract_vs_invoice": abs(c_to_i) < 0.5,
            "invoice_vs_receipt": abs(i_to_r) < 0.5,
            "contract_vs_receipt": abs(c_to_r) < 0.5
        }

        severity = "GREEN" if all(matches.values()) else "YELLOW" if abs(c_to_i) <= 2 and abs(c_to_r) <= 2 else "ORANGE" if abs(c_to_i) <= 5 else "RED"

        return {
            "contract_qty": contract_qty,
            "invoice_qty": invoice_qty,
            "receipt_qty": receipt_qty,
            "variance_contract_to_invoice_pct": round(c_to_i, 2),
            "variance_invoice_to_receipt_pct": round(i_to_r, 2),
            "variance_contract_to_receipt_pct": round(c_to_r, 2),
            "qty_matches": matches,
            "severity": severity,
            "variance_classification": {
                "contract_to_invoice": classify(c_to_i),
                "invoice_to_receipt": classify(i_to_r),
                "contract_to_receipt": classify(c_to_r)
            }
        }

    @staticmethod
    def calculate_price_variance(contract_price: float, invoice_price: float) -> Dict:
        """Calculate price variance with detailed breakdown."""
        if contract_price == 0:
            return {
                "contract_price": contract_price,
                "invoice_price": invoice_price,
                "variance_pct": 0,
                "variance_amount": invoice_price - contract_price,
                "price_match": False,
                "direction": "UNKNOWN",
                "severity": "RED"
            }

        variance_pct = (invoice_price - contract_price) / contract_price * 100
        variance_amount = invoice_price - contract_price

        if variance_pct > 0:
            direction = "INCREASE"
        elif variance_pct < 0:
            direction = "DECREASE"
        else:
            direction = "NEUTRAL"

        severity = "GREEN" if abs(variance_pct) < 0.5 else "YELLOW" if abs(variance_pct) <= 1 else "RED"

        return {
            "contract_price": contract_price,
            "invoice_price": invoice_price,
            "variance_pct": round(variance_pct, 2),
            "variance_amount": round(variance_amount, 2),
            "price_match": abs(variance_pct) < 0.5,
            "direction": direction,
            "severity": severity
        }

    @staticmethod
    def calculate_timeline_variance(receipt_date: str, invoice_date: str) -> Dict:
        """Calculate timeline variance."""
        try:
            r_date = datetime.strptime(receipt_date, "%Y-%m-%d")
            i_date = datetime.strptime(invoice_date, "%Y-%m-%d")
            days_diff = (i_date - r_date).days
        except:
            return {
                "receipt_date": receipt_date,
                "invoice_date": invoice_date,
                "days_diff": 0,
                "timeline_status": "INVALID",
                "severity": "RED"
            }

        if days_diff < 0:
            status = "VERY_LATE"
            severity = "RED"
        elif days_diff <= 5:
            status = "NORMAL"
            severity = "GREEN"
        elif days_diff <= 10:
            status = "LATE"
            severity = "YELLOW"
        else:
            status = "VERY_LATE"
            severity = "RED"

        return {
            "receipt_date": receipt_date,
            "invoice_date": invoice_date,
            "days_diff": days_diff,
            "timeline_status": status,
            "severity": severity
        }

    @staticmethod
    def classify_variance_severity(variance_pct: float) -> tuple:
        """Classify variance severity and return penalty."""
        abs_var = abs(variance_pct)
        if abs_var < 0.5:
            return ("GREEN", 0)
        elif abs_var <= 2:
            return ("YELLOW", 15)
        elif abs_var <= 5:
            return ("ORANGE", 25)
        else:
            return ("RED", 40)


class FraudDetector:
    """Detect fraud signals through pattern recognition."""

    @staticmethod
    def detect_qty_overstatement(contract_qty: float, invoice_qty: float, receipt_qty: float) -> Dict:
        """Detect if invoice overstates quantity."""
        detected = invoice_qty > receipt_qty or invoice_qty > contract_qty * 1.05
        qty_added = max(0, invoice_qty - receipt_qty)
        pct_added = (qty_added / receipt_qty * 100) if receipt_qty > 0 else 0

        return {
            "detected": detected,
            "signal_name": "QTY_OVERSTATEMENT" if detected else None,
            "severity": "CRITICAL" if detected else None,
            "qty_added": qty_added,
            "pct_added": round(pct_added, 2),
            "financial_impact": qty_added * (invoice_qty / max(1, invoice_qty)) if invoice_qty > 0 else 0,
            "penalty": 50 if detected else 0,
            "reason": f"Invoice claims {invoice_qty} MT but receipt shows {receipt_qty} MT"
        }

    @staticmethod
    def detect_price_manipulation(contract_price: float, invoice_price: float, contract_qty: float, invoice_qty: float) -> Dict:
        """Detect suspicious price changes."""
        price_variance_pct = (invoice_price - contract_price) / contract_price * 100 if contract_price > 0 else 0
        qty_variance_pct = (invoice_qty - contract_qty) / contract_qty * 100 if contract_qty > 0 else 0

        detected = False
        signal_name = None
        severity = None
        pattern = None
        penalty = 0

        if price_variance_pct < -5 and qty_variance_pct > 2:
            detected = True
            signal_name = "SUSPICIOUS_PRICE_QTY_COMBO"
            severity = "CRITICAL"
            pattern = "PRICE_DOWN_QTY_UP"
            penalty = 50
        elif price_variance_pct < -5:
            detected = True
            signal_name = "PRICE_MANIPULATION"
            severity = "HIGH"
            pattern = "PRICE_DOWN_ONLY"
            penalty = 30
        elif price_variance_pct > 10:
            detected = True
            signal_name = "PRICE_MANIPULATION"
            severity = "HIGH"
            pattern = "PRICE_UP_ONLY"
            penalty = 20

        return {
            "detected": detected,
            "signal_name": signal_name,
            "severity": severity,
            "price_variance_pct": round(price_variance_pct, 2),
            "qty_variance_pct": round(qty_variance_pct, 2),
            "pattern": pattern,
            "financial_impact": abs(invoice_price - contract_price) * contract_qty if contract_qty > 0 else 0,
            "penalty": penalty,
            "confidence": 0.9 if detected and severity == "CRITICAL" else 0.7 if detected else 0
        }

    @staticmethod
    def detect_timeline_manipulation(contract_date: str, receipt_date: str, invoice_date: str) -> Dict:
        """Detect suspicious timeline patterns."""
        try:
            c_date = datetime.strptime(contract_date, "%Y-%m-%d")
            r_date = datetime.strptime(receipt_date, "%Y-%m-%d")
            i_date = datetime.strptime(invoice_date, "%Y-%m-%d")
        except:
            return {
                "detected": True,
                "signal_name": "INVALID_DATE_FORMAT",
                "severity": "CRITICAL",
                "issue": "Invalid date format",
                "contract_to_receipt_days": 0,
                "receipt_to_invoice_days": 0,
                "penalty": 100,
                "recommendation": "REJECT"
            }

        c_to_r_days = (r_date - c_date).days
        r_to_i_days = (i_date - r_date).days

        detected = False
        signal_name = None
        severity = None
        issue = None
        penalty = 0

        if r_to_i_days < 0:
            detected = True
            signal_name = "INVOICE_BEFORE_RECEIPT"
            severity = "CRITICAL"
            issue = f"Invoice dated {r_to_i_days} days BEFORE receipt (impossible)"
            penalty = 100
        elif r_to_i_days > 30:
            detected = True
            signal_name = "UNUSUAL_DELAY"
            severity = "HIGH"
            issue = f"Invoice {r_to_i_days} days after receipt"
            penalty = 30
        elif c_to_r_days > 30:
            detected = True
            signal_name = "SHIPMENT_DELAY"
            severity = "HIGH"
            issue = f"Receipt {c_to_r_days} days after contract"
            penalty = 20

        return {
            "detected": detected,
            "signal_name": signal_name,
            "severity": severity,
            "issue": issue,
            "contract_to_receipt_days": c_to_r_days,
            "receipt_to_invoice_days": r_to_i_days,
            "penalty": penalty,
            "recommendation": "REJECT" if detected and severity == "CRITICAL" else "ESCALATE" if detected else "APPROVE"
        }

    def detect_fraud_signals(self, contract: dict, invoice: dict, receipt: dict) -> List[Dict]:
        """Detect multiple fraud signals."""
        signals = []

        qty_overstatement = self.detect_qty_overstatement(
            contract.get("qty_mt", 0),
            invoice.get("qty_mt", 0),
            receipt.get("qty_mt", 0)
        )
        if qty_overstatement["detected"]:
            signals.append({
                "signal_type": "QTY_OVERSTATEMENT",
                "severity": qty_overstatement["severity"],
                "message": qty_overstatement["reason"],
                "confidence_penalty": qty_overstatement["penalty"],
                "financial_exposure_usd": qty_overstatement["financial_impact"],
                "pattern": "INVOICE_QTY_NOT_IN_RECEIPT"
            })

        price_manip = self.detect_price_manipulation(
            contract.get("price_usd", 0),
            invoice.get("price_usd", 0),
            contract.get("qty_mt", 0),
            invoice.get("qty_mt", 0)
        )
        if price_manip["detected"]:
            signals.append({
                "signal_type": price_manip["signal_name"],
                "severity": price_manip["severity"],
                "message": f"{price_manip['pattern']}: {price_manip['price_variance_pct']:.2f}% price variance",
                "confidence_penalty": price_manip["penalty"],
                "financial_exposure_usd": price_manip["financial_impact"],
                "pattern": price_manip["pattern"]
            })

        timeline_manip = self.detect_timeline_manipulation(
            contract.get("date", ""),
            receipt.get("date", ""),
            invoice.get("date", "")
        )
        if timeline_manip["detected"]:
            signals.append({
                "signal_type": timeline_manip["signal_name"],
                "severity": timeline_manip["severity"],
                "message": timeline_manip["issue"],
                "confidence_penalty": timeline_manip["penalty"],
                "financial_exposure_usd": 0,
                "pattern": timeline_manip["signal_name"]
            })

        return signals

    def calculate_overall_fraud_score(self, fraud_signals: List[Dict]) -> Dict:
        """Calculate composite fraud score."""
        if not fraud_signals:
            return {
                "fraud_score": 0,
                "risk_level": "LOW",
                "total_signals_detected": 0,
                "critical_count": 0,
                "high_count": 0,
                "recommendation": "APPROVE"
            }

        base_score = 0
        critical_count = sum(1 for s in fraud_signals if s["severity"] == "CRITICAL")
        high_count = sum(1 for s in fraud_signals if s["severity"] == "HIGH")

        for signal in fraud_signals:
            if signal["severity"] == "CRITICAL":
                base_score += 30
            elif signal["severity"] == "HIGH":
                base_score += 15
            elif signal["severity"] == "MEDIUM":
                base_score += 8
            else:
                base_score += 3

        fraud_score = min(100, base_score)

        if fraud_score >= 75:
            risk_level = "CRITICAL"
            recommendation = "REJECT"
        elif fraud_score >= 50:
            risk_level = "HIGH"
            recommendation = "ESCALATE"
        elif fraud_score >= 25:
            risk_level = "MEDIUM"
            recommendation = "ESCALATE_TO_SPECIALIST"
        else:
            risk_level = "LOW"
            recommendation = "APPROVE"

        return {
            "fraud_score": fraud_score,
            "risk_level": risk_level,
            "total_signals_detected": len(fraud_signals),
            "critical_count": critical_count,
            "high_count": high_count,
            "recommendation": recommendation
        }


class AnomalyDetector:
    """Detect statistical and logical anomalies."""

    @staticmethod
    def detect_qty_mismatch_patterns(contract_qty: float, invoice_qty: float, receipt_qty: float) -> List[Dict]:
        """Detect various qty mismatch patterns."""
        anomalies = []

        if invoice_qty != receipt_qty:
            anomalies.append({
                "anomaly_type": "INVOICE_QTY_NOT_IN_RECEIPT",
                "pattern": f"Invoice {invoice_qty} ≠ Receipt {receipt_qty}",
                "description": "Items counted differently between invoice and receipt",
                "severity": "HIGH" if abs(invoice_qty - receipt_qty) > contract_qty * 0.05 else "MEDIUM",
                "confidence": 0.95,
                "penalty": 30 if abs(invoice_qty - receipt_qty) > contract_qty * 0.05 else 15
            })

        if contract_qty != invoice_qty:
            anomalies.append({
                "anomaly_type": "CONTRACT_INVOICE_MISMATCH",
                "pattern": f"Contract {contract_qty} ≠ Invoice {invoice_qty}",
                "description": "Order changed without approval",
                "severity": "HIGH",
                "confidence": 0.9,
                "penalty": 25
            })

        if contract_qty != receipt_qty:
            anomalies.append({
                "anomaly_type": "CONTRACT_RECEIPT_MISMATCH",
                "pattern": f"Contract {contract_qty} ≠ Receipt {receipt_qty}",
                "description": "Received quantity differs from order",
                "severity": "HIGH" if abs(receipt_qty - contract_qty) > contract_qty * 0.05 else "MEDIUM",
                "confidence": 0.85,
                "penalty": 20
            })

        return anomalies

    @staticmethod
    def detect_price_anomalies(contract_price: float, invoice_price: float, contract_qty: float) -> List[Dict]:
        """Detect price-related anomalies."""
        anomalies = []

        if contract_price > 0:
            price_ratio = invoice_price / contract_price

            if price_ratio < 0.7:
                anomalies.append({
                    "anomaly_type": "PRICE_TOO_LOW",
                    "pattern": f"Invoice price {invoice_price} < 70% of contract {contract_price * 0.7:.2f}",
                    "description": "Possible counterfeit goods or dumping",
                    "severity": "HIGH",
                    "confidence": 0.8,
                    "penalty": 30
                })

            if price_ratio > 1.3:
                anomalies.append({
                    "anomaly_type": "PRICE_TOO_HIGH",
                    "pattern": f"Invoice price {invoice_price} > 130% of contract {contract_price * 1.3:.2f}",
                    "description": "Possible overcharging or quality upgrade",
                    "severity": "MEDIUM",
                    "confidence": 0.75,
                    "penalty": 15
                })

        if invoice_price == 0:
            anomalies.append({
                "anomaly_type": "ZERO_PRICE",
                "pattern": "Invoice price = 0",
                "description": "Impossible in real trade",
                "severity": "CRITICAL",
                "confidence": 0.99,
                "penalty": 50
            })

        return anomalies

    def detect_all_anomalies(self, contract: dict, invoice: dict, receipt: dict) -> List[Dict]:
        """Run all anomaly checks."""
        all_anomalies = []

        qty_anomalies = self.detect_qty_mismatch_patterns(
            contract.get("qty_mt", 0),
            invoice.get("qty_mt", 0),
            receipt.get("qty_mt", 0)
        )
        all_anomalies.extend(qty_anomalies)

        price_anomalies = self.detect_price_anomalies(
            contract.get("price_usd", 0),
            invoice.get("price_usd", 0),
            contract.get("qty_mt", 0)
        )
        all_anomalies.extend(price_anomalies)

        return all_anomalies


class ReconciliationAgent:
    """3-way reconciliation agent with enhanced variance, fraud, and anomaly detection."""

    def __init__(self, openai_api_key: str, database, guardrails):
        """Initialize Reconciliation Agent."""
        self.openai_api_key = openai_api_key
        self.database = database
        self.guardrails = guardrails
        self.client = OpenAI(api_key=openai_api_key)
        self.variance_calc = VarianceCalculator()
        self.fraud_detector = FraudDetector()
        self.anomaly_detector = AnomalyDetector()

    def reconcile(self, contract: dict, invoice: dict, receipt: dict) -> Dict:
        """Comprehensive 3-way reconciliation with variance, fraud, and anomaly detection."""

        variance_analysis = {
            "qty_variance": self.variance_calc.calculate_qty_variance(
                contract.get("qty_mt", 0),
                invoice.get("qty_mt", 0),
                receipt.get("qty_mt", 0)
            ),
            "price_variance": self.variance_calc.calculate_price_variance(
                contract.get("price_usd", 0),
                invoice.get("price_usd", 0)
            ),
            "timeline_variance": self.variance_calc.calculate_timeline_variance(
                receipt.get("date", ""),
                invoice.get("date", "")
            )
        }

        fraud_signals = self.fraud_detector.detect_fraud_signals(contract, invoice, receipt)
        fraud_analysis = self.fraud_detector.calculate_overall_fraud_score(fraud_signals)
        fraud_analysis["signals_detected"] = fraud_signals
        fraud_analysis["total_financial_exposure"] = sum(s.get("financial_exposure_usd", 0) for s in fraud_signals)

        anomalies = self.anomaly_detector.detect_all_anomalies(contract, invoice, receipt)
        anomaly_analysis = {
            "anomalies_detected": anomalies,
            "total_anomalies": len(anomalies),
            "critical_anomalies": sum(1 for a in anomalies if a.get("severity") == "CRITICAL")
        }

        confidence_breakdown = self._calculate_confidence(variance_analysis, fraud_analysis, anomaly_analysis)

        routing = self.guardrails.route_by_confidence(confidence_breakdown["final_confidence"], "reconciliation")

        reasoning = self._build_reasoning(variance_analysis, fraud_analysis, anomaly_analysis, confidence_breakdown)

        decision = {
            "status": routing["action"],
            "confidence": confidence_breakdown["final_confidence"],
            "variance_analysis": variance_analysis,
            "fraud_analysis": fraud_analysis,
            "anomaly_analysis": anomaly_analysis,
            "routing": routing
        }

        audit_id = self.guardrails.log_agent_decision(
            agent_name="reconciliation_agent",
            decision=decision,
            confidence=confidence_breakdown["final_confidence"],
            reasoning=reasoning
        )

        financial_impact = self._calculate_financial_impact(contract, invoice, receipt, anomalies)

        return {
            "audit_id": audit_id,
            "status": routing["action"],
            "confidence": confidence_breakdown["final_confidence"],
            "variance_analysis": variance_analysis,
            "fraud_analysis": fraud_analysis,
            "anomaly_analysis": anomaly_analysis,
            "routing": routing,
            "confidence_breakdown": confidence_breakdown,
            "reasoning": reasoning,
            "financial_impact": financial_impact,
            "recommendation": fraud_analysis["recommendation"],
            "created_at": datetime.now().isoformat()
        }

    def _calculate_confidence(self, variance_analysis: Dict, fraud_analysis: Dict, anomaly_analysis: Dict) -> Dict:
        """Calculate confidence score with detailed breakdown."""
        confidence = 100

        qty_var_severity, qty_penalty = self.variance_calc.classify_variance_severity(
            variance_analysis["qty_variance"]["variance_contract_to_invoice_pct"]
        )
        confidence -= qty_penalty

        price_var_severity, price_penalty = self.variance_calc.classify_variance_severity(
            variance_analysis["price_variance"]["variance_pct"]
        )
        confidence -= price_penalty

        timeline_severity = variance_analysis["timeline_variance"]["severity"]
        timeline_penalty = 0 if timeline_severity == "GREEN" else 10 if timeline_severity == "YELLOW" else 30
        confidence -= timeline_penalty

        fraud_penalty = fraud_analysis.get("critical_count", 0) * 30 + fraud_analysis.get("high_count", 0) * 15
        confidence -= fraud_penalty

        anomaly_penalty = sum(a.get("penalty", 0) for a in anomaly_analysis["anomalies_detected"])
        confidence -= anomaly_penalty

        final_confidence = max(0, min(100, confidence))

        return {
            "initial_confidence": 100,
            "qty_variance_penalty": qty_penalty,
            "price_variance_penalty": price_penalty,
            "timeline_penalty": timeline_penalty,
            "fraud_penalty": fraud_penalty,
            "anomaly_penalty": anomaly_penalty,
            "final_confidence": final_confidence
        }

    def _build_reasoning(self, variance_analysis: Dict, fraud_analysis: Dict, anomaly_analysis: Dict, confidence_breakdown: Dict) -> str:
        """Build human-readable reasoning."""
        parts = []

        qty_var = variance_analysis["qty_variance"]
        parts.append(f"Qty: {qty_var['variance_contract_to_invoice_pct']:.2f}% variance ({qty_var['severity']})")

        price_var = variance_analysis["price_variance"]
        parts.append(f"Price: {price_var['variance_pct']:.2f}% variance ({price_var['severity']})")

        timeline_var = variance_analysis["timeline_variance"]
        parts.append(f"Timeline: {timeline_var['days_diff']} days ({timeline_var['severity']})")

        fraud_score = fraud_analysis["fraud_score"]
        parts.append(f"Fraud Score: {fraud_score}/100 ({fraud_analysis['risk_level']})")

        if anomaly_analysis["anomalies_detected"]:
            parts.append(f"{len(anomaly_analysis['anomalies_detected'])} anomalies detected")

        parts.append(f"Final Confidence: {confidence_breakdown['final_confidence']}%")

        return "; ".join(parts)

    def _calculate_financial_impact(self, contract: dict, invoice: dict, receipt: dict, anomalies: List[Dict]) -> float:
        """Calculate financial impact."""
        impact = 0

        contract_qty = contract.get("qty_mt", 0)
        invoice_qty = invoice.get("qty_mt", 0)
        contract_price = contract.get("price_usd", 0)
        invoice_price = invoice.get("price_usd", 0)
        receipt_qty = receipt.get("qty_mt", 0)

        qty_impact = abs(invoice_qty - contract_qty) * invoice_price
        price_impact = abs(invoice_price - contract_price) * contract_qty
        overstatement = max(0, invoice_qty - receipt_qty) * invoice_price

        impact = qty_impact + price_impact + overstatement

        return round(impact, 2)
