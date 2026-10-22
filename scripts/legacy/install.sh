#!/usr/bin/env bash
set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; CYAN='\033[0;36m'
BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'

info()  { printf "${CYAN}[INFO]${RESET}  %s\n" "$*"; }
ok()    { printf "${GREEN}[ OK ]${RESET}  %s\n" "$*"; }
skip()  { printf "${DIM}[ -- ]${RESET}  %s\n" "$*"; }
warn()  { printf "${YELLOW}[WARN]${RESET}  %s\n" "$*"; }
err()   { printf "${RED}[ERROR]${RESET} %s\n" "$*" >&2; }
die()   { err "$@"; exit 1; }

API_URL=""
API_KEY=""

usage() {
    cat <<'EOF'
CLIProxyAPI 一键安装脚本 (客户端配置)

用法: install.sh [选项]

选项:
  --url <url>     API 地址 (例: http://192.168.1.100:8317/v1)
  --key <key>     API Key  (例: sk-abc123...)
  -h, --help      显示帮助

脚本将自动配置:
  - Claude Code (~/.claude/settings.json)
  - Codex CLI (~/.codex/config.toml)
  - Shell 环境变量 (OPENAI_API_KEY, OPENAI_BASE_URL 等)
EOF
    exit 0
}

# ── Parse args ──────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --url) API_URL="$2"; shift 2 ;;
        --key) API_KEY="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) die "未知参数: $1 (用 --help 查看帮助)" ;;
    esac
done

# ── Banner ──────────────────────────────────────────────────────────────────
printf "\n${BOLD}${CYAN}  CLIProxyAPI 客户端安装${RESET}\n"
printf "  ════════════════════════════════════════\n\n"

# ── Gather input ────────────────────────────────────────────────────────────
if [[ -z "$API_URL" ]]; then
    printf "  请输入 API 地址 (例: http://192.168.1.100:8317/v1): "
    read -r API_URL
fi

if [[ -z "$API_KEY" ]]; then
    printf "  请输入 API Key  (例: sk-abc123...): "
    read -r API_KEY
fi

[[ -z "$API_URL" ]] && die "API 地址不能为空"
[[ -z "$API_KEY" ]] && die "API Key 不能为空"

