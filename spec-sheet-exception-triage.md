# SPEC SHEET: Exception Triage Agent with Real-Time Monitoring
## Complete Technical Specification for Claude Code Implementation

---

## PROJECT OVERVIEW

**Goal:** Build a real-time exception triage agent that automatically detects, classifies, and routes operational problems in trade execution.

**What It Does:**
1. **Real-Time Monitoring** - Continuously monitors shipment status, document status, LC deadlines, and demurrage exposure
2. **Problem Classification** - Categorizes exceptions into 4 types (shipment delay, missing document, LC discrepancy, demurrage risk)
3. **Intelligent Routing** - Routes to appropriate handler (freight team, docs team, finance, operations) with action plan and deadline
4. **Guardrails** - Same 5 guardrails as reconciliation agent (confidence, audit, privacy, compliance, HITL)
5. **Dashboard** - Real-time exception dashboard showing active exceptions, urgency levels, handlers, and time to deadline

**Tech Stack:**
- Backend: Python 3.8+
- LLM: OpenAI GPT-4o (for classification, reasoning)
- Database: SQLite (for exception tracking + audit trail)
- Frontend: Streamlit (real-time dashboard with auto-refresh)
- Scheduling: APScheduler (for periodic monitoring)
- Notifications: Email/Slack simulation (print to console for demo)

---

## FILE STRUCTURE

```
exception-triage-agent/
├── .env                              # API keys
├── .env.example                      # Template
├── requirements.txt                  # Dependencies
├── README.md                         # Setup + usage
│
├── # CORE FILES
├── app.py                            # Streamlit app with real-time dashboard
├── exception_triage_agent.py         # Core triage logic
├── real_time_monitor.py              # Monitoring + detection engine
├── database.py                       # SQLite for exceptions + audit
├── guardrails.py                     # 5 guardrails
├── notifier.py                       # Email/Slack notifications
│
├── # TEST DATA
├── test_data/
│   ├── shipment_tracking_data.json   # Mock shipment data (15 shipments)
│   ├── document_status_data.json     # Mock document status (10 LCs)
│   ├── lc_deadline_data.json         # Mock LC deadlines (8 LCs)
│   ├── laytime_data.json             # Mock laytime/demurrage (5 vessels)
│   │
│   ├── # EXCEPTION SCENARIOS (12 test cases)
│   ├── exception_01_shipment_delay.json
│   ├── exception_02_missing_document.json
│   ├── exception_03_lc_discrepancy.json
│   ├── exception_04_dd_risk.json
│   ├── exception_05_critical_delay.json
│   ├── exception_06_time_bar_approaching.json
│   ├── exception_07_multiple_issues.json
│   ├── exception_08_resolved_exception.json
│   ├── exception_09_false_alarm.json
│   ├── exception_10_urgent_escalation.json
│   ├── exception_11_routine_delay.json
│   └── exception_12_edge_case.json
│
├── # TESTING
├── run_tests.py                      # Test runner
├── test_exception_triage.py          # Unit tests
│
├── # DATABASE
├── exceptions.db                     # SQLite (auto-created)
│
└── # LOGS
    └── exception_logs/               # Exception event logs (auto-created)
```

---

## DEPENDENCIES (requirements.txt)

```txt
streamlit==1.32.0
openai==1.12.0
pandas==2.1.4
python-dotenv==1.0.0
pytest==7.4.3
apscheduler==3.10.4
```

---

## FILE 1: exception_triage_agent.py

**Purpose:** Core exception triage logic - classify problem, assess urgency, route to handler

### **Class: ExceptionTriageAgent**

```python
class ExceptionTriageAgent:
    """
    Exception triage agent that classifies problems and routes to appropriate handlers.
    
    Capabilities:
    - Classify exceptions into 4 types
    - Assess urgency (CRITICAL, HIGH, MEDIUM, LOW)
    - Route to handler with action plan
    - Generate deadlines based on urgency
    - Log all decisions to audit trail
    """
    
    def __init__(self, openai_api_key: str, database, guardrails):
        """
        Initialize Exception Triage Agent.
        
        Args:
            openai_api_key: OpenAI API key
            database: Database instance
            guardrails: Guardrails instance
        """
        self.openai_api_key = openai_api_key
        self.database = database
        self.guardrails = guardrails
        self.client = OpenAI(api_key=openai_api_key)
```

### **Exception Types (4 Categories)**

```python
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
```

### **Core Methods**

#### **1. detect_and_route()**

