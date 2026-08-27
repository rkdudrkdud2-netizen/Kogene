@echo off
setlocal
cd /d "%~dp0"

if /i "%~1"=="--silent" goto silent
start "" wscript.exe "%~dp0stop_qpcr_webapp.vbs"
exit /b 0

:silent
cscript.exe //nologo "%~dp0stop_qpcr_webapp.vbs" --silent
exit /b %errorlevel%
