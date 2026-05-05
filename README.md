# Trade Operations AI Platform

<img width="800" alt="Platform Demo" src="https://github.com/user-attachments/assets/a8b63e53-dc4a-4442-a5b5-42a6c80ef14d" />

**Intelligent AI agents for automated trade finance reconciliation, exception detection, and real-time monitoring.**

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## Overview

Two specialized AI agents working together to manage trade finance operations end-to-end — from document matching to real-time exception alerts on your phone.

| Agent | What It Does |
|-------|-------------|
| 🔄 **Reconciliation Agent** | 3-way document matching, fraud detection, anomaly analysis |
| 🚨 **Exception Triage Agent** | Real-time monitoring, classification, intelligent routing |

**Automation layer**: Hermes Agent runs cron jobs every 5 minutes and pushes Telegram alerts for CRITICAL/HIGH exceptions.

---

## Screenshots

<img width="1280" alt="Hermes Integration" src="https://github.com/user-attachments/assets/8755aae8-ac2a-4d67-b5a4-26aa41ab2600" />

<img width="729" alt="Auto Detection" src="https://github.com/user-attachments/assets/13845da5-e02b-4c60-a113-50b66bd8bfb7" />

<img width="705" alt="Alert Output" src="https://github.com/user-attachments/assets/7d84441d-e087-48c0-a6ec-54b5090b1aa7" />

<table>
  <tr>
    <td><img width="300" alt="Telegram Alert 1" src="https://github.com/user-attachments/assets/3a48ae01-5811-4b5a-9760-131e7f05c967" /></td>
    <td><img width="300" alt="Telegram Alert 2" src="https://github.com/user-attachments/assets/7cec2c6a-77d0-4f4d-9f8c-e340bfe0d257" /></td>
  </tr>
</table>

---

## Features

### Reconciliation Agent
- 3-way document matching (Contract ↔ Invoice ↔ Receipt)
- Variance analysis across quantity, price, and timeline
- Fraud detection with 9+ signals (including `PRICE_DOWN_QTY_UP`)
- Anomaly detection with 8+ patterns
- Confidence-based routing — auto-approve above 95%

### Exception Triage Agent
- 4 exception types: Shipment Delays, Missing Docs, LC Discrepancies, Demurrage Risk
- Urgency classification: CRITICAL / HIGH / MEDIUM / LOW
- Routing to 4 handler teams with owner assignment
- 3–5 step action plan generated per exception
- Financial exposure calculated in ₹ per issue

### Automation (via Hermes Agent)
- Cron job runs `auto_detect.py` every 5 minutes
- Telegram push alerts for CRITICAL and HIGH exceptions
- Skill saved as `bunge-exception-monitor` — persists across sessions
- 8 pre-built test scenarios for validation
- Full SQLite audit trail for compliance

---

## Telegram Alert Example

```
🔴 EXCEPTION ALERT - CRITICAL

⏳ Type: SHIPMENT_DELAY
ID: EXC-20260505210000-ABC12345

📝 Vessel MV CriticalDelay delayed 10 days — Mumbai to Singapore

🚢 Handler: FREIGHT_TEAM
👤 Owner: freight_specialist@agro-company.com
⏰ Deadline: 2 hours
💸 Financial Impact: ₹750,000

📋 Action Plan:
  1. Contact carrier immediately for updated ETA
  2. Calculate demurrage exposure if delay continues
  3. Notify customer with revised delivery date
  4. Assess if laytime extension is needed
  5. Check if penalty clauses apply in contract

Status: OPEN | 2026-05-05 20:55:23
```

---

## Quick Start

### Prerequisites
```
Python 3.9+
OpenAI API Key
Telegram Bot Token (optional)
Hermes Agent (for cron automation)
```

### Installation

```bash
git clone https://github.com/yourusername/agro-company-trade-ops.git
cd agro-company-trade-ops

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Add: OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

### Run

```bash
# Streamlit dashboard
streamlit run app.py             # http://localhost:8501

# Test Telegram connection
python test_scenarios.py --test-telegram

# Run a specific test scenario
python test_scenarios.py --scenario CRITICAL_SHIPMENT_DELAY --telegram

