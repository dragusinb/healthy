# Healthy Project - PowerShell Helper
# Usage: . .\healthy.ps1 [mode]
# Modes: dev, deploy, backend, frontend, test, ssh

param(
    [Parameter(Position=0)]
    [string]$Mode = "dev"
)

$baseTitle = "Healthy"

function Set-HealthyTitle {
    param([string]$Detail)
    $Host.UI.RawUI.WindowTitle = "$baseTitle - $Detail"
}

function Show-Help {
    Write-Host ""
    Write-Host "Healthy Project Commands" -ForegroundColor Cyan
    Write-Host "========================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  healthy dev       " -NoNewline -ForegroundColor Yellow
    Write-Host "- Set title to Development mode"
    Write-Host "  healthy backend   " -NoNewline -ForegroundColor Yellow
    Write-Host "- Start backend dev server"
    Write-Host "  healthy frontend  " -NoNewline -ForegroundColor Yellow
    Write-Host "- Start frontend dev server"
    Write-Host "  healthy deploy    " -NoNewline -ForegroundColor Yellow
    Write-Host "- Deploy to production server"
    Write-Host "  healthy ssh       " -NoNewline -ForegroundColor Yellow
    Write-Host "- SSH into production server"
    Write-Host "  healthy logs      " -NoNewline -ForegroundColor Yellow
    Write-Host "- View production API logs"
    Write-Host "  healthy status    " -NoNewline -ForegroundColor Yellow
    Write-Host "- Check production server status"
    Write-Host "  healthy test      " -NoNewline -ForegroundColor Yellow
    Write-Host "- Run backend tests"
    Write-Host "  healthy db        " -NoNewline -ForegroundColor Yellow
    Write-Host "- Connect to production database"
    Write-Host ""
}

switch ($Mode.ToLower()) {
    "dev" {
        Set-HealthyTitle "Development"
        Set-Location "c:\OldD\_Projects\Healthy"
        Write-Host "Healthy - Development Mode" -ForegroundColor Green
    }
    "backend" {
        Set-HealthyTitle "Backend Dev"
        Set-Location "c:\OldD\_Projects\Healthy\backend_v2"
        Write-Host "Starting backend..." -ForegroundColor Yellow
        & python -m uvicorn main:app --reload --port 8000
    }
    "frontend" {
        Set-HealthyTitle "Frontend Dev"
        Set-Location "c:\OldD\_Projects\Healthy\frontend_v2"
        Write-Host "Starting frontend..." -ForegroundColor Yellow
        & npm run dev
    }
    "deploy" {
        Set-HealthyTitle "Deploying..."
        Write-Host "Deploying to production..." -ForegroundColor Yellow
        Set-Location "c:\OldD\_Projects\Healthy"
        git push origin main
        ssh root@62.171.163.23 "cd /opt/healthy && git pull && cd frontend_v2 && npm run build && systemctl restart healthy-api"
        Set-HealthyTitle "Deploy Complete"
        Write-Host "Deployment complete!" -ForegroundColor Green
    }
    "ssh" {
        Set-HealthyTitle "SSH Production"
        ssh root@62.171.163.23
    }
    "logs" {
        Set-HealthyTitle "Production Logs"
        ssh root@62.171.163.23 "journalctl -u healthy-api -f"
    }
    "status" {
        Set-HealthyTitle "Server Status"
        Write-Host "Checking production server..." -ForegroundColor Yellow
        ssh root@62.171.163.23 "echo '=== Services ===' && systemctl status healthy-api --no-pager && echo '' && echo '=== Memory ===' && free -h && echo '' && echo '=== Disk ===' && df -h / && echo '' && echo '=== DB Stats ===' && PGPASSWORD=HealthyDB123 psql -h localhost -U healthy -d healthy -c 'SELECT (SELECT COUNT(*) FROM users) as users, (SELECT COUNT(*) FROM documents) as documents, (SELECT COUNT(*) FROM test_results) as biomarkers;'"
    }
    "test" {
        Set-HealthyTitle "Running Tests"
        Set-Location "c:\OldD\_Projects\Healthy\backend_v2"
        Write-Host "Running tests..." -ForegroundColor Yellow
        & python -m pytest tests/ -v
    }
    "db" {
        Set-HealthyTitle "Production DB"
        ssh root@62.171.163.23 "PGPASSWORD=HealthyDB123 psql -h localhost -U healthy -d healthy"
    }
    "help" {
        Set-HealthyTitle "Help"
        Show-Help
    }
    default {
        Set-HealthyTitle $Mode
        Write-Host "Title set to: Healthy - $Mode" -ForegroundColor Green
    }
}
