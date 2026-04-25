# Trade Operations AI Platform - Deployment Guide

**Version**: 3.0 (Unified)  
**Status**: Production Ready  
**Last Updated**: April 2026

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API Key

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Load Mock Data (Optional)

```bash
python load_mock_data.py
```

This initializes the database with:
- 5 shipments (some delayed)
- 4 LCs (some with missing documents)
- 5 vessels (some approaching laytime expiry)

### 4. Start the Platform

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Platform Overview

### Two Intelligent Agents

**Reconciliation Agent (v2.0)**
- 3-way document matching
- Variance analysis (3D)
- Fraud detection (9+ signals)
- Anomaly detection (8+ patterns)
- Financial impact tracking

**Exception Triage Agent (v1.0)**
- Real-time monitoring (shipments, docs, LCs, laytime)
- Automatic classification (4 types)
- Urgency assessment (CRITICAL/HIGH/MEDIUM/LOW)
- Intelligent routing (4 handler teams)
- Action plan generation

### Shared Infrastructure

- **Single Database**: SQLite with 7 tables
- **Unified Audit Trail**: Both agents' decisions
- **Shared Guardrails**: Confidence routing, privacy masking, compliance checks
- **Real-Time Monitoring**: APScheduler running in background
- **Notification System**: Alerts for CRITICAL/HIGH exceptions

---

## 7-Page Architecture

### Page 1: Home Dashboard
**What It Shows**:
- Platform overview metrics
- Total reconciliations today
- Active exceptions count
- Auto-approve rate
- Financial exposure at risk
- Recent activity feed

**When to Use**: Quick status check, see both agents' activity

---

### Page 2: Reconciliation Agent
**What It Does**:
- Run 3-way document matching
- Analyze variance (contract ↔ invoice ↔ receipt)
- Detect fraud signals (9+ patterns)
- Find anomalies (8+ patterns)
- Calculate confidence score
- Process human approvals

**How to Use**:
1. Choose input method (CSV upload, JSON paste, or test scenario)
2. Click "Run Reconciliation"
3. Review analysis:
   - Variance Analysis (3D breakdown)
   - Fraud Detection (score 0-100)
   - Anomaly Detection (patterns found)
   - Confidence Breakdown (penalty analysis)
4. Make approval decision in HITL section

**Expected Outcomes**:
- AUTO_APPROVE (>95% confidence)
- ROUTE_TO_SPECIALIST (80-95%)
- ESCALATE_TO_MANAGER (50-80%)
- ESCALATE_TO_DIRECTOR (<50%)

---

### Page 3: Exception Triage Dashboard
**What It Shows**:
- Real-time list of active exceptions
- Color-coded by urgency (🔴🟠🟡🟢)
- Deadline remaining
- Financial impact
- Quick action buttons

**How to Use**:
1. View active exceptions (auto-sorted by urgency)
2. For each exception:
   - View details
   - Review action plan
   - Mark as resolved
3. Dashboard auto-refreshes every 30 seconds

**Exception Types**:
- SHIPMENT_DELAY: Vessel delayed
- MISSING_DOCUMENT: Document not received
- LC_DISCREPANCY: LC vs contract mismatch
- DD_RISK: Demurrage/detention risk

---

### Page 4: Exception Details & Routing
**What It Shows**:
- Full exception details
- Handler and owner
- Deadline and financial impact
- Action plan (3-5 specific steps)
- Context data
- Resolution workflow

**How to Use**:
1. Select exception from dropdown
2. Review full details
3. Execute action plan steps
4. Mark as resolved with notes

---

### Page 5: Unified Audit Trail
**What It Shows**:
- All decisions from both agents
- Filterable by agent type
- Full decision reasoning
- Audit IDs for traceability
- Human approval history

**How to Use**:
1. Filter by agent (ReconciliationAgent / ExceptionTriageAgent)
2. Adjust limit (10-200 entries)
3. Review decision history
4. Check audit IDs for traceability

**Compliance**: Immutable append-only logs for regulatory requirements

---

