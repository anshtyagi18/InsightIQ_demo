@echo off
setlocal enabledelayedexpansion
title InsightIQ - Full Platform Launcher (ANSH)
color 0B

echo ================================================================================
echo               INSIGHTIQ - AUTONOMOUS DATA INTELLIGENCE PLATFORM
echo                           LAUNCHER BY ANSH
echo ================================================================================
echo.

:: 1. Verify Python availability
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not found in your system PATH!
    echo Please install Python 3.10+ and ensure it is added to your PATH.
    echo.
    pause
    exit /b 1
)

:: 2. Verify Node.js / npm availability
call npm.cmd -v >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js / npm is not found in your system PATH!
    echo Please install Node.js 18+ from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

:: 3. Start Backend in a dedicated window
echo [*] Starting FastAPI Backend on http://localhost:8000 ...
start "InsightIQ Backend (FastAPI)" cmd /k "cd /d "%~dp0backend" && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: 4. Start Frontend in a dedicated window
echo [*] Starting Vite Frontend on http://localhost:3000 ...
start "InsightIQ Frontend (Vite)" cmd /k "cd /d "%~dp0" && call npm.cmd run dev"

:: 5. Launch Cloudflare Tunnel and establish live public connection
echo [*] Launching Cloudflare Tunnel for secure live public access...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tunnel\run_tunnel.ps1"

pause
