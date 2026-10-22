<#
.SYNOPSIS
    CLIProxyAPI 一键安装脚本 (客户端配置, Windows)
.DESCRIPTION
    配置本地开发工具连接已部署的 CLIProxyAPI 服务。
    自动配置 Claude Code、Codex CLI 和系统环境变量。
.PARAMETER Url
    API 地址 (例: http://192.168.1.100:8317/v1)
.PARAMETER Key
    API Key  (例: sk-abc123...)
#>
[CmdletBinding()]
param(
    [string]$Url,
    [string]$Key
)

$ErrorActionPreference = "Stop"

function Write-Info  { Write-Host "[INFO]  $args" -ForegroundColor Cyan }
function Write-Ok    { Write-Host "[ OK ]  $args" -ForegroundColor Green }
function Write-Skip  { Write-Host "[ -- ]  $args" -ForegroundColor DarkGray }
function Write-Warn  { Write-Host "[WARN]  $args" -ForegroundColor Yellow }
function Write-Err   { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Stop-Install { Write-Err $args; exit 1 }

function Get-MaskedKey([string]$k) {
    if ($k.Length -gt 12) {
        return $k.Substring(0, 6) + "..." + $k.Substring($k.Length - 4)
    }
    return $k
}

# ── Banner ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  CLIProxyAPI 客户端安装" -ForegroundColor Cyan -NoNewline
Write-Host "  (Windows)" -ForegroundColor DarkGray
Write-Host "  ════════════════════════════════════════" -ForegroundColor DarkCyan
Write-Host ""

# ── Gather input ────────────────────────────────────────────────────────────
if (-not $Url) {
    $Url = Read-Host "  请输入 API 地址 (例: http://192.168.1.100:8317/v1)"
}
if (-not $Key) {
    $Key = Read-Host "  请输入 API Key  (例: sk-abc123...)"
}

if (-not $Url) { Stop-Install "API 地址不能为空" }
if (-not $Key) { Stop-Install "API Key 不能为空" }

if ($Url -notmatch "^https?://") {
    Stop-Install "API 地址格式错误，需以 http:// 或 https:// 开头"
}

$Url = $Url.TrimEnd("/")
if (-not $Url.EndsWith("/v1")) { $Url = "$Url/v1" }
$BaseUrl = $Url -replace "/v1$", ""
$MaskedKey = Get-MaskedKey $Key

# ── Test connectivity ───────────────────────────────────────────────────────
Write-Info "测试连接: $Url"

try {
    $resp = Invoke-WebRequest -Uri "$Url/models" `
        -Headers @{ "Authorization" = "Bearer $Key" } `
        -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    if ($resp.StatusCode -eq 200) {
        Write-Ok "连接成功"
    }
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    if ($code -eq 401 -or $code -eq 403) {
        Stop-Install "认证失败 (HTTP $code)，请检查 API Key 是否正确"
    } elseif ($code) {
        Stop-Install "服务返回异常状态码: $code"
    } else {
        Stop-Install "无法连接到 $Url，请检查地址和网络"
    }
}

$status = @{}

# ── Configure Claude Code ───────────────────────────────────────────────────
$claudeDir = "$env:USERPROFILE\.claude"
$claudeSettings = "$claudeDir\settings.json"

if (Test-Path $claudeDir) {
    Write-Info "配置 Claude Code..."

    if (Test-Path $claudeSettings) {
        Copy-Item $claudeSettings "${claudeSettings}.bak" -Force
    }

    $data = @{}
    if (Test-Path $claudeSettings) {
        $data = Get-Content $claudeSettings -Raw | ConvertFrom-Json -AsHashtable
    }
    if (-not $data.ContainsKey("env")) {
        $data["env"] = @{}
    }
    $data["env"]["ANTHROPIC_BASE_URL"] = $BaseUrl
    $data["env"]["ANTHROPIC_API_KEY"] = $Key

    $data | ConvertTo-Json -Depth 10 | Set-Content $claudeSettings -Encoding UTF8
    Write-Ok "Claude Code ($claudeSettings)"
    $status["claude"] = "ok"
} else {
    Write-Skip "Claude Code 未安装 (未找到 $claudeDir)"
    $status["claude"] = "none"
}

# ── Configure Codex CLI ─────────────────────────────────────────────────────
$codexDir = "$env:USERPROFILE\.codex"
$codexConfig = "$codexDir\config.toml"

if (Test-Path $codexDir) {
    Write-Info "配置 Codex CLI..."

    if (Test-Path $codexConfig) {
        Copy-Item $codexConfig "${codexConfig}.bak" -Force
    }

    $toml = @"
model_provider = "cliproxy"
model = "gpt-6-sol"
model_reasoning_effort = "high"

[model_providers.cliproxy]
name = "CLIProxyAPI"
base_url = "${Url}"
env_key = "CLIPROXY_API_KEY"
wire_api = "responses"
"@

    [System.IO.File]::WriteAllText($codexConfig, $toml, [System.Text.UTF8Encoding]::new($false))
    Write-Ok "Codex CLI ($codexConfig)"
    $status["codex"] = "ok"
} else {
    Write-Skip "Codex CLI 未安装 (未找到 $codexDir)"
    $status["codex"] = "none"
}

# ── Configure environment variables ─────────────────────────────────────────
Write-Info "设置环境变量..."

$envVars = @{
    "OPENAI_API_KEY"   = $Key
    "OPENAI_BASE_URL"  = $Url
    "OPENAI_API_BASE"  = $Url
    "CLIPROXY_API_KEY" = $Key
}

foreach ($kv in $envVars.GetEnumerator()) {
    [System.Environment]::SetEnvironmentVariable($kv.Key, $kv.Value, "User")
}

Write-Ok "系统环境变量 (用户级，新终端自动生效)"
$status["env"] = "ok"

# ── Summary ─────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ════════════════════════════════════════" -ForegroundColor Green
Write-Host "   CLIProxyAPI 客户端配置完成!" -ForegroundColor Green
Write-Host "  ════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  服务器:     $Url"
Write-Host "  API Key:    $MaskedKey"
Write-Host ""

$items = @(
    @("claude", "Claude Code"),
    @("codex", "Codex CLI"),
    @("env", "系统环境变量")
)

foreach ($item in $items) {
    $s = $status[$item[0]]
    if ($s -eq "ok") {
        Write-Host "  [OK]  $($item[1])" -ForegroundColor Green
    } elseif ($s -eq "skip") {
        Write-Host "  [!!]  $($item[1])" -ForegroundColor Yellow
    } else {
        Write-Host "  [--]  $($item[1])" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "  请重启终端使环境变量生效。" -ForegroundColor Yellow
Write-Host ""
