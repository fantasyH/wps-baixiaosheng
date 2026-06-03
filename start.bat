@echo off
REM ==============================================
REM WPS百晓生 - 一键启动服务
REM 双击此文件即可启动全部后端
REM ==============================================
title WPS百晓生 后端服务
cd /d "%~dp0"

echo.
echo  ========================================
echo   WPS百晓生 后端服务 v3.0
echo  ========================================
echo.

REM Step 1: Kill any existing processes on port 5099
echo [1/3] Stopping existing processes...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5099"') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo       Done.

REM Step 2: Start server.py
echo [2/3] Starting server.py on port 5099...
start "WPS百晓生 Backend" python server.py
timeout /t 2 /nobreak >nul

REM Step 3: Start cloudflared tunnel
echo [3/3] Starting cloudflared tunnel...
start "WPS百晓生 Tunnel" cloudflared tunnel --url http://127.0.0.1:5099
timeout /t 5 /nobreak >nul

echo.
echo  ========================================
echo   ALL SERVICES RUNNING
echo  ========================================
echo   Health: http://127.0.0.1:5099/health
echo.
echo   TUNNEL URL may appear in the cloudflared window.
echo   Press any key to exit this window...
echo  ========================================
pause >nul
