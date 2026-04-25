import streamlit as st
from reconciliation_agent import ReconciliationAgent, MOCK_SCENARIOS
from doc_agent import LCDocAgent
from guardrails import Guardrails
from database import Database
import pandas as pd
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    st.error("❌ OPENAI_API_KEY not found in .env file")
    st.stop()


@st.cache_resource
def init_components():
    """Initialize database, guardrails, and agents."""
    db = Database()
    guardrails = Guardrails(db)
    recon_agent = ReconciliationAgent(openai_api_key, db, guardrails)
    lc_agent = LCDocAgent(openai_api_key, db, guardrails)
    return db, guardrails, recon_agent, lc_agent


db, guardrails, recon_agent, lc_agent = init_components()

st.set_page_config(page_title="Trade Operations AI", layout="wide")
st.title("🚀 Trade Operations Agentic Assistant")

page = st.sidebar.radio("Choose Agent:", [
    "🏠 Home",
    "📊 Reconciliation Agent",
    "📄 LC Doc Agent",
    "📋 Audit Trail",
    "📈 Dashboard"
])

if page == "🏠 Home":
    st.header("Welcome to Trade Operations AI")

    col1, col2, col3, col4 = st.columns(4)

    audit_data = db.get_audit_trail(limit=100)
    total_decisions = len(audit_data)
    auto_approvals = sum(1 for d in audit_data if d.get("status") == "approved")
    avg_confidence = sum(d.get("confidence", 0) for d in audit_data) / len(audit_data) if audit_data else 0

    col1.metric("Total Decisions", total_decisions)
    col2.metric("Auto-Approvals", f"{auto_approvals}/{total_decisions}" if total_decisions > 0 else "0")
    col3.metric("Avg Confidence", f"{avg_confidence:.0f}%")
    col4.metric("System Status", "🟢 Active")

    st.divider()
    st.markdown("### Features")
    st.markdown("""
    - ✅ **Reconciliation Agent**: 3-way match with fraud detection & anomaly detection
    - ✅ **LC Doc Agent**: Letter of Credit validation (UCP 600)
    - ✅ **Variance Analysis**: 3D variance calculations (contract↔invoice, invoice↔receipt)
    - ✅ **Fraud Detection**: 9+ fraud signals with fraud_score (0-100)
    - ✅ **Anomaly Detection**: 8+ patterns with severity levels
    - ✅ **HITL Workflow**: Human-in-the-Loop with detailed comparison tables
    - ✅ **Audit Trail**: Immutable logs of all decisions
    """)

