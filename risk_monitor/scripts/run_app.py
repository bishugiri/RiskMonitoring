#!/usr/bin/env python3
"""
Entry point script for running the Risk Monitor web application.
"""

import os
import sys
import subprocess
import streamlit.web.cli as stcli

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def main():
    """Run the Streamlit app"""
    # Get the project root directory (where .streamlit/secrets.toml is located)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    
    # Change to the project root directory so Streamlit can find the secrets file
    os.chdir(project_root)
    
    # Get the path to the streamlit app
    app_path = os.path.join(project_root, "risk_monitor", "api", "streamlit_app.py")
    
    # Check if the app exists
    if not os.path.exists(app_path):
        print(f"Error: Streamlit app not found at {app_path}")
        sys.exit(1)
    
    # Run the streamlit app using streamlit's CLI directly
    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
