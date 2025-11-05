# PowerShell script to start backend and frontend together
# Usage:
# - Run in one console as background jobs:    powershell -ExecutionPolicy Bypass -File .\start_all.ps1
# - Or dot-source and call Start-All in current session:  . .\start_all.ps1; Start-All

function Start-All {
    Write-Host "Starting Backend and Frontend..." -ForegroundColor Cyan

    # Clean up old completed jobs first
    Write-Host "Cleaning up old jobs..." -ForegroundColor Yellow
    Get-Job | Where-Object { $_.State -eq "Completed" -or $_.State -eq "Failed" } | Remove-Job -Force -ErrorAction SilentlyContinue
    
    # Check if jobs are already running
    $existingBackend = Get-Job -Name backend -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Running" }
    $existingFrontend = Get-Job -Name frontend -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Running" }
    
    if ($existingBackend -or $existingFrontend) {
        Write-Host "Warning: Backend or Frontend jobs are already running!" -ForegroundColor Yellow
        Write-Host "Please stop existing jobs first using: Get-Job | Stop-Job" -ForegroundColor Yellow
        return
    }

    # Get the script directory
    $ScriptDir = if ($MyInvocation.MyCommand.Path) { 
        Split-Path -Parent $MyInvocation.MyCommand.Path 
    } else { 
        Get-Location 
    }
    
    Write-Host "Script directory: $ScriptDir" -ForegroundColor Yellow

    # Check if ports are available
    Write-Host "Checking port availability..." -ForegroundColor Yellow
    $backendPort = 8000
    $frontendPort = 3000
    
    $backendInUse = Test-NetConnection -ComputerName localhost -Port $backendPort -InformationLevel Quiet -WarningAction SilentlyContinue
    $frontendInUse = Test-NetConnection -ComputerName localhost -Port $frontendPort -InformationLevel Quiet -WarningAction SilentlyContinue
    
    if ($backendInUse) {
        Write-Host "Port $backendPort is already in use. Attempting to kill existing process..." -ForegroundColor Red
        $process = Get-NetTCPConnection -LocalPort $backendPort -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
        if ($process) {
            Stop-Process -Id $process -Force -ErrorAction SilentlyContinue
            Write-Host "Killed process using port $backendPort" -ForegroundColor Green
            Start-Sleep -Seconds 2
        }
    }
    
    if ($frontendInUse) {
        Write-Host "Port $frontendPort is already in use. Attempting to kill existing process..." -ForegroundColor Red
        $process = Get-NetTCPConnection -LocalPort $frontendPort -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
        if ($process) {
            Stop-Process -Id $process -Force -ErrorAction SilentlyContinue
            Write-Host "Killed process using port $frontendPort" -ForegroundColor Green
            Start-Sleep -Seconds 2
        }
    }

    # Start Backend (Django)
    Write-Host "Starting backend job..." -ForegroundColor Yellow
    $backendJob = Start-Job -Name backend -ScriptBlock {
        param($ScriptDir)
        try {
            Set-Location "$ScriptDir/backend"
            # If you use a venv, activate it here if exists
            if (Test-Path ".\venv\Scripts\Activate.ps1") { 
                . ".\venv\Scripts\Activate.ps1" 
            }
            $env:DJANGO_SETTINGS_MODULE = "settings.development"
            Write-Host "[backend] Running: python manage.py runserver 0.0.0.0:8000" -ForegroundColor Cyan
            Write-Host "[backend] Starting Django server..." -ForegroundColor Yellow
            python manage.py runserver 0.0.0.0:8000 2>&1 | ForEach-Object {
                Write-Host "[backend] $_" -ForegroundColor Green
            }
        } catch {
            Write-Host "[backend] ERROR: $_" -ForegroundColor Red
            Write-Host "[backend] Stack trace: $($_.ScriptStackTrace)" -ForegroundColor Red
            Write-Error "[backend] failed: $_"
        }
    } -ArgumentList $ScriptDir
    Write-Host "Backend job started with ID: $($backendJob.Id)" -ForegroundColor Green

    # Start Frontend (Next.js)
    Write-Host "Starting frontend job..." -ForegroundColor Yellow
    $frontendJob = Start-Job -Name frontend -ScriptBlock {
        param($ScriptDir)
        try {
            Set-Location "$ScriptDir/frontend"
            
            # Clean .next folder to prevent file system errors
            if (Test-Path ".next") {
                Write-Host "[frontend] Cleaning .next folder to prevent file system errors..." -ForegroundColor Yellow
                Remove-Item -Recurse -Force ".next" -ErrorAction SilentlyContinue
            }
            
            Write-Host "[frontend] Running: npm run dev:external" -ForegroundColor Cyan
            Write-Host "[frontend] Starting Next.js server..." -ForegroundColor Yellow
            npm run dev:external 2>&1 | ForEach-Object {
                Write-Host "[frontend] $_" -ForegroundColor Green
            }
        } catch {
            Write-Host "[frontend] ERROR: $_" -ForegroundColor Red
            Write-Host "[frontend] Stack trace: $($_.ScriptStackTrace)" -ForegroundColor Red
            Write-Error "[frontend] failed: $_"
        }
    } -ArgumentList $ScriptDir
    Write-Host "Frontend job started with ID: $($frontendJob.Id)" -ForegroundColor Green

    # Wait a bit and check server status
    Write-Host "Waiting for servers to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5

    # Check backend status
    $backendRunning = Test-NetConnection -ComputerName localhost -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($backendRunning) {
        Write-Host "Backend server is running on port 8000" -ForegroundColor Green
    } else {
        Write-Host "Warning: Backend server may not be running. Check logs with: Receive-Job -Name backend -Keep" -ForegroundColor Yellow
    }

    # Check frontend status
    $frontendRunning = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($frontendRunning) {
        Write-Host "Frontend server is running on port 3000" -ForegroundColor Green
    } else {
        Write-Host "Warning: Frontend server may not be running. Check logs with: Receive-Job -Name frontend -Keep" -ForegroundColor Yellow
    }

    Write-Host "`nStarted as background jobs. Use the following commands to view logs:" -ForegroundColor Green
    Write-Host "  - View backend logs: Receive-Job -Name backend -Keep" -ForegroundColor Cyan
    Write-Host "  - View frontend logs: Receive-Job -Name frontend -Keep" -ForegroundColor Cyan
    Write-Host "  - View all jobs: Get-Job" -ForegroundColor Cyan
    Write-Host "  - Stop all: Stop-All" -ForegroundColor Cyan
}

