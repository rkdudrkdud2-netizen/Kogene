@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" goto ready

call "%~dp0install_and_run.cmd"
if errorlevel 1 exit /b 1
exit /b 0

:ready
if /i "%~1"=="--silent" goto silent
cscript.exe //nologo "%~dp0stop_qpcr_webapp.vbs" --silent >nul 2>nul
start "" wscript.exe "%~dp0start_qpcr_webapp.vbs"
exit /b 0

:silent
cscript.exe //nologo "%~dp0stop_qpcr_webapp.vbs" --silent >nul 2>nul
cscript.exe //nologo "%~dp0start_qpcr_webapp.vbs" --silent --no-browser
exit /b %errorlevel%
