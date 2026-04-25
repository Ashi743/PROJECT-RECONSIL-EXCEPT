# SPEC SHEET: Reconciliation Agent + LC Doc Agent with Guardrails
## For Claude Code Terminal Implementation

---

## PROJECT OVERVIEW

**Goal:** Build a production-ready agentic AI system with 2 agents:
1. **Reconciliation Agent** - 3-way match (contract ↔ invoice ↔ receipt) with fraud detection
2. **LC Doc Agent** - Letter of Credit validation (UCP 600 compliance checks)

**Tech Stack:**
- Backend: Python 3.8+
- LLM: OpenAI GPT-4o (via `openai` package)
- Vector DB: ChromaDB (for LC document embeddings)
- Audit DB: SQLite3 (for immutable decision logs)
- Frontend: Streamlit
- Data Input: CSV files (contract, invoice, receipt) + text LC documents

**Deliverables:**
- 5 Python files (reconciliation_agent.py, doc_agent.py, guardrails.py, database.py, app.py)
- 4 mock data files (contract.csv, invoice.csv, receipt.csv, sample_lc.txt)
- 1 requirements.txt
- 1 .env.example file
- 1 README.md

---

## FILE STRUCTURE

```
reconciliation-doc-agent/
├── .env                          # API keys (user creates, not in repo)
├── .env.example                  # Template for API keys
├── requirements.txt              # Python dependencies
├── README.md                     # Setup + usage instructions
├── app.py                        # Streamlit main app
├── reconciliation_agent.py       # Reconciliation logic + GPT-4o integration
├── doc_agent.py                  # LC validation logic + GPT-4o integration
├── guardrails.py                 # 5 guardrails (confidence, audit, privacy, compliance, HITL)
├── database.py                   # ChromaDB + SQLite management
├── data/
│   ├── mock_contract.csv         # Sample contract data
│   ├── mock_invoice.csv          # Sample invoice data
│   ├── mock_receipt.csv          # Sample receipt data
│   └── sample_lc.txt             # Sample Letter of Credit text
├── chroma_db/                    # ChromaDB vector store (auto-created)
└── audit_logs.db                 # SQLite audit trail (auto-created)
```

---

## DEPENDENCIES (requirements.txt)

```txt
streamlit==1.32.0
openai==1.12.0
chromadb==0.4.22
pandas==2.1.4
python-dotenv==1.0.0
```

---

## FILE 1: .env.example

```bash
# Copy this file to .env and add your actual API key
OPENAI_API_KEY=your_openai_api_key_here
```

---

## FILE 2: database.py

**Purpose:** Manage ChromaDB (for LC document embeddings) and SQLite (for audit trail)

### Requirements:

**ChromaDB Management:**
1. Initialize ChromaDB client
2. Create collection: `lc_documents`
3. Function: `add_lc_to_vectordb(lc_text: str, lc_id: str, metadata: dict)`
   - Embed LC text using OpenAI embeddings
   - Store in ChromaDB with metadata
4. Function: `search_similar_lcs(query: str, top_k: int = 3)`
   - Search for similar LC clauses
   - Return top K results with metadata
5. Function: `get_lc_by_id(lc_id: str)`
   - Retrieve specific LC by ID

**SQLite Audit Trail Management:**
1. Initialize SQLite database: `audit_logs.db`
2. Create table: `audit_trail`
   - Columns: `id` (autoincrement), `timestamp` (TEXT), `audit_id` (TEXT UNIQUE), `agent` (TEXT), `decision` (JSON), `confidence` (INTEGER), `reasoning` (TEXT), `status` (TEXT), `created_at` (TIMESTAMP)
3. Create table: `human_approvals`
   - Columns: `id` (autoincrement), `audit_id` (TEXT FOREIGN KEY), `timestamp` (TEXT), `approver` (TEXT), `human_decision` (TEXT), `human_notes` (TEXT), `human_confidence` (INTEGER), `created_at` (TIMESTAMP)
