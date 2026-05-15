@echo off
REM Refresh KPI Data in RAG Vector Index
REM This updates the chatbot's KPI knowledge to match current dashboards

echo.
echo ========================================
echo   Refreshing KPI Data for Chatbot
echo ========================================
echo.

cd /d "%~dp0backend"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Run the refresh script
python refresh_kpi_index.py

echo.
echo Press any key to exit...
pause >nul
