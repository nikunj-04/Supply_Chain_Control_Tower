# Clean startup script for backend and frontend
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Clean Service Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kill all existing Python and Node processes
Write-Host "Cleaning up existing processes..." -ForegroundColor Yellow
Get-Process python,node -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Start Backend
Write-Host "Starting Backend on port 8000..." -ForegroundColor Yellow
$backendPath = "$PSScriptRoot\backend"
$pythonExe = "$backendPath\venv\Scripts\python.exe"
$mainPy = "$backendPath\main.py"

Start-Process -FilePath $pythonExe -ArgumentList $mainPy -WorkingDirectory $backendPath -WindowStyle Normal

# Wait for backend to start
Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
$maxAttempts = 15
$attempt = 0
$backendReady = $false

while ($attempt -lt $maxAttempts) {
    Start-Sleep -Seconds 1
    $attempt++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    } catch {
        # Keep trying
    }
    Write-Host "  Attempt $attempt/$maxAttempts..." -ForegroundColor Gray
}

if ($backendReady) {
    Write-Host "[OK] Backend is running at http://localhost:8000" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Backend failed to start" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Start Frontend
Write-Host "Starting Frontend on port 3000..." -ForegroundColor Yellow
$frontendPath = "$PSScriptRoot\frontend"

Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "cd /d `"$frontendPath`" && npm run dev" -WorkingDirectory $frontendPath

# Wait for frontend
Write-Host "Waiting for frontend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Services Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access the application at:" -ForegroundColor White
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop services, press Ctrl+C and close terminal windows" -ForegroundColor Yellow
Write-Host ""
