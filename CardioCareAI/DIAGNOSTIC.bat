@echo off
setlocal EnableDelayedExpansion
title CardioCare AI - DIAGNOSTIC TOOL
mode con: cols=78 lines=55
color 0E

set "BASEDIR=%~dp0"
if "%BASEDIR:~-1%"=="\" set "BASEDIR=%BASEDIR:~0,-1%"
set "VENV_DIR=%BASEDIR%\venv"
set "LOGS_DIR=%BASEDIR%\logs"
set "PORT=5060"

if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
set "RPT=%LOGS_DIR%\diagnostic_%DATE:~-4,4%%DATE:~-7,2%%DATE:~-10,2%.txt"

cls
echo.
echo  ================================================================
echo   CardioCare AI  -  FULL DIAGNOSTIC TOOL
echo  ================================================================
echo  Running system check. Report saved to logs folder.
echo  ================================================================
echo.

echo CardioCare AI Diagnostic Report > "%RPT%"
echo Date: %DATE%  Time: %TIME% >> "%RPT%"
echo ================================================================ >> "%RPT%"

:: 1. SYSTEM
call :SEC "1. SYSTEM INFORMATION"
for /f "skip=1 tokens=*" %%V in ('wmic os get Caption 2^>nul') do (
    if not "%%V"=="" echo    OS: %%V & echo OS: %%V >> "%RPT%"
)

:: 2. INTERNET
call :SEC "2. INTERNET"
ping -n 1 -w 2000 8.8.8.8 >nul 2>&1
if %errorlevel%==0 (call :OK "Internet: ONLINE") else (call :WARN "Internet: OFFLINE")
ping -n 1 -w 3000 api.anthropic.com >nul 2>&1
if %errorlevel%==0 (call :OK "Anthropic API: Reachable") else (call :WARN "Anthropic API: Not reachable")
ping -n 1 -w 3000 pypi.org >nul 2>&1
if %errorlevel%==0 (call :OK "PyPI: Reachable") else (call :WARN "PyPI: Not reachable")

:: 3. PYTHON
call :SEC "3. PYTHON"
python --version >nul 2>&1
if %errorlevel%==0 (
    for /f "delims=" %%V in ('python --version 2^>^&1') do call :OK "System Python: %%V"
) else (
    call :FAIL "System Python: NOT FOUND"
)
if exist "%VENV_DIR%\Scripts\python.exe" (
    for /f "delims=" %%V in ('"%VENV_DIR%\Scripts\python.exe" --version 2^>^&1') do call :OK "VEnv Python: %%V"
) else (
    call :FAIL "VEnv: NOT CREATED - run START_CardioCare_AI.bat first"
)

:: 4. PACKAGES
call :SEC "4. PACKAGES"
if exist "%VENV_DIR%\Scripts\python.exe" (
    for %%M in (flask flask_cors requests PIL fitz anthropic numpy colorama psutil) do (
        "%VENV_DIR%\Scripts\python.exe" -c "import %%M" >nul 2>&1
        if !errorlevel!==0 (call :OK "  %%M: installed") else (call :FAIL "  %%M: MISSING - run REPAIR_AND_RECOVER.bat")
    )
) else (
    call :WARN "Cannot check packages - venv not set up"
)

:: 5. FILES
call :SEC "5. APPLICATION FILES"
for %%F in (
    "server.py"
    "static\index.html"
    "START_CardioCare_AI.bat"
    "DIAGNOSTIC.bat"
    "REPAIR_AND_RECOVER.bat"
    "DOWNLOAD_OFFLINE_PACKAGES.bat"
    "UPDATE.bat"
    "STOP_SERVER.bat"
) do (
    if exist "%BASEDIR%\%%~F" (
        for %%S in ("%BASEDIR%\%%~F") do call :OK "  %%~F  (%%~zS bytes)"
    ) else (
        call :FAIL "  %%~F  MISSING"
    )
)

:: 6. FOLDERS
call :SEC "6. FOLDERS"
for %%D in (uploads offline_packages logs data static reports_db) do (
    if exist "%BASEDIR%\%%D\" (call :OK "  %%D exists") else (
        mkdir "%BASEDIR%\%%D" 2>nul
        call :WARN "  %%D was missing - created"
    )
)

:: 7. OFFLINE CACHE
call :SEC "7. OFFLINE PACKAGE CACHE"
if exist "%BASEDIR%\offline_packages\*.whl" (
    set /a N=0
    for %%W in ("%BASEDIR%\offline_packages\*.whl") do set /a N+=1
    call :OK "  Cached packages: !N! files"
) else (
    call :WARN "  No offline packages. Run DOWNLOAD_OFFLINE_PACKAGES.bat while online."
)

:: 8. SERVER
call :SEC "8. SERVER STATUS (port %PORT%)"
netstat -ano 2>nul | findstr ":%PORT% " >nul 2>&1
if %errorlevel%==0 (
    call :OK "  Server IS running on port %PORT%"
    curl -s "http://localhost:%PORT%/api/health" >nul 2>&1
    if !errorlevel!==0 (call :OK "  Health check: PASSED") else (call :WARN "  Health check: No response yet")
) else (
    call :WARN "  Server NOT running - start with START_CardioCare_AI.bat"
)

:: 9. API KEY
call :SEC "9. AI PROVIDER (Server-side default key, optional)"
if not "%ANTHROPIC_API_KEY%"=="" (
    call :OK "  ANTHROPIC_API_KEY: Set as server default - live AI enabled"
) else (
    call :WARN "  No server-side default key set - this is normal"
    call :INFO "  Choose any of 5 AI providers (Claude, ChatGPT, Gemini, Grok, DeepSeek)"
    call :INFO "  and enter your key directly in the app under Settings."
)

:: 10. RECENT LOG
call :SEC "10. RECENT SERVER LOG"
if exist "%LOGS_DIR%\server.log" (
    echo.
    echo   Last 10 lines of server.log:
    powershell -Command "Get-Content '%LOGS_DIR%\server.log' -Tail 10 2>$null | ForEach-Object { Write-Host '  ' $_ }"
) else (
    call :WARN "  No server log found yet"
)

echo.
echo  ================================================================
echo   DIAGNOSTIC COMPLETE
echo   Report: %RPT%
echo  ================================================================
echo.
echo   R = Repair   L = Open Report   S = Start   X = Exit
echo.

:DIAG_MENU
set /p "DC=  Choice [R/L/S/X]: "
if /i "%DC%"=="R" call "%BASEDIR%\REPAIR_AND_RECOVER.bat" & goto :DIAG_MENU
if /i "%DC%"=="L" start notepad "%RPT%" & goto :DIAG_MENU
if /i "%DC%"=="S" call "%BASEDIR%\START_CardioCare_AI.bat" & exit /b 0
if /i "%DC%"=="X" exit /b 0
goto :DIAG_MENU

:SEC
echo.
echo   --- %~1 ---
echo. >> "%RPT%"
echo --- %~1 --- >> "%RPT%"
goto :EOF

:OK
echo   [ OK ]  %~1
echo [OK] %~1 >> "%RPT%"
goto :EOF

:WARN
echo   [WARN]  %~1
echo [WARN] %~1 >> "%RPT%"
goto :EOF

:FAIL
echo   [FAIL]  %~1
echo [FAIL] %~1 >> "%RPT%"
goto :EOF

:INFO
echo          %~1
echo [INFO] %~1 >> "%RPT%"
goto :EOF
