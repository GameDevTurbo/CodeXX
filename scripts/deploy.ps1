<#
.SYNOPSIS
    CLIProxyAPI 一键部署脚本 (Windows)
.DESCRIPTION
    自动检查 Docker、生成配置、启动 CLIProxyAPI 服务。
.PARAMETER Dir
    安装目录 (默认: C:\CLIProxyAPI)
.PARAMETER Port
    服务端口 (默认: 8317)
.PARAMETER Expose
    绑定 0.0.0.0, 允许远程访问
.PARAMETER Local
    绑定 127.0.0.1, 仅本机访问
#>
[CmdletBinding()]
param(
    [string]$Dir = "C:\CLIProxyAPI",
    [int]$Port = 8317,
    [switch]$Expose,
    [switch]$Local
)

$ErrorActionPreference = "Stop"

function Write-Info  { Write-Host "[INFO]  $args" -ForegroundColor Cyan }
function Write-Ok    { Write-Host "[OK]    $args" -ForegroundColor Green }
function Write-Warn  { Write-Host "[WARN]  $args" -ForegroundColor Yellow }
function Write-Err   { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Stop-Deploy { Write-Err $args; exit 1 }

function New-RandomHex([int]$Bytes = 16) {
    $buf = New-Object byte[] $Bytes
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($buf)
    return ($buf | ForEach-Object { $_.ToString("x2") }) -join ""
}

function New-RandomPassword([int]$Length = 16) {
    $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    $buf = New-Object byte[] $Length
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($buf)
    return -join ($buf | ForEach-Object { $chars[$_ % $chars.Length] })
}

# ── Banner ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  CLIProxyAPI 一键部署" -ForegroundColor Cyan -NoNewline
Write-Host "  (Windows)" -ForegroundColor DarkGray
Write-Host "  ════════════════════════════════════════" -ForegroundColor DarkCyan
Write-Host ""

# ── Check Docker ────────────────────────────────────────────────────────────
Write-Info "检查 Docker..."

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Stop-Deploy "未找到 Docker。请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop/"
}

$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Stop-Deploy "Docker 未运行。请打开 Docker Desktop 并等待其启动完成。"
}

$composeVer = docker compose version 2>&1
if ($LASTEXITCODE -ne 0) {
    Stop-Deploy "未找到 docker compose 插件。请升级 Docker Desktop。"
}

Write-Ok "Docker 就绪"

# ── Install directory ───────────────────────────────────────────────────────
Write-Info "安装目录: $Dir"
New-Item -ItemType Directory -Force -Path "$Dir\auths", "$Dir\logs", "$Dir\plugins" | Out-Null
Set-Location $Dir

# ── Generate secrets ────────────────────────────────────────────────────────
$ApiKey1 = "sk-$(New-RandomHex)"
$ApiKey2 = "sk-$(New-RandomHex)"
$MgmtPassword = New-RandomPassword

Write-Ok "已生成 API Key 和管理密码"

# ── Port binding ────────────────────────────────────────────────────────────
$Bind = ""
if ($Expose) {
    $Bind = "0.0.0.0"
} elseif ($Local) {
    $Bind = "127.0.0.1"
} else {
    Write-Host ""
    Write-Host "  是否允许远程访问？" -ForegroundColor White
    Write-Host "    [y] 绑定 0.0.0.0 — 局域网/Tailscale/公网可访问"
    Write-Host "    [N] 绑定 127.0.0.1 — 仅本机可访问 (默认)"
    $choice = Read-Host "  选择 [y/N]"
    if ($choice -match "^[yY]") {
        $Bind = "0.0.0.0"
    } else {
        $Bind = "127.0.0.1"
    }
}

if ($Bind -eq "0.0.0.0") {
    Write-Warn "端口 ${Port} 将对所有网络接口开放，请确保已配置防火墙！"
}

Write-Info "端口绑定: ${Bind}:${Port}"

