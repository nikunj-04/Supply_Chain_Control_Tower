@echo off
echo ========================================
echo Refreshing Supply Chain Exceptions
echo ========================================
cd /d "%~dp0backend"
call ..\venv\Scripts\activate.bat
python refresh_exceptions.py
pause
