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
    st.markdown("### Quick Links")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Go to Reconciliation Agent", key="home_recon"):
            st.switch_page("page/📊 Reconciliation Agent")
    with col2:
        if st.button("📄 Go to LC Doc Agent", key="home_lc"):
            st.switch_page("page/📄 LC Doc Agent")

    st.markdown("### Features")
    st.markdown("""
    - ✅ **Reconciliation Agent**: 3-way match (contract ↔ invoice ↔ receipt) with fraud detection
    - ✅ **LC Doc Agent**: Letter of Credit validation with UCP 600 compliance checks
    - ✅ **Guardrails**: Confidence thresholds, audit trail, privacy masking, compliance checks, HITL workflow
    - ✅ **ChromaDB**: Vector storage for semantic search of LC documents
    - ✅ **SQLite**: Immutable audit trail for all decisions
    """)

elif page == "📊 Reconciliation Agent":
    st.header("📊 Reconciliation Agent")
    st.markdown("3-way reconciliation (contract ↔ invoice ↔ receipt) with fraud detection")

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
        st.markdown("### Choose Test Scenario")
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
            with st.spinner("Running reconciliation..."):
                result = recon_agent.reconcile(contract_data, invoice_data, receipt_data)

            st.subheader("📊 Results")

            col1, col2, col3, col4 = st.columns(4)

            status_color = {
                "AUTO_APPROVE": "🟢",
                "ROUTE_TO_SPECIALIST": "🟡",
                "ESCALATE_TO_MANAGER": "🟠",
                "ESCALATE_TO_DIRECTOR": "🔴"
            }

            col1.metric("Status", f"{status_color.get(result['status'], '❓')} {result['status']}")
            col2.metric("Confidence", f"{result['confidence']}%")
            col3.metric("Audit ID", result['audit_id'][:8] + "...")
            col4.metric("Financial Impact", f"${result['financial_impact']:.2f}")

            st.divider()

            st.markdown("### Match Summary")

            col1, col2, col3 = st.columns(3)

            qty_match = result["matches"]["qty_match"]
            with col1:
                status_icon = "✅" if qty_match["status"] == "GREEN" else "⚠️" if qty_match["status"] == "YELLOW" else "❌"
                st.write(f"**{status_icon} Quantity Match**")
                st.write(f"Contract: {qty_match['contract_qty']} MT")
                st.write(f"Invoice: {qty_match['invoice_qty']} MT")
                st.write(f"Variance: {qty_match['variance_pct']:.2f}%")
                st.write(f"*{qty_match['message']}*")

            price_match = result["matches"]["price_match"]
            with col2:
                status_icon = "✅" if price_match["status"] == "GREEN" else "⚠️" if price_match["status"] == "YELLOW" else "❌"
                st.write(f"**{status_icon} Price Match**")
                st.write(f"Contract: ${price_match['contract_price']}")
                st.write(f"Invoice: ${price_match['invoice_price']}")
                st.write(f"Variance: {price_match['variance_pct']:.2f}%")
                st.write(f"*{price_match['message']}*")

            timeline_match = result["matches"]["timeline_match"]
            with col3:
                status_icon = "✅" if timeline_match["status"] == "GREEN" else "⚠️" if timeline_match["status"] == "YELLOW" else "❌"
                st.write(f"**{status_icon} Timeline Match**")
                st.write(f"Receipt: {timeline_match['receipt_date']}")
                st.write(f"Invoice: {timeline_match['invoice_date']}")
                st.write(f"Days: {timeline_match['days_diff']}")
                st.write(f"*{timeline_match['message']}*")

            if result["anomalies"]:
                st.markdown("### 🚨 Anomalies Detected")
                for anomaly in result["anomalies"]:
                    severity_color = {
                        "LOW": "🟢",
                        "MEDIUM": "🟡",
                        "HIGH": "🟠",
                        "CRITICAL": "🔴"
                    }
                    st.warning(f"{severity_color.get(anomaly['severity'], '❓')} **{anomaly['type']}**: {anomaly['message']}")

            st.markdown("### 📌 Routing Decision")
            routing = result["routing"]
            st.info(f"""
**Action**: {routing['action']}
**Owner**: {routing['owner'] or 'Auto-approved (no owner)'}
**Deadline**: {routing['deadline'] or 'None'}
**Urgency**: {routing['urgency']}
            """)

            st.markdown("### 💭 Reasoning")
            st.write(result['reasoning'])

            if result['status'] != "AUTO_APPROVE":
                st.markdown("### 👤 HITL Approval Workflow")

                col1, col2 = st.columns([2, 1])

                with col1:
                    approval_decision = st.radio("Decision:", ["APPROVE", "REJECT", "REQUEST_INFO"])
                    approval_notes = st.text_area("Notes:", key="recon_notes")
                    approval_confidence = st.slider("Your Confidence:", 0, 100, 80)
                    approver_name = st.text_input("Your Name:", "analyst@company.com")

                with col1:
                    if st.button("✅ Submit Approval", key="submit_recon_approval"):
                        guardrails.log_human_approval(
                            result["audit_id"],
                            approver_name,
                            approval_decision,
                            approval_notes,
                            approval_confidence
                        )
                        st.success(f"✅ Approval logged for {result['audit_id']}")

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="⬇️ Download Result (JSON)",
                    data=json.dumps(result, indent=2),
                    file_name=f"reconciliation_{result['audit_id']}.json",
                    mime="application/json"
                )
        else:
            st.error("❌ Please provide contract, invoice, and receipt data")

