#!/usr/bin/env bash
set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; CYAN='\033[0;36m'
BOLD='\033[1m'; RESET='\033[0m'

info()  { printf "${CYAN}[INFO]${RESET}  %s\n" "$*"; }
ok()    { printf "${GREEN}[OK]${RESET}    %s\n" "$*"; }
warn()  { printf "${YELLOW}[WARN]${RESET}  %s\n" "$*"; }
err()   { printf "${RED}[ERROR]${RESET} %s\n" "$*" >&2; }
die()   { err "$@"; exit 1; }

# ── Defaults ────────────────────────────────────────────────────────────────
OS="$(uname -s)"
PORT=8317
BIND="ask"
INSTALL_DIR=""

usage() {
    cat <<'EOF'
CLIProxyAPI 一键部署脚本 (Linux / macOS)

用法: deploy.sh [选项]

选项:
  --dir <path>    安装目录 (默认: ~/cliproxyapi)
  --port <num>    服务端口 (默认: 8317)
  --expose        绑定 0.0.0.0, 允许远程访问
  --local         绑定 127.0.0.1, 仅本机访问
  -h, --help      显示帮助
EOF
    exit 0
}

# ── Parse args ──────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dir)    INSTALL_DIR="$2"; shift 2 ;;
        --port)   PORT="$2"; shift 2 ;;
        --expose) BIND="0.0.0.0"; shift ;;
        --local)  BIND="127.0.0.1"; shift ;;
        -h|--help) usage ;;
        *) die "未知参数: $1 (用 --help 查看帮助)" ;;
    esac
done

# ── Banner ──────────────────────────────────────────────────────────────────
printf "\n${BOLD}${CYAN}"
cat <<'BANNER'
   ____ _     ___ ____                        _    ____ ___
  / ___| |   |_ _|  _ \ _ __ _____  ___   _ / \  |  _ \_ _|
 | |   | |    | || |_) | '__/ _ \ \/ / | | / _ \ | |_) | |
 | |___| |___ | ||  __/| | | (_) >  <| |_| / ___ \|  __/| |
  \____|_____|___|_|   |_|  \___/_/\_\\__, /_/   \_\_|  |___|
                                      |___/
BANNER
printf "${RESET}\n  一键部署脚本  (${OS})\n\n"

# ── Check Docker ────────────────────────────────────────────────────────────
info "检查 Docker..."

if ! command -v docker &>/dev/null; then
    if [[ "$OS" == "Darwin" ]]; then
        die "未找到 Docker。请先安装 Docker Desktop:\n  https://www.docker.com/products/docker-desktop/"
    else
        warn "未找到 Docker，正在安装..."
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker "$USER"
        info "Docker 已安装。如果后续命令报权限错误，请重新登录终端或运行: newgrp docker"
    fi
fi

if ! docker info &>/dev/null; then
    if [[ "$OS" == "Darwin" ]]; then
        die "Docker 未运行。请打开 Docker Desktop 并等待其启动完成。"
    else
        die "Docker 守护进程未运行。请执行: sudo systemctl start docker"
    fi
fi

if ! docker compose version &>/dev/null; then
    die "未找到 docker compose 插件。请升级 Docker 或安装 docker-compose-plugin。"
fi

ok "Docker 就绪 ($(docker --version | head -c 40))"

# ── Install directory ───────────────────────────────────────────────────────
if [[ -z "$INSTALL_DIR" ]]; then
    INSTALL_DIR="$HOME/cliproxyapi"
fi

info "安装目录: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"/{auths,logs,plugins}
cd "$INSTALL_DIR"

# ── Generate secrets ────────────────────────────────────────────────────────
gen_hex() {
    if command -v openssl &>/dev/null; then
        openssl rand -hex 16
    else
        head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n'
    fi
}

gen_password() {
    tr -dc 'A-Za-z0-9' </dev/urandom | head -c 16 || true
}

API_KEY_1="sk-$(gen_hex)"
API_KEY_2="sk-$(gen_hex)"
MGMT_PASSWORD="$(gen_password)"

ok "已生成 API Key 和管理密码"