4. Function: `log_agent_decision(agent: str, decision: dict, confidence: int, reasoning: str) -> str`
   - Insert into `audit_trail`
   - Return audit_id
5. Function: `log_human_approval(audit_id: str, approver: str, decision: str, notes: str, confidence: int)`
   - Insert into `human_approvals`
6. Function: `get_audit_trail(limit: int = 50) -> list`
   - Return recent audit entries with human approvals joined
7. Function: `get_decision_by_audit_id(audit_id: str) -> dict`
   - Return specific decision with approval status

**Important:**
- All database operations must handle errors gracefully
- SQLite writes are append-only (no UPDATE or DELETE)
- Use `json.dumps()` for storing dict objects in SQLite

---

## FILE 3: guardrails.py

**Purpose:** Implement 5 guardrails for safe agent operations

### Requirements:

**Class: Guardrails**

**Guardrail 1: Confidence-Based Routing**
```python
def route_by_confidence(self, confidence: int, decision_type: str) -> dict:
    """
    Route based on confidence score (0-100).
    
    Routing Logic:
    - confidence > 95: AUTO_APPROVE (no human needed)
    - confidence 80-95: ROUTE_TO_SPECIALIST (24h deadline)
    - confidence 50-80: ESCALATE_TO_MANAGER (2h deadline)
    - confidence < 50: ESCALATE_TO_DIRECTOR (1h deadline)
    
    Returns:
    {
        "action": str,
        "owner": str,
        "deadline": str,
        "urgency": str
    }
    """
```

**Guardrail 2: Audit Trail Logging** (delegates to database.py)
```python
def log_agent_decision(self, agent_name: str, decision: dict, confidence: int, reasoning: str) -> str:
    """Log agent decision to audit trail. Returns audit_id."""
    
def log_human_approval(self, audit_id: str, approver: str, decision: str, notes: str, confidence: int):
    """Log human approval to audit trail."""
```

**Guardrail 3: Data Privacy Masking**
```python
def mask_for_display(self, data: dict, user_role: str) -> dict:
    """
    Mask sensitive fields based on user role.
    
    Roles:
    - viewer: Show only status, deadline, action_required
    - analyst: Show essentials, mask bank_details, counterparty_name, amounts (rounded to ₹Cr)
    - manager: Show most fields, partially mask counterparty_name (first 3 + last 3 chars)
    - compliance: Full access (no masking)
    
    Sensitive fields to mask:
    - counterparty_name
    - bank_details
    - customer_contact
    - invoice_line_items
    - account_numbers
    """
```

**Guardrail 4: Compliance Checks**
```python
def check_ucp600_compliance(self, lc_data: dict) -> dict:
    """
    Check LC against UCP 600 standards.
    
    Checks:
    1. Negotiability: If LC is 'NOT_NEGOTIABLE' but contract requires negotiation → VIOLATION
    2. Expiry (Time-bar): If days_to_expiry < 7 → WARNING, if <= 0 → VIOLATION
    3. Amount: If invoice_amount > lc_amount → VIOLATION
    4. Sanctions: If counterparty in mock sanctions list → VIOLATION
    5. Incoterm Alignment: If LC incoterm != contract incoterm → WARNING
    
    Returns:
    {
        "compliant": bool,
        "violations": [{"rule": str, "severity": str, "message": str}],
        "warnings": [{"rule": str, "severity": str, "message": str}],
        "status": "PASS" | "FAIL"
    }
    """
    
def check_sanctions(self, counterparty: str) -> bool:
    """
    Check if counterparty is on sanctions list.
    
    Mock sanctions list: ["Iran Inc", "Syria Corp", "North Korea Ltd", "Cuban Export"]
    
    Returns: True if safe, False if sanctioned
    """
    
def check_time_bar(self, days_remaining: int) -> dict:
    """
    Check if time-bar is approaching.
    
    Returns:
    {
        "alert_level": "CRITICAL" | "WARNING" | "OK",
        "message": str
    }
    """
```