```python
def detect_and_route(self, exception_message: str, context: dict = None) -> dict:
    """
    Main entry point: Detect exception type, assess urgency, route to handler.
    
    Args:
        exception_message: Natural language description of the exception
                          Examples:
                          - "Vessel MV Samudra delayed 5 days"
                          - "Bill of Lading not received yet, LC expires in 3 days"
                          - "LC amount ₹50Cr vs invoice ₹52Cr"
                          - "Laytime expires in 2 days, vessel still discharging"
        
        context: Optional additional context
                 {
                     "shipment_id": str,
                     "lc_id": str,
                     "days_delayed": int,
                     "days_to_lc_deadline": int,
                     "days_to_laytime_expiry": int,
                     "daily_dd_rate": float (₹),
                     "document_type": str,
                     "vessel_name": str,
                     "port": str
                 }
    
    Returns:
    {
        "exception_id": str (auto-generated),
        "exception_type": str (SHIPMENT_DELAY | MISSING_DOCUMENT | LC_DISCREPANCY | DD_RISK),
        "original_message": str,
        "classification_confidence": int (0-100),
        "urgency": str (CRITICAL | HIGH | MEDIUM | LOW),
        "urgency_score": int (0-100),
        "handler": str (FREIGHT_TEAM | DOCS_TEAM | TRADE_FINANCE_TEAM | OPERATIONS_TEAM),
        "owner": str (email),
        "deadline": str (e.g., "4 hours", "2 hours", "24 hours"),
        "deadline_timestamp": str (ISO timestamp),
        "action_plan": [str] (list of 3-5 action items),
        "financial_impact": float (₹ exposure),
        "notification_sent": bool,
        "created_at": str (ISO timestamp),
        "audit_id": str
    }
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
    self.database.save_exception(result)
    
    # STEP 10: Send notification (optional)
    # self.notifier.send_notification(result)
    
    return result
```

#### **2. classify_exception()**

```python
def classify_exception(self, exception_message: str, context: dict = None) -> tuple[str, int]:
    """
    Classify exception into one of 4 types using keyword matching + GPT-4o.
    
    Method:
    1. Keyword-based classification (fast, 80% accurate)
    2. If confidence < 70%, use GPT-4o for nuanced classification
    
    Returns: (exception_type: str, confidence: int)
    """
    
    # STEP 1: Keyword-based classification
    message_lower = exception_message.lower()
    
    type_scores = {}
    for exc_type, info in EXCEPTION_TYPES.items():
        # Count keyword matches
        matches = sum(1 for keyword in info["keywords"] if keyword in message_lower)
        type_scores[exc_type] = matches
    
    # Get type with most matches
    best_type = max(type_scores, key=type_scores.get)
    max_matches = type_scores[best_type]
    
    # Calculate confidence based on matches
    if max_matches >= 2:
        confidence = 90  # High confidence (2+ keyword matches)
    elif max_matches == 1:
        confidence = 65  # Medium confidence (1 keyword match)
    else:
        confidence = 40  # Low confidence (no keyword matches)
    
    # STEP 2: If confidence low, use GPT-4o
    if confidence < 70:
        best_type, confidence = self._classify_with_gpt(exception_message, context)
    
    return best_type, confidence

def _classify_with_gpt(self, exception_message: str, context: dict = None) -> tuple[str, int]:
    """
    Use GPT-4o to classify exception when keywords are ambiguous.
    
    Returns: (exception_type: str, confidence: int)
    """
    
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
```

#### **3. assess_urgency()**

```python
def assess_urgency(self, exception_type: str, exception_message: str, context: dict = None) -> tuple[str, int]:
    """
    Assess urgency level (CRITICAL, HIGH, MEDIUM, LOW) and urgency score (0-100).
    
    Urgency Rules:
    
    SHIPMENT_DELAY:
    - CRITICAL: > 7 days delayed OR critical cargo OR customer contract at risk
    - HIGH: 3-7 days delayed
    - MEDIUM: 1-3 days delayed
    - LOW: < 1 day delayed
    
    MISSING_DOCUMENT:
    - CRITICAL: < 3 days to LC deadline OR < 7 days to time-bar
    - HIGH: 3-7 days to LC deadline
    - MEDIUM: 7-14 days to LC deadline
    - LOW: > 14 days to LC deadline
    
    LC_DISCREPANCY:
    - CRITICAL: Cannot be cured OR > ₹10L discrepancy
    - HIGH: Can be cured but needs amendment OR ₹5-10L discrepancy
    - MEDIUM: Minor discrepancy OR ₹1-5L discrepancy
    - LOW: Negligible discrepancy OR < ₹1L
    
    DD_RISK:
    - CRITICAL: ≤ 2 days to laytime expiry
    - HIGH: 3-5 days to laytime expiry
    - MEDIUM: 6-10 days to laytime expiry
    - LOW: > 10 days to laytime expiry
    
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
        # TODO: Add logic based on discrepancy severity
        # For now, default to MEDIUM
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
    
    return "MEDIUM", 50  # Default
```

