@echo off
setlocal EnableDelayedExpansion
title CardioCare AI - Launching
mode con: cols=78 lines=50
color 0F

set "BASEDIR=%~dp0"
if "%BASEDIR:~-1%"=="\" set "BASEDIR=%BASEDIR:~0,-1%"

set "VENV_DIR=%BASEDIR%\venv"
set "OFFLINE_DIR=%BASEDIR%\offline_packages"
set "LOGS_DIR=%BASEDIR%\logs"
set "PORT=5060"
set "ONLINE=false"
set "PYTHON_EXE="
set "VPYTHON="
set "VPIP="

if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
set "LOGFILE=%LOGS_DIR%\launch_%DATE:~-4,4%%DATE:~-7,2%%DATE:~-10,2%.log"

call :LOG "===== CardioCare AI Launch Started %DATE% %TIME% ====="
call :LOG "Base folder: %BASEDIR%"

cls
echo.
echo  ================================================================
echo   CardioCare AI  -  Cardiac Health Intelligence Platform  v1.0
echo  ================================================================
echo.
echo  MEDICAL DISCLAIMER:
echo  This is an AI Research Tool ONLY. Not medical advice.
echo  ALWAYS consult your cardiologist before any decision.
echo  CARDIAC EMERGENCY: Call 112 (India) / 999 (UK) / 911 (US)
echo.
echo  ================================================================
echo.

:: ---------------------------------------------------------------
:: STEP 1 - CHECK INTERNET
:: ---------------------------------------------------------------
echo  [STEP 1/7]  Checking internet connection...
call :LOG "Checking internet"
ping -n 1 -w 2000 8.8.8.8 >nul 2>&1
if %errorlevel%==0 (
    set "ONLINE=true"
    echo              [ OK ]  Online - live AI features available
    call :LOG "Internet: ONLINE"
) else (
    set "ONLINE=false"
    echo              [ -- ]  Offline - offline research mode
    call :LOG "Internet: OFFLINE"
)
echo.

:: ---------------------------------------------------------------
:: STEP 2 - FIND PYTHON
:: ---------------------------------------------------------------
echo  [STEP 2/7]  Looking for Python...
call :LOG "Locating Python"

python --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_EXE=python"
    for /f "tokens=*" %%V in ('python --version 2^>^&1') do (
        echo              [ OK ]  %%V found
        call :LOG "Python: %%V"
    )
    goto :PYTHON_OK
)

py --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_EXE=py"
    for /f "tokens=*" %%V in ('py --version 2^>^&1') do (
        echo              [ OK ]  %%V via launcher
        call :LOG "Python launcher: %%V"
    )
    goto :PYTHON_OK
)

for %%D in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist %%D (
        set "PYTHON_EXE=%%~D"
        echo              [ OK ]  Python found at: %%~D
        call :LOG "Python: %%~D"
        goto :PYTHON_OK
    )
)

echo              [FAIL]  Python not found.
call :LOG "Python NOT found"
if "%ONLINE%"=="true" (
    echo  Downloading Python 3.11 installer...
    echo  CHECK the "Add Python to PATH" box when it opens!
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\py_setup.exe' -UseBasicParsing" >> "%LOGFILE%" 2>&1
    if exist "%TEMP%\py_setup.exe" (
        start /wait "" "%TEMP%\py_setup.exe"
        python --version >nul 2>&1
        if !errorlevel!==0 (
            set "PYTHON_EXE=python"
            goto :PYTHON_OK
        )
    )
)
echo  Please install Python from: https://www.python.org/downloads/
pause & exit /b 1

:PYTHON_OK
echo.

:: ---------------------------------------------------------------
:: STEP 3 - VIRTUAL ENVIRONMENT
:: ---------------------------------------------------------------
echo  [STEP 3/7]  Setting up virtual environment...
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo              Creating environment...
    "%PYTHON_EXE%" -m venv "%VENV_DIR%" >> "%LOGFILE%" 2>&1
    if !errorlevel! neq 0 (
        echo              [FAIL]  Run REPAIR_AND_RECOVER.bat
        pause & exit /b 1
    )
    echo              [ OK ]  Environment created.
) else (
    echo              [ OK ]  Environment ready.
)

set "VPYTHON=%VENV_DIR%\Scripts\python.exe"
set "VPIP=%VENV_DIR%\Scripts\pip.exe"
echo.

:: ---------------------------------------------------------------
:: STEP 4 - PACKAGES
:: ---------------------------------------------------------------
echo  [STEP 4/7]  Checking packages...
"%VPYTHON%" -c "import flask" >nul 2>&1
if %errorlevel%==0 (
    echo              [ OK ]  Packages already installed.
    goto :PKG_DONE
)

echo              Installing packages - please wait 2-5 minutes...
echo.
"%VPYTHON%" -m pip install --upgrade pip --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1

