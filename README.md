# Trade Operations AI Platform (Unified)

Production-ready platform with **2 intelligent agents** working together to manage trade operations in real-time.

1. **Reconciliation Agent** (v2.0) - 3-way reconciliation with 3D variance analysis, 9+ fraud signals, 8+ anomaly patterns, and financial impact tracking
2. **Exception Triage Agent** (v1.0) - Real-time monitoring, classification, and routing of operational exceptions with intelligent urgency assessment
3. **LC Doc Agent** - Letter of Credit validation with UCP 600 compliance checks (integrated into unified platform)

## ✨ Unified Platform Features (v3.0)

### Exception Triage Agent (NEW)

**Real-Time Monitoring**
- Continuous monitoring of shipments, documents, LCs, and laytime
- Automatic exception detection and classification
- 4 exception types: SHIPMENT_DELAY, MISSING_DOCUMENT, LC_DISCREPANCY, DD_RISK

**Intelligent Routing**
- Auto-routes to appropriate handler teams
- Urgency-based deadlines (CRITICAL: 1h, HIGH: 4h, MEDIUM: 6h, LOW: 8h+)
- Action plan generation (3-5 specific steps per exception)

**Financial Impact Tracking**
- Calculates ₹ exposure for each exception
- Demurrage costs for shipment delays
- LC amendment costs for discrepancies
- Payment rejection risk for missing documents

**Real-Time Dashboard**
- Active exceptions list (color-coded by urgency)
- Auto-refresh every 30 seconds
- Quick-access action plans
- Mark as resolved workflow

### Reconciliation Agent - Advanced Detection

**3D Variance Analysis**
- Contract ↔ Invoice variance calculation
- Invoice ↔ Receipt variance calculation
- Contract ↔ Receipt variance calculation
- Severity classification: GREEN (<0.5%), YELLOW (0.5-2%), ORANGE (2-5%), RED (>5%)

**Fraud Detection** (9+ patterns)
- Quantity overstatement (invoice claims > received)
- Price manipulation (suspicious price drops/increases)
- Timeline manipulation (impossible dates, excessive delays)
- Suspicious combos (price ↓ + qty ↑ = classic fraud signal)
- **Fraud Score**: 0-100 scale with financial exposure calculation

**Anomaly Detection** (8+ patterns)
- Quantity mismatches (contract↔invoice, invoice↔receipt, circular)
- Price anomalies (too low, too high, zero price)
- Logical inconsistencies
- Statistical outlier detection
- **Confidence Scoring**: Each anomaly deducts 3-50 points

**Enhanced HITL Workflow**
- Side-by-side comparison tables (Contract vs Invoice vs Receipt)
- Detailed issue summary for human review
- Blended confidence calculation (70% agent + 30% human if agreement)
- Approval chain tracking with override detection
- Suggested actions for each issue

## Features

- ✅ **OpenAI GPT-4o Integration** - Advanced reasoning for edge cases and LC field extraction
- ✅ **ChromaDB Vector Storage** - Semantic search for LC documents
- ✅ **SQLite Audit Trail** - Immutable logs of all decisions and approvals
- ✅ **5 Guardrails**:
  - Confidence-based routing (auto-approve >95%)
  - Audit trail logging
  - Data privacy masking by role
  - Compliance checks (UCP 600, sanctions)
  - Human-in-the-Loop workflow with HITL data structures
- ✅ **Streamlit UI** - 5 pages with enhanced Reconciliation page:
  - Home (metrics + quick links)
  - Reconciliation Agent (NEW: Variance, Fraud, Anomaly, Confidence Breakdown sections)
  - LC Doc Agent
  - Audit Trail
  - Dashboard

## Tech Stack

- **Backend**: Python 3.8+
- **LLM**: OpenAI GPT-4o
- **Vector DB**: ChromaDB (for LC embeddings)
- **Audit DB**: SQLite (immutable logs)
- **Frontend**: Streamlit
- **Testing**: Pytest (15 comprehensive test scenarios)
- **Data Format**: CSV files + text documents

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create .env File

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

Your `.env` should look like:
```
OPENAI_API_KEY=sk-...your-key-here...
```

### 3. Run the Application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Project Structure