#### **4. generate_action_plan()**

```python
def generate_action_plan(self, exception_type: str, context: dict = None) -> list[str]:
    """
    Generate 3-5 action items based on exception type.
    
    Returns: List of action items (strings)
    """
    
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
            f"3. Calculate demurrage exposure: ₹{daily_rate:,}/day",
            "4. Negotiate laytime extension with counterparty if needed",
            "5. Document all delays and reasons (weather, port congestion, equipment failure)"
        ]
    
    return ["1. Investigate issue", "2. Take corrective action", "3. Monitor resolution"]
```

#### **5. calculate_financial_impact()**

```python
def calculate_financial_impact(self, exception_type: str, context: dict = None) -> float:
    """
    Calculate potential financial impact (₹) of this exception if not resolved.
    
    Returns: float (₹ amount at risk)
    """
    
    if exception_type == "SHIPMENT_DELAY":
        days_delayed = context.get("days_delayed", 0) if context else 0
        daily_dd_rate = context.get("daily_dd_rate", 50000) if context else 50000
        
        # If already delayed, exposure is days_delayed * daily_rate
        # Plus assume another 3 days potential delay
        total_days = days_delayed + 3
        exposure = total_days * daily_dd_rate
        
        return exposure
    
    elif exception_type == "MISSING_DOCUMENT":
        # If LC misses, payment may be rejected
        # Assume LC amount as exposure
        lc_amount = context.get("lc_amount", 5000000) if context else 5000000  # ₹50L default
        
        # If < 3 days to deadline, risk is high (50% exposure)
        # If 3-7 days, risk is medium (20% exposure)
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
        # Amendment cost + potential rejection of payment
        amendment_cost = 50000  # ₹50K typical
        lc_amount = context.get("lc_amount", 5000000) if context else 5000000
        
        # Assume 10% risk of payment rejection
        exposure = amendment_cost + (lc_amount * 0.1)
        return exposure
    
    elif exception_type == "DD_RISK":
        days_to_expiry = context.get("days_to_laytime_expiry", 10) if context else 10
        daily_dd_rate = context.get("daily_dd_rate", 50000) if context else 50000
        
        # If laytime expires, we pay demurrage for every day vessel is detained
        # Assume 5 days of demurrage if we don't act
        potential_detention_days = max(0, 5 - days_to_expiry)
        exposure = potential_detention_days * daily_dd_rate
        
        return exposure
    
    return 0.0
```

#### **6. calculate_deadline_hours()**

```python
def calculate_deadline_hours(self, exception_type: str, urgency: str, context: dict = None) -> int:
    """
    Calculate deadline in hours based on exception type and urgency.
    
    Returns: int (hours until deadline)
    """
    
    # Get default deadline for this exception type
    default_hours = EXCEPTION_TYPES[exception_type]["default_deadline_hours"]
    
    # Adjust based on urgency
    if urgency == "CRITICAL":
        # Critical = half the default deadline (urgent action needed)
        return max(1, default_hours // 2)
    
    elif urgency == "HIGH":
        # High = default deadline
        return default_hours
    
    elif urgency == "MEDIUM":
        # Medium = 1.5x default deadline
        return int(default_hours * 1.5)
    
    elif urgency == "LOW":
        # Low = 2x default deadline
        return default_hours * 2
    
    return default_hours
```

---

## FILE 2: real_time_monitor.py

**Purpose:** Real-time monitoring engine that periodically checks for exceptions

### **Class: RealTimeMonitor**

