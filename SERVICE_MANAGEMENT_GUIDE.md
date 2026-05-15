# Service Management Guide

## Starting Services

```powershell
.\run-all-bg.ps1 --Start
```

**What it does:**
- Checks if ports 8000 (backend) and 5173 (frontend) are already in use
- Starts backend API server on http://localhost:8000
- Starts frontend dev server on http://localhost:5173
- Runs both services in background
- Shows process IDs for monitoring

**If start fails:**
- Port already in use → Run stop script first
- Missing dependencies → Run `.\setup.bat`
- Python not found → Check Python 3.9+ is installed

## Stopping Services

```powershell
.\run-all-bg.ps1 --Stop
```

**What it does:**
1. Finds all processes using ports 8000 and 5173
2. Kills each process using 3 methods:
   - `Stop-Process -Force` (gentle)
   - `taskkill /F` (forceful)
   - `WMIC process delete` (nuclear)
3. Performs aggressive cleanup (kills any project-specific Python/Node processes)
4. Verifies ports are freed

**Expected output:**
```
🛑 Stopping all services...
Checking port 8000 (Backend)...
Found 1 process(es) on port 8000: 12345
  Killing PID 12345 (python)
[OK] Port 8000 freed
[OK] Port 5173 freed

✅ All services stopped successfully!
```

## Troubleshooting

### Port Still in Use After Stop

**Symptoms:**
```
[WARNING] Port 8000 still in use by PID 12345 (python)
```

**Solution:**
The process is resistant. Try:
```powershell
Stop-Process -Id 12345 -Force
# or
taskkill /F /PID 12345
```

### Orphaned TCP Connection

**Symptoms:**
```
[WARNING] Port 8000 has orphaned TCP connection (from dead PID 12345)
```

**What it means:**
The process was killed but the TCP stack still holds the port. This is a Windows TCP timeout issue.

**Solutions (choose one):**

1. **Wait it out** (easiest):
   - Takes 2-3 minutes for automatic TCP timeout
   - No action needed

2. **Close browser tabs**:
   - Close any tabs showing `http://localhost:8000` or `http://localhost:5173`
   - Browser connections keep ports alive even after server dies

3. **Restart PowerShell**:
   ```powershell
   exit
   # Open new PowerShell window
   cd d:\projects\supplychain-controltower
   ```
   - Fresh shell = cleared TCP stack

4. **Emergency stop** (nuclear option):
   ```cmd
   .\emergency-stop.bat
   ```
   - Kills ALL Python and Node processes on your system
   - Use only if other methods fail

### Checking Port Status

**Check what's using a port:**
```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen | 
    Select-Object LocalPort, OwningProcess, State

# Then get process details:
Get-Process -Id <OwningProcess>
```

**Check all connections on a port:**
```cmd
netstat -ano | findstr ":8000"
```

**Understanding netstat output:**
```
TCP    0.0.0.0:8000    0.0.0.0:0    LISTENING    12345
       ^              ^            ^            ^
       Local          Remote       State        PID
```

Common states:
- `LISTENING`: Server is accepting connections
- `ESTABLISHED`: Active connection
- `CLOSE_WAIT`: Client closed, server hasn't yet
- `FIN_WAIT_2`: Server closed, client hasn't acknowledged
- `TIME_WAIT`: Connection closed, waiting for network packets to expire

### Multiple Service Instances Running

**Symptoms:**
- Multiple PIDs shown: "Found 3 process(es) on port 8000: 12345, 12346, 12347"
- App behaves erratically
- Old data appears after making changes

**Cause:**
Started services multiple times without stopping.

**Solution:**
```powershell
.\run-all-bg.ps1 --Stop
# Wait for confirmation all ports freed
.\run-all-bg.ps1 --Start
```

The script now prevents duplicate starts by checking ports before starting.

## Best Practices

### Clean Restart Procedure