**Guardrail 5: HITL Workflow Helper**
```python
def create_hitl_workflow(self, agent_recommendation: dict) -> dict:
    """
    Create HITL approval workflow structure.
    
    Returns:
    {
        "id": str (audit_id),
        "status": "awaiting_approval",
        "agent_recommendation": dict,
        "created_at": str (ISO timestamp),
        "deadline": str,
        "approval_options": ["APPROVE", "REJECT", "REQUEST_INFO"],
        "requires_comment": bool
    }
    """
```

**Utility Functions:**
```python
def _generate_audit_id(self) -> str:
    """Generate unique audit ID: AUD-{8_char_hex}"""
    
def _get_specialist(self, decision_type: str) -> str:
    """Get specialist email for decision type"""
    
def _get_manager(self, decision_type: str) -> str:
    """Get manager email for decision type"""
    
def _get_director(self, decision_type: str) -> str:
    """Get director email"""
    
def _calculate_deadline(self, recommendation: dict) -> str:
    """Calculate deadline based on urgency"""
```

---

## FILE 4: doc_agent.py

**Purpose:** LC (Letter of Credit) validation agent using GPT-4o

### Requirements:

**Class: LCDocAgent**

**Initialization:**
```python
def __init__(self, openai_api_key: str, database, guardrails):
    """
    Initialize LC Doc Agent.
    
    Args:
        openai_api_key: OpenAI API key
        database: Database instance (for ChromaDB + SQLite)
        guardrails: Guardrails instance
    """
```

**Core Functions:**

```python
def validate_lc(self, lc_text: str, contract_terms: dict) -> dict:
    """
    Validate LC document against contract terms using GPT-4o.
    
    Steps:
    1. Extract key LC fields using GPT-4o:
       - LC amount
       - Expiry date
       - Negotiability (NEGOTIABLE | NOT_NEGOTIABLE)
       - Incoterm
       - Beneficiary
       - Applicant
       - Issuing bank
       - Key clauses
    
    2. Store LC in ChromaDB for future semantic search
    
    3. Compare LC fields vs contract_terms:
       - Amount match (LC >= contract amount)
       - Incoterm match (LC incoterm == contract incoterm)
       - Expiry safe (> 7 days remaining)
       - Negotiability match
    
    4. Run compliance checks (via guardrails.check_ucp600_compliance)
    
    5. Calculate confidence score:
       - Perfect match: 100%
       - Minor warnings: 80-95%
       - Violations: < 50%
    
    6. Determine action using guardrails.route_by_confidence
    
    7. Log decision to audit trail
    
    Returns:
    {
        "lc_id": str,
        "status": str (APPROVED | ROUTE_TO_SPECIALIST | ESCALATE | REJECTED),
        "confidence": int,
        "extracted_fields": dict,
        "comparison_results": dict,
        "compliance_check": dict,
        "routing": dict,
        "audit_id": str,
        "reasoning": str
    }
    """

def extract_lc_fields(self, lc_text: str) -> dict:
    """
    Use GPT-4o to extract structured fields from LC text.
    
    Prompt GPT-4o to extract:
    - lc_amount (float)
    - currency (str)
    - expiry_date (str)
    - days_to_expiry (int) - calculate from today
    - negotiability (str)
    - incoterm (str)
    - beneficiary (str)
    - applicant (str)
    - issuing_bank (str)
    - key_clauses (list of str)
    
    Returns: dict with extracted fields
    """

def compare_lc_to_contract(self, lc_fields: dict, contract_terms: dict) -> dict:
    """
    Compare LC fields to contract terms.
    
    Checks:
    - Amount: LC amount >= contract amount? (allow up to 10% variance)
    - Incoterm: LC incoterm == contract incoterm?
    - Expiry: Days to expiry > 7?
    - Negotiability: LC negotiability matches contract requirement?
    
    Returns:
    {
        "amount_match": {"status": "PASS|FAIL|WARNING", "message": str},
        "incoterm_match": {"status": "PASS|FAIL", "message": str},
        "expiry_safe": {"status": "PASS|WARNING|FAIL", "message": str},
        "negotiability_match": {"status": "PASS|FAIL", "message": str},
        "overall_status": "PASS|FAIL"
    }
    """

def calculate_lc_confidence(self, comparison: dict, compliance: dict) -> int:
    """
    Calculate confidence score based on comparison results and compliance.
    
    Scoring:
    - Start at 100
    - Each FAIL: -40
    - Each WARNING: -15
    - Each compliance violation: -30
    - Each compliance warning: -10
    
    Returns: int (0-100)
    """
```