```python
from apscheduler.schedulers.background import BackgroundScheduler
import time

class RealTimeMonitor:
    """
    Real-time monitoring engine that periodically checks for exceptions.
    
    Monitors:
    1. Shipment tracking (delays)
    2. Document status (missing docs)
    3. LC deadlines (time-bars)
    4. Laytime/demurrage (DD risk)
    
    Runs checks every N minutes and creates exceptions when detected.
    """
    
    def __init__(self, exception_agent, database, check_interval_minutes=5):
        """
        Initialize real-time monitor.
        
        Args:
            exception_agent: ExceptionTriageAgent instance
            database: Database instance
            check_interval_minutes: How often to run checks (default 5 min)
        """
        self.exception_agent = exception_agent
        self.database = database
        self.check_interval_minutes = check_interval_minutes
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def start(self):
        """Start the monitoring scheduler"""
        if not self.is_running:
            # Schedule periodic checks
            self.scheduler.add_job(
                self.run_all_checks,
                'interval',
                minutes=self.check_interval_minutes,
                id='exception_monitor'
            )
            
            self.scheduler.start()
            self.is_running = True
            print(f"✅ Real-time monitor started (checking every {self.check_interval_minutes} min)")
    
    def stop(self):
        """Stop the monitoring scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            print("⏹️ Real-time monitor stopped")
    
    def run_all_checks(self):
        """Run all monitoring checks"""
        print(f"\n🔍 Running exception checks at {datetime.now().strftime('%H:%M:%S')}...")
        
        # Check 1: Shipment delays
        self.check_shipment_delays()
        
        # Check 2: Missing documents
        self.check_missing_documents()
        
        # Check 3: LC deadlines
        self.check_lc_deadlines()
        
        # Check 4: Demurrage risk
        self.check_demurrage_risk()
        
        print("✅ All checks complete\n")
    
    def check_shipment_delays(self):
        """Check for shipment delays"""
        # Load shipment tracking data
        shipments = self.database.get_shipments_in_transit()
        
        for shipment in shipments:
            # Check if delayed
            expected_arrival = datetime.fromisoformat(shipment["expected_arrival"])
            now = datetime.now()
            
            if now > expected_arrival:
                days_delayed = (now - expected_arrival).days
                
                # Only create exception if not already exists
                if not self.database.exception_exists(shipment["shipment_id"], "SHIPMENT_DELAY"):
                    exception_message = f"Vessel {shipment['vessel_name']} delayed {days_delayed} days"
                    
                    context = {
                        "shipment_id": shipment["shipment_id"],
                        "vessel_name": shipment["vessel_name"],
                        "days_delayed": days_delayed,
                        "daily_dd_rate": shipment.get("daily_dd_rate", 50000)
                    }
                    
                    result = self.exception_agent.detect_and_route(exception_message, context)
                    print(f"🚨 SHIPMENT_DELAY detected: {shipment['vessel_name']} ({days_delayed} days)")
    
    def check_missing_documents(self):
        """Check for missing documents approaching LC deadline"""
        # Load LC document status
        lcs = self.database.get_active_lcs()
        
        for lc in lcs:
            # Check if documents received
            required_docs = lc.get("required_documents", [])
            received_docs = lc.get("received_documents", [])
            
            missing_docs = [doc for doc in required_docs if doc not in received_docs]
            
            if missing_docs:
                # Calculate days to deadline
                lc_expiry = datetime.fromisoformat(lc["expiry_date"])
                days_to_expiry = (lc_expiry - datetime.now()).days
                
                # Only create exception if not already exists
                if not self.database.exception_exists(lc["lc_id"], "MISSING_DOCUMENT"):
                    for doc in missing_docs:
                        exception_message = f"{doc} not received yet, LC expires in {days_to_expiry} days"
                        
                        context = {
                            "lc_id": lc["lc_id"],
                            "document_type": doc,
                            "days_to_lc_deadline": days_to_expiry,
                            "lc_amount": lc.get("lc_amount", 5000000)
                        }
                        
                        result = self.exception_agent.detect_and_route(exception_message, context)
                        print(f"🚨 MISSING_DOCUMENT detected: {doc} (deadline in {days_to_expiry} days)")
    
    def check_lc_deadlines(self):
        """Check for approaching LC deadlines"""
        # Similar to missing docs, but focuses on time-bar warnings
        pass
    
    def check_demurrage_risk(self):
        """Check for vessels approaching laytime expiry"""
        # Load vessel laytime data
        vessels = self.database.get_vessels_discharging()
        
        for vessel in vessels:
            # Check days to laytime expiry
            laytime_expiry = datetime.fromisoformat(vessel["laytime_expiry"])
            days_to_expiry = (laytime_expiry - datetime.now()).days
            
            if days_to_expiry <= 10:  # Within 10 days of expiry
                # Only create exception if not already exists
                if not self.database.exception_exists(vessel["vessel_name"], "DD_RISK"):
                    exception_message = f"Laytime expires in {days_to_expiry} days for {vessel['vessel_name']}"
                    
                    context = {
                        "vessel_name": vessel["vessel_name"],
                        "days_to_laytime_expiry": days_to_expiry,
                        "daily_dd_rate": vessel.get("daily_dd_rate", 50000)
                    }
                    
                    result = self.exception_agent.detect_and_route(exception_message, context)
                    print(f"🚨 DD_RISK detected: {vessel['vessel_name']} ({days_to_expiry} days to expiry)")
```

---

## FILE 3: database.py

**Purpose:** SQLite database for exception tracking + audit trail

### **Schema**

