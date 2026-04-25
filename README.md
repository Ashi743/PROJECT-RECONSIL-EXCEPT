# Trade Operations Agentic Assistant

Production-ready AI system with 2 agents for trade finance operations using **advanced variance analysis, fraud detection, and anomaly detection**.

1. **Reconciliation Agent** - 3-way reconciliation with 3D variance analysis, 9+ fraud signals, and 8+ anomaly patterns
2. **LC Doc Agent** - Letter of Credit validation with UCP 600 compliance checks

## ✨ Major Enhancements (v2.0)

### Reconciliation Agent - Now with Advanced Detection

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
├── reconciliation_agent.py         # ENHANCED: VarianceCalculator, FraudDetector, AnomalyDetector
├── guardrails.py                   # ENHANCED: HITLWorkflow class
├── app.py                          # ENHANCED: 4 new UI sections
├── doc_agent.py                    # LC validation logic
├── database.py                     # ChromaDB + SQLite management
├── run_tests.py                    # NEW: 15 test scenarios with automation
├── requirements.txt                # Python dependencies (added pytest)
├── .env.example                    # API key template
├── ENHANCEMENTS.md                 # NEW: Complete enhancement documentation
├── PROGRESS.md                     # NEW: Implementation progress tracking
├── README.md                       # This file
├── data/
│   ├── mock_contract.csv
│   ├── mock_invoice.csv
│   ├── mock_receipt.csv
│   └── sample_lc.txt
├── tests/                          # NEW: Test infrastructure
│   └── __init__.py
├── chroma_db/                      # ChromaDB vector store (auto-created)
└── audit_logs.db                   # SQLite audit trail (auto-created)
```

## Usage

### Reconciliation Agent

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

### Run Test Suite

```bash
python run_tests.py
```

Runs 15 comprehensive test scenarios:

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
- JSON test results file (for analysis)
- Summary statistics (pass rate, coverage)

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