**GPT-4o Integration Pattern:**
```python
# Use OpenAI client
from openai import OpenAI
client = OpenAI(api_key=self.openai_api_key)

# Call GPT-4o with structured prompt
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are an expert LC validator..."},
        {"role": "user", "content": f"Extract fields from this LC:\n\n{lc_text}"}
    ],
    response_format={"type": "json_object"},  # Force JSON output
    temperature=0.1  # Low temp for consistency
)

result = json.loads(response.choices[0].message.content)
```

---

## FILE 5: reconciliation_agent.py

**Purpose:** 3-way reconciliation (contract ↔ invoice ↔ receipt) with fraud detection

### Requirements:

**Class: ReconciliationAgent**

**Initialization:**
```python
def __init__(self, openai_api_key: str, database, guardrails):
    """
    Initialize Reconciliation Agent.
    
    Args:
        openai_api_key: OpenAI API key
        database: Database instance
        guardrails: Guardrails instance
    """
```

**Mock Test Scenarios:**
```python
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
```

**Core Functions:**

```python
def reconcile(self, contract: dict, invoice: dict, receipt: dict) -> dict:
    """
    Perform 3-way reconciliation with fraud detection.
    
    Steps:
    1. Check quantity match (contract vs invoice vs receipt)
    2. Check price match (contract vs invoice)
    3. Check timeline (invoice date vs receipt date)
    4. Detect anomalies (fraud signals)
    5. Calculate confidence score
    6. Determine routing (via guardrails)
    7. Log decision to audit trail
    8. (Optional) Use GPT-4o for edge case reasoning
    
    Returns:
    {
        "status": str (AUTO_APPROVE | ROUTE_TO_SPECIALIST | ESCALATE_TO_MANAGER | ESCALATE_TO_DIRECTOR),
        "confidence": int,
        "matches": {
            "qty_match": dict,
            "price_match": dict,
            "timeline_match": dict
        },
        "anomalies": [dict],
        "routing": dict,
        "audit_id": str,
        "reasoning": str,
        "financial_impact": float
    }
    """

def check_qty_match(self, contract: dict, invoice: dict, receipt: dict) -> dict:
    """
    Check quantity matching across 3 documents.
    
    Variance Rules:
    - < 0.5%: GREEN (perfect match)
    - 0.5-2%: YELLOW (acceptable, -15 confidence)
    - > 2%: RED (requires review, -40 confidence)
    
    Returns:
    {
        "status": "GREEN|YELLOW|RED",
        "contract_qty": float,
        "invoice_qty": float,
        "receipt_qty": float,
        "variance_pct": float,
        "message": str,
        "confidence_penalty": int
    }
    """

def check_price_match(self, contract: dict, invoice: dict) -> dict:
    """
    Check price matching.
    
    Variance Rules:
    - < 0.5%: GREEN
    - 0.5-1%: YELLOW (-15 confidence)
    - > 1%: RED (-40 confidence)
    
    Returns: Similar to check_qty_match
    """

def check_timeline(self, invoice: dict, receipt: dict) -> dict:
    """
    Check timeline (invoice should be after receipt).
    
    Rules:
    - Invoice date <= 5 days after receipt: GREEN
    - 5-10 days: YELLOW (-10 confidence)
    - > 10 days: RED (-20 confidence)
    
    Returns:
    {
        "status": "GREEN|YELLOW|RED",
        "invoice_date": str,
        "receipt_date": str,
        "days_diff": int,
        "message": str,
        "confidence_penalty": int
    }
    """

def detect_anomalies(self, contract: dict, invoice: dict, receipt: dict) -> list:
    """
    Detect fraud signals and anomalies.
    
    Anomalies to detect:
    1. QTY_MISMATCH: Invoice qty != receipt qty (-20 confidence)
    2. PRICE_REDUCTION: Invoice price < contract price (track percentage)
    3. QTY_INCREASE: Invoice qty > contract qty
    4. SUSPICIOUS_COMBO: Price reduction + extra qty together (-30 confidence, fraud signal)
    5. TIMELINE_GAP: Invoice > 10 days after receipt
    
    Returns:
    [
        {
            "type": str,
            "severity": "LOW|MEDIUM|HIGH|CRITICAL",
            "message": str,
            "confidence_penalty": int,
            "financial_impact": float
        }
    ]
    """

def calculate_confidence(self, matches: dict, anomalies: list) -> int:
    """
    Calculate overall confidence score.
    
    Scoring:
    - Start at 100
    - Apply penalties from matches (qty, price, timeline)
    - Apply penalties from anomalies
    - Floor at 0, ceiling at 100
    
    Returns: int (0-100)
    """

def use_gpt_for_edge_case(self, contract: dict, invoice: dict, receipt: dict, anomalies: list) -> str:
    """
    (Optional) Use GPT-4o for complex reasoning on edge cases.
    
    Only call GPT if:
    - Confidence is in gray zone (60-80%)
    - Multiple anomalies detected
    - Unusual patterns
    
    Prompt GPT-4o to analyze and recommend action.
    
    Returns: str (GPT's reasoning)
    """
```

