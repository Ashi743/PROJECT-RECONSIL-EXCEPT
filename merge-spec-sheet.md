# CLAUDE CODE PROMPT: Merge Reconciliation + Exception Triage into Single App

---

## FULL MERGING PROMPT (Copy-Paste Ready)

```
You are building a unified Trade Operations AI Platform with TWO agents:
1. Reconciliation Agent (3-way matching, fraud detection, anomaly detection)
2. Exception Triage Agent (real-time monitoring, classification, routing)

Both agents share:
- Single SQLite database (platform.db)
- Same guardrails.py (confidence, audit, privacy, compliance, HITL)
- Same notifier.py (alerts)
- Single Streamlit app.py (7 pages)

TASK: After you finish building both agents separately, merge them into ONE app.

════════════════════════════════════════════════════════════════════════════════
PART 1: EXTEND database.py (ADD EXCEPTION TABLES)
════════════════════════════════════════════════════════════════════════════════

Current database.py has these tables:
- audit_trail
- human_approvals
- reconciliation_decisions

ADD these tables for Exception Triage Agent:

CREATE TABLE IF NOT EXISTS exceptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exception_id TEXT UNIQUE NOT NULL,
    exception_type TEXT NOT NULL,  -- SHIPMENT_DELAY | MISSING_DOCUMENT | LC_DISCREPANCY | DD_RISK
    original_message TEXT NOT NULL,
    classification_confidence INTEGER,
    urgency TEXT NOT NULL,  -- CRITICAL | HIGH | MEDIUM | LOW
    urgency_score INTEGER,
    handler TEXT NOT NULL,  -- FREIGHT_TEAM | DOCS_TEAM | TRADE_FINANCE_TEAM | OPERATIONS_TEAM
    owner TEXT NOT NULL,
    deadline TEXT NOT NULL,
    deadline_timestamp TEXT NOT NULL,
    action_plan TEXT NOT NULL,  -- JSON array
    financial_impact REAL,
    context TEXT,  -- JSON object
    status TEXT DEFAULT 'OPEN',  -- OPEN | IN_PROGRESS | RESOLVED | CLOSED
    created_at TEXT NOT NULL,
    updated_at TEXT,
    resolved_at TEXT,
    audit_id TEXT
);

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id TEXT PRIMARY KEY,
    vessel_name TEXT NOT NULL,
    expected_arrival TEXT NOT NULL,
    actual_arrival TEXT,
    status TEXT DEFAULT 'IN_TRANSIT',
    daily_dd_rate REAL DEFAULT 50000
);

CREATE TABLE IF NOT EXISTS lcs (
    lc_id TEXT PRIMARY KEY,
    lc_number TEXT NOT NULL,
    expiry_date TEXT NOT NULL,
    lc_amount REAL NOT NULL,
    required_documents TEXT NOT NULL,  -- JSON array
    received_documents TEXT,  -- JSON array
    status TEXT DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS vessels (
    vessel_name TEXT PRIMARY KEY,
    port TEXT NOT NULL,
    laytime_expiry TEXT NOT NULL,
    daily_dd_rate REAL DEFAULT 50000,
    status TEXT DEFAULT 'DISCHARGING'
);

ADD these methods to Database class:

1. save_exception(exception_data: dict) -> str:
   - Save exception to exceptions table
   - Return exception_id

2. get_exception(exception_id: str) -> dict:
   - Retrieve exception by ID
   - Return full exception record

3. update_exception_status(exception_id: str, status: str):
   - Update exception status (OPEN → IN_PROGRESS → RESOLVED)

4. get_active_exceptions(urgency: str = None) -> list[dict]:
   - Get all OPEN or IN_PROGRESS exceptions
   - If urgency specified, filter by urgency level
   - Return sorted by urgency_score (highest first)

5. get_exceptions_by_urgency(urgency: str) -> list[dict]:
   - Get exceptions of specific urgency (CRITICAL, HIGH, MEDIUM, LOW)

6. exception_exists(identifier: str, exception_type: str) -> bool:
   - Check if exception already exists for this shipment/LC/vessel
   - Prevent duplicate exceptions

7. get_shipments_in_transit() -> list[dict]:
   - Get all shipments with status='IN_TRANSIT'

8. get_active_lcs() -> list[dict]:
   - Get all LCs with status='ACTIVE'

9. get_vessels_discharging() -> list[dict]:
   - Get all vessels with status='DISCHARGING'

10. get_recent_reconciliations(limit: int = 50) -> list[dict]:
    - Get recent reconciliation decisions (for home page metrics)

11. get_auto_approve_rate() -> float:
    - Calculate % of reconciliations with status=AUTO_APPROVE

12. get_total_financial_exposure() -> float:
    - Sum of all financial_impact values from active exceptions

13. load_mock_data():
    - Load 15 shipments, 8 LCs, 5 vessels from test_data
    - Call this in __init__ if database is empty

════════════════════════════════════════════════════════════════════════════════
PART 2: EXTEND app.py (MERGE INTO SINGLE APP WITH 7 PAGES)
════════════════════════════════════════════════════════════════════════════════

Replace current app.py with unified app that has 7 pages:

IMPORTS at top:
import streamlit as st
import json
import time
from datetime import datetime, timedelta
from reconciliation_agent import ReconciliationAgent
from exception_triage_agent import ExceptionTriageAgent
from real_time_monitor import RealTimeMonitor
from database import Database
from guardrails import Guardrails
from dotenv import load_dotenv
import os

INITIALIZATION:
@st.cache_resource
def initialize_platform():
    """Initialize both agents and shared resources"""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    db = Database()
    guardrails = Guardrails(db)
    
    recon_agent = ReconciliationAgent(
        openai_api_key=api_key,
        database=db,
        guardrails=guardrails
    )
    
    exception_agent = ExceptionTriageAgent(
        openai_api_key=api_key,
        database=db,
        guardrails=guardrails
    )
    
    monitor = RealTimeMonitor(
        exception_agent=exception_agent,
        database=db,
        check_interval_minutes=5
    )
    
    return recon_agent, exception_agent, monitor, db, guardrails

# Initialize
recon_agent, exception_agent, monitor, db, guardrails = initialize_platform()

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
    "Choose Agent",
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

════════════════════════════════════════════════════════════════════════════════
PAGE 1: 🏠 HOME / UNIFIED DASHBOARD
════════════════════════════════════════════════════════════════════════════════

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
        if st.button("📊 Go to Reconciliation Agent", use_container_width=True):
            st.session_state.page = "Reconciliation Agent"
    
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
        if st.button("📍 Go to Exception Dashboard", use_container_width=True):
            st.session_state.page = "Exception Dashboard"
    
    st.write("---")
    
    # PLATFORM OVERVIEW METRICS
    st.subheader("📊 Platform Overview")
    
    reconciliation_count = len(db.get_recent_reconciliations())
    active_exceptions = db.get_active_exceptions()
    exception_count = len(active_exceptions)
    critical_count = len([e for e in active_exceptions if e['urgency'] == 'CRITICAL'])
    auto_approve_rate = db.get_auto_approve_rate()
    total_financial_exposure = db.get_total_financial_exposure()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Reconciliations Today", reconciliation_count)
    
    with col2:
        st.metric("Active Exceptions", exception_count, f"{critical_count} 🔴")
    
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

════════════════════════════════════════════════════════════════════════════════
PAGE 2: 🔄 RECONCILIATION AGENT (EXISTING CODE)
════════════════════════════════════════════════════════════════════════════════

elif page == "🔄 Reconciliation Agent":
    st.title("🔄 Reconciliation Agent")
    # KEEP EXISTING RECONCILIATION AGENT UI
    # (All the code from original app.py reconciliation section)

════════════════════════════════════════════════════════════════════════════════
PAGE 3: 🚨 EXCEPTION TRIAGE DASHBOARD (REAL-TIME)
════════════════════════════════════════════════════════════════════════════════

elif page == "🚨 Exception Triage Dashboard":
    st.title("🚨 Real-Time Exception Dashboard")
    
    # Auto-refresh placeholder
    placeholder = st.empty()
    refresh_interval = st.slider("Refresh Interval (seconds)", 10, 120, 30)
    
    while True:
        with placeholder.container():
            # Get active exceptions
            active_exceptions = db.get_active_exceptions()
            critical_count = len([e for e in active_exceptions if e['urgency'] == 'CRITICAL'])
            high_count = len([e for e in active_exceptions if e['urgency'] == 'HIGH'])
            
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
                for exception in sorted(active_exceptions, key=lambda x: x['urgency_score'], reverse=True):
                    # Color code by urgency
                    if exception['urgency'] == 'CRITICAL':
                        urgency_icon = "🔴"
                        container_type = st.error
                    elif exception['urgency'] == 'HIGH':
                        urgency_icon = "🟠"
                        container_type = st.warning
                    elif exception['urgency'] == 'MEDIUM':
                        urgency_icon = "🟡"
                        container_type = st.info
                    else:
                        urgency_icon = "🟢"
                        container_type = st.success
                    
                    with container_type(f"{urgency_icon} {exception['exception_type']} - {exception['urgency']}"):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"**Message:** {exception['original_message']}")
                            st.write(f"**Handler:** {exception['handler']} ({exception['owner']})")
                        
                        with col2:
                            st.write(f"**Deadline:** {exception['deadline']}")
                            st.write(f"**Impact:** ₹{exception['financial_impact']:,.0f}")
                        
                        with col3:
                            if st.button("View Details", key=f"view_{exception['exception_id']}"):
                                st.session_state.selected_exception = exception['exception_id']
                            
                            if st.button("✅ Mark Resolved", key=f"resolve_{exception['exception_id']}"):
                                db.update_exception_status(exception['exception_id'], 'RESOLVED')
                                st.success("Exception marked as resolved")
                                st.rerun()
                        
                        # Expandable action plan
                        with st.expander("📋 Action Plan"):
                            action_plan = json.loads(exception['action_plan'])
                            for i, action in enumerate(action_plan, 1):
                                st.write(f"{i}. {action}")
            else:
                st.success("✅ No active exceptions - all systems normal!")
            
            st.write("---")
            st.write(f"⏰ Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        time.sleep(refresh_interval)
        st.rerun()

════════════════════════════════════════════════════════════════════════════════
PAGE 4: 📋 EXCEPTION DETAILS & ROUTING
════════════════════════════════════════════════════════════════════════════════

elif page == "📋 Exception Details & Routing":
    st.title("📋 Exception Details & Routing")
    
    # Get list of exceptions for selection
    all_exceptions = db.get_active_exceptions()
    
    if not all_exceptions:
        st.info("No active exceptions")
    else:
        # Select exception
        exception_options = {e['exception_id']: f"{e['exception_type']} - {e['urgency']}" 
                            for e in all_exceptions}
        
        selected_exc_id = st.selectbox(
            "Select Exception",
            list(exception_options.keys()),
            format_func=lambda x: exception_options[x]
        )
        
        exception = db.get_exception(selected_exc_id)
        
        # Display full details
        st.subheader(f"{exception['exception_type']} - {exception['urgency']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Exception ID:** {exception['exception_id']}")
            st.write(f"**Type:** {exception['exception_type']}")
            st.write(f"**Urgency:** {exception['urgency']} (Score: {exception['urgency_score']}/100)")
            st.write(f"**Confidence:** {exception['classification_confidence']}%")
        
        with col2:
            st.write(f"**Handler:** {exception['handler']}")
            st.write(f"**Owner:** {exception['owner']}")
            st.write(f"**Deadline:** {exception['deadline_timestamp']}")
            st.write(f"**Status:** {exception['status']}")
            st.write(f"**Financial Impact:** ₹{exception['financial_impact']:,.0f}")
        
        st.write("---")
        
        st.write("**Original Message:**")
        st.write(exception['original_message'])
        
        st.write("---")
        
        st.write("**Action Plan:**")
        action_plan = json.loads(exception['action_plan'])
        for i, action in enumerate(action_plan, 1):
            st.write(f"{i}. {action}")
        
        st.write("---")
        
        # Context
        if exception['context']:
            st.write("**Context Data:**")
            context = json.loads(exception['context']) if isinstance(exception['context'], str) else exception['context']
            st.json(context)
        
        st.write("---")
        
        # Resolution
        if exception['status'] != 'RESOLVED':
            st.subheader("Resolve Exception")
            
            resolution_notes = st.text_area("Resolution Notes", placeholder="What was done to resolve this?")
            
            if st.button("✅ Mark as Resolved"):
                db.update_exception_status(exception['exception_id'], 'RESOLVED')
                st.success("Exception marked as resolved")
                st.rerun()

════════════════════════════════════════════════════════════════════════════════
PAGE 5: 📊 UNIFIED AUDIT TRAIL (BOTH AGENTS)
════════════════════════════════════════════════════════════════════════════════

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

════════════════════════════════════════════════════════════════════════════════
PAGE 6: 🔔 ALERTS & NOTIFICATIONS
════════════════════════════════════════════════════════════════════════════════

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
            **{exc['exception_type']}** - {exc['deadline']}
            
            {exc['original_message']}
            
            **Handler:** {exc['owner']}
            """)
    
    st.write("---")
    
    # HIGH exceptions
    high_exceptions = db.get_exceptions_by_urgency('HIGH')
    
    if high_exceptions:
        st.subheader("🟠 HIGH PRIORITY ALERTS")
        for exc in high_exceptions:
            st.warning(f"""
            **{exc['exception_type']}** - {exc['deadline']}
            
            {exc['original_message']}
            
            **Handler:** {exc['owner']}
            """)

════════════════════════════════════════════════════════════════════════════════
PAGE 7: ⚙️ SETTINGS
════════════════════════════════════════════════════════════════════════════════

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
        monitor = RealTimeMonitor(exception_agent, db, check_interval_minutes=monitoring_interval)
        monitor.start()
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

════════════════════════════════════════════════════════════════════════════════
AFTER BUILDING BOTH AGENTS:
════════════════════════════════════════════════════════════════════════════════

1. Extend database.py with exception tables and methods (see PART 1 above)

2. Replace app.py with merged version (see PART 2 above)

3. Test both agents:
   python run_tests.py
   Expected: 27/27 PASS (15 reconciliation + 12 exception)

4. Run merged app:
   streamlit run app.py

5. Test real-time monitoring:
   - Go to Exception Triage Dashboard
   - Wait for background monitor to run
   - See exceptions auto-created
   - Dashboard auto-refreshes every 30 seconds

6. Test unified audit trail:
   - Go to Unified Audit Trail
   - Filter by agent
   - See both agents' decisions in one place

════════════════════════════════════════════════════════════════════════════════
KEY DIFFERENCES FROM SEPARATE APPS:
════════════════════════════════════════════════════════════════════════════════

✅ Single database.py (both agents use same DB)
✅ Single guardrails.py (shared by both agents)
✅ Single notifier.py (alerts from both)
✅ Single app.py with 7 pages (not separate apps)
✅ Single SQLite database (platform.db)
✅ Unified audit trail (both agents log to same table)
✅ Home dashboard shows metrics from both agents
✅ Real-time refresh works across both systems

════════════════════════════════════════════════════════════════════════════════
THAT'S IT! You now have a UNIFIED PLATFORM with 2 AGENTS.
════════════════════════════════════════════════════════════════════════════════
```

