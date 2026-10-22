@echo off
chcp 65001 >nul
title CLIProxyAPI Offline Prep

echo.
echo  CLIProxyAPI - Offline Environment Preparation
echo  ================================================
echo  Run this on a machine WITH internet access.
echo  Copy the whole folder to the offline machine after.
echo.

set OUTDIR=%~dp0offline_deps
mkdir "%OUTDIR%\wheels" 2>nul
mkdir "%OUTDIR%\python-embed" 2>nul

rem ── 1. Python Embeddable (no install needed, ~10MB) ──────────────────────
echo [1/4] Downloading Python Embeddable (~10MB)...
where curl >nul 2>nul
if %ERRORLEVEL% equ 0 (
    curl -L --progress-bar -o "%OUTDIR%\python-embed.zip" ^
        "https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip"
    powershell -Command "Expand-Archive -Path '%OUTDIR%\python-embed.zip' -DestinationPath '%OUTDIR%\python-embed' -Force"
    rem Enable pip in embeddable python
    for %%f in ("%OUTDIR%\python-embed\*._pth") do (
        powershell -Command "(Get-Content '%%f') -replace '^#import site','import site' | Set-Content '%%f'"
    )
    rem Install pip into embeddable python
    curl -L -o "%OUTDIR%\get-pip.py" "https://bootstrap.pypa.io/get-pip.py"
    "%OUTDIR%\python-embed\python.exe" "%OUTDIR%\get-pip.py" -q
    echo [OK]  Python Embeddable ready at offline_deps\python-embed\
) else (
    echo [SKIP] curl not found
)

rem ── 2. customtkinter wheels ───────────────────────────────────────────────
echo.
echo [2/4] Downloading customtkinter wheels...
set PY=
where py     >nul 2>nul && set PY=py     && goto :pip
where python >nul 2>nul && set PY=python && goto :pip
if exist "%OUTDIR%\python-embed\python.exe" set PY="%OUTDIR%\python-embed\python.exe" && goto :pip
echo [SKIP] No Python found for pip download
goto :docker

:pip
%PY% -m pip download customtkinter --dest "%OUTDIR%\wheels" -q
if %ERRORLEVEL% equ 0 (
    echo [OK]  Wheels saved to offline_deps\wheels\
) else (
    echo [WARN] Some wheels failed
)

rem ── 3. Docker image ───────────────────────────────────────────────────────
:docker
echo.
echo [3/4] Saving Docker image (largest dep ~100-200MB)...
where docker >nul 2>nul
if %ERRORLEVEL% equ 0 (
    docker info >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        docker pull eceasy/cli-proxy-api:latest
        docker save eceasy/cli-proxy-api:latest -o "%OUTDIR%\cli-proxy-api-image.tar"
        echo [OK]  Docker image: offline_deps\cli-proxy-api-image.tar
    ) else (
        echo [SKIP] Docker not running - start Docker Desktop first
    )
) else (
    echo [SKIP] Docker not installed
)

rem ── 4. Python full installer (fallback, ~25MB) ───────────────────────────
echo.
echo [4/4] Downloading Python installer (fallback)...
where curl >nul 2>nul && (
    curl -L --progress-bar -o "%OUTDIR%\python-3.12-installer.exe" ^
        "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
    echo [OK]  Python installer saved
) || echo [SKIP] curl not found

rem ── Done ──────────────────────────────────────────────────────────────────
echo.
echo  ================================================
echo  Done! Contents of offline_deps\:
dir "%OUTDIR%" /b
echo.
echo  Deploy on offline machine:
echo    1. Copy this entire folder to target machine
echo    2. Double-click Server.bat or Client.bat
echo       (Python Embeddable will be used automatically)
echo    3. Load Docker image (Server only):
echo       docker load -i offline_deps\cli-proxy-api-image.tar
echo  ================================================
echo.
pause
