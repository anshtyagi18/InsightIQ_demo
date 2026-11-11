@echo off
setlocal enabledelayedexpansion
title InsightIQ - Full Platform Launcher (ANSH)
color 0B

echo ================================================================================
echo               INSIGHTIQ - AUTONOMOUS DATA INTELLIGENCE PLATFORM
echo                           LAUNCHER BY ANSH
echo ================================================================================
echo.

:: 1. Terminate any previous orphaned cloudflared instances
echo [*] Cleaning up previous tunnel instances...
taskkill /F /IM cloudflared.exe >nul 2>&1

:: 2. Flush local DNS cache
echo [*] Refreshing DNS cache...
ipconfig /flushdns >nul 2>&1

:: 3. Verify Python availability
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not found in your system PATH!
    echo Please install Python 3.10+ and ensure it is added to your PATH.
    echo.
    pause
    exit /b 1
)

:: 4. Verify Node.js / npm availability
call npm.cmd -v >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js / npm is not found in your system PATH!
    echo Please install Node.js 18+ from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

:: 5. Start Backend in a dedicated window
echo [*] Starting FastAPI Backend on http://localhost:8000 ...
start "InsightIQ Backend (FastAPI)" cmd /k "cd /d "%~dp0backend" && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: 6. Start Frontend in a dedicated window
echo [*] Starting Vite Frontend on http://localhost:3000 ...
start "InsightIQ Frontend (Vite)" cmd /k "cd /d "%~dp0" && call npm.cmd run dev"

:: 7. Launch Cloudflare Tunnel and establish verified live connection
echo [*] Initializing Cloudflare Tunnel and verifying live route...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tunnel\run_tunnel.ps1"

pause
