@echo off
echo Killing old server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5099"') do taskkill /f /pid %%a >nul 2>&1
timeout /t 3 >nul
echo Starting server...
start /B python C:\Users\Administrator\.wpscomate\agent\workspace\wps-baixiaosheng\server.py
timeout /t 10 >nul
echo Server should be running