```sql
-- Exceptions table
CREATE TABLE IF NOT EXISTS exceptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exception_id TEXT UNIQUE NOT NULL,
    exception_type TEXT NOT NULL,
    original_message TEXT NOT NULL,
    classification_confidence INTEGER,
    urgency TEXT NOT NULL,
    urgency_score INTEGER,
    handler TEXT NOT NULL,
    owner TEXT NOT NULL,
    deadline TEXT NOT NULL,
    deadline_timestamp TEXT NOT NULL,
    action_plan TEXT NOT NULL,  -- JSON array
    financial_impact REAL,
    context TEXT,  -- JSON object
    status TEXT DEFAULT 'OPEN',  -- OPEN, IN_PROGRESS, RESOLVED, CLOSED
    created_at TEXT NOT NULL,
    updated_at TEXT,
    resolved_at TEXT,
    audit_id TEXT
);

-- Audit trail table (same as reconciliation agent)
CREATE TABLE IF NOT EXISTS audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    audit_id TEXT UNIQUE NOT NULL,
    agent TEXT NOT NULL,
    decision TEXT NOT NULL,  -- JSON
    confidence INTEGER,
    reasoning TEXT,
    status TEXT DEFAULT 'logged',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Human approvals table
CREATE TABLE IF NOT EXISTS human_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    approver TEXT NOT NULL,
    human_decision TEXT NOT NULL,
    human_notes TEXT,
    human_confidence INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audit_id) REFERENCES audit_trail(audit_id)
);

-- Shipment tracking table (mock data)
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id TEXT PRIMARY KEY,
    vessel_name TEXT NOT NULL,
    expected_arrival TEXT NOT NULL,
    actual_arrival TEXT,
    status TEXT DEFAULT 'IN_TRANSIT',
    daily_dd_rate REAL DEFAULT 50000
);

-- LC tracking table (mock data)
CREATE TABLE IF NOT EXISTS lcs (
    lc_id TEXT PRIMARY KEY,
    lc_number TEXT NOT NULL,
    expiry_date TEXT NOT NULL,
    lc_amount REAL NOT NULL,
    required_documents TEXT NOT NULL,  -- JSON array
    received_documents TEXT,  -- JSON array
    status TEXT DEFAULT 'ACTIVE'
);

-- Vessel laytime table (mock data)
CREATE TABLE IF NOT EXISTS vessels (
    vessel_name TEXT PRIMARY KEY,
    port TEXT NOT NULL,
    laytime_expiry TEXT NOT NULL,
    daily_dd_rate REAL DEFAULT 50000,
    status TEXT DEFAULT 'DISCHARGING'
);
```

### **Database Methods**

```python
class Database:
    def save_exception(self, exception_data: dict):
        """Save exception to database"""
        
    def get_exception(self, exception_id: str) -> dict:
        """Retrieve exception by ID"""
        
    def update_exception_status(self, exception_id: str, status: str):
        """Update exception status (OPEN → IN_PROGRESS → RESOLVED)"""
        
    def get_active_exceptions(self) -> list[dict]:
        """Get all OPEN or IN_PROGRESS exceptions"""
        
    def get_exceptions_by_urgency(self, urgency: str) -> list[dict]:
        """Get all exceptions of given urgency level"""
        
    def exception_exists(self, identifier: str, exception_type: str) -> bool:
        """Check if exception already exists for this shipment/LC/vessel"""
        
    def get_shipments_in_transit(self) -> list[dict]:
        """Get all shipments currently in transit"""
        
    def get_active_lcs(self) -> list[dict]:
        """Get all active LCs"""
        
    def get_vessels_discharging(self) -> list[dict]:
        """Get all vessels currently discharging"""
        
    def log_agent_decision(self, agent: str, decision: dict, confidence: int, reasoning: str) -> str:
        """Log agent decision to audit trail"""
        
    def log_human_approval(self, audit_id: str, approver: str, decision: str, notes: str, confidence: int):
        """Log human approval"""
```

---

## FILE 4: app.py (Real-Time Dashboard)

**Purpose:** Streamlit app with real-time exception dashboard

### **Page: Exception Dashboard**

