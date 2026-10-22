#!/bin/bash
# CLIProxyAPI 离线包准备工具 — macOS / Linux
# 有网络时运行，下载全部依赖到 offline_deps/

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
OUTDIR="$DIR/offline_deps"
mkdir -p "$OUTDIR/wheels"

echo ""
echo "准备离线安装包: $OUTDIR"
echo ""

# 1. pip wheels
PY=$(command -v python3 || command -v python || true)
if [ -n "$PY" ]; then
    echo "[1/3] 下载 Python 依赖包..."
    "$PY" -m pip download customtkinter --dest "$OUTDIR/wheels" -q
    echo "[OK]  wheels -> $OUTDIR/wheels/"
else
    echo "[跳过] 未找到 Python"
fi

# 2. macOS: Homebrew Python 安装脚本提示
if [ "$(uname -s)" = "Darwin" ]; then
    echo "[2/3] macOS: 使用 Homebrew 安装 Python"
    echo "      离线环境请提前安装: https://www.python.org/downloads/macos/"
else
    echo "[2/3] Linux: 使用系统包管理器安装 Python (apt/dnf/pacman)"
fi

# 3. 保存 Docker 镜像
echo "[3/3] 保存 Docker 镜像..."
if command -v docker &>/dev/null && docker info &>/dev/null; then
    docker pull eceasy/cli-proxy-api:latest
    docker save eceasy/cli-proxy-api:latest -o "$OUTDIR/cli-proxy-api-image.tar"
    echo "[OK]  镜像已保存: $OUTDIR/cli-proxy-api-image.tar"
else
    echo "[跳过] Docker 未运行"
fi

echo ""
echo "完成！离线部署时："
echo "  1. 复制整个项目目录到目标机器"
echo "  2. bash start.sh  (Server) 或  bash start.sh client.py  (Client)"
echo "  3. 加载 Docker 镜像: docker load -i offline_deps/cli-proxy-api-image.tar"
echo ""
