@echo off
if not exist "%~dp0CLIProxyAPI-Server.exe" goto source
if not "%~1"=="" goto diagnostic
start "" "%~dp0CLIProxyAPI-Server.exe"
exit /b
:diagnostic
"%~dp0CLIProxyAPI-Server.exe" %*
exit /b %errorlevel%
:source
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start.ps1" -Role server %*
if errorlevel 1 pause