```
bunge-agents/
├── # CORE AGENTS
├── reconciliation_agent.py         # 3-way matching with fraud/anomaly detection
├── exception_triage_agent.py       # NEW: Exception classification & routing
├── real_time_monitor.py            # NEW: Background monitoring (APScheduler)
├── doc_agent.py                    # Letter of Credit validation
│
├── # INFRASTRUCTURE
├── app.py                          # MERGED: 7-page unified Streamlit app
├── guardrails.py                   # Shared guardrails (confidence, audit, privacy, compliance, HITL)
├── database.py                     # EXTENDED: SQLite + ChromaDB (7 tables total)
├── requirements.txt                # Python dependencies
├── .env.example                    # API key template
│
├── # TESTING
├── run_tests.py                    # 15 reconciliation scenarios
├── run_exception_tests.py          # NEW: 12 exception scenarios
├── test_data/                      # NEW: 12 exception test files
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
├── # DOCUMENTATION
├── README.md                       # This file (updated for v3.0)
├── ENHANCEMENTS.md                 # Technical details of v2.0 features
├── PROGRESS.md                     # Implementation tracking
├── MERGE_SUMMARY.md                # NEW: Merge architecture & results
│
├── # DATA
├── data/
│   ├── mock_contract.csv
│   ├── mock_invoice.csv
│   ├── mock_receipt.csv
│   └── sample_lc.txt
│
├── # BACKUPS
├── app_v1_reconciliation_only.py   # BACKUP: Original app before merge
│
├── # DATABASE
├── chroma_db/                      # ChromaDB vector store (auto-created)
└── audit_logs.db                   # SQLite audit trail (auto-created)
```

## Usage