# ── Port binding ────────────────────────────────────────────────────────────
if [[ "$BIND" == "ask" ]]; then
    printf "\n${BOLD}是否允许远程访问？${RESET}\n"
    printf "  [y] 绑定 0.0.0.0 — 局域网/Tailscale/公网可访问\n"
    printf "  [N] 绑定 127.0.0.1 — 仅本机可访问（默认）\n"
    printf "选择 [y/N]: "
    read -r choice
    case "$choice" in
        [yY]*) BIND="0.0.0.0" ;;
        *)     BIND="127.0.0.1" ;;
    esac
fi

if [[ "$BIND" == "0.0.0.0" ]]; then
    warn "端口 ${PORT} 将对所有网络接口开放，请确保已配置防火墙！"
fi

info "端口绑定: ${BIND}:${PORT}"

# ── Write config.yaml ──────────────────────────────────────────────────────
cat > config.yaml <<EOF
config-version: 8
host: "0.0.0.0"
port: ${PORT}
access:
  api-keys:
    - "${API_KEY_1}"
    - "${API_KEY_2}"
oauth:
  auth-dir: "/root/.cli-proxy-api"
routing:
  strategy: "round-robin"
remote-management:
  allow-remote: true
  secret-key: "${MGMT_PASSWORD}"
  disable-control-panel: false
EOF

ok "已写入 config.yaml"

# ── Write docker-compose.yml ───────────────────────────────────────────────
cat > docker-compose.yml <<EOF
services:
  cli-proxy-api:
    image: eceasy/cli-proxy-api:latest
    pull_policy: always
    container_name: cli-proxy-api
    ports:
      - "${BIND}:${PORT}:${PORT}"
      - "127.0.0.1:8085:8085"
    volumes:
      - ./config.yaml:/CLIProxyAPI/config.yaml
      - ./auths:/root/.cli-proxy-api
      - ./logs:/CLIProxyAPI/logs
      - ./plugins:/CLIProxyAPI/plugins
    restart: unless-stopped
EOF

ok "已写入 docker-compose.yml"

# ── Set permissions ─────────────────────────────────────────────────────────
chmod 600 config.yaml
chmod 700 auths
ok "已设置文件权限"

# ── Pull and start ──────────────────────────────────────────────────────────
info "拉取镜像..."
docker compose pull

info "启动服务..."
docker compose up -d

# ── Verify ──────────────────────────────────────────────────────────────────
info "等待服务启动..."
for i in $(seq 1 10); do
    if curl -sf "http://127.0.0.1:${PORT}/v1/models" \
         -H "Authorization: Bearer ${API_KEY_1}" &>/dev/null; then
        ok "服务已启动"
        break
    fi
    if [[ $i -eq 10 ]]; then
        warn "服务可能尚未就绪，请稍后手动检查: curl http://127.0.0.1:${PORT}/v1/models"
    fi
    sleep 2
done

# ── Summary ─────────────────────────────────────────────────────────────────
LOCAL_IP=""
if [[ "$BIND" == "0.0.0.0" ]]; then
    if command -v hostname &>/dev/null; then
        LOCAL_IP="$(hostname -I 2>/dev/null | awk '{print $1}')" || true
    fi
fi

printf "\n${BOLD}${GREEN}"
echo "========================================"
echo " CLIProxyAPI 部署完成!"
echo "========================================"
printf "${RESET}\n"
echo "  安装目录:       $INSTALL_DIR"
echo "  API 地址:       http://127.0.0.1:${PORT}/v1"
[[ -n "$LOCAL_IP" ]] && echo "  局域网地址:     http://${LOCAL_IP}:${PORT}/v1"
echo ""
echo "  API Key 1:      ${API_KEY_1}"
echo "  API Key 2:      ${API_KEY_2}"
echo ""
echo "  管理面板:       http://localhost:${PORT}/management.html"
echo "  管理密码:       ${MGMT_PASSWORD}"
echo ""
printf "${YELLOW}  请妥善保存以上信息！管理密码首次登录后将自动哈希化。${RESET}\n"
if [[ "$BIND" == "0.0.0.0" ]]; then
    printf "${RED}  警告: 端口 ${PORT} 已对外开放，请配置防火墙和云安全组！${RESET}\n"
fi
echo ""
echo "  常用命令:"
echo "    cd $INSTALL_DIR"
echo "    docker compose logs -f          # 实时日志"
echo "    docker compose restart          # 重启"
echo "    docker compose down             # 停止"
echo "    docker compose pull && docker compose up -d  # 更新"
echo ""