# ── Write config.yaml ──────────────────────────────────────────────────────
$configYaml = @"
config-version: 8
host: "0.0.0.0"
port: ${Port}
access:
  api-keys:
    - "${ApiKey1}"
    - "${ApiKey2}"
oauth:
  auth-dir: "/root/.cli-proxy-api"
routing:
  strategy: "round-robin"
remote-management:
  allow-remote: true
  secret-key: "${MgmtPassword}"
  disable-control-panel: false
"@

[System.IO.File]::WriteAllText("$Dir\config.yaml", $configYaml, [System.Text.UTF8Encoding]::new($false))
Write-Ok "已写入 config.yaml"

# ── Write docker-compose.yml ───────────────────────────────────────────────
$composeYaml = @"
services:
  cli-proxy-api:
    image: eceasy/cli-proxy-api:latest
    pull_policy: always
    container_name: cli-proxy-api
    ports:
      - "${Bind}:${Port}:${Port}"
      - "127.0.0.1:8085:8085"
    volumes:
      - ./config.yaml:/CLIProxyAPI/config.yaml
      - ./auths:/root/.cli-proxy-api
      - ./logs:/CLIProxyAPI/logs
      - ./plugins:/CLIProxyAPI/plugins
    restart: unless-stopped
"@

[System.IO.File]::WriteAllText("$Dir\docker-compose.yml", $composeYaml, [System.Text.UTF8Encoding]::new($false))
Write-Ok "已写入 docker-compose.yml"

# ── Pull and start ──────────────────────────────────────────────────────────
Write-Info "拉取镜像..."
docker compose pull
if ($LASTEXITCODE -ne 0) { Stop-Deploy "镜像拉取失败。请检查网络连接。" }

Write-Info "启动服务..."
docker compose up -d
if ($LASTEXITCODE -ne 0) { Stop-Deploy "服务启动失败。请检查端口是否被占用。" }

# ── Verify ──────────────────────────────────────────────────────────────────
Write-Info "等待服务启动..."
$ready = $false
for ($i = 1; $i -le 10; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:${Port}/v1/models" `
            -Headers @{ "Authorization" = "Bearer $ApiKey1" } `
            -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) {
            Write-Ok "服务已启动"
            $ready = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 2
}
if (-not $ready) {
    Write-Warn "服务可能尚未就绪，请稍后手动检查"
}

# ── Summary ─────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ════════════════════════════════════════" -ForegroundColor Green
Write-Host "   CLIProxyAPI 部署完成!" -ForegroundColor Green
Write-Host "  ════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  安装目录:       $Dir"
Write-Host "  API 地址:       http://127.0.0.1:${Port}/v1"

if ($Bind -eq "0.0.0.0") {
    try {
        $localIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch "Loopback" -and $_.PrefixOrigin -ne "WellKnown" } | Select-Object -First 1).IPAddress
        if ($localIp) { Write-Host "  局域网地址:     http://${localIp}:${Port}/v1" }
    } catch {}
}

Write-Host ""
Write-Host "  API Key 1:      $ApiKey1"
Write-Host "  API Key 2:      $ApiKey2"
Write-Host ""
Write-Host "  管理面板:       http://localhost:${Port}/management.html"
Write-Host "  管理密码:       $MgmtPassword"
Write-Host ""
Write-Host "  请妥善保存以上信息！管理密码首次登录后将自动哈希化。" -ForegroundColor Yellow
if ($Bind -eq "0.0.0.0") {
    Write-Host "  警告: 端口 ${Port} 已对外开放，请配置防火墙！" -ForegroundColor Red
}
Write-Host ""
Write-Host "  常用命令:"
Write-Host "    cd $Dir"
Write-Host "    docker compose logs -f          # 实时日志"
Write-Host "    docker compose restart          # 重启"
Write-Host "    docker compose down             # 停止"
Write-Host "    docker compose pull; docker compose up -d  # 更新"
Write-Host ""
