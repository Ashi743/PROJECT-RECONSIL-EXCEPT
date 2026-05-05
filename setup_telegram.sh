#!/bin/bash

# AgroCompany Trade Operations - Quick Setup Script
# Installs dependencies and tests Telegram connection

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   AgroCompany Trade Operations - Auto-Detection & Telegram Setup     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python version: $(python --version)"
echo ""

# Check if in project directory
if [ ! -f "app.py" ]; then
    echo "❌ Please run this script from the agro-company-agents directory"
    exit 1
fi

# Step 1: Install requirements
echo "📦 Installing dependencies..."
pip install requests --quiet
echo "✅ Dependencies installed"
echo ""

# Step 2: Check .env file
echo "🔑 Checking .env file..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    echo ""
    echo "📋 Please create a .env file with:"
    echo ""
    echo "   OPENAI_API_KEY=your_openai_key_here"
    echo "   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here"
    echo "   TELEGRAM_CHAT_ID=your_telegram_chat_id_here"
    echo ""
    echo "📖 Instructions:"
    echo "   1. Get TELEGRAM_BOT_TOKEN from @BotFather on Telegram"
    echo "   2. Get TELEGRAM_CHAT_ID by running: python test_scenarios.py --test-telegram"
    echo "   3. Get OPENAI_API_KEY from https://platform.openai.com/account/api-keys"
    echo ""
    exit 1
fi

# Check required env vars
if ! grep -q "OPENAI_API_KEY=" .env; then
    echo "❌ OPENAI_API_KEY not found in .env"
    exit 1
fi

if ! grep -q "TELEGRAM_BOT_TOKEN=" .env; then
    echo "❌ TELEGRAM_BOT_TOKEN not found in .env"
    exit 1
fi

if ! grep -q "TELEGRAM_CHAT_ID=" .env; then
    echo "❌ TELEGRAM_CHAT_ID not found in .env"
    exit 1
fi

echo "✅ .env file configured"
echo ""

# Step 3: Test Telegram connection
echo "📱 Testing Telegram connection..."
echo ""

python test_scenarios.py --test-telegram

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "📋 Next steps:"
    echo ""
    echo "   1. Run a test scenario:"
    echo "      python test_scenarios.py --scenario CRITICAL_SHIPMENT_DELAY --telegram"
    echo ""
    echo "   2. Check cron job status:"
    echo "      hermes cron list"
    echo ""
    echo "   3. Start Streamlit app:"
    echo "      streamlit run app.py"
    echo ""
    echo "   4. Monitor exceptions in real-time on Telegram!"
    echo ""
else
    echo ""
    echo "⚠️  Telegram connection test failed"
    echo "    Check your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID"
    echo ""
    exit 1
fi