if [[ ! "$API_URL" =~ ^https?:// ]]; then
    die "API 地址格式错误，需以 http:// 或 https:// 开头"
fi

# Normalize: ensure URL ends with /v1
API_URL="${API_URL%/}"
if [[ ! "$API_URL" =~ /v1$ ]]; then
    API_URL="${API_URL}/v1"
fi

BASE_URL="${API_URL%/v1}"

mask_key() {
    local k="$1"
    if [[ ${#k} -gt 12 ]]; then
        echo "${k:0:6}...${k: -4}"
    else
        echo "${k}"
    fi
}

MASKED_KEY="$(mask_key "$API_KEY")"

# ── Test connectivity ───────────────────────────────────────────────────────
info "测试连接: $API_URL"

if ! command -v curl &>/dev/null; then
    die "未找到 curl 命令"
fi

HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" \
    "${API_URL}/models" -H "Authorization: Bearer ${API_KEY}" 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "200" ]]; then
    ok "连接成功"
elif [[ "$HTTP_CODE" == "401" || "$HTTP_CODE" == "403" ]]; then
    die "认证失败 (HTTP $HTTP_CODE)，请检查 API Key 是否正确"
elif [[ "$HTTP_CODE" == "000" ]]; then
    die "无法连接到 $API_URL，请检查地址和网络"
else
    die "服务返回异常状态码: $HTTP_CODE"
fi

# ── Track what was configured ───────────────────────────────────────────────
declare -A STATUS

# ── Configure Claude Code ───────────────────────────────────────────────────
CLAUDE_DIR="$HOME/.claude"
CLAUDE_SETTINGS="$CLAUDE_DIR/settings.json"

if [[ -d "$CLAUDE_DIR" ]]; then
    info "配置 Claude Code..."

    if [[ -f "$CLAUDE_SETTINGS" ]]; then
        cp "$CLAUDE_SETTINGS" "${CLAUDE_SETTINGS}.bak"
    fi

    if command -v python3 &>/dev/null; then
        python3 -c "
import json, os
path = '$CLAUDE_SETTINGS'
data = {}
if os.path.exists(path):
    with open(path) as f:
        data = json.load(f)
if 'env' not in data:
    data['env'] = {}
data['env']['ANTHROPIC_BASE_URL'] = '$BASE_URL'
data['env']['ANTHROPIC_API_KEY'] = '$API_KEY'
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
"
        ok "Claude Code ($CLAUDE_SETTINGS)"
        STATUS[claude]="ok"
    elif command -v jq &>/dev/null; then
        if [[ ! -f "$CLAUDE_SETTINGS" ]]; then
            echo '{}' > "$CLAUDE_SETTINGS"
        fi
        tmp=$(mktemp)
        jq --arg base "$BASE_URL" --arg key "$API_KEY" \
            '.env.ANTHROPIC_BASE_URL = $base | .env.ANTHROPIC_API_KEY = $key' \
            "$CLAUDE_SETTINGS" > "$tmp" && mv "$tmp" "$CLAUDE_SETTINGS"
        ok "Claude Code ($CLAUDE_SETTINGS)"
        STATUS[claude]="ok"
    else
        warn "需要 python3 或 jq 来修改 JSON 配置，已跳过 Claude Code"
        STATUS[claude]="skip"
    fi
else
    skip "Claude Code 未安装 (未找到 $CLAUDE_DIR)"
    STATUS[claude]="none"
fi

# ── Configure Codex CLI ─────────────────────────────────────────────────────
CODEX_DIR="$HOME/.codex"
CODEX_CONFIG="$CODEX_DIR/config.toml"

if [[ -d "$CODEX_DIR" ]]; then
    info "配置 Codex CLI..."

    if [[ -f "$CODEX_CONFIG" ]]; then
        cp "$CODEX_CONFIG" "${CODEX_CONFIG}.bak"
    fi

    cat > "$CODEX_CONFIG" <<TOML
model_provider = "cliproxy"
model = "gpt-6-sol"
model_reasoning_effort = "high"

[model_providers.cliproxy]
name = "CLIProxyAPI"
base_url = "${API_URL}"
env_key = "CLIPROXY_API_KEY"
wire_api = "responses"
TOML

    ok "Codex CLI ($CODEX_CONFIG)"
    STATUS[codex]="ok"
else
    skip "Codex CLI 未安装 (未找到 $CODEX_DIR)"
    STATUS[codex]="none"
fi

# ── Configure shell environment ─────────────────────────────────────────────
ENV_FILE="$HOME/.cliproxyapi.env"
MARKER="# CLIProxyAPI Configuration"

cat > "$ENV_FILE" <<EOF
${MARKER}
export OPENAI_API_KEY="${API_KEY}"
export OPENAI_BASE_URL="${API_URL}"
export OPENAI_API_BASE="${API_URL}"
export CLIPROXY_API_KEY="${API_KEY}"
EOF

SHELL_NAME="$(basename "${SHELL:-/bin/bash}")"
PROFILE=""
case "$SHELL_NAME" in
    zsh)  PROFILE="$HOME/.zshrc" ;;
    fish) PROFILE="$HOME/.config/fish/config.fish" ;;
    *)    PROFILE="$HOME/.bashrc" ;;
esac

SOURCE_LINE="source \"$ENV_FILE\""
if [[ "$SHELL_NAME" == "fish" ]]; then
    SOURCE_LINE="source \"$ENV_FILE\""
    cat > "$ENV_FILE" <<EOF
${MARKER}
set -gx OPENAI_API_KEY "${API_KEY}"
set -gx OPENAI_BASE_URL "${API_URL}"
set -gx OPENAI_API_BASE "${API_URL}"
set -gx CLIPROXY_API_KEY "${API_KEY}"
EOF
fi

if [[ -f "$PROFILE" ]]; then
    if ! grep -qF "$ENV_FILE" "$PROFILE" 2>/dev/null; then
        printf "\n%s\n" "$SOURCE_LINE" >> "$PROFILE"
    fi
    ok "Shell 环境变量 ($PROFILE → $ENV_FILE)"
    STATUS[shell]="ok"
else
    ok "Shell 环境变量 ($ENV_FILE，请手动 source)"
    STATUS[shell]="ok"
fi

# ── Summary ─────────────────────────────────────────────────────────────────
printf "\n${BOLD}${GREEN}"
echo "  ════════════════════════════════════════"
echo "   CLIProxyAPI 客户端配置完成!"
echo "  ════════════════════════════════════════"
printf "${RESET}\n"
echo "  服务器:     ${API_URL}"
echo "  API Key:    ${MASKED_KEY}"
echo ""

for item in claude codex shell; do
    case "${STATUS[$item]:-none}" in
        ok)   printf "  ${GREEN}[OK]${RESET}  " ;;
        skip) printf "  ${YELLOW}[!!]${RESET}  " ;;
        none) printf "  ${DIM}[--]${RESET}  " ;;
    esac
    case "$item" in
        claude) echo "Claude Code" ;;
        codex)  echo "Codex CLI" ;;
        shell)  echo "Shell 环境变量" ;;
    esac
done

echo ""
if [[ -n "$PROFILE" ]]; then
    printf "  请重启终端或执行: ${BOLD}source ${PROFILE}${RESET}\n"
fi
echo ""
