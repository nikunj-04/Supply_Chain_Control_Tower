# Stop All E-commerce Fulfillment Control Tower Services
# This script helps identify and stop the running services

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "E-commerce Fulfillment Control Tower - Stop Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Searching for running services..." -ForegroundColor Yellow
Write-Host ""

# Find Python processes (backend)
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*supplychain-controltower*"
}

if ($pythonProcesses) {
    Write-Host "Found Backend processes:" -ForegroundColor Green
    $pythonProcesses | ForEach-Object {
        Write-Host "  PID: $($_.Id) - $($_.ProcessName)" -ForegroundColor White
    }
    
    $confirm = Read-Host "`nStop backend processes? (y/n)"
    if ($confirm -eq 'y') {
        $pythonProcesses | Stop-Process -Force
        Write-Host "✓ Backend stopped" -ForegroundColor Green
    }
} else {
    Write-Host "No backend processes found" -ForegroundColor Gray
}

Write-Host ""

# Find Node processes (frontend)
$nodeProcesses = Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*supplychain-controltower*" -or
    $_.CommandLine -like "*vite*" -or
    $_.CommandLine -like "*npm*"
}

if ($nodeProcesses) {
    Write-Host "Found Frontend processes:" -ForegroundColor Green
    $nodeProcesses | ForEach-Object {
        Write-Host "  PID: $($_.Id) - $($_.ProcessName)" -ForegroundColor White
    }
    
    $confirm = Read-Host "`nStop frontend processes? (y/n)"
    if ($confirm -eq 'y') {
        $nodeProcesses | Stop-Process -Force
        Write-Host "✓ Frontend stopped" -ForegroundColor Green
    }
} else {
    Write-Host "No frontend processes found" -ForegroundColor Gray
}

Write-Host ""

# Alternative: Check ports
Write-Host "Checking ports 8000 and 3000..." -ForegroundColor Yellow

$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue

if ($port8000) {
    Write-Host "Port 8000 (Backend) is in use by PID: $($port8000.OwningProcess)" -ForegroundColor Yellow
    $confirm = Read-Host "Kill process on port 8000? (y/n)"
    if ($confirm -eq 'y') {
        Stop-Process -Id $port8000.OwningProcess -Force
        Write-Host "✓ Process stopped" -ForegroundColor Green
    }
}

if ($port3000) {
    Write-Host "Port 3000 (Frontend) is in use by PID: $($port3000.OwningProcess)" -ForegroundColor Yellow
    $confirm = Read-Host "Kill process on port 3000? (y/n)"
    if ($confirm -eq 'y') {
        Stop-Process -Id $port3000.OwningProcess -Force
        Write-Host "✓ Process stopped" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
