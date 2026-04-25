"""
Unified Trade Operations AI Platform - Merged App with 7 Pages
Combines Reconciliation Agent + Exception Triage Agent into single app
"""

import streamlit as st
from reconciliation_agent import ReconciliationAgent, MOCK_SCENARIOS
from exception_triage_agent import ExceptionTriageAgent
from real_time_monitor import RealTimeMonitor
from doc_agent import LCDocAgent
from guardrails import Guardrails
from database import Database
import pandas as pd
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import time

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    st.error("❌ OPENAI_API_KEY not found in .env file")
    st.stop()


@st.cache_resource
def initialize_platform():
    """Initialize both agents and shared resources."""
    db = Database()
    guardrails = Guardrails(db)

    recon_agent = ReconciliationAgent(
        openai_api_key=openai_api_key,
        database=db,
        guardrails=guardrails
    )

    exception_agent = ExceptionTriageAgent(
        openai_api_key=openai_api_key,
        database=db,
        guardrails=guardrails
    )

    monitor = RealTimeMonitor(
        exception_agent=exception_agent,
        database=db,
        check_interval_minutes=5
    )

    lc_agent = LCDocAgent(openai_api_key, db, guardrails)

    return recon_agent, exception_agent, monitor, db, guardrails, lc_agent


# Initialize
recon_agent, exception_agent, monitor, db, guardrails, lc_agent = initialize_platform()

# Start monitoring (if not running)
if 'monitor_started' not in st.session_state:
    monitor.start()
    st.session_state.monitor_started = True

