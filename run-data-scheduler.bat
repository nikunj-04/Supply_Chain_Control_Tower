@echo off
echo ========================================
echo Live Data Scheduler - Continuous Mode
echo ========================================
echo.
echo This will populate data every 5 minutes
echo Press Ctrl+C to stop
echo.
pause

cd /d "%~dp0backend"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting scheduler...
python scripts/run_live_data_scheduler.py
