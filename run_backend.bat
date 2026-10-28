@echo off
title APAAR-Setu Backend (Port 8000)
cd /d "%~dp0backend"
echo ========================================================
echo   Starting APAAR-Setu Backend Server on Port 8000
echo ========================================================
py -3.13 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
