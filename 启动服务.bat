@echo off
title WPS百晓生
echo.
echo  ╔═══════════════════════════════════╗
echo  ║    WPS百晓生 - 一键启动          ║
echo  ╚═══════════════════════════════════╝
echo.

cd /d "%~dp0"

:: Kill old processes
taskkill /F /IM python.exe 2>nul
taskkill /F /IM cloudflared.exe 2>nul
timeout /t 2 /nobreak >nul

:: Start server
echo [1/2] Starting server on port 5099...
start "WPS百晓生后端" python server.py
timeout /t 4 /nobreak >nul

:: Health check
curl -s http://localhost:5099/health >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Server failed to start!
    pause
    exit /b 1
)
echo [OK] Server is running!
echo.

:: Start tunnel
echo [2/2] Creating public tunnel...
start "WPS百晓生隧道" cmd /c "npx localtunnel --port 5099"
timeout /t 8 /nobreak >nul

echo.
echo ╔═══════════════════════════════════════════════════╗
echo ║  ✅ WPS百晓生 已启动!                             ║
echo ║                                                   ║
echo ║  本机访问：http://localhost:5099                  ║
echo ║                                                   ║
echo ║  请查看上方 tunnel 输出的新 URL（如有）          ║
echo ║                                                   ║
echo ║  在页面右上角点击「登录 ACH」可授权实时数据      ║
echo ╚═══════════════════════════════════════════════════╝
echo.
echo 按 Ctrl+C 停止所有服务
pause
