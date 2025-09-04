#!/bin/bash
# Script to run the Risk Monitor web application with Python 3.11

echo "🚀 Starting Risk Monitor with Python 3.11..."

# Activate virtual environment
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    exit 1
fi

# Check Python version
echo "🐍 Python version:"
venv/bin/python --version

# Run the web application using the virtual environment's Python
echo "🌐 Starting Streamlit app..."
venv/bin/python risk_monitor/scripts/run_app.py
