#!/bin/bash
# Script to install the package in development mode

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install the package in development mode
pip install -e .

echo "Development installation complete!"
echo "You can now run the following commands:"
echo "  - python -m risk_monitor.scripts.run_app"
echo "  - python -m risk_monitor.scripts.run_data_refresh --setup"
echo "  - python -m risk_monitor.scripts.run_data_refresh --run-now"
