@echo off
echo ========================================
echo E-commerce Fulfillment Control Tower - Quick Start Setup
echo ========================================
echo.

echo Step 1: Setting up Backend...
cd backend

echo Creating virtual environment...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo Setting up environment file...
if not exist .env (
    copy .env.example .env
    echo Created .env file
)

echo Generating sample data...
python scripts\seed_data.py
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to generate sample data
    pause
    exit /b 1
)

echo.
echo Backend setup complete!
echo.

cd ..

echo Step 2: Setting up Frontend...
cd frontend

echo Installing Node dependencies...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install Node dependencies
    pause
    exit /b 1
)

echo.
echo Frontend setup complete!
echo.

cd ..

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the application:
echo.
echo 1. Start Backend:
echo    cd backend
echo    venv\Scripts\activate
echo    python main.py
echo.
echo 2. Start Frontend (in new terminal):
echo    cd frontend
echo    npm run dev
echo.
echo Then open: http://localhost:3000
echo.

pause