elif page == "📊 Reconciliation Agent":
    st.header("📊 Reconciliation Agent")
    st.markdown("3-way reconciliation with advanced variance, fraud, and anomaly detection")

    st.subheader("1️⃣ Input Method")
    input_method = st.radio("Choose input method:", ["Upload CSV Files", "Paste JSON", "Choose Test Scenario"])

    contract_data = invoice_data = receipt_data = None

    if input_method == "Upload CSV Files":
        st.markdown("### Upload CSV Files")
        col1, col2, col3 = st.columns(3)

        with col1:
            contract_file = st.file_uploader("Contract CSV", key="contract_csv")
            if contract_file:
                contract_df = pd.read_csv(contract_file)
                st.write("**Contract Preview:**")
                st.dataframe(contract_df.head(3))
                contract_data = contract_df.iloc[0].to_dict()

        with col2:
            invoice_file = st.file_uploader("Invoice CSV", key="invoice_csv")
            if invoice_file:
                invoice_df = pd.read_csv(invoice_file)
                st.write("**Invoice Preview:**")
                st.dataframe(invoice_df.head(3))
                invoice_data = invoice_df.iloc[0].to_dict()

        with col3:
            receipt_file = st.file_uploader("Receipt CSV", key="receipt_csv")
            if receipt_file:
                receipt_df = pd.read_csv(receipt_file)
                st.write("**Receipt Preview:**")
                st.dataframe(receipt_df.head(3))
                receipt_data = receipt_df.iloc[0].to_dict()

    elif input_method == "Paste JSON":
        st.markdown("### Paste JSON Data")
        json_text = st.text_area("Paste JSON data:", height=200)
        if json_text:
            try:
                parsed = json.loads(json_text)
                contract_data = parsed.get("contract", {})
                invoice_data = parsed.get("invoice", {})
                receipt_data = parsed.get("receipt", {})
            except json.JSONDecodeError:
                st.error("Invalid JSON format")

    else:
        st.markdown("### Choose Test Scenario (15 Available)")
        scenario_name = st.selectbox("Select scenario:", list(MOCK_SCENARIOS.keys()))
        scenario = MOCK_SCENARIOS[scenario_name]
        contract_data = scenario["contract"]
        invoice_data = scenario["invoice"]
        receipt_data = scenario["receipt"]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**Contract:**")
            st.json(contract_data)
        with col2:
            st.write("**Invoice:**")
            st.json(invoice_data)
        with col3:
            st.write("**Receipt:**")
            st.json(receipt_data)

    if st.button("▶️ Run Reconciliation", key="run_recon"):
        if contract_data and invoice_data and receipt_data:
            with st.spinner("Running comprehensive reconciliation..."):
                result = recon_agent.reconcile(contract_data, invoice_data, receipt_data)

            st.subheader("📊 COMPREHENSIVE ANALYSIS RESULTS")

            col1, col2, col3, col4 = st.columns(4)

            status_color = {
                "AUTO_APPROVE": "🟢",
                "ROUTE_TO_SPECIALIST": "🟡",
                "ESCALATE_TO_MANAGER": "🟠",
                "ESCALATE_TO_DIRECTOR": "🔴"
            }

            col1.metric("Status", f"{status_color.get(result['status'], '❓')} {result['status']}")
            col2.metric("Confidence", f"{result['confidence']}%")
            col3.metric("Fraud Score", f"{result['fraud_analysis']['fraud_score']}/100")
            col4.metric("Anomalies", result['anomaly_analysis']['total_anomalies'])

            st.divider()

            st.subheader("📊 Variance Analysis")
            var_analysis = result['variance_analysis']

            col1, col2, col3 = st.columns(3)

            with col1:
                qty_var = var_analysis['qty_variance']
                status_icon = {"GREEN": "✅", "YELLOW": "🟡", "ORANGE": "🟠", "RED": "❌"}.get(qty_var['severity'], "❓")
                st.metric(
                    "Quantity Variance",
                    f"{qty_var['variance_contract_to_invoice_pct']:.2f}%",
                    f"{qty_var['severity']}",
                )

            with col2:
                price_var = var_analysis['price_variance']
                status_icon = {"GREEN": "✅", "YELLOW": "🟡", "RED": "❌"}.get(price_var['severity'], "❓")
                st.metric(
                    "Price Variance",
                    f"{price_var['variance_pct']:.2f}%",
                    f"{price_var['severity']}",
                )

            with col3:
                timeline_var = var_analysis['timeline_variance']
                st.metric(
                    "Timeline Gap",
                    f"{timeline_var['days_diff']} days",
                    f"{timeline_var['severity']}",
                )

            variance_df = pd.DataFrame([
                {
                    "Dimension": "Quantity (MT)",
                    "Contract": contract_data.get('qty_mt', 0),
                    "Invoice": invoice_data.get('qty_mt', 0),
                    "Receipt": receipt_data.get('qty_mt', 0),
                    "Variance %": f"{qty_var['variance_contract_to_invoice_pct']:.2f}%",
                    "Status": "✅" if qty_var['qty_matches']['contract_vs_invoice'] else "⚠️"
                },
                {
                    "Dimension": "Price (USD)",
                    "Contract": f"${contract_data.get('price_usd', 0)}",
                    "Invoice": f"${invoice_data.get('price_usd', 0)}",
                    "Receipt": "N/A",
                    "Variance %": f"{price_var['variance_pct']:.2f}%",
                    "Status": "✅" if price_var['price_match'] else "⚠️"
                },
                {
                    "Dimension": "Timeline",
                    "Contract": contract_data.get('date', 'N/A'),
                    "Invoice": invoice_data.get('date', 'N/A'),
                    "Receipt": receipt_data.get('date', 'N/A'),
                    "Variance %": f"{timeline_var['days_diff']} days",
                    "Status": "✅" if timeline_var['severity'] == 'GREEN' else "⚠️"
                }
            ])

            st.dataframe(variance_df, use_container_width=True)

            st.divider()

            st.subheader("🚨 Fraud Detection Analysis")

            fraud_data = result['fraud_analysis']
            col1, col2, col3 = st.columns(3)

            with col1:
                fraud_score = fraud_data['fraud_score']
                if fraud_score < 25:
                    color, level = "🟢", "LOW RISK"
                elif fraud_score < 50:
                    color, level = "🟡", "MEDIUM RISK"
                elif fraud_score < 75:
                    color, level = "🟠", "HIGH RISK"
                else:
                    color, level = "🔴", "CRITICAL RISK"

                st.metric("Fraud Score", f"{fraud_score}/100", level)

            with col2:
                st.metric("Signals Detected", len(fraud_data['signals_detected']))

            with col3:
                st.metric("Financial Exposure", f"${fraud_data['total_financial_exposure']:,.0f}")

            if fraud_data['signals_detected']:
                st.write("**Fraud Signals:**")
                for signal in fraud_data['signals_detected']:
                    with st.expander(f"🚩 {signal['signal_type']} ({signal['severity']})"):
                        st.write(f"**Message:** {signal['message']}")
                        st.write(f"**Severity:** {signal['severity']}")
                        st.write(f"**Financial Impact:** ${signal['financial_exposure_usd']:,.2f}")
            else:
                st.success("✅ No fraud signals detected")

            st.divider()

            st.subheader("⚠️ Anomaly Detection")

            anomaly_data = result['anomaly_analysis']

            if anomaly_data['anomalies_detected']:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Anomalies", anomaly_data['total_anomalies'])

                with col2:
                    st.metric("Critical Count", anomaly_data['critical_anomalies'])

                with col3:
                    severity_counts = {
                        "HIGH": len([a for a in anomaly_data['anomalies_detected'] if a['severity'] == "HIGH"]),
                        "MEDIUM": len([a for a in anomaly_data['anomalies_detected'] if a['severity'] == "MEDIUM"]),
                        "LOW": len([a for a in anomaly_data['anomalies_detected'] if a['severity'] == "LOW"])
                    }
                    st.metric("Distribution", f"H:{severity_counts['HIGH']} M:{severity_counts['MEDIUM']} L:{severity_counts['LOW']}")

                st.write("**Detected Anomalies:**")
                for anomaly in anomaly_data['anomalies_detected']:
                    severity_color = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
                    st.write(f"{severity_color.get(anomaly['severity'], '❓')} **{anomaly['anomaly_type']}** - {anomaly['pattern']}")
                    st.write(f"*{anomaly['description']}* (Confidence: {anomaly['confidence']:.1%})")
            else:
                st.success("✅ No anomalies detected")

            st.divider()

            st.subheader("📈 Confidence Score Breakdown")

            conf_data = result['confidence_breakdown']
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Penalties Applied:**")
                st.write(f"- Initial: **{conf_data['initial_confidence']}**")
                st.write(f"- Qty Variance: **-{conf_data['qty_variance_penalty']}**")
                st.write(f"- Price Variance: **-{conf_data['price_variance_penalty']}**")
                st.write(f"- Timeline: **-{conf_data['timeline_penalty']}**")
                st.write(f"- Fraud: **-{conf_data['fraud_penalty']}**")
                st.write(f"- Anomalies: **-{conf_data['anomaly_penalty']}**")

            with col2:
                st.write("**Final Result:**")
                st.write(f"# {conf_data['final_confidence']}%")

                if conf_data['final_confidence'] > 95:
                    st.success("✅ AUTO-APPROVE")
                elif conf_data['final_confidence'] > 80:
                    st.info("📋 Route to Specialist")
                elif conf_data['final_confidence'] > 50:
                    st.warning("⚠️ Escalate to Manager")
                else:
                    st.error("🚫 Escalate to Director / REJECT")

            st.divider()

            if result['status'] != "AUTO_APPROVE":
                st.subheader("👤 Human-in-the-Loop Approval")

                hitl_data = guardrails.create_hitl_display_data(result, contract_data, invoice_data, receipt_data)

                st.info(f"**Agent Recommendation:** {result['status']} (Confidence: {result['confidence']}%)")

                st.write("**Document Comparison:**")
                comparison_df = pd.DataFrame(hitl_data['comparison_table']['rows'])
                st.dataframe(comparison_df, use_container_width=True)

                approval_decision = st.radio("Your Decision:", ["APPROVE", "REJECT", "REQUEST_MORE_INFO"])
                approval_notes = st.text_area("Your Justification:")
                approval_confidence = st.slider("Your Confidence:", 0, 100, 80)
                approver_name = st.text_input("Your Name:", "analyst@company.com")

                if st.button("✅ Submit Decision", key="submit_recon_approval"):
                    guardrails.log_human_approval(
                        result["audit_id"],
                        approver_name,
                        approval_decision,
                        approval_notes,
                        approval_confidence
                    )
                    st.success(f"✅ Decision logged: {approval_decision}")

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="⬇️ Download Result (JSON)",
                    data=json.dumps(result, indent=2, default=str),
                    file_name=f"reconciliation_{result['audit_id']}.json",
                    mime="application/json"
                )
        else:
            st.error("❌ Please provide contract, invoice, and receipt data")

