# Trade Operations AI Platform

<img width="800" height="424" alt="Recording2026-04-25222950-ezgif com-speed" src="https://github.com/user-attachments/assets/a8b63e53-dc4a-4442-a5b5-42a6c80ef14d" />

**Intelligent AI agents for automated trade finance reconciliation, exception detection, and real-time monitoring.**

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## 🎯 Overview

AgroCompany Trade Operations Platform is an intelligent automation system that combines two specialized AI agents to manage complex trade finance operations:

- **🔄 Reconciliation Agent** - 3-way document matching, fraud detection, anomaly analysis
- **🚨 Exception Triage Agent** - Real-time monitoring, classification, intelligent routing
- **📱 Telegram Alerts** - Instant notifications for critical exceptions
- **📊 SQLite Audit Trail** - Complete compliance logging

## ✨ Key Features

### Reconciliation Agent
- ✅ **3-way document matching** (Contract ↔ Invoice ↔ Receipt)
- ✅ **Variance analysis** (Quantity, Price, Timeline)
- ✅ **Fraud detection** (9+ signals including PRICE_DOWN_QTY_UP)
- ✅ **Anomaly detection** (8+ patterns)
- ✅ **Confidence-based routing** (auto-approve >95%)

### Exception Triage Agent
- ✅ **4 exception types** (Shipment Delays, Missing Docs, LC Discrepancies, Demurrage Risk)
- ✅ **Real-time monitoring** (Every 5 minutes)
- ✅ **Urgency assessment** (CRITICAL/HIGH/MEDIUM/LOW)
- ✅ **Intelligent routing** (4 handler teams)
- ✅ **Action plan generation** (3-5 specific steps per exception)
- ✅ **Financial impact calculation** (₹ exposure per issue)

### Automation
- ✅ **Auto-detection cron job** (runs every 5 minutes)
- ✅ **Telegram notifications** (formatted alerts with emojis)
- ✅ **8 pre-built test scenarios** (for validation)
- ✅ **SQLite audit database** (full compliance trail)

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.9+
pip install -r requirements.txt
OpenAI API Key (for GPT-4o)
Telegram Bot Token (optional, for alerts)
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/agro-company-trade-ops.git
cd agro-company-trade-ops
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials:
OPENAI_API_KEY=your_key_here
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### Run the App

**Start Streamlit dashboard:**
```bash
streamlit run app.py
```
App runs on `http://localhost:8501`

**Test Telegram connection:**
```bash
python test_scenarios.py --test-telegram
```

**Run a test scenario:**
```bash
python test_scenarios.py --scenario CRITICAL_SHIPMENT_DELAY --telegram
```

## 📋 Project Structure

```
agro-company-trade-ops/
├── app.py                           # Main Streamlit dashboard (7 pages)
├── reconciliation_agent.py          # 3-way reconciliation logic
├── exception_triage_agent.py        # Exception classification & routing
├── real_time_monitor.py             # APScheduler-based monitoring
├── telegram_notifier.py             # Telegram alert formatting
├── auto_detect.py                   # Auto-detection script
├── test_scenarios.py                # 8 test scenarios
├── database.py                      # SQLite operations
├── guardrails.py                    # Compliance & audit logging
├── doc_agent.py                     # LC document validation
├── reconciliation_agent.py          # Reconciliation logic
├── requirements.txt                 # Dependencies
├── TELEGRAM_SETUP.md                # Telegram setup guide
├── README_AUTOMATION.md             # Auto-detection guide
└── audit_logs.db                    # SQLite audit database
```

## 🔄 System Architecture

### Data Flow
```
1. Input Data (CSV/JSON/Test)
           ↓
2. Reconciliation Agent
   ├─ 3-way matching
   ├─ Variance analysis
   ├─ Fraud detection
   └─ Anomaly detection
           ↓
3. Decision Output
   ├─ AUTO_APPROVE (>95% confidence)
   ├─ ROUTE_TO_SPECIALIST
   ├─ ESCALATE_TO_MANAGER
   └─ ESCALATE_TO_DIRECTOR
           ↓
4. Audit Logging → SQLite
```

### Exception Monitoring
```
Every 5 minutes (via cron job):

1. Check shipment delays
2. Check missing documents
3. Check LC deadlines
4. Check demurrage risk
   ↓
5. Classify exception type
6. Assess urgency (CRITICAL/HIGH/MEDIUM/LOW)
7. Route to handler team
8. Send Telegram alert (if CRITICAL/HIGH)
9. Log to audit_logs.db
```

## 📊 Dashboard Pages

1. **🏠 Home** - Unified metrics dashboard
2. **🔄 Reconciliation Agent** - Upload/test reconciliation
3. **🚨 Exception Triage Dashboard** - Real-time exceptions
4. **📋 Exception Details & Routing** - Full exception analysis
5. **📊 Unified Audit Trail** - Compliance records
6. **🔔 Alerts & Notifications** - Alert history
7. **⚙️ Settings** - Configuration options

## 🔧 Configuration

### Change Detection Frequency
Edit `app.py`, line 49:
```python
monitor = RealTimeMonitor(
    exception_agent=exception_agent,
    database=db,
    check_interval_minutes=5  # Change this
)
```

