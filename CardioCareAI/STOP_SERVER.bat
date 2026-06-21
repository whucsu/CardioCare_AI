@echo off
title CardioCare AI - Stopping Server
color 0C
set "PORT=5060"

echo.
echo  ================================================================
echo   CardioCare AI  -  STOP SERVER
echo  ================================================================
echo.
echo  Stopping server on port %PORT%...

taskkill /FI "WINDOWTITLE eq CardioCare AI Server*" /F >nul 2>&1

for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr ":%PORT% "') do (
    echo  Stopping process %%P...
    taskkill /PID %%P /F >nul 2>&1
)

timeout /t 2 /nobreak >nul

netstat -ano 2>nul | findstr ":%PORT% " >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ OK ]  CardioCare AI server stopped. Port %PORT% is free.
) else (
    echo   [WARN]  Port %PORT% may still be in use.
    echo   Try REPAIR_AND_RECOVER.bat option 6 to force-free it.
)

echo.
timeout /t 3 /nobreak >nul
