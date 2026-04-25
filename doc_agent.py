import json
from typing import Dict
from datetime import datetime, timedelta
from openai import OpenAI


class LCDocAgent:
    """LC (Letter of Credit) validation agent using GPT-4o."""

    def __init__(self, openai_api_key: str, database, guardrails):
        """
        Initialize LC Doc Agent.

        Args:
            openai_api_key: OpenAI API key
            database: Database instance
            guardrails: Guardrails instance
        """
        self.openai_api_key = openai_api_key
        self.database = database
        self.guardrails = guardrails
        self.client = OpenAI(api_key=openai_api_key)

    def validate_lc(self, lc_text: str, contract_terms: dict) -> Dict:
        """
        Validate LC document against contract terms using GPT-4o.

        Args:
            lc_text: Full LC document text
            contract_terms: Contract terms dict with amount, incoterm, etc.

        Returns:
            Dict with validation results, confidence, routing, and audit_id
        """
        lc_fields = self.extract_lc_fields(lc_text)

        lc_id = lc_fields.get("lc_id", "LC-UNKNOWN")
        metadata = {
            "lc_id": lc_id,
            "date": lc_fields.get("issue_date", ""),
            "counterparty": lc_fields.get("beneficiary", ""),
            "amount": float(lc_fields.get("lc_amount", 0))
        }
        self.database.add_lc_to_vectordb(lc_text, lc_id, metadata)

        comparison = self.compare_lc_to_contract(lc_fields, contract_terms)

        lc_data_for_compliance = {
            **lc_fields,
            **contract_terms,
            "invoice_amount": contract_terms.get("amount", 0)
        }
        compliance_check = self.guardrails.check_ucp600_compliance(lc_data_for_compliance)

        confidence = self.calculate_lc_confidence(comparison, compliance_check)

        routing = self.guardrails.route_by_confidence(confidence, "lc_validation")

        reasoning = self._build_lc_reasoning(comparison, compliance_check)

        decision = {
            "status": routing["action"],
            "lc_id": lc_id,
            "confidence": confidence,
            "extracted_fields": lc_fields,
            "comparison_results": comparison,
            "compliance_check": compliance_check,
            "routing": routing
        }

        audit_id = self.guardrails.log_agent_decision(
            agent_name="doc_agent",
            decision=decision,
            confidence=confidence,
            reasoning=reasoning
        )

        return {
            "lc_id": lc_id,
            "status": routing["action"],
            "confidence": confidence,
            "extracted_fields": lc_fields,
            "comparison_results": comparison,
            "compliance_check": compliance_check,
            "routing": routing,
            "audit_id": audit_id,
            "reasoning": reasoning
        }

    def extract_lc_fields(self, lc_text: str) -> Dict:
        """
        Use GPT-4o to extract structured fields from LC text.

        Args:
            lc_text: Full LC document text

        Returns:
            Dict with extracted fields
        """
        try:
            prompt = f"""Extract all key fields from this Letter of Credit. Return as JSON.

Fields to extract:
- lc_id: LC number/identifier
- lc_amount: Amount (as number)
- currency: Currency code (USD, EUR, etc.)
- expiry_date: Expiry date (YYYY-MM-DD format)
- days_to_expiry: Days until expiry (calculate from today)
- negotiability: NEGOTIABLE or NOT_NEGOTIABLE
- incoterm: Incoterm (FOB, CIF, CFR, EXW, etc.)
- beneficiary: Beneficiary name
- applicant: Applicant/Buyer name
- issuing_bank: Issuing bank name
- issue_date: Issue date
- key_clauses: List of important conditions/clauses

LC Text:
{lc_text}

Return valid JSON with all fields. If a field cannot be found, set to null or empty string for strings, 0 for numbers, [] for lists."""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in Letter of Credit documents. Extract structured data accurately."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            result = json.loads(response.choices[0].message.content)

            if result.get("days_to_expiry") is None and result.get("expiry_date"):
                try:
                    expiry_date = datetime.strptime(result["expiry_date"], "%Y-%m-%d")
                    days_to_expiry = (expiry_date - datetime.now()).days
                    result["days_to_expiry"] = days_to_expiry
                except:
                    result["days_to_expiry"] = 0

            return result
        except Exception as e:
            print(f"Error extracting LC fields: {e}")
            return {
                "lc_id": "ERROR",
                "lc_amount": 0,
                "currency": "",
                "expiry_date": "",
                "days_to_expiry": 0,
                "negotiability": "",
                "incoterm": "",
                "beneficiary": "",
                "applicant": "",
                "issuing_bank": "",
                "issue_date": "",
                "key_clauses": []
            }

    def compare_lc_to_contract(self, lc_fields: dict, contract_terms: dict) -> Dict:
        """
        Compare LC fields to contract terms.

        Checks:
        - Amount: LC >= contract amount (allow 10% variance)
        - Incoterm: LC incoterm == contract incoterm
        - Expiry: Days to expiry > 7
        - Negotiability: LC negotiability matches requirement

        Args:
            lc_fields: Extracted LC fields
            contract_terms: Contract terms dict

        Returns:
            Dict with comparison results
        """
        results = {}

        lc_amount = lc_fields.get("lc_amount", 0)
        contract_amount = contract_terms.get("amount", 0)

        if lc_amount >= contract_amount * 0.9:
            results["amount_match"] = {
                "status": "PASS",
                "message": f"LC amount ({lc_amount}) meets contract requirement ({contract_amount})"
            }
        elif lc_amount >= contract_amount * 0.85:
            results["amount_match"] = {
                "status": "WARNING",
                "message": f"LC amount ({lc_amount}) slightly below contract ({contract_amount})"
            }
        else:
            results["amount_match"] = {
                "status": "FAIL",
                "message": f"LC amount ({lc_amount}) below contract ({contract_amount})"
            }

        lc_incoterm = str(lc_fields.get("incoterm", "")).upper()
        contract_incoterm = str(contract_terms.get("incoterm", "")).upper()

        if lc_incoterm == contract_incoterm:
            results["incoterm_match"] = {
                "status": "PASS",
                "message": f"Incoterm match: {lc_incoterm}"
            }
        else:
            results["incoterm_match"] = {
                "status": "FAIL",
                "message": f"Incoterm mismatch: LC={lc_incoterm}, Contract={contract_incoterm}"
            }

        days_to_expiry = lc_fields.get("days_to_expiry", 0)
        if days_to_expiry > 7:
            results["expiry_safe"] = {
                "status": "PASS",
                "message": f"LC expires in {days_to_expiry} days (safe)"
            }
        elif days_to_expiry > 0:
            results["expiry_safe"] = {
                "status": "WARNING",
                "message": f"LC expires in {days_to_expiry} days (less than 7)"
            }
        else:
            results["expiry_safe"] = {
                "status": "FAIL",
                "message": f"LC has expired ({days_to_expiry} days)"
            }

        lc_negotiable = str(lc_fields.get("negotiability", "")).upper() == "NEGOTIABLE"
        requires_negotiable = contract_terms.get("requires_negotiation", False)

        if lc_negotiable == requires_negotiable:
            results["negotiability_match"] = {
                "status": "PASS",
                "message": f"Negotiability match: {lc_fields.get('negotiability')}"
            }
        else:
            results["negotiability_match"] = {
                "status": "FAIL",
                "message": f"Negotiability mismatch: LC={lc_fields.get('negotiability')}, Requires={requires_negotiable}"
            }

        overall_status = "PASS" if all(
            r.get("status") in ["PASS", "WARNING"] for r in results.values()
        ) else "FAIL"

        results["overall_status"] = overall_status

        return results

    def calculate_lc_confidence(self, comparison: dict, compliance: dict) -> int:
        """
        Calculate confidence score based on comparison and compliance.

        Scoring:
        - Start at 100
        - Each FAIL: -40
        - Each WARNING: -15
        - Each compliance violation: -30
        - Each compliance warning: -10

        Args:
            comparison: Comparison results
            compliance: Compliance check results

        Returns:
            Confidence score (0-100)
        """
        confidence = 100

        for key, result in comparison.items():
            if key == "overall_status":
                continue
            if result.get("status") == "FAIL":
                confidence -= 40
            elif result.get("status") == "WARNING":
                confidence -= 15

        for violation in compliance.get("violations", []):
            confidence -= 30

        for warning in compliance.get("warnings", []):
            confidence -= 10

        return max(0, min(100, confidence))

    def _build_lc_reasoning(self, comparison: dict, compliance: dict) -> str:
        """Build human-readable reasoning string."""
        parts = []

        for key, result in comparison.items():
            if key == "overall_status":
                continue
            status = result.get("status", "")
            message = result.get("message", "")
            if status == "PASS":
                parts.append(f"✓ {message}")
            elif status == "WARNING":
                parts.append(f"⚠ {message}")
            else:
                parts.append(f"✗ {message}")

        if compliance.get("violations"):
            parts.append(f"✗ {len(compliance['violations'])} compliance violation(s)")
            for v in compliance["violations"]:
                parts.append(f"  - {v['message']}")

        if compliance.get("warnings"):
            parts.append(f"⚠ {len(compliance['warnings'])} compliance warning(s)")
            for w in compliance["warnings"]:
                parts.append(f"  - {w['message']}")

        return "; ".join(parts)
