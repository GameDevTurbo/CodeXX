@echo off
if exist "%~dp0..\CodeXX-Client\Client.bat" (
  call "%~dp0..\CodeXX-Client\Client.bat" %*
  exit /b
)
start "" "https://github.com/GameDevTurbo/CodeXX-Client/releases"