elif page == "📄 LC Doc Agent":
    st.header("📄 LC Doc Agent")
    st.markdown("Validate Letter of Credit with UCP 600 compliance checks")

    st.subheader("1️⃣ Input LC Document")
    lc_input_method = st.radio("Choose LC input method:", ["Upload TXT File", "Paste LC Text", "Use Sample LC"])

    lc_text = None

    if lc_input_method == "Upload TXT File":
        lc_file = st.file_uploader("Upload LC text file", type="txt")
        if lc_file:
            lc_text = lc_file.read().decode("utf-8")
            st.write("**LC Preview:**")
            st.text(lc_text[:500] + "..." if len(lc_text) > 500 else lc_text)

    elif lc_input_method == "Paste LC Text":
        lc_text = st.text_area("Paste LC text:", height=300)

    else:
        try:
            with open("data/sample_lc.txt", "r") as f:
                lc_text = f.read()
            st.write("**Sample LC:**")
            st.text(lc_text)
        except:
            st.warning("Sample LC file not found")

    st.subheader("2️⃣ Input Contract Terms")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Manual Entry:**")
        contract_amount = st.number_input("Contract Amount (USD):", value=50000.0, min_value=0.0)
        contract_currency = st.text_input("Currency:", "USD")
        contract_incoterm = st.selectbox("Incoterm:", ["FOB", "CIF", "CFR", "EXW", "FCA", "DDP", "CIP"])
        requires_negotiation = st.checkbox("Requires Negotiation?")

    with col2:
        contract_terms = {
            "amount": contract_amount,
            "currency": contract_currency,
            "incoterm": contract_incoterm,
            "requires_negotiation": requires_negotiation
        }
        st.write("**Contract Terms Summary:**")
        st.json(contract_terms)

    if st.button("▶️ Validate LC", key="validate_lc"):
        if lc_text:
            with st.spinner("Validating LC with GPT-4o..."):
                result = lc_agent.validate_lc(lc_text, contract_terms)

            st.subheader("📄 Validation Results")

            col1, col2, col3, col4 = st.columns(4)

            status_color = {
                "AUTO_APPROVE": "🟢",
                "ROUTE_TO_SPECIALIST": "🟡",
                "ESCALATE_TO_MANAGER": "🟠",
                "ESCALATE_TO_DIRECTOR": "🔴"
            }

            col1.metric("Status", f"{status_color.get(result['status'], '❓')} {result['status']}")
            col2.metric("Confidence", f"{result['confidence']}%")
            col3.metric("LC ID", result['lc_id'][:15] + "...")
            col4.metric("Audit ID", result['audit_id'][:8] + "...")

            st.divider()

            st.markdown("### Extracted LC Fields")

            fields = result["extracted_fields"]
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**LC Amount**: {fields.get('currency', 'USD')} {fields.get('lc_amount', 0)}")
                st.write(f"**Expiry Date**: {fields.get('expiry_date', 'N/A')}")
                st.write(f"**Days to Expiry**: {fields.get('days_to_expiry', 0)}")

            with col2:
                st.write(f"**Negotiability**: {fields.get('negotiability', 'N/A')}")
                st.write(f"**Incoterm**: {fields.get('incoterm', 'N/A')}")
                st.write(f"**Issuing Bank**: {fields.get('issuing_bank', 'N/A')}")

            with col3:
                st.write(f"**Beneficiary**: {fields.get('beneficiary', 'N/A')}")
                st.write(f"**Applicant**: {fields.get('applicant', 'N/A')}")
                st.write(f"**Issue Date**: {fields.get('issue_date', 'N/A')}")

            st.markdown("### Comparison Results")

            comparison = result["comparison_results"]
            for check_type, check_result in comparison.items():
                if check_type != "overall_status":
                    status_icon = "✅" if check_result["status"] == "PASS" else "⚠️" if check_result["status"] == "WARNING" else "❌"
                    st.write(f"{status_icon} **{check_type.replace('_', ' ').title()}**: {check_result['message']}")

            compliance = result["compliance_check"]
            if compliance["violations"]:
                st.markdown("### 🚨 Compliance Violations")
                for v in compliance["violations"]:
                    st.error(f"**{v['rule'].upper()}**: {v['message']}")

            if compliance["warnings"]:
                st.markdown("### ⚠️ Compliance Warnings")
                for w in compliance["warnings"]:
                    st.warning(f"**{w['rule'].upper()}**: {w['message']}")

            if not compliance["violations"] and not compliance["warnings"]:
                st.success("✅ All compliance checks passed")

            if result['status'] != "AUTO_APPROVE":
                st.markdown("### 👤 HITL Approval")

                approval_decision = st.radio("Decision:", ["APPROVE", "REJECT", "REQUEST_MORE_INFO"], key="lc_decision")
                approval_notes = st.text_area("Notes:", key="lc_notes")
                approval_confidence = st.slider("Your Confidence:", 0, 100, 80, key="lc_confidence")
                approver_name = st.text_input("Your Name:", "analyst@company.com", key="lc_approver")

                if st.button("✅ Submit Approval", key="submit_lc_approval"):
                    guardrails.log_human_approval(
                        result["audit_id"],
                        approver_name,
                        approval_decision,
                        approval_notes,
                        approval_confidence
                    )
                    st.success(f"✅ Approval logged")

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="⬇️ Download Result (JSON)",
                    data=json.dumps(result, indent=2, default=str),
                    file_name=f"lc_validation_{result['lc_id']}.json",
                    mime="application/json"
                )
        else:
            st.error("❌ Please provide LC document text")

