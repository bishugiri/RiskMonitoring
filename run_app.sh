#!/bin/bash
# Script to run the Risk Monitor web application

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the web application
python -m risk_monitor.scripts.run_app
