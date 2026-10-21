@echo off
if exist "%~dp0CLIProxyAPI-Client.exe" (start "" "%~dp0CLIProxyAPI-Client.exe" & goto :eof)
powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0_bootstrap.ps1" "%~dp0" "client.py"
