@echo off
rem ── CLIProxyAPI 离线包准备工具 ────────────────────────────────────────────
rem 在有网络的机器上运行，下载全部依赖到 offline_deps\
rem 然后将整个项目目录（含 offline_deps\）复制到目标机器即可离线部署
setlocal
set OUTDIR=%~dp0offline_deps
mkdir "%OUTDIR%" 2>nul
mkdir "%OUTDIR%\wheels" 2>nul
echo.
echo 准备离线安装包: %OUTDIR%
echo.

rem ── 1. 查找 Python ───────────────────────────────────────────────────────
set PY=
where py     >nul 2>nul && set PY=py     && goto :pip_download
where python >nul 2>nul && set PY=python && goto :pip_download
for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%d\python.exe" set PY="%%d\python.exe" && goto :pip_download
)
echo [跳过] 未找到 Python，跳过 pip wheels 下载

rem ── 2. 下载 pip wheels ───────────────────────────────────────────────────
:pip_download
if defined PY (
    echo [1/3] 下载 Python 依赖包 (customtkinter)...
    %PY% -m pip download customtkinter --dest "%OUTDIR%\wheels" -q
    if %ERRORLEVEL% equ 0 (echo [OK]  wheels -> %OUTDIR%\wheels\) else echo [警告] 部分包下载失败
)

rem ── 3. 下载 Python 安装包 ────────────────────────────────────────────────
echo [2/3] 下载 Python 3.12 安装包 (Windows 离线安装)...
where curl >nul 2>nul && (
    curl -L --progress-bar -o "%OUTDIR%\python-3.12-installer.exe" ^
        "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
    if %ERRORLEVEL% equ 0 (echo [OK]  Python installer 已保存) else echo [警告] 下载失败
) || echo [跳过] curl 未找到，请手动下载 Python 安装包

rem ── 4. 保存 Docker 镜像 ──────────────────────────────────────────────────
echo [3/3] 保存 Docker 镜像 (最大依赖，约 100-200MB)...
where docker >nul 2>nul && docker info >nul 2>nul && (
    docker pull eceasy/cli-proxy-api:latest
    docker save eceasy/cli-proxy-api:latest -o "%OUTDIR%\cli-proxy-api-image.tar"
    if %ERRORLEVEL% equ 0 (echo [OK]  Docker 镜像已保存: %OUTDIR%\cli-proxy-api-image.tar) else echo [警告] 镜像保存失败
) || echo [跳过] Docker 未运行，请先启动 Docker Desktop 再运行此脚本

rem ── 5. 汇总 ─────────────────────────────────────────────────────────────
echo.
echo ══ 完成 ══════════════════════════════════
echo 已保存到: %OUTDIR%
dir "%OUTDIR%" /b
echo.
echo 离线部署步骤:
echo   1. 将整个项目文件夹（含 offline_deps\）复制到目标机器
echo   2. 双击 Server.bat 或 Client.bat
echo   3. Docker 镜像加载（首次）:
echo      docker load -i offline_deps\cli-proxy-api-image.tar
echo.
pause