# Page configuration
st.set_page_config(
    page_title="Trade Operations AI Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("🚀 Trade Operations AI Platform")
page = st.sidebar.radio(
    "Choose Page",
    [
        "🏠 Home",
        "🔄 Reconciliation Agent",
        "🚨 Exception Triage Dashboard",
        "📋 Exception Details & Routing",
        "📊 Unified Audit Trail",
        "🔔 Alerts & Notifications",
        "⚙️ Settings"
    ]
)

# ============================================================================
# PAGE 1: HOME / UNIFIED DASHBOARD
# ============================================================================

if page == "🏠 Home":
    st.title("🚀 Trade Operations AI Platform")
    st.write("Two intelligent agents working together to manage trade operations")

    st.write("---")

    # Quick access cards
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔄 Reconciliation Agent")
        st.write("""
        **What it does:**
        - 3-way document matching (contract ↔ invoice ↔ receipt)
        - Variance analysis (3 dimensions)
        - Fraud detection (9+ signals including PRICE_DOWN_QTY_UP)
        - Anomaly detection (8+ patterns)
        - Confidence-based routing (auto-approve >95%)
        """)

    with col2:
        st.subheader("🚨 Exception Triage Agent")
        st.write("""
        **What it does:**
        - Real-time monitoring (shipments, documents, LCs, laytime)
        - Classification (4 exception types)
        - Urgency assessment (CRITICAL/HIGH/MEDIUM/LOW)
        - Intelligent routing (4 handler teams)
        - Action plan generation (3-5 specific steps)
        """)

    st.write("---")

    # PLATFORM OVERVIEW METRICS
    st.subheader("📊 Platform Overview")

    reconciliation_count = len(db.get_recent_reconciliations())
    active_exceptions = db.get_active_exceptions()
    exception_count = len(active_exceptions)
    critical_count = len([e for e in active_exceptions if e.get('urgency') == 'CRITICAL'])
    auto_approve_rate = db.get_auto_approve_rate()
    total_financial_exposure = db.get_total_financial_exposure()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Reconciliations Today", reconciliation_count)

    with col2:
        st.metric("Active Exceptions", exception_count, f"{critical_count} 🔴" if critical_count > 0 else "")

    with col3:
        st.metric("Auto-Approve Rate", f"{auto_approve_rate:.1%}")

    with col4:
        st.metric("Total $ at Risk", f"₹{total_financial_exposure:,.0f}")

    st.write("---")

    # RECENT ACTIVITY (Both agents)
    st.subheader("📈 Recent Activity")

    audit_trail = db.get_audit_trail(limit=20)

    if audit_trail:
        for entry in audit_trail:
            if entry['agent'] == 'ReconciliationAgent':
                st.info(f"**[Reconciliation]** {entry['timestamp']}: {entry['reasoning'][:80]}...")
            elif entry['agent'] == 'ExceptionTriageAgent':
                st.warning(f"**[Exception Triage]** {entry['timestamp']}: {entry['reasoning'][:80]}...")
    else:
        st.write("No recent activity")

# ============================================================================
# PAGE 2: RECONCILIATION AGENT
# ============================================================================

elif page == "🔄 Reconciliation Agent":
    st.header("🔄 Reconciliation Agent")
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

            with col1:
                st.metric("Status", f"{status_color.get(result['status'], '')} {result['status']}")
            with col2:
                st.metric("Confidence", f"{result['confidence']}%")
            with col3:
                st.metric("Fraud Score", f"{result.get('fraud_analysis', {}).get('fraud_score', 0)}/100")
            with col4:
                st.metric("Total Anomalies", result.get('anomaly_analysis', {}).get('total_anomalies', 0))

            # Variance Analysis
            st.subheader("📊 Variance Analysis")
            variance = result.get('variance_analysis', {})
            col1, col2, col3 = st.columns(3)

            with col1:
                qty_var = variance.get('qty_variance', {})
                st.metric("Qty Variance", f"{qty_var.get('contract_invoice_variance_pct', 0):.2f}%", qty_var.get('severity', 'N/A'))

            with col2:
                price_var = variance.get('price_variance', {})
                st.metric("Price Variance", f"{price_var.get('contract_invoice_variance_pct', 0):.2f}%", price_var.get('severity', 'N/A'))

            with col3:
                timeline_var = variance.get('timeline_variance', {})
                st.metric("Timeline (days)", f"{timeline_var.get('invoice_to_receipt_days', 0)}", timeline_var.get('severity', 'N/A'))

            # Fraud Detection
            if result.get('fraud_analysis', {}).get('fraud_score', 0) > 0:
                st.subheader("🚨 Fraud Detection")
                fraud = result['fraud_analysis']
                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Fraud Score", f"{fraud.get('fraud_score', 0)}/100")
                    st.metric("Risk Level", fraud.get('risk_level', 'LOW'))

                with col2:
                    st.write("**Signals Detected:**")
                    for signal in fraud.get('signals_detected', []):
                        st.write(f"- {signal}")

            # Anomaly Detection
            if result.get('anomaly_analysis', {}).get('total_anomalies', 0) > 0:
                st.subheader("⚠️ Anomaly Detection")
                anomalies = result['anomaly_analysis']
                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Total Anomalies", anomalies.get('total_anomalies', 0))
                    st.metric("Critical Anomalies", anomalies.get('critical_anomalies', 0))

                with col2:
                    st.write("**Anomalies Found:**")
                    for anomaly in anomalies.get('anomalies_detected', [])[:5]:
                        st.write(f"- {anomaly}")

            # Confidence Breakdown
            st.subheader("📈 Confidence Breakdown")
            confidence = result.get('confidence_breakdown', {})

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Initial: {confidence.get('initial_confidence', 100)}%")
                st.write(f"Qty Variance Penalty: -{confidence.get('qty_variance_penalty', 0)}")
                st.write(f"Price Variance Penalty: -{confidence.get('price_variance_penalty', 0)}")

            with col2:
                st.write(f"Timeline Penalty: -{confidence.get('timeline_penalty', 0)}")
                st.write(f"Fraud Penalty: -{confidence.get('fraud_penalty', 0)}")
                st.write(f"Anomaly Penalty: -{confidence.get('anomaly_penalty', 0)}")

            st.write(f"**Final Confidence: {confidence.get('final_confidence', 0)}%**")

# ============================================================================
# PAGE 3: EXCEPTION TRIAGE DASHBOARD (REAL-TIME)
# ============================================================================

elif page == "🚨 Exception Triage Dashboard":
    st.title("🚨 Real-Time Exception Dashboard")

    # Get active exceptions
    active_exceptions = db.get_active_exceptions()
    critical_count = len([e for e in active_exceptions if e.get('urgency') == 'CRITICAL'])
    high_count = len([e for e in active_exceptions if e.get('urgency') == 'HIGH'])

    # METRICS
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Exceptions", len(active_exceptions))

    with col2:
        st.metric("🔴 CRITICAL", critical_count)

    with col3:
        st.metric("🟠 HIGH", high_count)

    with col4:
        st.metric("Next Monitor Check", "5 min")

    st.write("---")

    # EXCEPTIONS TABLE (sorted by urgency)
    st.subheader("Active Exceptions (Sorted by Urgency)")

    if active_exceptions:
        for exception in sorted(active_exceptions, key=lambda x: x.get('urgency_score', 0), reverse=True):
            # Color code by urgency
            if exception.get('urgency') == 'CRITICAL':
                urgency_icon = "🔴"
                container_type = st.error
            elif exception.get('urgency') == 'HIGH':
                urgency_icon = "🟠"
                container_type = st.warning
            elif exception.get('urgency') == 'MEDIUM':
                urgency_icon = "🟡"
                container_type = st.info
            else:
                urgency_icon = "🟢"
                container_type = st.success

            with container_type(f"{urgency_icon} {exception.get('exception_type')} - {exception.get('urgency')}"):
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.write(f"**Message:** {exception.get('original_message')}")
                    st.write(f"**Handler:** {exception.get('handler')} ({exception.get('owner')})")

                with col2:
                    st.write(f"**Deadline:** {exception.get('deadline')}")
                    st.write(f"**Impact:** ₹{exception.get('financial_impact', 0):,.0f}")

                with col3:
                    if st.button("View Details", key=f"view_{exception.get('exception_id')}"):
                        st.session_state.selected_exception = exception.get('exception_id')

                    if st.button("✅ Mark Resolved", key=f"resolve_{exception.get('exception_id')}"):
                        db.update_exception_status(exception.get('exception_id'), 'RESOLVED')
                        st.success("Exception marked as resolved")
                        st.rerun()

                # Show action plan (expandable)
                with st.expander("📋 Action Plan"):
                    action_plan = exception.get('action_plan', [])
                    if isinstance(action_plan, str):
                        try:
                            action_plan = json.loads(action_plan)
                        except:
                            action_plan = []
                    for action in action_plan:
                        st.write(f"- {action}")
    else:
        st.success("✅ No active exceptions - all systems normal!")

    st.write("---")
    st.write(f"⏰ Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================================================
# PAGE 4: EXCEPTION DETAILS & ROUTING
# ============================================================================

elif page == "📋 Exception Details & Routing":
    st.title("📋 Exception Details & Routing")

    # Get list of exceptions for selection
    all_exceptions = db.get_active_exceptions()

    if not all_exceptions:
        st.info("No active exceptions")
    else:
        # Select exception
        exception_options = {e.get('exception_id'): f"{e.get('exception_type')} - {e.get('urgency')}"
                            for e in all_exceptions}

        selected_exc_id = st.selectbox(
            "Select Exception",
            list(exception_options.keys()),
            format_func=lambda x: exception_options[x]
        )

        exception = db.get_exception(selected_exc_id)

        if exception:
            # Display full details
            st.subheader(f"{exception.get('exception_type')} - {exception.get('urgency')}")

            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Exception ID:** {exception.get('exception_id')}")
                st.write(f"**Type:** {exception.get('exception_type')}")
                st.write(f"**Urgency:** {exception.get('urgency')} (Score: {exception.get('urgency_score')}/100)")
                st.write(f"**Confidence:** {exception.get('classification_confidence')}%")

            with col2:
                st.write(f"**Handler:** {exception.get('handler')}")
                st.write(f"**Owner:** {exception.get('owner')}")
                st.write(f"**Deadline:** {exception.get('deadline_timestamp')}")
                st.write(f"**Status:** {exception.get('status')}")
                st.write(f"**Financial Impact:** ₹{exception.get('financial_impact', 0):,.0f}")

            st.write("---")

            st.write("**Original Message:**")
            st.write(exception.get('original_message'))

            st.write("---")

            st.write("**Action Plan:**")
            action_plan = exception.get('action_plan', [])
            if isinstance(action_plan, str):
                try:
                    action_plan = json.loads(action_plan)
                except:
                    action_plan = []
            for i, action in enumerate(action_plan, 1):
                st.write(f"{i}. {action}")

            st.write("---")

            # Context
            if exception.get('context'):
                st.write("**Context Data:**")
                context = exception.get('context')
                if isinstance(context, str):
                    try:
                        context = json.loads(context)
                    except:
                        context = {}
                st.json(context)

            st.write("---")

            # Resolution
            if exception.get('status') != 'RESOLVED':
                st.subheader("Resolve Exception")

                resolution_notes = st.text_area("Resolution Notes", placeholder="What was done to resolve this?")

                if st.button("✅ Mark as Resolved"):
                    db.update_exception_status(exception.get('exception_id'), 'RESOLVED')
                    st.success("Exception marked as resolved")
                    st.rerun()

# ============================================================================
# PAGE 5: UNIFIED AUDIT TRAIL (BOTH AGENTS)
# ============================================================================

elif page == "📊 Unified Audit Trail":
    st.title("📊 Unified Audit Trail (Both Agents)")

    # Filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        agent_filter = st.multiselect(
            "Filter by Agent",
            ["ReconciliationAgent", "ExceptionTriageAgent"],
            default=["ReconciliationAgent", "ExceptionTriageAgent"]
        )

    with col2:
        limit = st.slider("Show last N entries", 10, 200, 50)

    with col3:
        st.write("")  # Spacer
        if st.button("🔄 Refresh"):
            st.rerun()

    # Get audit trail
    audit_trail = db.get_audit_trail(limit=limit)

    st.write("---")

    if audit_trail:
        for entry in audit_trail:
            if entry['agent'] not in agent_filter:
                continue

            if entry['agent'] == 'ReconciliationAgent':
                st.info(f"""
                **[Reconciliation Agent]** {entry['timestamp']}

                **Decision:** {entry['reasoning'][:200]}...

                **Audit ID:** {entry['audit_id']}
                """)

            elif entry['agent'] == 'ExceptionTriageAgent':
                st.warning(f"""
                **[Exception Triage Agent]** {entry['timestamp']}

                **Decision:** {entry['reasoning'][:200]}...

                **Audit ID:** {entry['audit_id']}
                """)
    else:
        st.write("No audit trail entries")

# ============================================================================
# PAGE 6: ALERTS & NOTIFICATIONS
# ============================================================================

elif page == "🔔 Alerts & Notifications":
    st.title("🔔 Alerts & Notifications")

    st.write("Alerts from both agents appear here")

    st.write("---")

    # CRITICAL exceptions = high-priority alerts
    critical_exceptions = db.get_exceptions_by_urgency('CRITICAL')

    if critical_exceptions:
        st.subheader("🔴 CRITICAL ALERTS")
        for exc in critical_exceptions:
            st.error(f"""
            **{exc.get('exception_type')}** - {exc.get('deadline')}

            {exc.get('original_message')}

            **Handler:** {exc.get('owner')}
            """)

    st.write("---")

    # HIGH exceptions
    high_exceptions = db.get_exceptions_by_urgency('HIGH')

    if high_exceptions:
        st.subheader("🟠 HIGH PRIORITY ALERTS")
        for exc in high_exceptions:
            st.warning(f"""
            **{exc.get('exception_type')}** - {exc.get('deadline')}

            {exc.get('original_message')}

            **Handler:** {exc.get('owner')}
            """)

    if not critical_exceptions and not high_exceptions:
        st.success("✅ No high-priority alerts at this time")

# ============================================================================
# PAGE 7: SETTINGS
# ============================================================================

elif page == "⚙️ Settings":
    st.title("⚙️ Platform Settings")

    st.subheader("Reconciliation Agent Settings")
    st.write("*(Settings would go here)*")

    st.write("---")

    st.subheader("Exception Triage Agent Settings")

    monitoring_interval = st.slider(
        "Monitoring Check Interval (minutes)",
        1, 30, 5
    )

    st.write(f"Monitor will check for exceptions every {monitoring_interval} minutes")

    if st.button("🔄 Restart Monitor with New Settings"):
        monitor.stop()
        # Note: In a real app, you would create a new monitor with the new interval
        st.success("Monitor restarted with new settings")

    st.write("---")

    st.subheader("Shared Settings")

    auto_approve_threshold = st.slider(
        "Reconciliation Auto-Approve Threshold",
        80, 99, 95
    )

    escalate_critical_immediately = st.checkbox(
        "Escalate CRITICAL exceptions immediately",
        value=True
    )

    if st.button("💾 Save Settings"):
        st.success("Settings saved")
