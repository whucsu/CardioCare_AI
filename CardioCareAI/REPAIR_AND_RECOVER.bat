@echo off
setlocal EnableDelayedExpansion
title CardioCare AI - REPAIR AND RECOVERY
mode con: cols=78 lines=50
color 0C

set "BASEDIR=%~dp0"
if "%BASEDIR:~-1%"=="\" set "BASEDIR=%BASEDIR:~0,-1%"
set "VENV_DIR=%BASEDIR%\venv"
set "LOGS_DIR=%BASEDIR%\logs"
set "OFFLINE_DIR=%BASEDIR%\offline_packages"
set "PYTHON_EXE="
set "ONLINE=false"

if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
set "LOGFILE=%LOGS_DIR%\repair_%DATE:~-4,4%%DATE:~-7,2%%DATE:~-10,2%.log"

cls
echo.
echo  ================================================================
echo   CardioCare AI  -  REPAIR AND RECOVERY TOOL
echo  ================================================================
echo  Fixes the most common problems. Shows each step clearly.
echo  ================================================================
echo.

echo  Checking internet...
ping -n 1 -w 2000 8.8.8.8 >nul 2>&1
if %errorlevel%==0 (set "ONLINE=true" & echo   [ OK ]  Online) else (set "ONLINE=false" & echo   [ -- ]  Offline)
echo.

echo  Finding Python...
python --version >nul 2>&1
if %errorlevel%==0 (set "PYTHON_EXE=python" & goto :PY_FOUND_R)
py --version >nul 2>&1
if %errorlevel%==0 (set "PYTHON_EXE=py" & goto :PY_FOUND_R)
for %%D in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python312\python.exe" "C:\Python311\python.exe"
) do (
    if exist %%D (set "PYTHON_EXE=%%~D" & goto :PY_FOUND_R)
)
echo   [FAIL]  Python not found.
if "%ONLINE%"=="true" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\py_setup.exe' -UseBasicParsing" >> "%LOGFILE%" 2>&1
    if exist "%TEMP%\py_setup.exe" (start /wait "" "%TEMP%\py_setup.exe" & set "PYTHON_EXE=python")
)

:PY_FOUND_R
for /f "delims=" %%V in ('"%PYTHON_EXE%" --version 2^>^&1') do echo   [ OK ]  %%V found
echo.

echo  ================================================================
echo   What would you like to repair?
echo  ================================================================
echo.
echo   1  =  Rebuild virtual environment
echo   2  =  Reinstall all packages
echo   3  =  Recreate missing folders
echo   4  =  Clear logs and cache
echo   5  =  Full factory reset (keeps uploads)
echo   6  =  Fix port 5060 conflict
echo   7  =  Run ALL repairs (recommended)
echo   0  =  Exit
echo.
set /p "CHOICE=  Enter choice (0-7): "

if "%CHOICE%"=="0" exit /b 0
if "%CHOICE%"=="1" goto :VENV
if "%CHOICE%"=="2" goto :PACKAGES
if "%CHOICE%"=="3" goto :FOLDERS
if "%CHOICE%"=="4" goto :LOGS
if "%CHOICE%"=="5" goto :FACTORY
if "%CHOICE%"=="6" goto :PORT
if "%CHOICE%"=="7" goto :ALL
echo  Invalid. exit /b 0

:VENV
echo.
echo  Rebuilding virtual environment...
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%" >> "%LOGFILE%" 2>&1
"%PYTHON_EXE%" -m venv "%VENV_DIR%" >> "%LOGFILE%" 2>&1
if %errorlevel%==0 (echo   [ OK ]  Venv rebuilt.) else (echo   [FAIL]  See: %LOGFILE%)
goto :DONE

:PACKAGES
echo.
echo  Reinstalling packages...
if not exist "%VENV_DIR%\Scripts\pip.exe" (
    "%PYTHON_EXE%" -m venv "%VENV_DIR%" >> "%LOGFILE%" 2>&1
)
set "PIP=%VENV_DIR%\Scripts\pip.exe"
"%PIP%" install --upgrade pip --quiet >> "%LOGFILE%" 2>&1
if "%ONLINE%"=="true" (
    for %%K in (flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil) do (
        echo     Installing %%K ...
        "%PIP%" install %%K --upgrade --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
        "%PIP%" download %%K --dest="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
    )
) else (
    if exist "%OFFLINE_DIR%\*.whl" (
        "%PIP%" install flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil --no-index --find-links="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
    ) else (
        echo   [FAIL]  No offline cache. Connect and retry.
        goto :DONE
    )
)
echo   [ OK ]  Packages reinstalled.
goto :DONE