---

## FILE 6: app.py

**Purpose:** Streamlit frontend with HITL approval workflow

### Requirements:

**Structure:**

```python
import streamlit as st
from reconciliation_agent import ReconciliationAgent, MOCK_SCENARIOS
from doc_agent import LCDocAgent
from guardrails import Guardrails
from database import Database
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize components
@st.cache_resource
def init_components():
    db = Database()
    guardrails = Guardrails(db)
    recon_agent = ReconciliationAgent(openai_api_key, db, guardrails)
    lc_agent = LCDocAgent(openai_api_key, db, guardrails)
    return db, guardrails, recon_agent, lc_agent

db, guardrails, recon_agent, lc_agent = init_components()

# Streamlit UI configuration
st.set_page_config(page_title="Trade Operations AI", layout="wide")
st.title("🚀 Trade Operations Agentic Assistant")

# Sidebar navigation
page = st.sidebar.radio("Choose Agent:", [
    "🏠 Home",
    "📊 Reconciliation Agent",
    "📄 LC Doc Agent",
    "📋 Audit Trail",
    "📈 Dashboard"
])
```

**Page 1: Home**
- Welcome message
- Quick stats (total decisions, auto-approvals, escalations)
- Quick links to agents

**Page 2: Reconciliation Agent**

UI Flow:
```
1. Input Method Selection:
   ☑ Upload CSV Files  ☐ Paste JSON  ☐ Choose Test Scenario

2a. If Upload CSV:
    - Upload contract.csv, invoice.csv, receipt.csv
    - Preview uploaded data (show first 3 rows)
    - Parse CSV to dict
    - [▶️ Run Reconciliation] button

2b. If Paste JSON:
    - Text area to paste JSON
    - [▶️ Parse & Run] button

2c. If Choose Test Scenario:
    - Dropdown: Select from MOCK_SCENARIOS keys
    - Show scenario data (contract, invoice, receipt side-by-side)
    - [▶️ Run] button

3. Results Display:
   - Show status (with color coding)
   - Show confidence meter (progress bar)
   - Show matches summary (qty, price, timeline) with ✅ or ⚠️ icons
   - Show anomalies (if any) with severity badges
   - Show routing decision (who to send, deadline)
   - Show financial impact

4. HITL Approval Workflow (if needed):
   - Show agent's recommendation clearly
   - Show side-by-side comparison table
   - Decision buttons: [✅ APPROVE] [❌ REJECT] [❓ REQUEST_INFO]
   - Text area for human notes
   - Slider for human confidence (0-100)
   - [Submit Decision] button
   - On submit: Log to audit trail, show success message

5. Download Result as JSON button
```

