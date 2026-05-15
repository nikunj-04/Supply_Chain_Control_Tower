# E-commerce Fulfillment Control Tower - Service Management Script
# Usage: .\run-all-bg.ps1 --Start | --Stop | --Install | --Status | --Rebuild-Index

param(
    [Parameter(Position=0)]
    [string]$Action
)

# Function to show usage
function Show-Usage {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "E-commerce Fulfillment Control Tower - Service Management" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor White
    Write-Host "  .\run-all-bg.ps1 --Start          Start all services (backend + frontend + RAG)" -ForegroundColor Green
    Write-Host "  .\run-all-bg.ps1 --Stop           Stop all services" -ForegroundColor Yellow
    Write-Host "  .\run-all-bg.ps1 --Install        Install all dependencies + build RAG index" -ForegroundColor Cyan
    Write-Host "  .\run-all-bg.ps1 --Status         Check service status" -ForegroundColor Blue
    Write-Host "  .\run-all-bg.ps1 --Rebuild-Index  Rebuild RAG vector database" -ForegroundColor Magenta
    Write-Host ""
    exit 0
}

# Function to check prerequisites
function Test-Prerequisites {
    param([bool]$ExitOnError = $true)
    
    $allGood = $true
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Python not found. Please install Python 3.9+" -ForegroundColor Red
        $allGood = $false
    }

    # Check Node.js
    try {
        $nodeVersion = node --version 2>&1
        Write-Host "[OK] Node.js found: $nodeVersion" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Node.js not found. Please install Node.js 18+" -ForegroundColor Red
        $allGood = $false
    }

    if (-not $allGood -and $ExitOnError) {
        Write-Host ""
        Write-Host "Please install missing prerequisites and try again." -ForegroundColor Red
        exit 1
    }
    
    return $allGood
}

# Function to install dependencies
function Install-Dependencies {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Installing Dependencies" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    Test-Prerequisites -ExitOnError $true

    # Install Backend
    Write-Host "Step 1: Setting up Backend..." -ForegroundColor Yellow
    Set-Location "$PSScriptRoot\backend"

    if (-not (Test-Path "venv")) {
        Write-Host "Creating virtual environment..." -ForegroundColor White
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Virtual environment already exists" -ForegroundColor Gray
    }

    Write-Host "Installing Python dependencies..." -ForegroundColor White
    & ".\venv\Scripts\pip.exe" install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install Python dependencies" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Installing RAG dependencies..." -ForegroundColor White
    & ".\venv\Scripts\pip.exe" install -r requirements-rag.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARNING] Failed to install RAG dependencies" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] RAG dependencies installed" -ForegroundColor Green
    }

    Write-Host "Setting up environment file..." -ForegroundColor White
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Host "[OK] Created .env file" -ForegroundColor Green
        }
    } else {
        Write-Host ".env file already exists" -ForegroundColor Gray
    }

    Write-Host "Generating sample data..." -ForegroundColor White
    & ".\venv\Scripts\python.exe" scripts\seed_data.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to generate sample data" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Building RAG vector index..." -ForegroundColor White
    & ".\venv\Scripts\python.exe" build_index.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] RAG vector index built successfully!" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] RAG index build had issues (will rebuild on first start)" -ForegroundColor Yellow
    }

    Write-Host "[OK] Backend setup complete!" -ForegroundColor Green
    Write-Host ""

    # Install Frontend
    Set-Location "$PSScriptRoot\frontend"
    Write-Host "Step 2: Setting up Frontend..." -ForegroundColor Yellow
    Write-Host "Installing Node dependencies..." -ForegroundColor White
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install Node dependencies" -ForegroundColor Red
        exit 1
    }

    Write-Host "[OK] Frontend setup complete!" -ForegroundColor Green
    Write-Host ""

    Set-Location $PSScriptRoot

    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Run: .\run-all-bg.ps1 --Start" -ForegroundColor Cyan
    Write-Host ""
}