# Run all 8 test scenarios
python test_scenarios.py --all --telegram
```

---

## Project Structure

```
agro-company-trade-ops/
├── app.py                      # Streamlit dashboard (7 pages)
├── reconciliation_agent.py     # 3-way reconciliation + fraud + anomaly
├── exception_triage_agent.py   # Exception classification & routing
├── real_time_monitor.py        # Background monitoring engine
├── auto_detect.py              # Hermes cron entry point
├── telegram_notifier.py        # Alert formatting & delivery
├── test_scenarios.py           # 8 test scenarios
├── database.py                 # SQLite operations
├── guardrails.py               # Compliance & audit logging
├── doc_agent.py                # LC document validation
├── requirements.txt
├── audit_logs.db               # SQLite audit database (auto-created)
├── TELEGRAM_SETUP.md
└── README_AUTOMATION.md
```

---

## System Flow

```
Input (CSV / JSON / Test Scenario)
         ↓
Reconciliation Agent
  ├── 3-way document match
  ├── Variance analysis
  ├── Fraud detection
  └── Anomaly detection
         ↓
Decision → AUTO_APPROVE / ROUTE_TO_SPECIALIST / ESCALATE_TO_MANAGER / ESCALATE_TO_DIRECTOR
         ↓
Audit Log → SQLite

──────────────────────────────────────

Every 5 minutes (Hermes cron):
  auto_detect.py
  ├── Check shipment delays
  ├── Check missing documents
  ├── Check LC deadlines
  └── Check demurrage risk
         ↓
  Classify → Assess urgency → Route to handler
         ↓
  Telegram alert (CRITICAL/HIGH) + SQLite log
```

---

## Dashboard Pages

| Page | Purpose |
|------|---------|
| 🏠 Home | Unified metrics — both agents |
| 🔄 Reconciliation Agent | Upload CSV or run test scenario |
| 🚨 Exception Triage Dashboard | Live exception view |
| 📋 Exception Details & Routing | Full analysis + resolution |
| 📊 Unified Audit Trail | Compliance records |
| 🔔 Alerts & Notifications | Alert history |
| ⚙️ Settings | Thresholds, intervals, routing |

---

## Test Scenarios

| Scenario | Urgency |
|----------|---------|
| `CRITICAL_SHIPMENT_DELAY` | 🔴 CRITICAL |
| `HIGH_SHIPMENT_DELAY` | 🟠 HIGH |
| `CRITICAL_MISSING_DOC` | 🔴 CRITICAL |
| `HIGH_MISSING_DOC` | 🟠 HIGH |
| `CRITICAL_DEMURRAGE` | 🔴 CRITICAL |
| `HIGH_DEMURRAGE` | 🟠 HIGH |
| `LC_DISCREPANCY` | 🟡 MEDIUM |
| `MULTIPLE_ISSUES` | 🔴 CRITICAL |

---

## Hermes Cron Management

```bash
hermes cron list                                    # View all jobs
hermes cron pause agro-company-auto-detection       # Pause
hermes cron resume agro-company-auto-detection      # Resume
hermes cron run agro-company-auto-detection         # Trigger immediately
```

---

## Troubleshooting

**No Telegram alerts?**
```bash
grep TELEGRAM .env
python test_scenarios.py --test-telegram
```

**Auto-detection not running?**
```bash
hermes cron list
python auto_detect.py              # Run manually to see errors
```

**OpenAI errors?**
```bash
echo $OPENAI_API_KEY               # Verify key is set
# Check credits at platform.openai.com
```

---

## Performance

| Metric | Value |
|--------|-------|
| Exception detection interval | 5 minutes |
| Telegram alert delay | < 2 seconds |
| Reconciliation processing | < 5 seconds |
| Auto-approve target rate | > 90% |
| False positive rate | < 5% |

---

## Tech Stack

- **UI**: Streamlit
- **AI**: OpenAI GPT-4o
- **Automation**: Hermes Agent (cron + skills)
- **Database**: SQLite
- **Alerts**: Telegram Bot API
- **Scheduling**: APScheduler (in-app) + Hermes cron (external)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

**Status**: ✅ Production Ready &nbsp;|&nbsp; **Last Updated**: May 2026