```python
import streamlit as st
import time
from real_time_monitor import RealTimeMonitor

# Initialize
exception_agent = ExceptionTriageAgent(...)
database = Database()
guardrails = Guardrails(...)
monitor = RealTimeMonitor(exception_agent, database, check_interval_minutes=5)

# Start monitor
if 'monitor_started' not in st.session_state:
    monitor.start()
    st.session_state.monitor_started = True

st.title("🚨 Real-Time Exception Dashboard")

# Auto-refresh every 30 seconds
if st.button("🔄 Refresh Now") or True:
    time.sleep(0.1)  # Small delay
    st.rerun()

# Metrics at top
col1, col2, col3, col4 = st.columns(4)

active_exceptions = database.get_active_exceptions()
critical_count = len([e for e in active_exceptions if e['urgency'] == 'CRITICAL'])
high_count = len([e for e in active_exceptions if e['urgency'] == 'HIGH'])

with col1:
    st.metric("Active Exceptions", len(active_exceptions))

with col2:
    st.metric("🔴 CRITICAL", critical_count)

with col3:
    st.metric("🟠 HIGH", high_count)

with col4:
    # Time to next check
    next_check_in = 5  # minutes (calculate from scheduler)
    st.metric("Next Check In", f"{next_check_in} min")

# Exception table
st.subheader("Active Exceptions")

if active_exceptions:
    for exception in sorted(active_exceptions, key=lambda x: x['urgency_score'], reverse=True):
        # Color code by urgency
        if exception['urgency'] == 'CRITICAL':
            urgency_color = "🔴"
            container_type = st.error
        elif exception['urgency'] == 'HIGH':
            urgency_color = "🟠"
            container_type = st.warning
        elif exception['urgency'] == 'MEDIUM':
            urgency_color = "🟡"
            container_type = st.info
        else:
            urgency_color = "🟢"
            container_type = st.success
        
        with container_type(f"{urgency_color} {exception['exception_type']} - {exception['urgency']}"):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**Message:** {exception['original_message']}")
                st.write(f"**Handler:** {exception['handler']} ({exception['owner']})")
            
            with col2:
                st.write(f"**Deadline:** {exception['deadline']}")
                st.write(f"**Impact:** ₹{exception['financial_impact']:,.0f}")
            
            with col3:
                if st.button("View Details", key=exception['exception_id']):
                    st.session_state.selected_exception = exception['exception_id']
                
                if st.button("Mark Resolved", key=f"resolve_{exception['exception_id']}"):
                    database.update_exception_status(exception['exception_id'], 'RESOLVED')
                    st.success("Exception marked as resolved")
                    st.rerun()
            
            # Show action plan (expandable)
            with st.expander("Action Plan"):
                action_plan = json.loads(exception['action_plan'])
                for action in action_plan:
                    st.write(f"- {action}")
else:
    st.success("✅ No active exceptions")

# Auto-refresh
st.write("---")
st.write("Dashboard auto-refreshes every 30 seconds")
time.sleep(30)
st.rerun()
```

---

## FILE 5: Test Scenarios (12 Scenarios)

### **Exception Test Scenarios**

