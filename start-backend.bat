@echo off
echo ========================================
echo Starting E-commerce Fulfillment Control Tower Backend
echo ========================================
echo.

cd backend

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting FastAPI server...
echo Backend will be available at: http://localhost:8000
echo API Docs: http://localhost:8000/api/docs
echo.

venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
