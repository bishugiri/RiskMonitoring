@echo off
echo Starting Risk Monitoring Tool - Streamlit Web App...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher
    pause
    exit /b 1
)

REM Check if Streamlit is installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Installing Streamlit and dependencies...
    pip install -r requirements.txt
)

REM Run the Streamlit app
echo Starting Streamlit web application...
echo The app will open in your default web browser
echo.
echo Press Ctrl+C to stop the server
echo.

streamlit run streamlit_app.py

pause 