if "%ONLINE%"=="true" (
    echo              Downloading from internet...
    for %%K in (flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil) do (
        echo                Installing %%K ...
        "%VPIP%" install %%K --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
        if !errorlevel! neq 0 (
            "%VPIP%" install %%K --quiet --no-index --find-links="%OFFLINE_DIR%" >> "%LOGFILE%" 2>&1
        ) else (
            "%VPIP%" download %%K --dest="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
        )
    )
) else (
    if exist "%OFFLINE_DIR%\*.whl" (
        echo              Installing from offline cache...
        "%VPIP%" install flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil --no-index --find-links="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
    ) else (
        echo  No offline packages. Run DOWNLOAD_OFFLINE_PACKAGES.bat while online.
        pause & exit /b 1
    )
)

"%VPYTHON%" -c "import flask" >nul 2>&1
if !errorlevel! neq 0 (
    echo  [FAIL] Installation failed. Check: %LOGFILE%
    call :LOG "Package install FAILED"
    start notepad "%LOGFILE%"
    pause & exit /b 1
)
echo              [ OK ]  All packages ready.
call :LOG "Packages OK"

:PKG_DONE
echo.

:: ---------------------------------------------------------------
:: STEP 5 - CHECK FILES
:: ---------------------------------------------------------------
echo  [STEP 5/7]  Checking application files...
if not exist "%BASEDIR%\server.py" (
    echo              [FAIL]  server.py missing. Re-extract ZIP.
    pause & exit /b 1
)
if not exist "%BASEDIR%\static\index.html" (
    echo              [FAIL]  static\index.html missing. Re-extract ZIP.
    pause & exit /b 1
)
for %%D in (uploads offline_packages logs data static reports_db) do (
    if not exist "%BASEDIR%\%%D\" mkdir "%BASEDIR%\%%D" >nul 2>&1
)
echo              [ OK ]  All files verified.
echo.

:: ---------------------------------------------------------------
:: STEP 6 - PORT
:: ---------------------------------------------------------------
echo  [STEP 6/7]  Checking port %PORT%...
netstat -ano 2>nul | findstr ":%PORT% " >nul 2>&1
if %errorlevel%==0 (
    echo              Freeing port %PORT%...
    for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr ":%PORT% "') do taskkill /PID %%P /F >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo              [ OK ]  Port freed.
) else (
    echo              [ OK ]  Port %PORT% available.
)
echo.

:: ---------------------------------------------------------------
:: STEP 7 - START SERVER
:: ---------------------------------------------------------------
echo  [STEP 7/7]  Starting CardioCare AI server...
call :LOG "Starting server"

if not "%ANTHROPIC_API_KEY%"=="" (
    echo              [ OK ]  Server default API key found - live AI enabled.
) else (
    echo              [ -- ]  No server default key - choose a provider in Settings.
    echo              5 AI options available: Claude, ChatGPT, Gemini, Grok, DeepSeek.
)

start "CardioCare AI Server" cmd /k "echo CardioCare AI Server - Keep Open && "%VPYTHON%" "%BASEDIR%\server.py" --port %PORT%"

echo              Waiting for server...
set "SERVER_UP=false"
for /L %%i in (1,1,25) do (
    timeout /t 1 /nobreak >nul
    curl -s "http://localhost:%PORT%/api/health" >nul 2>&1
    if !errorlevel!==0 (
        set "SERVER_UP=true"
        goto :SRV_READY
    )
    echo              Starting... [%%i/25]
)

:SRV_READY
if "%SERVER_UP%"=="true" (
    echo              [ OK ]  Server running.
    call :LOG "Server confirmed running"
) else (
    echo              Server may still be loading - try browser manually.
    call :LOG "Server startup timeout"
)

cls
echo.
echo  ================================================================
echo   CardioCare AI IS RUNNING
echo  ================================================================
echo.
echo   Open this in your browser:
echo.
echo      http://localhost:%PORT%
echo.
echo   Server window: Keep the other CMD window open.
echo   Mode: Online = %ONLINE%
echo   Log:  %LOGFILE%
echo.
echo  ================================================================
echo   DISCLAIMER: For research only. Not medical advice.
echo   Consult your cardiologist before any health decision.
echo   CARDIAC EMERGENCY: Call 112 (India) / 999 (UK) / 911 (US)
echo  ================================================================
echo.

timeout /t 2 /nobreak >nul
start "" "http://localhost:%PORT%"

echo.
echo   V = View log   D = Diagnostics   U = Update   Q = Quit
echo.

:MENU
set /p "CHOICE=  Choice [V/D/U/Q]: "
if /i "!CHOICE!"=="V" start notepad "%LOGFILE%" & goto :MENU
if /i "!CHOICE!"=="D" call "%BASEDIR%\DIAGNOSTIC.bat" & goto :MENU
if /i "!CHOICE!"=="U" call "%BASEDIR%\UPDATE.bat" & goto :MENU
if /i "!CHOICE!"=="Q" goto :QUIT
echo  Type V, D, U, or Q then press Enter.
goto :MENU

:QUIT
echo  Stopping CardioCare AI...
taskkill /FI "WINDOWTITLE eq CardioCare AI Server*" /F >nul 2>&1
for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr ":%PORT% "') do taskkill /PID %%P /F >nul 2>&1
echo  Stopped. Goodbye.
call :LOG "Stopped."
timeout /t 2 /nobreak >nul
exit /b 0

:LOG
echo [%DATE% %TIME%] %~1 >> "%LOGFILE%"
goto :EOF