### Page 6: Alerts & Notifications
**What It Shows**:
- CRITICAL alerts (immediate action needed) 🔴
- HIGH priority alerts (urgent) 🟠
- No HIGH/CRITICAL = All clear ✅

**How to Use**:
1. Check for RED and ORANGE alerts
2. Click alert details to route to handler
3. Track alert resolution

**Notification Types**:
- Exception alerts (CRITICAL/HIGH urgency)
- Fraud alerts (fraud score > 75)
- Anomaly alerts (3+ issues detected)

---

### Page 7: Settings
**What You Can Configure**:
- Monitoring interval (1-30 min)
- Auto-approve threshold (80-99%)
- Critical exception escalation (on/off)

**How to Use**:
1. Adjust settings sliders
2. Click "Save Settings"
3. (Optional) Restart monitor with new interval

---

## Real-Time Monitoring

### How It Works

1. **Automatic Start**: Monitor starts when app loads
2. **Background Check**: Runs every 5 minutes (configurable)
3. **4 Checks Performed**:
   - Shipment delays (vs expected arrival)
   - Missing documents (vs LC deadline)
   - LC time-bar (expires within 3 days)
   - Demurrage risk (laytime expires within 10 days)
4. **Auto-Exception**: Creates exception if issue found
5. **Duplicate Prevention**: Won't create same exception twice

### Configuration

In Settings page:
- Change monitoring interval (1-30 minutes)
- Restart monitor to apply new interval

### What Gets Monitored

**Shipments** (from database):
- Expected arrival date
- Current status (IN_TRANSIT)
- Demurrage rate per day

**LCs** (from database):
- Required documents
- Received documents
- Expiry date

**Vessels** (from database):
- Laytime expiry
- Port and status
- Demurrage rate

---

## Testing

### Run All Tests

```bash
# Reconciliation tests (15 scenarios)
python run_tests.py

# Exception tests (12 scenarios)
python run_exception_tests.py

# Both (27 scenarios total)
python run_tests.py && python run_exception_tests.py
```

### Expected Results

**Reconciliation Tests**: 15/15 PASS ✅
- Perfect match scenarios
- Variance scenarios (minor and major)
- Fraud signal scenarios
- Anomaly scenarios
- Edge cases

**Exception Tests**: 12/12 PASS ✅
- Shipment delay scenarios
- Missing document scenarios
- LC discrepancy scenarios
- Demurrage risk scenarios
- Critical urgency scenarios
- Edge cases (ambiguous, false alarms)

### Test Output

- Console report with pass/fail status
- JSON results file (test_results.json)
- Detailed failure analysis if any fail

---

## Database Schema

### Existing Tables (Reconciliation Agent)
- `audit_trail` - Agent decisions
- `human_approvals` - Human approval records

### ChromaDB
- `lc_documents` - LC embeddings for semantic search

### New Tables (Exception Triage Agent)
- `exceptions` - Exception records with full details
- `shipments` - Shipment tracking (expected arrival, status)
- `lcs` - LC data (expiry, required/received docs)
- `vessels` - Vessel data (laytime expiry, demurrage rate)

### Total Tables: 7 (4 existing + 3 new)

---

## Guardrails

### 1. Confidence-Based Routing
- **AUTO_APPROVE** (>95%): No human review needed
- **ROUTE_TO_SPECIALIST** (80-95%): 24-hour deadline
- **ESCALATE_TO_MANAGER** (50-80%): 2-hour deadline
- **ESCALATE_TO_DIRECTOR** (<50%): 1-hour deadline

### 2. Audit Trail
- All decisions logged to SQLite
- Immutable append-only design
- Full reasoning preserved
- Human approvals tracked

### 3. Data Privacy
- Role-based masking (viewer/analyst/manager/compliance)
- Sensitive fields protected
- Counterparty redaction
- Amount masking

### 4. Compliance Checks
- UCP 600 (Letter of Credit)
- Sanctions screening
- Time-bar monitoring
- Incoterm alignment

### 5. Human-in-the-Loop (HITL)
- Side-by-side comparison tables
- Detailed issue lists
- Suggested actions
- Human confidence capture
- Approval chain tracking

---

## Common Workflows

