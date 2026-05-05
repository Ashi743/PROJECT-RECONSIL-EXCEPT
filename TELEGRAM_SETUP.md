# AgroCompany Trade Operations - Auto-Detection & Telegram Setup Guide

## 📋 Overview

This guide covers:
1. **Auto-Detection System** - Runs every 5 minutes via Hermes cron job
2. **Telegram Integration** - Sends formatted alerts to your Telegram chat
3. **Test Scenarios** - Manually trigger exceptions and test the system

---

## 🚀 Quick Start (5 minutes)

### Step 1: Update Your `.env` File

Add your Telegram credentials:

```bash
OPENAI_API_KEY=your_openai_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

**How to get these:**

1. **TELEGRAM_BOT_TOKEN**: 
   - Chat with @BotFather on Telegram
   - Create a new bot: `/newbot`
   - Copy the token

2. **TELEGRAM_CHAT_ID**:
   - Send a message to your bot (any text)
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Look for `"chat":{"id": 123456789}`

### Step 2: Install Required Package

```bash
pip install requests
```

### Step 3: Test Telegram Connection

```bash
python test_scenarios.py --test-telegram
```

You should receive a test message on Telegram! ✅

---

## 🔄 Auto-Detection System (Every 5 Minutes)

### How It Works

1. **Runs automatically** every 5 minutes via Hermes cron job `agro-company-auto-detection`
2. **Checks for 4 exception types:**
   - 🚢 **Shipment Delays** (vessel tracking)
   - 📄 **Missing Documents** (LC documents)
   - 💳 **LC Discrepancies** (credit issues)
   - ⚠️ **Demurrage Risk** (laytime expiry)

3. **Sends Telegram alerts** for CRITICAL and HIGH urgency exceptions
4. **Logs to audit_logs.db** for compliance tracking

### View Cron Job Status

```bash
hermes cron list
```

Look for `agro-company-auto-detection` - it will show:
- ✅ Next run time
- 📊 Last run status
- 📝 Delivery status (Telegram)

---

## 🧪 Test Scenarios

Use test scenarios to manually trigger exceptions and test Telegram alerts.

### List All Scenarios

```bash
python test_scenarios.py --list
```

### Run Single Scenario (with Telegram alert)

```bash
python test_scenarios.py --scenario CRITICAL_SHIPMENT_DELAY --telegram
```

### Run All Scenarios

```bash
python test_scenarios.py --all --telegram
```

### Available Scenarios

| Scenario Key | Description | Expected Urgency |
|---|---|---|
| `CRITICAL_SHIPMENT_DELAY` | Vessel delayed 10 days | CRITICAL |
| `HIGH_SHIPMENT_DELAY` | Vessel delayed 5 days | HIGH |
| `CRITICAL_MISSING_DOC` | Document missing, 2 days to deadline | CRITICAL |
| `HIGH_MISSING_DOC` | Document missing, 5 days to deadline | HIGH |
| `CRITICAL_DEMURRAGE` | Laytime expires in 2 days | CRITICAL |
| `HIGH_DEMURRAGE` | Laytime expires in 5 days | HIGH |
| `LC_DISCREPANCY` | LC amount mismatch | MEDIUM |
| `MULTIPLE_ISSUES` | 3+ issues combined | CRITICAL |

---

## 📱 Telegram Message Format

### Exception Alert Example

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

### Fraud Alert Example

```
🚨 FRAUD ALERT - HIGH RISK

🎯 Fraud Score: 85/100
⚠️ Risk Level: HIGH

📋 Signals Detected:
  • PRICE_DOWN_QTY_UP
  • TIMELINE_ANOMALY
  • DOUBLE_INVOICE_AMOUNT

Audit ID: AUD-20260505210000-XYZ98765
Time: 2026-05-05 20:55:23

⚡ Action Required: Review immediately by compliance team
```

---

## 📝 File Structure

```
agro-company-agents/
├── app.py                    # Main Streamlit app
├── auto_detect.py           # ✨ NEW: Auto-detection script
├── telegram_notifier.py      # ✨ NEW: Telegram formatting & sending
├── test_scenarios.py         # ✨ NEW: Test scenario runner
├── exception_triage_agent.py # Exception classification
├── real_time_monitor.py      # Background monitoring
├── reconciliation_agent.py   # 3-way reconciliation
├── database.py              # SQLite management
├── guardrails.py            # Audit logging
├── .env                     # ← Add your credentials here
└── audit_logs.db            # Compliance audit trail
```

---

## 🛠️ Manual Triggers

### Trigger Auto-Detection Now (Don't wait 5 minutes)

```bash
python auto_detect.py
```

### Send Test Exception to Telegram

```bash
python test_scenarios.py --scenario CRITICAL_SHIPMENT_DELAY --telegram
```

### Run Streamlit App with Auto-Detection

```bash
streamlit run app.py
```

The app will:
1. Run the Streamlit UI on `http://localhost:8501`
2. Start auto-detection in the background (every 5 minutes)
3. Send Telegram alerts for CRITICAL/HIGH exceptions
4. Log everything to audit_logs.db