### Starting the Platform

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501` with 7 pages available in the sidebar.

### Platform Navigation (7 Pages)

**Page 1: 🏠 Home**
- Platform overview and key metrics
- Quick links to both agents
- Recent activity feed (both agents)
- Auto-approve rate, total financial exposure

**Page 2: 🔄 Reconciliation Agent**
- 3-way document matching
- Upload CSV files or paste JSON data
- 15 test scenarios available
- Comprehensive analysis: variance, fraud, anomaly detection
- HITL workflow for human approval

**Page 3: 🚨 Exception Triage Dashboard**
- Real-time view of active exceptions
- Color-coded by urgency (CRITICAL/HIGH/MEDIUM/LOW)
- Auto-refresh every 30 seconds
- Quick actions: View Details, Mark Resolved
- Expandable action plans

**Page 4: 📋 Exception Details & Routing**
- Select any active exception
- Full details and routing information
- Context data and action plan
- Resolution workflow
- Mark as resolved

**Page 5: 📊 Unified Audit Trail**
- Both agents' decisions in one place
- Filter by agent type
- Comprehensive decision history
- Audit trail export capability

**Page 6: 🔔 Alerts & Notifications**
- CRITICAL alerts (immediate action needed)
- HIGH priority alerts (urgent)
- Alert details and handler information

**Page 7: ⚙️ Settings**
- Monitoring interval configuration
- Auto-approve threshold adjustment
- Critical exception escalation settings

### Reconciliation Agent (Page 2)

Use for 3-way matching with advanced variance, fraud, and anomaly detection.

**Steps:**
1. Go to **📊 Reconciliation Agent** page
2. Choose input method:
   - Upload CSV files (contract, invoice, receipt)
   - Paste JSON data
   - Select a test scenario (5 mock scenarios included)
3. Click **Run Reconciliation**
4. Review comprehensive results:
   - **📊 Variance Analysis**: 3D variance with severity
   - **🚨 Fraud Detection**: Fraud score (0-100) + financial exposure
   - **⚠️ Anomaly Detection**: Patterns with severity + confidence
   - **📈 Confidence Breakdown**: Detailed penalty analysis
5. **👤 HITL Approval**: Side-by-side comparison + detailed issue list
   - Review issues with suggested actions
   - Make informed approval decision
   - Capture human confidence (0-100)
   - Submit with notes

**Mock Scenarios:**
- `perfect_match` - All fields match exactly (100% confidence)
- `minor_variance` - Small discrepancies < 2% (75-85% confidence)
- `major_variance` - Large discrepancies 2-5% (40-60% confidence)
- `fraud_signal` - Extra qty + price drop (15-30% confidence) 🚨
- `qty_mismatch` - Invoice ≠ receipt (45-65% confidence)

### LC Doc Agent

Use for Letter of Credit validation against contract terms.

**Steps:**
1. Go to **📄 LC Doc Agent** page
2. Input LC document:
   - Upload TXT file
   - Paste LC text
   - Use sample LC
3. Input contract terms:
   - Amount, Currency, Incoterm, Negotiation requirement
4. Click **Validate LC**
5. Review validation results:
   - Extracted LC fields (via GPT-4o)
   - Comparison with contract (amount, incoterm, expiry, negotiability)
   - Compliance check results (UCP 600)
   - Confidence score and routing decision
6. Search similar LCs in vector database

## Guardrails Explained

### 1. Confidence-Based Routing

Routes decisions automatically:

| Confidence | Action | Owner | Deadline | Urgency |
|-----------|--------|-------|----------|---------|
| > 95% | AUTO_APPROVE | None | None | NONE |
| 80-95% | ROUTE_TO_SPECIALIST | Specialist | 24h | MEDIUM |
| 50-80% | ESCALATE_TO_MANAGER | Manager | 2h | HIGH |
| < 50% | ESCALATE_TO_DIRECTOR | Director | 1h | CRITICAL |

### 2. Audit Trail Logging

Every decision logged to immutable SQLite database:
- Agent decision with full details
- Variance analysis breakdown
- Fraud signals detected
- Anomalies found
- Confidence breakdown
- Human approval (if applicable)
- Approver notes and timestamp

### 3. Data Privacy Masking

Sensitive fields masked based on user role:
- **viewer**: Full redaction
- **analyst**: Essential fields, masked amounts
- **manager**: Most fields, partial masking of counterparty
- **compliance**: Full access

### 4. Compliance Checks

Validates against trade finance standards:
- **UCP 600** - LC negotiability, expiry, amount
- **Sanctions** - Check if counterparty is sanctioned
- **Time-bar** - Days until LC expiry
- **Incoterm alignment** - LC incoterm matches contract

### 5. Human-in-the-Loop (HITL)

For decisions that need human review:
- Agent recommendation shown clearly
- Side-by-side comparison of all documents
- Issues highlighted with severity and suggested actions
- Human can approve, reject, or request more info
- Human confidence and notes logged
- Approval is traceable in audit trail

## Variance Analysis Details

### 3D Variance Calculation

The system calculates variance across three dimensions:

**Contract ↔ Invoice:**
```
Variance % = (invoice_value - contract_value) / contract_value × 100
```

**Invoice ↔ Receipt:**
```
Variance % = (receipt_value - invoice_value) / invoice_value × 100
```

**Contract ↔ Receipt:**
```
Variance % = (receipt_value - contract_value) / contract_value × 100
```

### Severity Classification

- **GREEN**: < 0.5% variance (perfect match, no penalty)
- **YELLOW**: 0.5% - 2% variance (acceptable, -15 confidence)
- **ORANGE**: 2% - 5% variance (major, requires review, -25 confidence)
- **RED**: > 5% variance (extreme, -40 confidence)

## Fraud Detection Details

### Fraud Signals (9+ patterns)

1. **QTY_OVERSTATEMENT** - Invoice claims more than receipt shows
2. **PRICE_DOWN_QTY_UP** - Classic fraud pattern (price ↓ while qty ↑)
3. **PRICE_MANIPULATION** - Suspicious price changes (>5% variance)
4. **INVOICE_BEFORE_RECEIPT** - CRITICAL: Impossible timeline
5. **UNUSUAL_DELAY** - Invoice > 30 days after receipt
6. **SHIPMENT_DELAY** - Shipment > 30 days after contract
7. **PRICE_TOO_HIGH** - Invoice > 130% of contract
8. **PRICE_TOO_LOW** - Invoice < 70% of contract
9. **DUPLICATE_INVOICE** - Same invoice submitted twice

### Fraud Score (0-100)

- **0-25**: LOW RISK (safe to approve)
- **25-50**: MEDIUM RISK (escalate to specialist)
- **50-75**: HIGH RISK (escalate to manager)
- **75-100**: CRITICAL RISK (escalate to director, investigate)

### Financial Exposure

Each fraud signal includes potential financial loss:
```
Exposure = Quantity_Discrepancy × Price
```

## Anomaly Detection Details

### Quantity Anomalies

- **INVOICE_QTY_NOT_IN_RECEIPT** - Items counted differently
- **CONTRACT_INVOICE_MISMATCH** - Order changed without approval
- **CONTRACT_RECEIPT_MISMATCH** - Received qty differs from order
- **CIRCULAR_MISMATCH** - All three values different

### Price Anomalies

- **UNIT_PRICE_CHANGED** - Per-unit price differs from contract
- **PRICE_TOO_LOW** - < 70% of contract (counterfeit goods?)
- **PRICE_TOO_HIGH** - > 130% of contract (overcharging?)
- **ZERO_PRICE** - Impossible in real trade

### Severity Levels

- **CRITICAL**: Must reject or escalate immediately
- **HIGH**: Requires escalation to manager
- **MEDIUM**: Requires review by specialist
- **LOW**: Monitor but acceptable

## Audit Trail

All decisions logged to `audit_logs.db`:
- **audit_trail table**: Agent decisions with confidence, reasoning
- **human_approvals table**: Human decisions and notes

View on the **📋 Audit Trail** page:
- Filter by agent
- Filter by status
- Download as CSV
- View full details for any decision

## Dashboard

Real-time metrics on the **📈 Dashboard** page:
- Total decisions
- Auto-approval rate
- Escalation rate
- Average confidence
- Confidence distribution chart
- Recent activity feed

## Testing

### Reconciliation Agent Tests

```bash
python run_tests.py
```

Runs 15 comprehensive reconciliation scenarios:

**Scenario Coverage:**
- ✅ Perfect match (100% confidence)
- ✅ Minor variances (75-95% confidence)
- ✅ Major variances (40-75% confidence)
- ✅ Fraud signals (15-40% confidence)
- ✅ Multiple anomalies (10-50% confidence)
- ✅ Edge cases & boundaries
- ✅ Extreme variances

**Test Output:**
- Console report (pass/fail for each scenario)
- JSON test results file (`reconciliation_test_results.json`)
- Summary statistics (pass rate: 100%)

### Exception Triage Agent Tests

```bash
python run_exception_tests.py
```

Runs 12 comprehensive exception scenarios:

**Scenario Coverage:**
- ✅ Shipment delays (various durations)
- ✅ Missing documents (various deadlines)
- ✅ LC discrepancies
- ✅ Demurrage/detention risks
- ✅ Critical urgency cases
- ✅ Multiple overlapping issues
- ✅ False alarms
- ✅ Edge cases (ambiguous messages)

**Test Output:**
- Console report (pass/fail for each scenario)
- JSON test results file (`exception_test_results.json`)
- Category breakdown (by exception type)

### Combined Test Suite

```bash
# Run both agents' tests
python run_tests.py && python run_exception_tests.py
```

**Total Test Coverage**: 27 scenarios (15 + 12)
**Expected Result**: 100% pass rate for both suites

### Test Example

```python
from reconciliation_agent import ReconciliationAgent, MOCK_SCENARIOS
from database import Database
from guardrails import Guardrails
import os
from dotenv import load_dotenv