# Function to start services
function Start-Services {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Starting All Services" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    Test-Prerequisites -ExitOnError $true

    # Check if backend venv exists
    if (-not (Test-Path "$PSScriptRoot\backend\venv")) {
        Write-Host "[ERROR] Backend not installed. Run: .\run-all-bg.ps1 --Install" -ForegroundColor Red
        exit 1
    }

    # Check if frontend node_modules exists
    if (-not (Test-Path "$PSScriptRoot\frontend\node_modules")) {
        Write-Host "[ERROR] Frontend not installed. Run: .\run-all-bg.ps1 --Install" -ForegroundColor Red
        exit 1
    }

    # Check if services are already running
    $port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    $port5173 = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue

    if ($port8000 -or $port5173) {
        Write-Host "[ERROR] Services are already running!" -ForegroundColor Red
        Write-Host ""
        
        if ($port8000) {
            $pids8000 = $port8000 | Select-Object -ExpandProperty OwningProcess -Unique
            Write-Host "  Backend on port 8000 (PIDs: $($pids8000 -join ', '))" -ForegroundColor Yellow
        }
        if ($port5173) {
            $pids5173 = $port5173 | Select-Object -ExpandProperty OwningProcess -Unique
            Write-Host "  Frontend on port 5173 (PIDs: $($pids5173 -join ', '))" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "Please stop existing services first:" -ForegroundColor White
        Write-Host "  .\run-all-bg.ps1 --Stop" -ForegroundColor Cyan
        Write-Host ""
        exit 1
    }
    
    # Check RAG index
    $ragIndexPath = "$PSScriptRoot\backend\data\vector_index\supplychain_full.index"
    if (-not (Test-Path $ragIndexPath)) {
        Write-Host "[INFO] RAG vector index not found. Building index..." -ForegroundColor Yellow
        & "$PSScriptRoot\backend\venv\Scripts\python.exe" "$PSScriptRoot\backend\build_index.py"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] RAG index built successfully!" -ForegroundColor Green
        } else {
            Write-Host "[WARNING] RAG index build had issues, but continuing..." -ForegroundColor Yellow
        }
        Write-Host ""
    } else {
        Write-Host "[OK] RAG vector index found" -ForegroundColor Green
        Write-Host ""
    }

    # Create logs directory
    $logsDir = "$PSScriptRoot\logs"
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    }

    Write-Host "Starting Backend..." -ForegroundColor Yellow

    # Start Backend in background
    $backendPython = "$PSScriptRoot\backend\venv\Scripts\python.exe"
    $backendMain = "$PSScriptRoot\backend\main.py"
    $backendLog = "$logsDir\backend.log"

    $backendProcess = Start-Process -FilePath $backendPython `
        -ArgumentList $backendMain `
        -WorkingDirectory "$PSScriptRoot\backend" `
        -WindowStyle Hidden `
        -RedirectStandardOutput $backendLog `
        -RedirectStandardError "$logsDir\backend-error.log" `
        -PassThru

    Write-Host "[OK] Backend started (PID: $($backendProcess.Id)) - http://localhost:8000" -ForegroundColor Green
    Write-Host "  Log: $backendLog" -ForegroundColor Gray
    Write-Host ""

    # Wait for backend to initialize
    Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
    $maxWait = 15
    $waited = 0
    $backendReady = $false

    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds 1
        $waited++
        $port = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
        if ($port) {
            $backendReady = $true
            break
        }
    }

    if ($backendReady) {
        Write-Host "[OK] Backend is ready!" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Backend may still be starting (check logs)" -ForegroundColor Yellow
    }
    Write-Host ""

    Write-Host "Starting Frontend..." -ForegroundColor Yellow

    # Start Frontend in background
    $frontendLog = "$logsDir\frontend.log"

    $frontendProcess = Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c","npm run dev > `"$frontendLog`" 2> `"$logsDir\frontend-error.log`"" `
        -WorkingDirectory "$PSScriptRoot\frontend" `
        -WindowStyle Hidden `
        -PassThru

    Write-Host "[OK] Frontend started (PID: $($frontendProcess.Id)) - http://localhost:5173" -ForegroundColor Green
    Write-Host "  Log: $frontendLog" -ForegroundColor Gray
    Write-Host ""

    # Wait for frontend to initialize
    Write-Host "Waiting for frontend to initialize..." -ForegroundColor Yellow
    $maxWait = 20
    $waited = 0
    $frontendReady = $false

    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds 1
        $waited++
        $port = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
        if ($port) {
            $frontendReady = $true
            break
        }
    }

    if ($frontendReady) {
        Write-Host "[OK] Frontend is ready!" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Frontend may still be starting (check logs)" -ForegroundColor Yellow
    }
    Write-Host ""

    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "All Services Started!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Access Points:" -ForegroundColor White
    Write-Host "  Dashboard:  http://localhost:5173" -ForegroundColor Cyan
    Write-Host "  API:        http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  API Docs:   http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Features:" -ForegroundColor White
    Write-Host "  ✓ RAG-powered AI Chat (8NAP AI)" -ForegroundColor Green
    Write-Host "  ✓ Vector database semantic search" -ForegroundColor Green
    Write-Host "  ✓ KPI calculation from raw data" -ForegroundColor Green
    Write-Host "  ✓ 7 Database systems indexed" -ForegroundColor Green
    Write-Host ""
    Write-Host "Logs:" -ForegroundColor White
    Write-Host "  Backend:  $backendLog" -ForegroundColor Gray
    Write-Host "  Frontend: $frontendLog" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To stop services: .\run-all-bg.ps1 --Stop" -ForegroundColor Yellow
    Write-Host "To view logs: Get-Content '$logsDir\backend.log' -Wait" -ForegroundColor Gray
    Write-Host ""
}