function Stop-All {
    Write-Host "Stopping Backend and Frontend jobs..." -ForegroundColor Cyan
    
    # Stop running jobs
    Get-Job -Name backend -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Running" } | Stop-Job
    Get-Job -Name frontend -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Running" } | Stop-Job
    
    # Remove all jobs
    Get-Job | Remove-Job -Force -ErrorAction SilentlyContinue
    
    Write-Host "All jobs stopped and removed." -ForegroundColor Green
}

function Start-AllWindows {
    Write-Host "Launching Backend and Frontend in new windows..." -ForegroundColor Cyan
    $ScriptDir = if ($MyInvocation.MyCommand.Path) { 
        Split-Path -Parent $MyInvocation.MyCommand.Path 
    } else { 
        Get-Location 
    }
    Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$ScriptDir'; cd backend; if (Test-Path .\venv\Scripts\Activate.ps1) { . .\venv\Scripts\Activate.ps1 }; `$env:DJANGO_SETTINGS_MODULE='settings.development'; python manage.py runserver 0.0.0.0:8000" | Out-Null
    Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$ScriptDir'; cd frontend; if (Test-Path '.next') { Remove-Item -Recurse -Force '.next' -ErrorAction SilentlyContinue }; npm run dev:external" | Out-Null
    Write-Host "New windows launched." -ForegroundColor Green
}

# Auto-run as background jobs if executed directly
if ($MyInvocation.InvocationName -eq ".\start_all.ps1") {
    Start-All
}