```python
# test_data/exception_01_shipment_delay.json
{
  "scenario_id": "exception_01_shipment_delay",
  "description": "Vessel delayed 5 days - HIGH urgency",
  "exception_message": "Vessel MV Samudra delayed 5 days from Chennai to Mumbai",
  "context": {
    "shipment_id": "SHP-2024-001",
    "vessel_name": "MV Samudra",
    "days_delayed": 5,
    "daily_dd_rate": 50000
  },
  "expected_output": {
    "exception_type": "SHIPMENT_DELAY",
    "classification_confidence": 90,
    "urgency": "HIGH",
    "urgency_score": 75,
    "handler": "FREIGHT_TEAM",
    "owner": "freight_specialist@agro-company.com",
    "deadline": "4 hours",
    "financial_impact": 400000  # (5+3)*50K
  }
}

# test_data/exception_02_missing_document.json
{
  "scenario_id": "exception_02_missing_document",
  "description": "Bill of Lading missing, 5 days to LC deadline - HIGH urgency",
  "exception_message": "Bill of Lading not received yet, LC expires in 5 days",
  "context": {
    "lc_id": "LC-2024-001",
    "document_type": "Bill of Lading",
    "days_to_lc_deadline": 5,
    "lc_amount": 5000000
  },
  "expected_output": {
    "exception_type": "MISSING_DOCUMENT",
    "classification_confidence": 90,
    "urgency": "HIGH",
    "urgency_score": 75,
    "handler": "DOCS_TEAM",
    "owner": "docs_specialist@agro-company.com",
    "deadline": "2 hours",
    "financial_impact": 1000000  # 5M * 0.2
  }
}

# test_data/exception_03_lc_discrepancy.json
{
  "scenario_id": "exception_03_lc_discrepancy",
  "description": "LC amount vs invoice mismatch - MEDIUM urgency",
  "exception_message": "LC amount ₹50Cr vs invoice ₹52Cr - discrepancy detected",
  "context": {
    "lc_id": "LC-2024-002",
    "lc_amount": 50000000,
    "invoice_amount": 52000000
  },
  "expected_output": {
    "exception_type": "LC_DISCREPANCY",
    "classification_confidence": 90,
    "urgency": "MEDIUM",
    "urgency_score": 50,
    "handler": "TRADE_FINANCE_TEAM",
    "owner": "lc_specialist@agro-company.com",
    "deadline": "24 hours",
    "financial_impact": 5050000  # 50K amendment + 5M*0.1
  }
}

# test_data/exception_04_dd_risk.json
{
  "scenario_id": "exception_04_dd_risk",
  "description": "Laytime expires in 2 days - CRITICAL urgency",
  "exception_message": "Laytime expires in 2 days for MV Atlantic at Visakhapatnam port",
  "context": {
    "vessel_name": "MV Atlantic",
    "port": "Visakhapatnam",
    "days_to_laytime_expiry": 2,
    "daily_dd_rate": 75000
  },
  "expected_output": {
    "exception_type": "DD_RISK",
    "classification_confidence": 90,
    "urgency": "CRITICAL",
    "urgency_score": 95,
    "handler": "OPERATIONS_TEAM",
    "owner": "operations_mgr@agro-company.com",
    "deadline": "1 hour",
    "financial_impact": 225000  # (5-2)*75K
  }
}

# test_data/exception_05_critical_delay.json
{
  "scenario_id": "exception_05_critical_delay",
  "description": "Vessel delayed 10 days - CRITICAL urgency",
  "exception_message": "MV Horizon delayed 10 days - critical customer contract at risk",
  "context": {
    "shipment_id": "SHP-2024-005",
    "vessel_name": "MV Horizon",
    "days_delayed": 10,
    "daily_dd_rate": 60000
  },
  "expected_output": {
    "exception_type": "SHIPMENT_DELAY",
    "urgency": "CRITICAL",
    "urgency_score": 95,
    "deadline": "2 hours",  # Half of default 4 hours (CRITICAL)
    "financial_impact": 780000  # (10+3)*60K
  }
}

# test_data/exception_06_time_bar_approaching.json
{
  "scenario_id": "exception_06_time_bar_approaching",
  "description": "Certificate of Origin missing, 2 days to LC deadline - CRITICAL",
  "exception_message": "Certificate of Origin not received, LC deadline in 2 days",
  "context": {
    "lc_id": "LC-2024-006",
    "document_type": "Certificate of Origin",
    "days_to_lc_deadline": 2,
    "lc_amount": 8000000
  },
  "expected_output": {
    "exception_type": "MISSING_DOCUMENT",
    "urgency": "CRITICAL",
    "urgency_score": 95,
    "deadline": "1 hour",
    "financial_impact": 4000000  # 8M * 0.5
  }
}

# test_data/exception_07_multiple_issues.json
{
  "scenario_id": "exception_07_multiple_issues",
  "description": "Multiple issues: delay + missing doc + DD risk",
  "exception_message": "MV Ganges delayed 4 days, Bill of Lading missing, laytime expires in 3 days",
  "context": {
    "shipment_id": "SHP-2024-007",
    "vessel_name": "MV Ganges",
    "days_delayed": 4,
    "document_type": "Bill of Lading",
    "days_to_lc_deadline": 10,
    "days_to_laytime_expiry": 3,
    "daily_dd_rate": 55000
  },
  "expected_output": {
    "exception_type": "MISSING_DOCUMENT",  # Or SHIPMENT_DELAY or DD_RISK (GPT decides priority)
    "urgency": "HIGH",
    "classification_confidence": 85  # Lower confidence due to multiple signals
  }
}

# test_data/exception_08_resolved_exception.json
{
  "scenario_id": "exception_08_resolved_exception",
  "description": "Exception that gets resolved (test status update)",
  "exception_message": "Invoice discrepancy - amount mismatch",
  "context": {
    "lc_id": "LC-2024-008"
  },
  "resolution": {
    "resolved_by": "analyst@agro-company.com",
    "resolved_at": "2024-04-20T14:30:00Z",
    "resolution_notes": "LC amendment obtained, discrepancy cleared"
  }
}

# test_data/exception_09_false_alarm.json
{
  "scenario_id": "exception_09_false_alarm",
  "description": "False alarm - vessel actually on time",
  "exception_message": "Vessel status unclear, possible delay",
  "context": {
    "shipment_id": "SHP-2024-009",
    "vessel_name": "MV Swift",
    "days_delayed": 0
  },
  "expected_output": {
    "urgency": "LOW",
    "urgency_score": 25
  }
}

# test_data/exception_10_urgent_escalation.json
{
  "scenario_id": "exception_10_urgent_escalation",
  "description": "Immediate escalation needed - contract penalty risk",
  "exception_message": "Force majeure event - port strike blocking discharge, contract penalty of ₹2Cr at risk",
  "context": {
    "shipment_id": "SHP-2024-010",
    "vessel_name": "MV Thunder",
    "days_delayed": 12,
    "daily_dd_rate": 100000,
    "contract_penalty": 20000000
  },
  "expected_output": {
    "exception_type": "SHIPMENT_DELAY",
    "urgency": "CRITICAL",
    "urgency_score": 95,
    "deadline": "1 hour",
    "financial_impact": 21500000  # (12+3)*100K + contract penalty risk
  }
}

# test_data/exception_11_routine_delay.json
{
  "scenario_id": "exception_11_routine_delay",
  "description": "Minor routine delay - LOW urgency",
  "exception_message": "Vessel running 8 hours behind schedule due to weather",
  "context": {
    "shipment_id": "SHP-2024-011",
    "vessel_name": "MV Breeze",
    "days_delayed": 0.33,  # 8 hours
    "daily_dd_rate": 45000
  },
  "expected_output": {
    "exception_type": "SHIPMENT_DELAY",
    "urgency": "LOW",
    "urgency_score": 25,
    "deadline": "8 hours",  # 2x default
    "financial_impact": 148500  # (0.33+3)*45K
  }
}

# test_data/exception_12_edge_case.json
{
  "scenario_id": "exception_12_edge_case",
  "description": "Edge case - ambiguous exception message",
  "exception_message": "Something is wrong with shipment ABC-123",
  "context": {
    "shipment_id": "SHP-2024-012"
  },
  "expected_output": {
    "classification_confidence": 40,  # Low confidence (ambiguous)
    "should_use_gpt": true
  }
}
```

