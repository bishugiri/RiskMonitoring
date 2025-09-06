#!/bin/bash

# Risk Monitor Scheduler Runner
# This script activates the virtual environment and runs the scheduler

echo "🚀 Starting Risk Monitor Scheduler..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment activated: $VIRTUAL_ENV"
else
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Install toml if not already installed
echo "📚 Checking dependencies..."
pip install toml > /dev/null 2>&1

# Show scheduler configuration
echo "📋 Scheduler Configuration:"
echo "   ⏰ Scheduled time: 06:45 US/Eastern"
echo "   📊 Monitoring entities: SBUX, CHTR, ISRG, LRCX"
echo "   📧 Email notifications: Enabled"
echo "   🗄️  Pinecone storage: Enabled"
echo "   🔍 Keywords: risk, financial, market, crisis, volatility, earnings, revenue, stock, trading, investment"
echo "============================================================"

# Run the scheduler using the proper script
echo "🔄 Starting scheduler..."
echo "💡 Press Ctrl+C to stop the scheduler"
echo ""

# Use the proper run_data_refresh.py script
python3 risk_monitor/scripts/run_data_refresh.py

# Deactivate virtual environment
deactivate
echo "👋 Scheduler stopped"
