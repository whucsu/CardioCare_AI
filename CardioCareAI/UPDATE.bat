@echo off
setlocal EnableDelayedExpansion
title CardioCare AI - UPDATE
mode con: cols=78 lines=40
color 0A

set "BASEDIR=%~dp0"
if "%BASEDIR:~-1%"=="\" set "BASEDIR=%BASEDIR:~0,-1%"
set "VENV_DIR=%BASEDIR%\venv"
set "OFFLINE_DIR=%BASEDIR%\offline_packages"
set "LOGS_DIR=%BASEDIR%\logs"

if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
set "LOGFILE=%LOGS_DIR%\update_%DATE:~-4,4%%DATE:~-7,2%%DATE:~-10,2%.log"

cls
echo.
echo  ================================================================
echo   CardioCare AI  -  UPDATE TOOL
echo  ================================================================
echo  Updates packages to latest versions.
echo  Your uploads and data are NOT affected.
echo  ================================================================
echo.

ping -n 1 -w 2000 8.8.8.8 >nul 2>&1
if %errorlevel% neq 0 (
    echo   [FAIL]  No internet. Connect and retry.
    pause & exit /b 1
)
echo   [ OK ]  Internet connected.
echo.

if not exist "%VENV_DIR%\Scripts\pip.exe" (
    echo   [FAIL]  Venv not found. Run START_CardioCare_AI.bat first.
    pause & exit /b 1
)
set "PIP=%VENV_DIR%\Scripts\pip.exe"
echo   [ OK ]  Venv found.
echo.

echo   1  =  Update all packages
echo   2  =  Update + refresh offline cache
echo   3  =  Check what has updates available
echo   0  =  Cancel
echo.
set /p "CHOICE=  Choice (0-3): "
if "%CHOICE%"=="0" exit /b 0
if "%CHOICE%"=="3" (
    echo.
    echo  Checking for outdated packages...
    "%PIP%" list --outdated 2>>"%LOGFILE%"
    echo.
    pause & exit /b 0
)

echo.
echo  [1/2]  Upgrading pip...
"%PIP%" install --upgrade pip --quiet >> "%LOGFILE%" 2>&1
echo   [ OK ]  pip upgraded.
echo.
echo  [2/2]  Upgrading packages...
for %%K in (flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil) do (
    echo     Upgrading %%K ...
    "%PIP%" install --upgrade %%K --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
    if "%CHOICE%"=="2" ("%PIP%" download %%K --dest="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1)
)
echo   [ OK ]  All packages updated.
echo.
echo  ================================================================
echo   Update complete. Restart CardioCare AI to use new packages.
echo   Log: %LOGFILE%
echo  ================================================================
echo.
pause