**Page 3: LC Doc Agent**

UI Flow:
```
1. Input LC Document:
   ☑ Upload TXT file  ☐ Paste LC Text  ☐ Use Sample LC

2. Input Contract Terms:
   - Form fields:
     * Contract Amount (float)
     * Currency (str, default USD)
     * Incoterm (dropdown: FOB, CIF, CFR, EXW, etc.)
     * Requires Negotiation? (checkbox)
   - OR upload contract.csv

3. [▶️ Validate LC] button

4. Results Display:
   - Show extracted LC fields (table format)
   - Show comparison results (LC vs contract)
   - Show compliance check results (violations, warnings)
   - Show confidence score
   - Show routing decision
   - Show reasoning (text from GPT-4o + rule-based logic)

5. HITL Approval (similar to reconciliation)

6. Search Similar LCs:
   - Input: Query text
   - Button: [🔍 Search Vector DB]
   - Results: Show top 3 similar LCs from ChromaDB
```

**Page 4: Audit Trail**

UI Flow:
```
1. Display recent audit entries (last 50)
   - Table with columns:
     * Audit ID
     * Timestamp
     * Agent
     * Decision
     * Confidence
     * Status (awaiting_approval | approved | rejected)
     * Approver
     * Human Notes
   
2. Filter options:
   - By agent (Reconciliation | LC Doc)
   - By status (all | awaiting | approved | rejected)
   - Date range

3. Search by audit ID

4. Click row to expand and see full details

5. Download audit trail as CSV
```

**Page 5: Dashboard**

UI Flow:
```
1. Metrics (4 columns):
   - Total Decisions
   - Auto-Approvals (%)
   - Escalations (%)
   - Average Confidence

2. Charts:
   - Decisions over time (line chart)
   - Decision distribution (pie chart: auto-approve, specialist, manager, director)
   - Confidence distribution (histogram)

3. Recent Activity:
   - Last 10 decisions (mini table)
```

**UI Styling Guidelines:**
- Use st.columns() for side-by-side layouts
- Use st.metric() for key metrics
- Use st.success(), st.warning(), st.error() for color-coded messages
- Use st.expander() for collapsible sections
- Use st.progress() for confidence bars
- Use emojis for visual clarity (✅ ⚠️ ❌ 🟢 🟡 🔴)

---

## FILE 7: Mock Data Files

**data/mock_contract.csv:**
```csv
qty_mt,price_usd,date,incoterm,counterparty
100,500,2024-04-01,CIF,Reliance Industries
```

**data/mock_invoice.csv:**
```csv
qty_mt,price_usd,date,invoice_number
100,500,2024-04-15,INV-2024-001
```

**data/mock_receipt.csv:**
```csv
qty_mt,date,receipt_number
100,2024-04-10,RCP-2024-001
```

