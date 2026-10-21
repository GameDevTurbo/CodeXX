@echo off
rem ── CLIProxyAPI Offline Dependency Downloader ────────────────────────────
rem Run this script on a machine WITH internet access.
rem It downloads everything into offline_deps\ so you can deploy
rem to machines WITHOUT internet.
setlocal
set OUTDIR=%~dp0offline_deps
mkdir "%OUTDIR%" 2>nul
echo.
echo Downloading offline dependencies to: %OUTDIR%
echo.

rem ── 1. Find Python ───────────────────────────────────────────────────────
where py     >nul 2>nul && set PY=py     && goto :pip_download
where python >nul 2>nul && set PY=python && goto :pip_download
for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%d\python.exe" set PY="%%d\python.exe" && goto :pip_download
)
echo [ERROR] Python not found. Please install Python first.
exit /b 1

rem ── 2. Download pip wheels ────────────────────────────────────────────────
:pip_download
echo [1/3] Downloading Python packages (customtkinter + deps)...
%PY% -m pip download customtkinter --dest "%OUTDIR%\wheels" -q
if %ERRORLEVEL% neq 0 (echo [WARN] Some packages failed to download) else (
    echo [OK] Wheels saved to %OUTDIR%\wheels\
)

rem ── 3. Download Python installer (Windows) ────────────────────────────────
echo [2/3] Downloading Python 3.12 installer for offline use...
where curl >nul 2>nul && (
    curl -L -o "%OUTDIR%\python-3.12-installer.exe" ^
        "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe" ^
        --progress-bar
    echo [OK] Python installer saved.
) || echo [SKIP] curl not found, skipping Python installer download.

rem ── 4. Summary ───────────────────────────────────────────────────────────
echo.
echo [3/3] Done!
echo.
echo Contents of %OUTDIR%:
dir "%OUTDIR%" /b
echo.
echo To deploy offline:
echo   1. Copy the entire CodeXX folder (including offline_deps\) to the target machine
echo   2. Double-click start.bat — it will use offline_deps\ automatically
echo.
pause