elif page == "📋 Audit Trail":
    st.header("📋 Audit Trail")

    col1, col2 = st.columns([3, 1])

    with col1:
        agent_filter = st.selectbox("Filter by Agent:", ["All", "reconciliation_agent", "doc_agent"])

    with col2:
        limit = st.number_input("Show last N entries:", min_value=10, max_value=500, value=50)

    audit_data = db.get_audit_trail(limit=limit)

    if agent_filter != "All":
        audit_data = [d for d in audit_data if d.get("agent") == agent_filter]

    if audit_data:
        st.markdown(f"### Showing {len(audit_data)} entries")

        for entry in audit_data:
            with st.expander(f"🆔 {entry['audit_id']} | {entry['agent']} | Confidence: {entry['confidence']}%"):
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.write(f"**Timestamp**: {entry['timestamp']}")
                    st.write(f"**Agent**: {entry['agent']}")
                    st.write(f"**Confidence**: {entry['confidence']}%")

                with col2:
                    if entry['approver']:
                        st.write(f"**Approved By**: {entry['approver']}")
                        st.write(f"**Human Decision**: {entry['human_decision']}")

                st.write(f"**Reasoning**: {entry['reasoning']}")

        csv_data = pd.DataFrame([
            {
                "audit_id": d["audit_id"],
                "timestamp": d["timestamp"],
                "agent": d["agent"],
                "confidence": d["confidence"],
                "approver": d["approver"] or "Pending"
            }
            for d in audit_data
        ])

        st.download_button(
            label="⬇️ Download Audit Trail (CSV)",
            data=csv_data.to_csv(index=False),
            file_name="audit_trail.csv",
            mime="text/csv"
        )
    else:
        st.info("No audit entries found")

