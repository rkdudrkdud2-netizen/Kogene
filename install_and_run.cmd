@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if errorlevel 1 (
        echo Python 3.10 or later is required.
        echo Install Python from https://www.python.org/downloads/windows/
        pause
        exit /b 1
    )
    py -3 -m venv .venv
    if errorlevel 1 goto :error
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

start "" wscript.exe "%~dp0start_qpcr_webapp.vbs"
exit /b 0

:error
echo Installation or startup failed.
pause
exit /b 1