---

## 🔍 Monitoring & Logs

### Check Cron Job Status

```bash
hermes cron list
```

### View Recent Exceptions

Check the Streamlit app → "🚨 Exception Triage Dashboard" page

### View Audit Trail

Check the Streamlit app → "📊 Unified Audit Trail" page

### View Telegram Delivery Status

```bash
hermes cron list
# Look for "last_delivery_error" - empty = success
```

---

## ⚙️ Configuration

### Change Detection Interval

Edit `auto_detect.py` or modify in `app.py`:

```python
# In app.py, line 49:
monitor = RealTimeMonitor(
    exception_agent=exception_agent,
    database=db,
    check_interval_minutes=5  # Change to desired minutes
)
```

### Change Telegram Alert Thresholds

Edit `auto_detect.py`:

```python
# Currently sends alerts for CRITICAL and HIGH urgency
if result.get("urgency") in ["CRITICAL", "HIGH"]:
    telegram_notifier.send_exception_alert(result)

# To also send MEDIUM:
if result.get("urgency") in ["CRITICAL", "HIGH", "MEDIUM"]:
    telegram_notifier.send_exception_alert(result)
```

### Disable/Pause Cron Job

```bash
hermes cron pause agro-company-auto-detection
```

### Resume Cron Job

```bash
hermes cron resume agro-company-auto-detection
```

### Remove Cron Job

```bash
hermes cron remove agro-company-auto-detection
```

---

## 🐛 Troubleshooting

### Telegram messages not arriving?

1. **Check .env credentials:**
   ```bash
   grep TELEGRAM .env
   ```

2. **Test connection:**
   ```bash
   python test_scenarios.py --test-telegram
   ```

3. **Check Telegram Bot:**
   - Make sure bot has permission to send messages
   - Verify you've messaged the bot at least once

### Auto-detection not running?

1. **Check cron job status:**
   ```bash
   hermes cron list
   ```

2. **Run manually to debug:**
   ```bash
   python auto_detect.py
   ```

3. **Check logs:**
   - View Streamlit app dashboard
   - Check terminal output

### OpenAI API errors?

1. **Verify API key:**
   ```bash
   echo $OPENAI_API_KEY
   ```

2. **Check API account:**
   - Ensure you have credits remaining
   - Verify API key is valid at openai.com

---

## 📊 System Architecture

```
Real-Time Monitoring Flow:
┌─────────────────────┐
│   Hermes Cron Job   │ (Every 5 min)
│ agro-company-auto-detection│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  auto_detect.py     │ Checks for:
│  + Shipment delays  │ • Vessel tracking
│  + Missing docs     │ • LC documents
│  + LC discrepancies │ • Credit issues
│  + Demurrage risk   │ • Laytime expiry
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ ExceptionTriageAgent│ Classifies & routes
└──────────┬──────────┘
           │
    ┌──────┴──────────┐
    │                 │
    ▼                 ▼
┌──────────┐     ┌──────────────┐
│Database  │     │TelegramAlert │ (CRITICAL/HIGH only)
│audit_logs│     │ Sends to Telegram
└──────────┘     └──────────────┘
```

---

## 🚀 Next Steps

1. ✅ **Setup credentials** in `.env`
2. ✅ **Test Telegram** with `--test-telegram`
3. ✅ **Run a test scenario** with `--scenario CRITICAL_SHIPMENT_DELAY --telegram`
4. ✅ **Verify cron job** with `hermes cron list`
5. ✅ **Run Streamlit app** with `streamlit run app.py`
6. ✅ **Monitor** via Telegram alerts

---

## 📞 Support

For issues:
1. Check the troubleshooting section above
2. Review `auto_detect.py` and `telegram_notifier.py` for debug prints
3. Check Streamlit dashboard for audit trail
4. Review Telegram delivery status in `hermes cron list`

---

## 🎯 Key Features

✅ **Automated Detection** - Runs every 5 minutes
✅ **Real-Time Alerts** - Telegram notifications
✅ **Smart Formatting** - Easy-to-read messages with emojis
✅ **Audit Trail** - All decisions logged to SQLite
✅ **Test Scenarios** - 8 pre-built scenarios to validate
✅ **Compliance Ready** - CRITICAL urgency flagged immediately
✅ **Financial Impact** - Calculates ₹ exposure for each exception
✅ **Action Plans** - Auto-generates 3-5 action items per exception

---

**Created:** 2026-05-05
**Status:** Ready for Testing