# Function to stop services
function Stop-Services {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Stopping All Services" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $stoppedAny = $false

    # Step 1: Kill ALL processes using port 8000 (backend)
    Write-Host "Checking port 8000 (Backend)..." -ForegroundColor Yellow
    $port8000Connections = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    
    if ($port8000Connections) {
        $processIds = $port8000Connections | Select-Object -ExpandProperty OwningProcess -Unique
        Write-Host "Found $($processIds.Count) process(es) on port 8000: $($processIds -join ', ')" -ForegroundColor Green
        
        foreach ($procId in $processIds) {
            if ($procId -and $procId -ne 0) {
                $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "  Killing PID $procId ($($proc.ProcessName))" -ForegroundColor White
                    
                    # Method 1: Stop-Process
                    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Milliseconds 300
                    $stoppedAny = $true
                    
                    # Check if still alive
                    if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
                        Write-Host "    Resistant process, trying taskkill..." -ForegroundColor Yellow
                        # Method 2: taskkill
                        taskkill /F /PID $procId 2>&1 | Out-Null
                        Start-Sleep -Milliseconds 300
                        
                        # Still alive?
                        if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
                            Write-Host "    Still resistant, trying WMIC..." -ForegroundColor Yellow
                            # Method 3: WMIC
                            wmic process where ProcessId=$procId delete 2>&1 | Out-Null
                        }
                    }
                } else {
                    # Process already dead but try cleanup anyway (orphaned connection)
                    Write-Host "  PID $procId already terminated (orphaned connection)" -ForegroundColor DarkGray
                    taskkill /F /PID $procId 2>&1 | Out-Null
                }
            }
        }
        
        Start-Sleep -Seconds 1
    } else {
        Write-Host "Port 8000 not in use" -ForegroundColor Gray
    }

    # Step 2: Kill ALL processes using port 5173 (frontend)
    Write-Host "Checking port 5173 (Frontend)..." -ForegroundColor Yellow
    $port5173Connections = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
    
    if ($port5173Connections) {
        $processIds = $port5173Connections | Select-Object -ExpandProperty OwningProcess -Unique
        Write-Host "Found $($processIds.Count) process(es) on port 5173: $($processIds -join ', ')" -ForegroundColor Green
        
        foreach ($procId in $processIds) {
            if ($procId -and $procId -ne 0) {
                $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "  Killing PID $procId ($($proc.ProcessName))" -ForegroundColor White
                    
                    # Method 1: Stop-Process
                    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Milliseconds 300
                    $stoppedAny = $true
                    
                    # Check if still alive
                    if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
                        Write-Host "    Resistant process, trying taskkill..." -ForegroundColor Yellow
                        # Method 2: taskkill
                        taskkill /F /PID $procId 2>&1 | Out-Null
                        Start-Sleep -Milliseconds 300
                        
                        # Still alive?
                        if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
                            Write-Host "    Still resistant, trying WMIC..." -ForegroundColor Yellow
                            # Method 3: WMIC
                            wmic process where ProcessId=$procId delete 2>&1 | Out-Null
                        }
                    }
                } else {
                    # Process already dead but try cleanup anyway (orphaned connection)
                    Write-Host "  PID $procId already terminated (orphaned connection)" -ForegroundColor DarkGray
                    taskkill /F /PID $procId 2>&1 | Out-Null
                }
            }
        }
        
        Start-Sleep -Seconds 1
    } else {
        Write-Host "Port 5173 not in use" -ForegroundColor Gray
    }

    # Step 3: Aggressive cleanup - kill any remaining python/node processes from this project
    Write-Host ""
    Write-Host "Performing aggressive cleanup..." -ForegroundColor Yellow
    
    # Get all python processes
    $pythonProcs = Get-Process python -ErrorAction SilentlyContinue
    if ($pythonProcs) {
        $killedPython = 0
        foreach ($proc in $pythonProcs) {
            # Check if it's running from our project directory
            if ($proc.Path -and $proc.Path -like "*supplychain-controltower*") {
                Write-Host "  Killing Python PID $($proc.Id)" -ForegroundColor White
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 300
                
                # Check if still alive
                if (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) {
                    taskkill /F /PID $proc.Id 2>&1 | Out-Null
                    Start-Sleep -Milliseconds 300
                    
                    if (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) {
                        wmic process where ProcessId=$($proc.Id) delete 2>&1 | Out-Null
                    }
                }
                
                $killedPython++
                $stoppedAny = $true
            }
        }
        if ($killedPython -gt 0) {
            Write-Host "Cleaned up $killedPython Python process(es)" -ForegroundColor Green
        }
    }
    
    # Get all node processes
    $nodeProcs = Get-Process node -ErrorAction SilentlyContinue
    if ($nodeProcs) {
        $killedNode = 0
        foreach ($proc in $nodeProcs) {
            # Check if it's running from our project directory
            if ($proc.Path -and $proc.Path -like "*supplychain-controltower*") {
                Write-Host "  Killing Node PID $($proc.Id)" -ForegroundColor White
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 300
                
                # Check if still alive
                if (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) {
                    taskkill /F /PID $proc.Id 2>&1 | Out-Null
                    Start-Sleep -Milliseconds 300
                    
                    if (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) {
                        wmic process where ProcessId=$($proc.Id) delete 2>&1 | Out-Null
                    }
                }
                
                $killedNode++
                $stoppedAny = $true
            }
        }
        if ($killedNode -gt 0) {
            Write-Host "Cleaned up $killedNode Node process(es)" -ForegroundColor Green
        }
    }

    # Step 4: Final verification with orphan detection
    Write-Host ""
    Write-Host "Verifying ports are free..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    
    $finalCheck8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    $finalCheck5173 = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
    
    # Check port 8000
    if ($finalCheck8000) {
        $procId = $finalCheck8000.OwningProcess
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        
        if ($proc) {
            Write-Host "[WARNING] Port 8000 still in use by PID $procId ($($proc.ProcessName))" -ForegroundColor Red
            Write-Host "  💡 Emergency stop: Stop-Process -Id $procId -Force" -ForegroundColor Yellow
        } else {
            Write-Host "[WARNING] Port 8000 has orphaned TCP connection (from dead PID $procId)" -ForegroundColor Yellow
            Write-Host "  💡 Wait 2-3 minutes for automatic TCP timeout, or:" -ForegroundColor Cyan
            Write-Host "     - Close browser tabs connected to http://localhost:8000" -ForegroundColor Cyan
            Write-Host "     - Restart PowerShell/Terminal (clears TCP stack)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "[OK] Port 8000 freed" -ForegroundColor Green
    }
    
    # Check port 5173
    if ($finalCheck5173) {
        $procId = $finalCheck5173.OwningProcess
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        
        if ($proc) {
            Write-Host "[WARNING] Port 5173 still in use by PID $procId ($($proc.ProcessName))" -ForegroundColor Red
            Write-Host "  💡 Emergency stop: Stop-Process -Id $procId -Force" -ForegroundColor Yellow
        } else {
            Write-Host "[WARNING] Port 5173 has orphaned TCP connection (from dead PID $procId)" -ForegroundColor Yellow
            Write-Host "  💡 Wait 2-3 minutes for automatic TCP timeout, or:" -ForegroundColor Cyan
            Write-Host "     - Close browser tabs connected to http://localhost:5173" -ForegroundColor Cyan
            Write-Host "     - Restart PowerShell/Terminal (clears TCP stack)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "[OK] Port 5173 freed" -ForegroundColor Green
    }

    Write-Host ""
    if ($stoppedAny) {
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "Services Stopped!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
    } else {
        Write-Host "No services were running" -ForegroundColor Gray
    }
    Write-Host ""
}

# Function to check service status
function Get-ServiceStatus {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Service Status" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Check Backend
    $port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($port8000) {
        $process = Get-Process -Id $port8000.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "[✓] Backend:   RUNNING" -ForegroundColor Green
        Write-Host "    PID: $($port8000.OwningProcess)" -ForegroundColor Gray
        Write-Host "    URL: http://localhost:8000" -ForegroundColor Cyan
    } else {
        Write-Host "[✗] Backend:   STOPPED" -ForegroundColor Red
    }
    Write-Host ""
    
    # Check Frontend
    $port5173 = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
    if ($port5173) {
        $process = Get-Process -Id $port5173.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "[✓] Frontend:  RUNNING" -ForegroundColor Green
        Write-Host "    PID: $($port5173.OwningProcess)" -ForegroundColor Gray
        Write-Host "    URL: http://localhost:5173" -ForegroundColor Cyan
    } else {
        Write-Host "[✗] Frontend:  STOPPED" -ForegroundColor Red
    }
    Write-Host ""
    
    # Check RAG Index
    $ragIndexPath = "$PSScriptRoot\backend\data\vector_index\supplychain_full.index"
    if (Test-Path $ragIndexPath) {
        $indexInfo = Get-Item $ragIndexPath
        Write-Host "[✓] RAG Index: EXISTS" -ForegroundColor Green
        Write-Host "    Size: $([math]::Round($indexInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
        Write-Host "    Modified: $($indexInfo.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
    } else {
        Write-Host "[✗] RAG Index: NOT BUILT" -ForegroundColor Red
            Write-Host "[✗] RAG Index: NOT BUILT" -ForegroundColor Red
        Write-Host "    Run: .\run-all-bg.ps1 --Rebuild-Index" -ForegroundColor Yellow
            Write-Host ""
            # Check Dependencies
            if (Test-Path "$PSScriptRoot\backend\venv") {
                Write-Host "[✓] Backend Dependencies: INSTALLED" -ForegroundColor Green
            } else {
                Write-Host "[✗] Backend Dependencies: NOT INSTALLED" -ForegroundColor Red
                Write-Host "    Run: .\run-all-bg.ps1 --Install" -ForegroundColor Yellow
            }
            if (Test-Path "$PSScriptRoot\frontend\node_modules") {
                Write-Host "[✓] Frontend Dependencies: INSTALLED" -ForegroundColor Green
            } else {
                Write-Host "[✗] Frontend Dependencies: NOT INSTALLED" -ForegroundColor Red
                Write-Host "    Run: .\run-all-bg.ps1 --Install" -ForegroundColor Yellow
            }
            Write-Host ""
        }
    }
    Write-Host ""
    
    # Check Dependencies
    if (Test-Path "$PSScriptRoot\backend\venv") {
        Write-Host "[✓] Backend Dependencies: INSTALLED" -ForegroundColor Green
    } else {
        Write-Host "[✗] Backend Dependencies: NOT INSTALLED" -ForegroundColor Red
        Write-Host "    Run: .\run-all-bg.ps1 --Install" -ForegroundColor Yellow
    }
    
    if (Test-Path "$PSScriptRoot\frontend\node_modules") {
        Write-Host "[✓] Frontend Dependencies: INSTALLED" -ForegroundColor Green
    } else {
        Write-Host "[✗] Frontend Dependencies: NOT INSTALLED" -ForegroundColor Red
        Write-Host "    Run: .\run-all-bg.ps1 --Install" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Function to rebuild RAG index
function Rebuild-RAGIndex {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Rebuilding RAG Vector Index" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if (-not (Test-Path "$PSScriptRoot\backend\venv")) {
        Write-Host "[ERROR] Backend not installed. Run: .\run-all-bg.ps1 --Install" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "This will rebuild the vector database from all 7 databases..." -ForegroundColor Yellow
    Write-Host "Estimated time: 2-5 minutes" -ForegroundColor Gray
    Write-Host ""
    
    $backendPython = "$PSScriptRoot\backend\venv\Scripts\python.exe"
    $buildScript = "$PSScriptRoot\backend\build_index.py"
    
    & $backendPython $buildScript
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[OK] RAG index rebuilt successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "If backend is running, restart it to load the new index:" -ForegroundColor Yellow
        Write-Host "  .\run-all-bg.ps1 --Stop" -ForegroundColor White
        Write-Host "  .\run-all-bg.ps1 --Start" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "[ERROR] Failed to rebuild RAG index" -ForegroundColor Red
    }
    Write-Host ""
}

# Main script logic
if (-not $Action) {
    Show-Usage
}

switch ($Action.ToLower()) {
    "--start" {
        Start-Services
    }
    "--stop" {
        Stop-Services
    }
    "--install" {
        Install-Dependencies
    }
    "--status" {
        Get-ServiceStatus
    }
    "--rebuild-index" {
        Rebuild-RAGIndex
    }
    default {
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        Write-Host ""
        Show-Usage
    }
    }
}