---

## FILE 6: run_tests.py

```python
"""
Test runner for all 12 exception scenarios.
"""

def run_all_exception_tests():
    """
    Run all 12 test scenarios and generate report.
    
    Returns:
    {
        "total_tests": 12,
        "passed": int,
        "failed": int,
        "test_results": [...]
    }
    """
    
    scenarios = load_all_scenarios()
    results = []
    
    for scenario in scenarios:
        result = exception_agent.detect_and_route(
            scenario['exception_message'],
            scenario['context']
        )
        
        expected = scenario['expected_output']
        
        passed = (
            result['exception_type'] == expected['exception_type'] and
            result['urgency'] == expected['urgency'] and
            result['handler'] == expected['handler']
        )
        
        results.append({
            "scenario": scenario['scenario_id'],
            "passed": passed,
            "result": result,
            "expected": expected
        })
    
    return {
        "total_tests": len(scenarios),
        "passed": sum(1 for r in results if r['passed']),
        "failed": sum(1 for r in results if not r['passed']),
        "test_results": results
    }
```

---

## GUARDRAILS (Same 5 as Reconciliation Agent)

1. **Confidence Thresholds** - Route by classification confidence
2. **Audit Trails** - Immutable SQLite logging
3. **Data Privacy** - Role-based masking
4. **Compliance** - Time-bar checking, LC validation
5. **HITL** - Human approval for CRITICAL exceptions

---

## SUCCESS CRITERIA

✅ **Real-Time Monitoring:**
- Background scheduler runs every 5 minutes
- Checks shipment delays, missing docs, LC deadlines, DD risk
- Auto-creates exceptions when detected

✅ **Classification:**
- Keyword-based (fast, 80% accurate)
- GPT-4o fallback (for ambiguous cases)
- Confidence scoring (0-100)

✅ **Routing:**
- 4 exception types → 4 handler teams
- Urgency-based deadlines (CRITICAL = 1-2 hrs, LOW = 8+ hrs)
- Action plan generation (3-5 specific steps)

✅ **Financial Impact:**
- Calculate ₹ exposure for each exception
- Show on dashboard

✅ **Testing:**
- 12 test scenarios (all pass)
- Edge cases covered (ambiguous, false alarms, multiple issues)

✅ **Dashboard:**
- Real-time view of active exceptions
- Color-coded by urgency
- Auto-refresh every 30 seconds
- Mark as resolved

---

## IMPLEMENTATION PRIORITIES

**Day 1: Core Logic**
1. exception_triage_agent.py (classification, routing, action plans)
2. database.py (SQLite schema + methods)
3. guardrails.py (reuse from reconciliation agent)

**Day 2: Real-Time Monitoring**
4. real_time_monitor.py (APScheduler + checks)
5. Test data (12 scenarios + mock shipment/LC/vessel data)
6. run_tests.py

**Day 3: Dashboard**
7. app.py (Streamlit dashboard with real-time refresh)
8. Testing + debugging

---
This spec is complete and ready for Claude Code implementation. 🚀
