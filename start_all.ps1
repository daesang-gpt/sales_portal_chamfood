# PowerShell script to start backend and frontend together
# Usage:
# - Run in one console as background jobs:    powershell -ExecutionPolicy Bypass -File .\start_all.ps1
# - Or dot-source and call Start-All in current session:  . .\start_all.ps1; Start-All

function Start-All {
    Write-Host "Starting Backend and Frontend..." -ForegroundColor Cyan

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
            Write-Host "[backend] running: python manage.py runserver 0.0.0.0:8000"
            python manage.py runserver 0.0.0.0:8000
        } catch {
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
                Write-Host "[frontend] Cleaning .next folder to prevent file system errors..."
                Remove-Item -Recurse -Force ".next" -ErrorAction SilentlyContinue
            }
            
            Write-Host "[frontend] running: npm run dev:external"
            npm run dev:external
        } catch {
            Write-Error "[frontend] failed: $_"
        }
    } -ArgumentList $ScriptDir
    Write-Host "Frontend job started with ID: $($frontendJob.Id)" -ForegroundColor Green

    Write-Host "Started as background jobs. Use 'Get-Job' and 'Receive-Job -Keep' to view logs." -ForegroundColor Green
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