elif page == "📄 LC Doc Agent":
    st.header("📄 LC Doc Agent")
    st.markdown("Validate Letter of Credit against contract terms with UCP 600 compliance")

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
        with open("data/sample_lc.txt", "r") as f:
            lc_text = f.read()
        st.write("**Sample LC:**")
        st.text(lc_text)

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

            st.markdown("### 💭 Reasoning")
            st.write(result['reasoning'])

            if result['status'] != "AUTO_APPROVE":
                st.markdown("### 👤 HITL Approval Workflow")

                approval_decision = st.radio("Decision:", ["APPROVE", "REJECT", "REQUEST_INFO"], key="lc_decision")
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
                    st.success(f"✅ Approval logged for {result['audit_id']}")

            st.divider()
            st.markdown("### 🔍 Vector Search Similar LCs")

            search_query = st.text_input("Search for similar LC clauses:", key="lc_search")
            if st.button("🔍 Search Vector DB", key="search_lc"):
                with st.spinner("Searching ChromaDB..."):
                    search_results = db.search_similar_lcs(search_query, top_k=3)

                if search_results["documents"] and search_results["documents"][0]:
                    st.write("**Similar LCs Found:**")
                    for i, (doc, meta) in enumerate(zip(search_results["documents"][0], search_results["metadatas"][0])):
                        st.write(f"**Result {i+1}:** {meta.get('lc_id', 'Unknown')}")
                        st.text(doc[:200] + "..." if len(doc) > 200 else doc)
                else:
                    st.info("No similar LCs found in database")

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
    st.markdown("Immutable audit log of all agent decisions and human approvals")

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
                    st.write(f"**Status**: {entry['status']}")

                with col2:
                    if entry['approver']:
                        st.write(f"**Approved By**: {entry['approver']}")
                        st.write(f"**Human Decision**: {entry['human_decision']}")
                        st.write(f"**Human Confidence**: {entry['human_confidence']}%")

                st.write("**Reasoning:**")
                st.text(entry['reasoning'])

                st.write("**Decision:**")
                st.json(entry['decision'])

                if entry['human_notes']:
                    st.write("**Human Notes:**")
                    st.text(entry['human_notes'])

        csv_data = pd.DataFrame([
            {
                "audit_id": d["audit_id"],
                "timestamp": d["timestamp"],
                "agent": d["agent"],
                "confidence": d["confidence"],
                "status": d["status"],
                "approver": d["approver"] or "N/A",
                "human_decision": d["human_decision"] or "N/A"
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
    auto_approvals = sum(1 for d in audit_data if d.get("status") == "approved" and d.get("routing", {}).get("action") == "AUTO_APPROVE")
    escalations = sum(1 for d in audit_data if d.get("routing", {}).get("urgency") in ["HIGH", "CRITICAL"])
    avg_confidence = sum(d.get("confidence", 0) for d in audit_data) / len(audit_data) if audit_data else 0

    col1.metric("Total Decisions", total_decisions)
    col2.metric("Auto-Approvals", f"{auto_approvals}/{total_decisions}" if total_decisions > 0 else "0")
    col3.metric("Escalations", f"{escalations}/{total_decisions}" if total_decisions > 0 else "0")
    col4.metric("Avg Confidence", f"{avg_confidence:.0f}%")

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
        st.markdown("### Decision Distribution")
        if audit_data:
            actions = {}
            for d in audit_data:
                routing = d.get("routing", {})
                action = routing.get("action", "UNKNOWN")
                actions[action] = actions.get(action, 0) + 1

            st.bar_chart(pd.Series(actions))
        else:
            st.info("No data available")

    st.markdown("### Recent Decisions")
    if audit_data:
        recent_df = pd.DataFrame([
            {
                "Audit ID": d["audit_id"][:8] + "...",
                "Agent": d["agent"],
                "Confidence": d["confidence"],
                "Status": d["status"],
                "Timestamp": d["timestamp"][:19]
            }
            for d in audit_data[:10]
        ])
        st.dataframe(recent_df, use_container_width=True)
    else:
        st.info("No recent decisions")