**data/sample_lc.txt:**
```
LETTER OF CREDIT

LC Number: LC-2024-001
Issuing Bank: HDFC Bank, Mumbai
Issue Date: March 15, 2024
Expiry Date: June 30, 2024

Applicant: ABC Trading Company
Beneficiary: Reliance Industries

Amount: USD 50,000.00
Currency: United States Dollars

Incoterm: CIF Mumbai

Negotiability: NEGOTIABLE

Description of Goods:
100 Metric Tons of Crude Oil

Documents Required:
1. Commercial Invoice in triplicate
2. Full set of clean on-board Bill of Lading
3. Certificate of Origin
4. Insurance Certificate covering 110% of invoice value

Shipment: From Ras Tanura to Mumbai
Latest Shipment Date: May 31, 2024

Special Conditions:
- Partial shipments: Not allowed
- Transshipment: Not allowed
- Documents must be presented within 21 days of shipment date

Charges: All banking charges outside issuing bank are for beneficiary's account

This LC is subject to UCP 600.
```

---

## FILE 8: README.md

**Contents:**

```markdown
# Trade Operations Agentic Assistant

Production-ready AI system with 2 agents:
1. Reconciliation Agent - 3-way match with fraud detection
2. LC Doc Agent - Letter of Credit validation

## Features
- ✅ OpenAI GPT-4o integration
- ✅ ChromaDB vector storage for LC documents
- ✅ SQLite audit trail (immutable logs)
- ✅ 5 guardrails (confidence, audit, privacy, compliance, HITL)
- ✅ Streamlit UI with human approval workflow

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create .env file:
```bash
cp .env.example .env
# Add your OpenAI API key to .env
```

3. Run the app:
```bash
streamlit run app.py
```

## Usage

### Reconciliation Agent
1. Upload CSV files (contract, invoice, receipt) OR choose test scenario
2. Click "Run Reconciliation"
3. Review results
4. Approve/Reject if needed

### LC Doc Agent
1. Upload LC text file OR paste LC content
2. Enter contract terms
3. Click "Validate LC"
4. Review validation results
5. Approve/Reject if needed

## Project Structure
- `app.py` - Streamlit frontend
- `reconciliation_agent.py` - 3-way reconciliation logic
- `doc_agent.py` - LC validation logic
- `guardrails.py` - 5 guardrails implementation
- `database.py` - ChromaDB + SQLite management
- `data/` - Mock test data

## Guardrails
1. Confidence Thresholds (auto-approve >95%)
2. Audit Trail (immutable SQLite logs)
3. Data Privacy (role-based masking)
4. Compliance Checks (UCP 600, sanctions)
5. Human-in-the-Loop (approval workflow)

## Tech Stack
- Python 3.8+
- OpenAI GPT-4o
- ChromaDB (vector storage)
- SQLite (audit logs)
- Streamlit (UI)
```

---

## IMPLEMENTATION PRIORITIES

**Day 1 (Core Logic):**
1. ✅ database.py (ChromaDB + SQLite setup)
2. ✅ guardrails.py (all 5 guardrails)
3. ✅ reconciliation_agent.py (3-way match + fraud detection)

**Day 2 (LC Agent + UI):**
4. ✅ doc_agent.py (LC validation with GPT-4o)
5. ✅ app.py (Streamlit UI - Reconciliation page)
6. ✅ app.py (Streamlit UI - LC Doc page)

**Day 3 (Polish):**
7. ✅ app.py (Audit Trail + Dashboard pages)
8. ✅ Mock data files
9. ✅ README.md
10. ✅ Testing + bug fixes

---

## CRITICAL REQUIREMENTS

**Error Handling:**
- All OpenAI API calls must have try-except blocks
- All database operations must handle errors gracefully
- Show user-friendly error messages in Streamlit

**GPT-4o Response Format:**
- Always use `response_format={"type": "json_object"}` for structured extraction
- Always set `temperature=0.1` for consistency
- Always validate JSON response before using

**Audit Trail:**
- SQLite operations are append-only (no UPDATE or DELETE)
- Use `json.dumps()` for storing dicts
- Every decision must be logged before returning to user

