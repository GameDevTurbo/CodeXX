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
set ERRORS=0

rem ── 1. Python Embeddable (~10MB, no install, no admin) ──────────────────
echo [1/4] Downloading Python Embeddable (~10MB)...
where curl >nul 2>nul
if %ERRORLEVEL% neq 0 (echo [SKIP] curl not found & goto :pip)

curl -L --progress-bar -o "%OUTDIR%\python-embed.zip" ^
    "https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip"
if %ERRORLEVEL% neq 0 (echo [FAIL] Download failed & set ERRORS=1 & goto :pip)

powershell -ExecutionPolicy Bypass -Command ^
    "Expand-Archive -Path '%OUTDIR%\python-embed.zip' -DestinationPath '%OUTDIR%\python-embed' -Force"
if %ERRORLEVEL% neq 0 (echo [FAIL] Extract failed & set ERRORS=1 & goto :pip)

rem Enable pip in embeddable python (uncomment import site)
powershell -ExecutionPolicy Bypass -Command ^
    "Get-ChildItem '%OUTDIR%\python-embed' -Filter '*._pth' | ForEach-Object { ^
     (Get-Content $_.FullName) -replace '^#import site','import site' | ^
     Set-Content $_.FullName -Encoding UTF8 }"

curl -L -o "%OUTDIR%\get-pip.py" "https://bootstrap.pypa.io/get-pip.py"
if %ERRORLEVEL% neq 0 (echo [FAIL] get-pip.py download failed & set ERRORS=1 & goto :pip)

"%OUTDIR%\python-embed\python.exe" "%OUTDIR%\get-pip.py" -q 2>nul
if %ERRORLEVEL% neq 0 (echo [WARN] pip setup in embeddable may have issues)

"%OUTDIR%\python-embed\python.exe" -m pip install customtkinter -q 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK]  Python Embeddable ready at offline_deps\python-embed\
) else (
    echo [WARN] customtkinter install in embeddable failed - wheels step will cover this
)

rem ── 2. customtkinter wheels ──────────────────────────────────────────────
:pip
echo.
echo [2/4] Downloading customtkinter wheels...
set PY=
where py     >nul 2>nul && set PY=py     && goto :do_pip
where python >nul 2>nul && set PY=python && goto :do_pip
if exist "%OUTDIR%\python-embed\python.exe" set "PY=%OUTDIR%\python-embed\python.exe" && goto :do_pip
echo [SKIP] No Python available for wheel download
goto :docker

:do_pip
%PY% -m pip download customtkinter --dest "%OUTDIR%\wheels" -q
if %ERRORLEVEL% equ 0 (
    echo [OK]  Wheels saved to offline_deps\wheels\
) else (
    echo [WARN] Some wheels failed to download & set ERRORS=1
)

rem ── 3. Docker image ──────────────────────────────────────────────────────
:docker
echo.
echo [3/4] Saving Docker image (~100-200MB)...
where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (echo [SKIP] Docker not installed & goto :installer)

docker info >nul 2>nul
if %ERRORLEVEL% neq 0 (echo [SKIP] Docker not running - start Docker Desktop first & goto :installer)

docker pull eceasy/cli-proxy-api:latest
if %ERRORLEVEL% neq 0 (echo [FAIL] Pull failed & set ERRORS=1 & goto :installer)

docker save eceasy/cli-proxy-api:latest -o "%OUTDIR%\cli-proxy-api-image.tar"
if %ERRORLEVEL% equ 0 (
    echo [OK]  Docker image: offline_deps\cli-proxy-api-image.tar
) else (
    echo [FAIL] Save failed - check disk space & set ERRORS=1
)

rem ── 4. Python full installer (fallback) ──────────────────────────────────
:installer
echo.
echo [4/4] Downloading Python 3.12 installer (admin install fallback)...
where curl >nul 2>nul
if %ERRORLEVEL% neq 0 (echo [SKIP] curl not found & goto :done)

curl -L --progress-bar -o "%OUTDIR%\python-3.12-installer.exe" ^
    "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
if %ERRORLEVEL% equ 0 (
    echo [OK]  Python installer saved
) else (
    echo [FAIL] Download failed & set ERRORS=1
)

rem ── Done ─────────────────────────────────────────────────────────────────
:done
echo.
echo  ================================================
if %ERRORS% equ 0 (
    echo  All done! No errors.
) else (
    echo  Done with some warnings - check output above.
)
echo.
echo  Contents of offline_deps\:
dir "%OUTDIR%" /b
echo.
echo  On the offline machine:
echo    1. Copy this whole folder to the target machine
echo    2. Double-click Server.bat or Client.bat
echo       (Python Embeddable is used automatically)
echo    3. Load Docker image ^(Server only^):
echo       docker load -i offline_deps\cli-proxy-api-image.tar
echo  ================================================
echo.
pause