```powershell
# 1. Stop services
.\run-all-bg.ps1 --Stop

# 2. Close browser tabs to app
# Close tabs showing localhost:8000 or localhost:5173

# 3. Verify ports are free
Get-NetTCPConnection -LocalPort 8000,5173 -State Listen -ErrorAction SilentlyContinue
# Should return nothing

# 4. Start fresh
.\run-all-bg.ps1 --Start
```

### Before Demo

1. **Test full cycle:**
   ```powershell
   .\run-all-bg.ps1 --Stop
   .\run-all-bg.ps1 --Start
   # Open browser to http://localhost:5173
   # Test key features
   .\run-all-bg.ps1 --Stop
   ```

2. **Verify clean state:**
   - No orphaned processes
   - Ports freed completely
   - Can restart without issues

3. **Keep emergency stop ready:**
   - Have `emergency-stop.bat` available
   - Know how to force-kill: `Stop-Process -Name python,node -Force`

### During Development

**After code changes:**
```powershell
# Quick restart (if stop works cleanly)
.\run-all-bg.ps1 --Stop && .\run-all-bg.ps1 --Start

# If port stuck, close browser first then:
.\run-all-bg.ps1 --Stop
# Wait 10 seconds
.\run-all-bg.ps1 --Start
```

**If making database changes:**
```powershell
.\run-all-bg.ps1 --Stop
# Make DB changes/run migrations
.\populate-data.bat  # if repopulating data
.\run-all-bg.ps1 --Start
```

## Advanced

### Monitoring Services

**Check if services are running:**
```powershell
.\run-all-bg.ps1 --Status
```

**View service logs:**
- Backend: `backend/logs/app.log`
- Terminal output: Check PowerShell window where you started services

**Monitor in real-time:**
```powershell
# Backend health
Invoke-RestMethod http://localhost:8000/health

# Frontend dev server
# Watch PowerShell window for Vite output
```

### Manual Process Management

**Start backend manually:**
```powershell
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Start frontend manually:**
```powershell
cd frontend
npm run dev
```

**Benefits of manual start:**
- See real-time logs
- Easier debugging
- Auto-reload on code changes

**Downsides:**
- Requires 2 terminal windows
- Must stop manually (Ctrl+C)

## FAQ

**Q: Why does stop sometimes leave ports in use?**
A: When processes are force-killed, the Windows TCP stack may not immediately release ports. This creates "orphaned connections" that timeout after 2-3 minutes.

**Q: Is it safe to use emergency-stop.bat?**
A: Yes, but it kills ALL Python and Node processes on your system, not just this project. Save your work in other Python/Node projects first.

**Q: Can I change the ports?**
A: Yes, but you need to update:
- Backend: `backend/config.py` (API_PORT)
- Frontend: `frontend/vite.config.js` (server.port)
- Scripts: `run-all-bg.ps1` (portsToCheck array)

**Q: How do I know if services are running correctly?**
A: After start:
- Visit http://localhost:5173 (should see app)
- Visit http://localhost:8000/docs (should see API docs)
- Check: `.\run-all-bg.ps1 --Status`

**Q: What if stop script hangs?**
A: Press Ctrl+C to cancel, then:
1. Close browser tabs to app
2. Try stop again
3. If still stuck, use `emergency-stop.bat`
4. If completely stuck, restart PowerShell/Terminal

## Summary

**Happy Path:**
```powershell
.\run-all-bg.ps1 --Start   # Start services
# ... use the app ...
.\run-all-bg.ps1 --Stop    # Stop services
```

**Problem Path:**
```powershell
.\run-all-bg.ps1 --Stop    # Attempt stop
# [WARNING] Orphaned TCP connection detected
# Close browser tabs
# Wait 2-3 minutes OR restart PowerShell
.\run-all-bg.ps1 --Start   # Fresh start
```

**Nuclear Option:**
```cmd
.\emergency-stop.bat       # Kill everything
# Wait 10 seconds
.\run-all-bg.ps1 --Start   # Fresh start
```