### Change Alert Threshold
Edit `auto_detect.py`:
```python
if result.get("urgency") in ["CRITICAL", "HIGH"]:  # Add "MEDIUM" if desired
    telegram_notifier.send_exception_alert(result)
```

### Customize Fraud Detection
Edit `reconciliation_agent.py` to adjust:
- Fraud signal weights
- Anomaly detection thresholds
- Confidence penalties

## 📱 Telegram Alerts Example

```
🔴 EXCEPTION ALERT - CRITICAL

⏳ Type: SHIPMENT_DELAY
ID: EXC-20260505210000-ABC12345

📝 Details:
Vessel MV CriticalDelay delayed 10 days from Mumbai to Singapore

🚢 Handler: FREIGHT_TEAM
Owner: freight_specialist@agro-company.com

⏰ Deadline: 2 hours
💸 Financial Impact: ₹750,000

📋 Action Plan:
  1. Contact carrier immediately for updated ETA
  2. Calculate demurrage exposure if vessel is delayed further
  3. Notify customer of delay and provide revised delivery date
  4. Assess if laytime extension is needed
  5. Check if penalty clauses apply in contract

Status: OPEN
Time: 2026-05-05 20:55:23
```

## 🧪 Testing

### Test Scenarios (8 Available)

Run individual test:
```bash
python test_scenarios.py --scenario CRITICAL_SHIPMENT_DELAY --telegram
```

Run all tests:
```bash
python test_scenarios.py --all --telegram
```

Available scenarios:
- `CRITICAL_SHIPMENT_DELAY` - 10-day delay (CRITICAL)
- `HIGH_SHIPMENT_DELAY` - 5-day delay (HIGH)
- `CRITICAL_MISSING_DOC` - 2 days to deadline (CRITICAL)
- `HIGH_MISSING_DOC` - 5 days to deadline (HIGH)
- `CRITICAL_DEMURRAGE` - 2 days to laytime (CRITICAL)
- `HIGH_DEMURRAGE` - 5 days to laytime (HIGH)
- `LC_DISCREPANCY` - Amount mismatch (MEDIUM)
- `MULTIPLE_ISSUES` - 3+ combined issues (CRITICAL)

### Cron Job Management

```bash
# View all jobs
hermes cron list

# Pause auto-detection
hermes cron pause agro-company-auto-detection

# Resume auto-detection
hermes cron resume agro-company-auto-detection

# Run immediately
hermes cron run agro-company-auto-detection
```

## 📚 Documentation

- **[TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)** - Complete Telegram integration guide
- **[README_AUTOMATION.md](README_AUTOMATION.md)** - Auto-detection & cron jobs
- **[spec-sheet.md](spec-sheet.md)** - Reconciliation specifications
- **[spec-sheet-exception-triage.md](spec-sheet-exception-triage.md)** - Exception triage specs

## 🐛 Troubleshooting

### No Telegram alerts?
```bash
# 1. Check .env
grep TELEGRAM .env

# 2. Test connection
python test_scenarios.py --test-telegram

# 3. Verify cron job
hermes cron list
```

### Auto-detection not running?
```bash
# 1. Check status
hermes cron list

# 2. Run manually
python auto_detect.py

# 3. Check for errors
python auto_detect.py 2>&1
```

### OpenAI errors?
```bash
# Verify API key
echo $OPENAI_API_KEY

# Check account at openai.com for credits
```

## 📊 Monitoring

### Via Streamlit Dashboard
- Real-time metrics
- Exception dashboard
- Audit trail viewer
- Settings panel

### Via Telegram
- Instant CRITICAL alerts
- Action items included
- Financial impact shown
- Handler team identified

### Via SQLite
```bash
# Query audit logs
sqlite3 audit_logs.db "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 10;"
```

## 🔐 Security

- ✅ Environment variables for sensitive data (.env)
- ✅ SQLite encryption support (optional)
- ✅ Audit trail for all decisions
- ✅ Role-based handler team assignment
- ✅ Confidence scoring for auto-approvals

## 🚀 Deployment

### Local Development
```bash
streamlit run app.py
```

### Production Deployment
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for:
- Docker containerization
- Environment setup
- Scaling considerations
- Security hardening

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| Exception Detection | Every 5 minutes |
| Telegram Alert Delay | <2 seconds |
| Reconciliation Processing | <5 seconds per transaction |
| Auto-approve Rate | Target >90% |
| False Positive Rate | <5% |

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 📧 Support

- **Documentation**: See [docs/](docs/) folder
- **Issues**: [GitHub Issues](https://github.com/yourusername/agro-company-trade-ops/issues)
- **Email**: support@agro-company.com

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for UI
- [OpenAI GPT-4o](https://openai.com/) for AI intelligence
- [APScheduler](https://apscheduler.readthedocs.io/) for job scheduling
- [SQLite](https://www.sqlite.org/) for audit logging

---

**Created:** 2026-05-05  
**Status:** ✅ Production Ready  
**Last Updated:** 2026-05-05  

**Made with ❤️ for trade finance automation**
