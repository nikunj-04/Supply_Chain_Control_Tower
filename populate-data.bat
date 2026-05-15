@echo off
echo ========================================
echo Live Data Population - One-Time Run
echo ========================================
echo.

cd /d "%~dp0backend"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Running live data population...
python scripts/populate_live_data.py

echo.
echo ========================================
echo Done! Press any key to exit...
pause > nul