load_dotenv()

db = Database()
guardrails = Guardrails(db)
agent = ReconciliationAgent(os.getenv("OPENAI_API_KEY"), db, guardrails)

# Test fraud signal scenario
scenario = MOCK_SCENARIOS["fraud_signal"]
result = agent.reconcile(scenario["contract"], scenario["invoice"], scenario["receipt"])

print(f"Status: {result['status']}")  # ESCALATE_TO_DIRECTOR
print(f"Confidence: {result['confidence']}%")  # 15-40%
print(f"Fraud Score: {result['fraud_analysis']['fraud_score']}/100")  # 70-90
```

## Confidence Breakdown

The system provides detailed breakdown of confidence calculation:

```json
{
  "confidence_breakdown": {
    "initial_confidence": 100,
    "qty_variance_penalty": 15,
    "price_variance_penalty": 10,
    "timeline_penalty": 5,
    "fraud_penalty": 30,
    "anomaly_penalty": 15,
    "final_confidence": 25
  }
}
```

Each penalty is explained and can be reviewed by humans making approval decisions.

## Error Handling

The system handles errors gracefully:
- Invalid API key → error message shown
- Malformed data → validation errors  
- OpenAI API errors → retry with fallback
- Database errors → logged, partial results returned

## Performance Tips

1. **Confidence Threshold**: Adjust > 95% for stricter auto-approval
2. **Sanctions List**: Customize in `guardrails.py` for your region
3. **Role-Based Masking**: Configure in guardrails for your organization
4. **ChromaDB**: Runs locally, no external API calls needed
5. **Batch Processing**: Process multiple documents in sequence

## Troubleshooting

### "OPENAI_API_KEY not found"
- Copy `.env.example` to `.env`
- Add your OpenAI API key to `.env`
- Restart the app

### ChromaDB permission errors
- Ensure `chroma_db/` directory is writable
- Run from project root directory

### Streamlit session resets
- Use `@st.cache_resource` for components (already done)
- Use `st.session_state` for user data

### Slow GPT-4o calls
- Reduce complexity of prompts
- Use mock scenarios for testing
- Consider batch processing

## License

Proprietary - Trade Finance Operations

## Support

For issues or questions, contact: ashishdangwal97@gmail.com

---

**Version**: 2.0 (Enhanced with Variance, Fraud, Anomaly Detection)  
**Last Updated**: April 2026  
**Status**: ✅ Production Ready

### What's New in v2.0

✅ 3D Variance Analysis (3 dimensions)
✅ Fraud Detection (9+ signals, fraud_score 0-100)
✅ Anomaly Detection (8+ patterns)
✅ Enhanced HITL Workflow (side-by-side tables)
✅ Confidence Breakdown (detailed penalty analysis)
✅ Financial Impact Tracking
✅ 15 Test Scenarios (comprehensive coverage)
✅ Streamlit UI Enhancement (4 new sections)
✅ Blended Confidence Calculation
✅ Approval Chain Tracking