### Workflow 1: Reconcile Trade Documents

1. Go to **Reconciliation Agent** page
2. Upload 3 CSV files (contract, invoice, receipt)
3. Click "Run Reconciliation"
4. Review results:
   - Variance Analysis
   - Fraud Detection
   - Anomaly Detection
   - Confidence Breakdown
5. Make decision in HITL section:
   - Approve / Reject / Request More Info
   - Enter human confidence (0-100%)
   - Add notes
6. Review audit trail (automatic)

**Expected Time**: 2-5 minutes

---

### Workflow 2: Respond to Exception Alert

1. Check **Exception Triage Dashboard** page
2. See 🔴 or 🟠 colored exceptions
3. Click "View Details" on exception
4. Review action plan (3-5 steps)
5. Execute action items
6. Enter resolution notes
7. Click "Mark as Resolved"
8. Check **Alerts & Notifications** to confirm cleared

**Expected Time**: 5-30 minutes (depends on issue)

---

### Workflow 3: Review Audit Trail

1. Go to **Audit Trail** page
2. Filter by agent:
   - ReconciliationAgent: 3-way matching decisions
   - ExceptionTriageAgent: Exception classifications
3. Adjust limit (10-200 entries)
4. Review decision reasoning
5. Check audit IDs for traceability

**Expected Time**: 5-10 minutes

---

## Troubleshooting

### "OPENAI_API_KEY not found"
- Solution: Create `.env` file with `OPENAI_API_KEY=sk-...your-key...`
- Restart app with `streamlit run app.py`

### Monitor not detecting exceptions
- Solution: Run `python load_mock_data.py` to load test shipments/LCs/vessels
- Wait 5 minutes for monitor to run first check
- Check Exception Triage Dashboard for new exceptions

### Database errors when loading mock data
- Solution: Database is auto-initialized by `load_mock_data.py`
- If issues persist, delete `audit_logs.db` and restart

### Slow Streamlit performance
- Solution: Reduce auto-refresh frequency in Settings (increase interval)
- Clear browser cache
- Restart Streamlit with `streamlit run app.py`

### GPT-4o API errors
- Check OpenAI API key is valid
- Check account has credit
- Check API rate limits not exceeded
- Reduce number of parallel requests

---

## Production Deployment

### Pre-Deployment Checklist

```
[ ] Python 3.8+ installed
[ ] All dependencies installed: pip install -r requirements.txt
[ ] .env file created with valid OPENAI_API_KEY
[ ] Mock data loaded: python load_mock_data.py
[ ] All 27 tests passing: python run_tests.py && python run_exception_tests.py
[ ] Streamlit app runs without errors: streamlit run app.py
[ ] Real-time monitor starts automatically
[ ] Home page shows metrics from both agents
[ ] Exception Dashboard auto-refreshes
[ ] Unified Audit Trail shows both agents
[ ] Database tables created successfully
[ ] Backup strategy for audit_logs.db in place
```

### Running in Production

```bash
# Standard (local development)
streamlit run app.py

# Production (with custom host/port)
streamlit run app.py --server.port 8080 --server.address 0.0.0.0

# With logging
streamlit run app.py --logger.level=info
```

### Monitoring in Production

- Watch for fraud_score > 75 (CRITICAL fraud)
- Monitor confidence < 50 (escalations)
- Track approval time vs deadline
- Alert on impossible timeline signals
- Review high anomaly counts

---

## Support & Documentation

- **README.md**: Feature overview and setup
- **ENHANCEMENTS.md**: Technical details of v2.0
- **MERGE_SUMMARY.md**: Architecture of unified platform
- **PROGRESS.md**: Implementation tracking
- **DEPLOYMENT_GUIDE.md**: This file

---

## Version History

| Version | Date | Features | Status |
|---------|------|----------|--------|
| 1.0 | Apr 2024 | Core system (reconciliation + LC validation) | Archived |
| 2.0 | Apr 2026 | Enhanced reconciliation (variance, fraud, anomaly) | Stable |
| 3.0 | Apr 2026 | Unified platform (merged with exception triage) | Production |

---

**Ready to deploy!** 🚀
