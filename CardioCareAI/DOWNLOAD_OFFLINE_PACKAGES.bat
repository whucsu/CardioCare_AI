@echo off
setlocal EnableDelayedExpansion
title CardioCare AI - Download Offline Packages
mode con: cols=78 lines=45
color 0B

set "BASEDIR=%~dp0"
if "%BASEDIR:~-1%"=="\" set "BASEDIR=%BASEDIR:~0,-1%"
set "OFFLINE_DIR=%BASEDIR%\offline_packages"
set "VENV_DIR=%BASEDIR%\venv"
set "LOGS_DIR=%BASEDIR%\logs"

if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
if not exist "%OFFLINE_DIR%" mkdir "%OFFLINE_DIR%"
set "LOGFILE=%LOGS_DIR%\offline_%DATE:~-4,4%%DATE:~-7,2%%DATE:~-10,2%.log"

cls
echo.
echo  ================================================================
echo   CardioCare AI  -  OFFLINE PACKAGE DOWNLOADER
echo  ================================================================
echo  Downloads all required packages to this folder.
echo  After this, CardioCare AI works WITHOUT internet.
echo  Run once while online - then use offline forever.
echo  ================================================================
echo.

echo  Checking internet...
ping -n 1 -w 3000 8.8.8.8 >nul 2>&1
if %errorlevel% neq 0 (
    echo   [FAIL]  No internet. Connect and try again.
    pause & exit /b 1
)
echo   [ OK ]  Internet connected.
echo.

echo  Finding pip...
set "PIP="
if exist "%VENV_DIR%\Scripts\pip.exe" (set "PIP=%VENV_DIR%\Scripts\pip.exe" & echo   [ OK ]  Using venv pip.) else (
    pip --version >nul 2>&1
    if !errorlevel!==0 (set "PIP=pip" & echo   [ OK ]  Using system pip.) else (
        echo   [FAIL]  pip not found. Run START_CardioCare_AI.bat first.
        pause & exit /b 1
    )
)
echo.

echo  [Step 1/4]  Upgrading pip...
%PIP% install --upgrade pip --quiet >> "%LOGFILE%" 2>&1
echo   [ OK ]  pip upgraded.
echo.

echo  [Step 2/4]  Downloading core packages...
echo  This takes 3-8 minutes. Please wait...
echo.
set /a DONE=0
set /a TOTAL=10
for %%K in (flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil) do (
    set /a DONE+=1
    echo   [!DONE!/%TOTAL%]  Downloading: %%K
    %PIP% download %%K --dest="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (echo              [ OK ]  %%K cached) else (echo              [WARN]  %%K - check log)
)
echo.

echo  [Step 3/4]  Downloading optional packages...
for %%K in (langchain openai) do (
    echo   Trying: %%K
    %PIP% download %%K --dest="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
    if !errorlevel!==0 (echo          [ OK ]) else (echo          [ -- ]  skipped)
)
echo.

echo  [Step 4/4]  Verifying...
set /a WHLCOUNT=0
for %%W in ("%OFFLINE_DIR%\*.whl") do set /a WHLCOUNT+=1
for %%W in ("%OFFLINE_DIR%\*.tar.gz") do set /a WHLCOUNT+=1
echo   [ OK ]  %WHLCOUNT% packages cached in offline_packages folder.

(
echo CardioCare AI Offline Cache Manifest
echo Downloaded: %DATE% %TIME%
echo Total: %WHLCOUNT% files
) > "%OFFLINE_DIR%\MANIFEST.txt"
echo   [ OK ]  Manifest saved.
echo.
echo  ================================================================
echo   DOWNLOAD COMPLETE
echo   CardioCare AI will now work WITHOUT internet.
echo   Just run START_CardioCare_AI.bat normally.
echo  ================================================================
echo.
pause