---

## HOW TO USE THIS PROMPT

### **Step 1: Build Reconciliation Agent First**
- Use: `UPDATED_SPEC_SHEET_COMPREHENSIVE.md`
- In Claude Code, build completely
- Expected: `reconciliation_agent.py`, `database.py`, `guardrails.py`, `app.py` (version 1)
- Run tests: `python run_tests.py` → 15/15 PASS

### **Step 2: Build Exception Triage Agent**
- Use: `SPEC_SHEET_EXCEPTION_TRIAGE_AGENT.md`
- In Claude Code, build:
  - `exception_triage_agent.py`
  - `real_time_monitor.py`
  - Extend `database.py` (add exception tables)
  - Test data (12 scenarios)
- Run tests: `python run_tests.py` → 12/12 PASS (exception tests only)

### **Step 3: Merge Into Single App**
- Copy-paste the prompt above into Claude Code
- Tell Claude: "Read the prompt completely and execute PART 1 and PART 2"
- This will:
  1. Extend database.py with exception tables + methods
  2. Replace app.py with merged 7-page app
- Run merged tests: `python run_tests.py` → 27/27 PASS (all tests)
- Run app: `streamlit run app.py`

---

## FINAL VERIFICATION CHECKLIST

After merging, verify:

```
✅ database.py has 10 tables (4 old + 6 new)
✅ database.py has all 13 methods for exceptions
✅ app.py has 7 pages (not 5)
✅ app.py initializes both agents
✅ Real-time monitor starts automatically
✅ Home page shows metrics from both agents
✅ Exception Dashboard auto-refreshes
✅ Unified Audit Trail shows both agents
✅ All 27 tests pass: python run_tests.py
✅ Streamlit app runs without errors: streamlit run app.py
✅ Real-time exceptions are auto-created and appear on dashboard
✅ Clicking "Mark Resolved" updates database
✅ Refreshing page keeps real-time state
```

---

**Now you're ready to merge! Good luck! 🚀**
