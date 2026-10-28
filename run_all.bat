@echo off
title Launch APAAR-Setu Platform
cd /d "%~dp0"
echo ========================================================
echo   Launching APAAR-Setu Platform (Backend + Frontend)
echo ========================================================
start "APAAR-Setu Backend" run_backend.bat
timeout /t 3 /nobreak >nul
start "APAAR-Setu Frontend" run_frontend.bat
echo.
echo Both servers have been launched in separate console windows:
echo   - Backend:  http://localhost:8000 (API & Swagger at /docs)
echo   - Frontend: http://localhost:3000 (UI Portal)
echo.
pause
