@echo off
setlocal

rem Check Python
where python >/dev/null 2>/dev/null && goto :has_python

rem Try installing Python via winget
where winget >/dev/null 2>/dev/null && (
    echo Installing Python...
    winget install Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements
    where python >/dev/null 2>/dev/null && goto :has_python
)

rem Fallback: PowerShell launcher
powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0launcher.ps1"
goto :eof

:has_python
python -m pip install customtkinter -q 2>nul
python "%~dp0launcher.py"