**ChromaDB:**
- Initialize collection only once (check if exists)
- Store LC text with metadata (lc_id, date, counterparty, etc.)
- Use OpenAI embeddings for semantic search

**Streamlit Best Practices:**
- Use `@st.cache_resource` for database/agent initialization
- Use `st.session_state` for maintaining state between reruns
- Show loading spinners for long operations (`with st.spinner()`)
- Clear, color-coded UI (success=green, warning=yellow, error=red)

---

## TESTING CHECKLIST

Before delivery:
- [ ] Test reconciliation with all 5 mock scenarios
- [ ] Test LC validation with sample_lc.txt
- [ ] Test file upload (CSV + TXT)
- [ ] Test HITL approval workflow
- [ ] Test audit trail logging and retrieval
- [ ] Test ChromaDB vector search
- [ ] Test error handling (invalid API key, malformed data)
- [ ] Test UI responsiveness (mobile view)
- [ ] Verify audit logs are immutable
- [ ] Verify all guardrails function correctly

---

## DELIVERABLE CHECKLIST

Files to create:
- [ ] requirements.txt
- [ ] .env.example
- [ ] database.py
- [ ] guardrails.py
- [ ] reconciliation_agent.py
- [ ] doc_agent.py
- [ ] app.py
- [ ] data/mock_contract.csv
- [ ] data/mock_invoice.csv
- [ ] data/mock_receipt.csv
- [ ] data/sample_lc.txt
- [ ] README.md

---

## SUCCESS CRITERIA

✅ **Reconciliation Agent:**
- Correctly identifies perfect match (100% confidence)
- Detects fraud signals (extra qty + price drop)
- Routes based on confidence (auto-approve >95%)
- Logs every decision to audit trail

✅ **LC Doc Agent:**
- Extracts LC fields using GPT-4o
- Validates against contract terms
- Checks UCP 600 compliance
- Stores LC in ChromaDB for semantic search

✅ **Guardrails:**
- Confidence thresholds work correctly
- Audit trail is immutable
- Data masking works by role
- Compliance checks detect violations
- HITL workflow captures human decisions

✅ **UI:**
- Clean, intuitive interface
- File upload works
- Mock scenarios work
- HITL approval buttons work
- Audit trail displays correctly
- Dashboard shows metrics

---

## NOTES FOR CLAUDE CODE

1. **Start with database.py** - this is the foundation
2. **Then guardrails.py** - this is used by both agents
3. **Then reconciliation_agent.py** - simpler than LC agent
4. **Then doc_agent.py** - uses GPT-4o for extraction
5. **Finally app.py** - ties everything together

**OpenAI API Pattern:**
```python
from openai import OpenAI
import json

client = OpenAI(api_key=api_key)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are an expert..."},
        {"role": "user", "content": "Task..."}
    ],
    response_format={"type": "json_object"},
    temperature=0.1
)

result = json.loads(response.choices[0].message.content)
```

**SQLite Pattern:**
```python
import sqlite3
import json

conn = sqlite3.connect('audit_logs.db')
cursor = conn.cursor()

# Insert
cursor.execute(
    "INSERT INTO audit_trail (audit_id, agent, decision, confidence) VALUES (?, ?, ?, ?)",
    (audit_id, agent, json.dumps(decision), confidence)
)
conn.commit()

# Query
cursor.execute("SELECT * FROM audit_trail ORDER BY created_at DESC LIMIT 50")
rows = cursor.fetchall()
```

**ChromaDB Pattern:**
```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("lc_documents")

# Add document
collection.add(
    documents=[lc_text],
    metadatas=[{"lc_id": lc_id, "date": date}],
    ids=[lc_id]
)

# Search
results = collection.query(
    query_texts=[query],
    n_results=3
)
```

---

## END OF SPEC SHEET

This spec sheet contains everything needed to build the complete system.
Claude Code should implement each file sequentially, following the patterns and requirements outlined above.

Good luck! 🚀
