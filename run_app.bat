@echo off
REM Batch file to run the Risk Monitor web application

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run the web application
python -m risk_monitor.scripts.run_app

REM Pause to see any errors
pause