elif page == "📈 Dashboard":
    st.header("📈 Dashboard")

    audit_data = db.get_audit_trail(limit=100)

    col1, col2, col3, col4 = st.columns(4)

    total_decisions = len(audit_data)
    auto_approvals = sum(1 for d in audit_data if d.get("status") == "approved")
    avg_confidence = sum(d.get("confidence", 0) for d in audit_data) / len(audit_data) if audit_data else 0

    col1.metric("Total Decisions", total_decisions)
    col2.metric("Auto-Approvals", auto_approvals)
    col3.metric("Avg Confidence", f"{avg_confidence:.0f}%")
    col4.metric("Audit Entries", len(audit_data))

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Confidence Distribution")
        if audit_data:
            confidences = [d.get("confidence", 0) for d in audit_data]
            st.bar_chart(data=pd.Series(confidences).value_counts().sort_index())
        else:
            st.info("No data available")

    with col2:
        st.markdown("### Recent Activity")
        if audit_data:
            recent_df = pd.DataFrame([
                {
                    "Audit ID": d["audit_id"][:8],
                    "Agent": d["agent"].replace("_agent", ""),
                    "Confidence": f"{d['confidence']}%",
                    "Time": d["timestamp"][:10]
                }
                for d in audit_data[:10]
            ])
            st.dataframe(recent_df, use_container_width=True)
        else:
            st.info("No recent decisions")
