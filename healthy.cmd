@echo off
:: Healthy Project - CMD Helper
:: Usage: healthy [mode]

if "%1"=="" goto dev
if "%1"=="dev" goto dev
if "%1"=="backend" goto backend
if "%1"=="frontend" goto frontend
if "%1"=="deploy" goto deploy
if "%1"=="ssh" goto ssh
if "%1"=="logs" goto logs
if "%1"=="status" goto status
if "%1"=="help" goto help
goto custom

:dev
title Healthy - Development
cd /d c:\OldD\_Projects\Healthy
echo Healthy - Development Mode
goto end

:backend
title Healthy - Backend Dev
cd /d c:\OldD\_Projects\Healthy\backend_v2
echo Starting backend...
python -m uvicorn main:app --reload --port 8000
goto end

:frontend
title Healthy - Frontend Dev
cd /d c:\OldD\_Projects\Healthy\frontend_v2
echo Starting frontend...
npm run dev
goto end

:deploy
title Healthy - Deploying...
cd /d c:\OldD\_Projects\Healthy
echo Deploying to production...
git push origin main
ssh root@62.171.163.23 "cd /opt/healthy && git pull && cd frontend_v2 && npm run build && systemctl restart healthy-api"
title Healthy - Deploy Complete
echo Deployment complete!
goto end

:ssh
title Healthy - SSH Production
ssh root@62.171.163.23
goto end

:logs
title Healthy - Production Logs
ssh root@62.171.163.23 "journalctl -u healthy-api -f"
goto end

:status
title Healthy - Server Status
echo Checking production server...
ssh root@62.171.163.23 "systemctl status healthy-api --no-pager && free -h && df -h /"
goto end

:help
title Healthy - Help
echo.
echo Healthy Project Commands
echo ========================
echo.
echo   healthy dev       - Set title to Development mode
echo   healthy backend   - Start backend dev server
echo   healthy frontend  - Start frontend dev server
echo   healthy deploy    - Deploy to production server
echo   healthy ssh       - SSH into production server
echo   healthy logs      - View production API logs
echo   healthy status    - Check production server status
echo   healthy [text]    - Set custom title
echo.
goto end

:custom
title Healthy - %*
echo Title set to: Healthy - %*
goto end

:end
