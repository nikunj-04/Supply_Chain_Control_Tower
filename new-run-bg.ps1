# New unified PowerShell script for service management
param(
    [Parameter(Position=0)]
    [string]$Action
)

function Install-Services {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Installing Backend & Frontend" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    # Backend setup
    Set-Location "$PSScriptRoot\backend"
    if (-not (Test-Path "venv")) {
        Write-Host "Creating virtual environment..." -ForegroundColor White
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to create virtual environment" -ForegroundColor Red
            Set-Location $PSScriptRoot
            return
        }
    } else {
        Write-Host "Virtual environment already exists" -ForegroundColor Gray
    }
    
    Write-Host "Upgrading pip..." -ForegroundColor White
    & "venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
    
    Write-Host "Installing Python dependencies (this may take 2-3 minutes)..." -ForegroundColor White
    & "venv\Scripts\pip.exe" install -r requirements.txt --no-cache-dir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install requirements.txt" -ForegroundColor Red
    }
    
    Write-Host "Installing RAG dependencies..." -ForegroundColor White
    & "venv\Scripts\pip.exe" install -r requirements-rag.txt --no-cache-dir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: RAG dependencies installation had issues" -ForegroundColor Yellow
    }
    
    if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env file" -ForegroundColor Green
    }
    
    Write-Host "Generating sample data..." -ForegroundColor White
    & "venv\Scripts\python.exe" scripts\seed_data.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: Sample data generation had issues" -ForegroundColor Yellow
    }
    
    Write-Host "Building RAG vector index..." -ForegroundColor White
    & "venv\Scripts\python.exe" build_index.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: RAG index build had issues" -ForegroundColor Yellow
    }
    
    Write-Host "Backend setup complete!" -ForegroundColor Green
    Write-Host ""

    # Frontend setup
    Set-Location "$PSScriptRoot\frontend"
    Write-Host "Installing Node dependencies (this may take 2-3 minutes)..." -ForegroundColor White
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install Node dependencies" -ForegroundColor Red
    } else {
        Write-Host "Frontend setup complete!" -ForegroundColor Green
    }
    
    Set-Location $PSScriptRoot
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
}

function Start-Services {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Starting Backend & Frontend" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    # Start Backend
    $backendPython = "$PSScriptRoot\backend\venv\Scripts\python.exe"
    $backendMain = "$PSScriptRoot\backend\main.py"
    $backendLog = "$PSScriptRoot\logs\backend.log"
    if (-not (Test-Path "$PSScriptRoot\logs")) {
        New-Item -ItemType Directory -Path "$PSScriptRoot\logs" -Force | Out-Null
    }
    $backendProcess = Start-Process -FilePath $backendPython -ArgumentList $backendMain -WorkingDirectory "$PSScriptRoot\backend" -WindowStyle Hidden -RedirectStandardOutput $backendLog -RedirectStandardError "$PSScriptRoot\logs\backend-error.log" -PassThru
    Write-Host "Backend started (PID: $($backendProcess.Id)) - http://localhost:8000" -ForegroundColor Green

    # Start Frontend
    $frontendLog = "$PSScriptRoot\logs\frontend.log"
    $frontendErrorLog = "$PSScriptRoot\logs\frontend-error.log"
    $frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"npm run dev > `"$frontendLog`" 2> `"$frontendErrorLog`"`"" -WorkingDirectory "$PSScriptRoot\frontend" -WindowStyle Hidden -PassThru
    Write-Host "Frontend started (PID: $($frontendProcess.Id)) - http://localhost:5173" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "All Services Started!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
}

function Stop-Services {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Stopping Backend & Frontend" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    # Stop Backend
    $port8000Connections = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($port8000Connections) {
        $processIds = $port8000Connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $processIds) {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
        Write-Host "Backend stopped." -ForegroundColor Green
    } else {
        Write-Host "Backend not running." -ForegroundColor Gray
    }
    # Stop Frontend
    $port5173Connections = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
    if ($port5173Connections) {
        $processIds = $port5173Connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $processIds) {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
        Write-Host "Frontend stopped." -ForegroundColor Green
    } else {
        Write-Host "Frontend not running." -ForegroundColor Gray
    }
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "All Services Stopped!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
}

if (-not $Action) {
    Write-Host "Usage: .\new-run-bg.ps1 --Install | --Start | --Stop" -ForegroundColor Cyan
    exit 0
}

switch ($Action.ToLower()) {
    "--install" { Install-Services }
    "--start" { Start-Services }
    "--stop" { Stop-Services }
    default {
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        Write-Host "Usage: .\new-run-bg.ps1 --Install | --Start | --Stop" -ForegroundColor Cyan
    }
}
