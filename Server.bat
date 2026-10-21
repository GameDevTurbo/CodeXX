@echo off
if exist "%~dp0CLIProxyAPI-Server.exe" (start "" "%~dp0CLIProxyAPI-Server.exe" & goto :eof)
powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0_bootstrap.ps1" "%~dp0" "launcher.py"
