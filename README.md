# Trade Operations Agentic Assistant

Production-ready AI system with 2 agents for trade finance operations:

1. **Reconciliation Agent** - 3-way reconciliation (contract ↔ invoice ↔ receipt) with fraud detection
2. **LC Doc Agent** - Letter of Credit validation with UCP 600 compliance checks

## Features

- ✅ **OpenAI GPT-4o Integration** - Advanced reasoning for edge cases and LC field extraction
- ✅ **ChromaDB Vector Storage** - Semantic search for LC documents
- ✅ **SQLite Audit Trail** - Immutable logs of all decisions and approvals
- ✅ **5 Guardrails**:
  - Confidence-based routing (auto-approve >95%)
  - Audit trail logging
  - Data privacy masking by role
  - Compliance checks (UCP 600, sanctions)
  - Human-in-the-Loop workflow
- ✅ **Streamlit UI** - 5 pages: Home, Reconciliation, LC Doc, Audit Trail, Dashboard

## Tech Stack

- **Backend**: Python 3.8+
- **LLM**: OpenAI GPT-4o
- **Vector DB**: ChromaDB (for LC embeddings)
- **Audit DB**: SQLite (immutable logs)
- **Frontend**: Streamlit
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
reconciliation-doc-agent/
├── app.py                          # Streamlit UI (5 pages)
├── reconciliation_agent.py         # 3-way reconciliation logic
├── doc_agent.py                    # LC validation logic
├── guardrails.py                   # 5 guardrails implementation
├── database.py                     # ChromaDB + SQLite management
├── requirements.txt                # Python dependencies
├── .env.example                    # API key template
├── .env                            # API keys (user creates)
├── README.md                       # This file
├── data/
│   ├── mock_contract.csv          # Sample contract data
│   ├── mock_invoice.csv           # Sample invoice data
│   ├── mock_receipt.csv           # Sample receipt data
│   └── sample_lc.txt              # Sample Letter of Credit
├── chroma_db/                     # ChromaDB vector store (auto-created)
└── audit_logs.db                  # SQLite audit trail (auto-created)
```

## Usage

### Reconciliation Agent

Use for 3-way matching and fraud detection.

**Steps:**
1. Go to **📊 Reconciliation Agent** page
2. Choose input method:
   - Upload CSV files (contract, invoice, receipt)
   - Paste JSON data
   - Select a test scenario (5 mock scenarios included)
3. Click **Run Reconciliation**
4. Review results:
   - Quantity matching
   - Price matching
   - Timeline validation
   - Anomaly detection (fraud signals)
5. Approve or reject in HITL workflow

**Mock Scenarios:**
- `perfect_match` - All fields match exactly
- `minor_variance` - Small discrepancies (< 2%)
- `major_variance` - Large discrepancies (> 2%)
- `fraud_signal` - Price reduction + extra quantity
- `qty_mismatch` - Invoice qty ≠ receipt qty

### LC Doc Agent

Use for Letter of Credit validation.

**Steps:**
1. Go to **📄 LC Doc Agent** page
2. Input LC document:
   - Upload TXT file
   - Paste LC text
   - Use sample LC
3. Input contract terms:
   - Amount
   - Currency
   - Incoterm
   - Negotiation requirement
4. Click **Validate LC**
5. Review results:
   - Extracted LC fields (via GPT-4o)
   - Comparison with contract terms
   - UCP 600 compliance check
   - Confidence score
6. Search for similar LCs using vector DB
7. Approve/reject in HITL workflow

## Guardrails Explained

### 1. Confidence-Based Routing

Routes decisions automatically based on confidence score:

| Confidence | Action | Owner | Deadline |
|-----------|--------|-------|----------|
| > 95% | AUTO_APPROVE | None | None |
| 80-95% | ROUTE_TO_SPECIALIST | Specialist | 24 hours |
| 50-80% | ESCALATE_TO_MANAGER | Manager | 2 hours |
| < 50% | ESCALATE_TO_DIRECTOR | Director | 1 hour |

### 2. Audit Trail Logging

Every decision is logged to an immutable SQLite database:
- Agent decision (with full details)
- Confidence score
- Reasoning
- Human approval (if applicable)
- Approver notes
- Approval timestamp

### 3. Data Privacy Masking

Sensitive fields are masked based on user role:
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
- Agent recommendation is shown clearly
- Human can approve, reject, or request more info
- Human confidence and notes are logged
- Approval is traceable in audit trail

## Audit Trail

All decisions are logged to `audit_logs.db` with:
- **audit_trail table**: Agent decisions, confidence, reasoning
- **human_approvals table**: Human approvals and notes

View on the **📋 Audit Trail** page:
- Filter by agent
- Filter by status
- Download as CSV
- View full details

## Dashboard

Real-time metrics on the **📈 Dashboard** page:
- Total decisions
- Auto-approval rate
- Escalation rate
- Average confidence
- Confidence distribution chart
- Decision distribution chart
- Recent activity feed

## How the Agents Work

### Reconciliation Agent

1. **Check Quantity Match**
   - Compares contract qty vs invoice vs receipt
   - Flags variances > 2%
   - Confidence penalty: -15 (warning) or -40 (critical)

2. **Check Price Match**
   - Compares contract price vs invoice price
   - Flags variances > 1%
   - Confidence penalty: -15 or -40

3. **Check Timeline**
   - Ensures invoice date is after receipt date
   - Flags delays > 10 days
   - Confidence penalty: -10 or -20

4. **Detect Anomalies**
   - QTY_MISMATCH: Invoice qty ≠ receipt qty
   - PRICE_REDUCTION: Invoice price < contract price
   - QTY_INCREASE: Invoice qty > contract qty
   - SUSPICIOUS_COMBO: Price reduction + extra qty (fraud signal)
   - TIMELINE_GAP: Invoice > 10 days after receipt

5. **Calculate Confidence**
   - Start at 100%
   - Apply penalties from matches and anomalies
   - Floor at 0%, ceiling at 100%

6. **Route & Log**
   - Route based on confidence (via guardrails)
   - Log decision to audit trail
   - Return decision to user

### LC Doc Agent

1. **Extract LC Fields** (using GPT-4o)
   - LC amount, currency, expiry date
   - Negotiability, incoterm, beneficiary
   - Applicant, issuing bank
   - Key clauses
   - Calculates days to expiry

2. **Store in Vector DB**
   - LC text embedded and stored in ChromaDB
   - Enables semantic search of LC documents

3. **Compare to Contract**
   - Amount: LC >= contract amount (90% rule)
   - Incoterm: Must match exactly
   - Expiry: Must have > 7 days remaining
   - Negotiability: Must match contract requirement

4. **Check Compliance**
   - UCP 600 violations and warnings
   - Sanctions check
   - Time-bar check
   - Incoterm alignment

5. **Calculate Confidence**
   - Each FAIL: -40%
   - Each WARNING: -15%
   - Each compliance violation: -30%
   - Each compliance warning: -10%

6. **Route & Log**
   - Route based on confidence
   - Log decision to audit trail
   - Return decision to user

## Example Workflows

### Perfect Reconciliation

Contract: 100 MT @ $500
Invoice: 100 MT @ $500
Receipt: 100 MT

Result: ✅ AUTO_APPROVE (100% confidence)

### Fraud Detection

Contract: 100 MT @ $500
Invoice: 110 MT @ $450 (extra qty + price reduction)
Receipt: 100 MT

Result: 🔴 ESCALATE_TO_DIRECTOR (15% confidence) - Fraud signal!

### LC Validation with Issues

- Amount: ✅ OK
- Incoterm: ✅ OK
- Expiry: ⚠️ 5 days (< 7 required)
- Compliance: ✗ Counterparty on sanctions list

Result: 🟠 ESCALATE_TO_MANAGER (40% confidence)

## Error Handling

The system handles errors gracefully:
- Invalid API key → error message shown
- Malformed data → validation errors
- OpenAI API errors → retry with fallback
- Database errors → logged, partial results returned

## API Integration

### OpenAI GPT-4o

Used for:
- LC field extraction (JSON mode)
- Edge case reasoning (structured JSON)
- Complex pattern analysis

Pattern:
```python
from openai import OpenAI
client = OpenAI(api_key=api_key)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    response_format={"type": "json_object"},
    temperature=0.1
)
result = json.loads(response.choices[0].message.content)
```

### ChromaDB

Used for:
- Storing LC documents with embeddings
- Semantic search for similar LCs
- Vector similarity matching

### SQLite

Used for:
- Immutable audit trail (append-only)
- Human approval tracking
- Decision history

## Performance Tips

1. **Confidence Threshold**: Adjust > 95% for stricter auto-approval
2. **Sanctions List**: Customize in `guardrails.py` for your region
3. **Role-Based Masking**: Configure in guardrails for your organization
4. **ChromaDB**: Runs locally, no external API calls
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
- Use `@st.cache_resource` for components
- Use `st.session_state` for user data

### Slow GPT-4o calls
- Reduce complexity of prompts
- Use mock scenarios for testing
- Consider batch processing

## Testing

Run all test scenarios:

```bash
streamlit run app.py
# Navigate to Reconciliation Agent → Test Scenario
# Try all 5 scenarios
# Verify routing and confidence scores
```

Test LC validation:

```bash
# Use Sample LC from LC Doc Agent page
# Verify field extraction
# Check compliance violations
```

Test HITL workflow:

```bash
# Run a scenario that requires escalation
# Click Approve/Reject
# Check Audit Trail for logged approval
```

## License

Proprietary - Trade Finance Operations

## Support

For issues or questions, contact: ashishdangwal97@gmail.com

---

**Version**: 1.0.0
**Last Updated**: April 2024