:FOLDERS
echo.
echo  Recreating folders...
for %%D in (uploads offline_packages logs data static reports_db) do (
    if not exist "%BASEDIR%\%%D\" (mkdir "%BASEDIR%\%%D" & echo     Created: %%D) else (echo     OK: %%D)
)
goto :DONE

:LOGS
echo.
echo  Clearing logs and cache...
if exist "%LOGS_DIR%" del /q "%LOGS_DIR%\*.log" >nul 2>&1 & del /q "%LOGS_DIR%\*.txt" >nul 2>&1
if exist "%BASEDIR%\__pycache__" rmdir /s /q "%BASEDIR%\__pycache__" >nul 2>&1
echo   [ OK ]  Cleared.
goto :DONE

:PORT
echo.
echo  Fixing port 5060...
netstat -ano 2>nul | findstr ":5060 " >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr ":5060 "') do (
        echo   Stopping PID %%P...
        taskkill /PID %%P /F >nul 2>&1
    )
    echo   [ OK ]  Port 5060 freed.
) else (
    echo   [ OK ]  Port 5060 already free.
)
goto :DONE

:FACTORY
echo.
set /p "CONFIRM=  Type YES to confirm factory reset: "
if /i not "%CONFIRM%"=="YES" (echo  Cancelled. & goto :DONE)
echo  Resetting...
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"
if exist "%LOGS_DIR%" del /q "%LOGS_DIR%\*.*" >nul 2>&1
if exist "%BASEDIR%\__pycache__" rmdir /s /q "%BASEDIR%\__pycache__"
for %%D in (uploads offline_packages logs data static reports_db) do if not exist "%BASEDIR%\%%D\" mkdir "%BASEDIR%\%%D"
"%PYTHON_EXE%" -m venv "%VENV_DIR%" >> "%LOGFILE%" 2>&1
set "PIP=%VENV_DIR%\Scripts\pip.exe"
if "%ONLINE%"=="true" (
    "%PIP%" install flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil --quiet >> "%LOGFILE%" 2>&1
) else (
    if exist "%OFFLINE_DIR%\*.whl" (
        "%PIP%" install flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil --no-index --find-links="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
    )
)
echo   [ OK ]  Factory reset complete.
goto :DONE

:ALL
echo.
echo  Running all repairs...
netstat -ano 2>nul | findstr ":5060 " >nul 2>&1
if %errorlevel%==0 (for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr ":5060 "') do taskkill /PID %%P /F >nul 2>&1)
echo   [ OK ]  Port done.
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%" >> "%LOGFILE%" 2>&1
"%PYTHON_EXE%" -m venv "%VENV_DIR%" >> "%LOGFILE%" 2>&1
echo   [ OK ]  Venv rebuilt.
set "PIP=%VENV_DIR%\Scripts\pip.exe"
"%PIP%" install --upgrade pip --quiet >> "%LOGFILE%" 2>&1
if "%ONLINE%"=="true" (
    "%PIP%" install flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil --quiet --no-warn-script-location >> "%LOGFILE%" 2>&1
) else (
    if exist "%OFFLINE_DIR%\*.whl" (
        "%PIP%" install flask flask-cors requests Pillow PyMuPDF anthropic numpy python-docx colorama psutil --no-index --find-links="%OFFLINE_DIR%" --quiet >> "%LOGFILE%" 2>&1
    )
)
echo   [ OK ]  Packages installed.
for %%D in (uploads offline_packages logs data static reports_db) do if not exist "%BASEDIR%\%%D\" mkdir "%BASEDIR%\%%D" >nul 2>&1
echo   [ OK ]  Folders ready.
if exist "%LOGS_DIR%" del /q "%LOGS_DIR%\*.log" >nul 2>&1
echo   [ OK ]  Logs cleared.
echo   [ OK ]  All repairs done.
goto :DONE

:DONE
echo.
echo  ================================================================
echo   Repair complete. Log: %LOGFILE%
echo  ================================================================
echo.
echo   S = Start CardioCare AI   D = Run Diagnostic   X = Exit
echo.
set /p "POST=  Choice [S/D/X]: "
if /i "%POST%"=="S" call "%BASEDIR%\START_CardioCare_AI.bat"
if /i "%POST%"=="D" call "%BASEDIR%\DIAGNOSTIC.bat"
exit /b 0
