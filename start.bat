@echo off
setlocal

rem Find pythonw (no console window) or python
where pythonw >/dev/null 2>/dev/null && set PYEXE=pythonw && goto :run
where python  >/dev/null 2>/dev/null && set PYEXE=python  && goto :install

rem No Python - try winget
where winget >/dev/null 2>/dev/null || goto :nopython
echo Installing Python via winget...
winget install Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements
where pythonw >/dev/null 2>/dev/null && set PYEXE=pythonw && goto :install
where python  >/dev/null 2>/dev/null && set PYEXE=python  && goto :install

:nopython
powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0launcher.ps1"
goto :eof

:install
python -m pip install customtkinter -q 2>nul

:run
start "" %PYEXE% "%~dp0launcher.py"
