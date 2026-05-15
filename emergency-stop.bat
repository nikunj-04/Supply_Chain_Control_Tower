@echo off
echo ================================================
echo EMERGENCY STOP - Nuclear Option
echo ================================================
echo.
echo This will force-kill ALL Python and Node processes
echo on your system (not just this project).
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Killing all Python processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul

echo Killing all Node processes...
taskkill /F /IM node.exe 2>nul

echo.
echo Verifying ports are freed...
timeout /t 2 >nul

netstat -ano | findstr ":8000 " >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Port 8000 still in use - close browser tabs
) else (
    echo [OK] Port 8000 freed
)

netstat -ano | findstr ":5173 " >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Port 5173 still in use - close browser tabs
) else (
    echo [OK] Port 5173 freed
)

echo.
echo ================================================
echo Emergency stop complete
echo ================================================
pause
