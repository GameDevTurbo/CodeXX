Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$container  = "cli-proxy-api"
$mgmtUrl    = "http://localhost:8317/management.html"
$apiUrl     = "http://localhost:8317/v1"

# ── Colors ──────────────────────────────────────────────────────────────────
$cBg     = [System.Drawing.Color]::FromArgb(15, 15, 20)
$cPanel  = [System.Drawing.Color]::FromArgb(26, 26, 36)
$cBlue   = [System.Drawing.Color]::FromArgb(56, 139, 253)
$cGreen  = [System.Drawing.Color]::FromArgb(63, 185, 80)
$cRed    = [System.Drawing.Color]::FromArgb(218, 54, 51)
$cOrange = [System.Drawing.Color]::FromArgb(210, 140, 40)
$cText   = [System.Drawing.Color]::FromArgb(220, 220, 230)
$cDim    = [System.Drawing.Color]::FromArgb(100, 100, 120)

# ── Main form ───────────────────────────────────────────────────────────────
$form = New-Object System.Windows.Forms.Form
$form.Text = "CLIProxyAPI Launcher"
$form.Size = [System.Drawing.Size]::new(560, 560)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedSingle"
$form.MaximizeBox = $false
$form.BackColor = $cBg
$form.ForeColor = $cText
$form.Font = [System.Drawing.Font]::new("Segoe UI", 9)

# ── Title ───────────────────────────────────────────────────────────────────
$lbTitle = New-Object System.Windows.Forms.Label
$lbTitle.Text = "CLIProxyAPI"
$lbTitle.Font = [System.Drawing.Font]::new("Segoe UI", 18, [System.Drawing.FontStyle]::Bold)
$lbTitle.ForeColor = $cBlue
$lbTitle.Location = [System.Drawing.Point]::new(20, 14)
$lbTitle.Size = [System.Drawing.Size]::new(320, 38)
$form.Controls.Add($lbTitle)

$lbSub = New-Object System.Windows.Forms.Label
$lbSub.Text = "AI 订阅转 API 代理服务"
$lbSub.ForeColor = $cDim
$lbSub.Location = [System.Drawing.Point]::new(23, 52)
$lbSub.Size = [System.Drawing.Size]::new(300, 18)
$form.Controls.Add($lbSub)

# ── Status panel ────────────────────────────────────────────────────────────
$pSt = New-Object System.Windows.Forms.Panel
$pSt.Location = [System.Drawing.Point]::new(20, 82)
$pSt.Size = [System.Drawing.Size]::new(510, 68)
$pSt.BackColor = $cPanel
$form.Controls.Add($pSt)

$dot = New-Object System.Windows.Forms.Label
$dot.Text = [char]0x25CF
$dot.Font = [System.Drawing.Font]::new("Segoe UI", 20)
$dot.ForeColor = $cDim
$dot.Location = [System.Drawing.Point]::new(14, 12)
$dot.Size = [System.Drawing.Size]::new(32, 38)
$pSt.Controls.Add($dot)

$lblSt = New-Object System.Windows.Forms.Label
$lblSt.Text = "检查中..."
$lblSt.Font = [System.Drawing.Font]::new("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$lblSt.ForeColor = $cDim
$lblSt.Location = [System.Drawing.Point]::new(52, 10)
$lblSt.Size = [System.Drawing.Size]::new(200, 26)
$pSt.Controls.Add($lblSt)

$lblDk = New-Object System.Windows.Forms.Label
$lblDk.Text = "Docker: 检查中..."
$lblDk.ForeColor = $cDim
$lblDk.Location = [System.Drawing.Point]::new(52, 36)
$lblDk.Size = [System.Drawing.Size]::new(440, 18)
$pSt.Controls.Add($lblDk)

# ── Button helper ───────────────────────────────────────────────────────────
function New-Btn($text, $x, $y, $w, $color) {
    $b = New-Object System.Windows.Forms.Button
    $b.Text = $text
    $b.Location = [System.Drawing.Point]::new($x, $y)
    $b.Size = [System.Drawing.Size]::new($w, 38)
    $b.FlatStyle = "Flat"
    $b.FlatAppearance.BorderSize = 0
    $b.BackColor = $color
    $b.ForeColor = [System.Drawing.Color]::White
    $b.Font = [System.Drawing.Font]::new("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
    $b.Cursor = "Hand"
    $form.Controls.Add($b)
    return $b
}

$btnStart   = New-Btn "▶  启动服务"     20  162 155 ([System.Drawing.Color]::FromArgb(35, 105, 55))
$btnStop    = New-Btn "■  停止服务"    182  162 155 $cRed
$btnRestart = New-Btn "↺  重启服务"    344  162 186 ([System.Drawing.Color]::FromArgb(70, 60, 20))
$btnDeploy  = New-Btn "⚡  首次部署"     20  208 230 $cBlue
$btnPull    = New-Btn "⬇  拉取镜像"    258  208 180 ([System.Drawing.Color]::FromArgb(50, 50, 80))
$btnPanel   = New-Btn "🌐"             444  208  86 ([System.Drawing.Color]::FromArgb(44, 82, 130))

# ── API copy bar ────────────────────────────────────────────────────────────
$pC = New-Object System.Windows.Forms.Panel
$pC.Location = [System.Drawing.Point]::new(20, 258)
$pC.Size = [System.Drawing.Size]::new(510, 36)
$pC.BackColor = $cPanel
$form.Controls.Add($pC)

$lA = New-Object System.Windows.Forms.Label
$lA.Text = "API: $apiUrl"
$lA.ForeColor = $cDim
$lA.Location = [System.Drawing.Point]::new(10, 10)
$lA.Size = [System.Drawing.Size]::new(380, 18)
$pC.Controls.Add($lA)

$btnCP = New-Object System.Windows.Forms.Button
$btnCP.Text = "复制地址"
$btnCP.Location = [System.Drawing.Point]::new(400, 5)
$btnCP.Size = [System.Drawing.Size]::new(102, 26)
$btnCP.FlatStyle = "Flat"
$btnCP.FlatAppearance.BorderSize = 1
$btnCP.FlatAppearance.BorderColor = [System.Drawing.Color]::FromArgb(45, 45, 60)
$btnCP.BackColor = $cPanel
$btnCP.ForeColor = $cDim
$btnCP.Font = [System.Drawing.Font]::new("Segoe UI", 8)
$btnCP.Cursor = "Hand"
$pC.Controls.Add($btnCP)

# ── Log area ────────────────────────────────────────────────────────────────
$lblL = New-Object System.Windows.Forms.Label
$lblL.Text = "日志"
$lblL.ForeColor = $cDim
$lblL.Location = [System.Drawing.Point]::new(20, 304)
$lblL.Size = [System.Drawing.Size]::new(60, 18)
$form.Controls.Add($lblL)

$btnCL = New-Object System.Windows.Forms.Button
$btnCL.Text = "清空"
$btnCL.Location = [System.Drawing.Point]::new(462, 300)
$btnCL.Size = [System.Drawing.Size]::new(68, 22)
$btnCL.FlatStyle = "Flat"
$btnCL.FlatAppearance.BorderSize = 0
$btnCL.BackColor = $cPanel
$btnCL.ForeColor = $cDim
$btnCL.Font = [System.Drawing.Font]::new("Segoe UI", 8)
$btnCL.Cursor = "Hand"
$form.Controls.Add($btnCL)

$txt = New-Object System.Windows.Forms.RichTextBox
$txt.Location = [System.Drawing.Point]::new(20, 324)
$txt.Size = [System.Drawing.Size]::new(510, 174)
$txt.BackColor = [System.Drawing.Color]::FromArgb(10, 10, 14)
$txt.ForeColor = $cText
$txt.Font = [System.Drawing.Font]::new("Consolas", 8.5)
$txt.ReadOnly = $true
$txt.BorderStyle = "None"
$txt.ScrollBars = "Vertical"
$form.Controls.Add($txt)

# ── Helper functions ────────────────────────────────────────────────────────
function Log($m, $c = "LightGray") {
    $txt.SelectionStart = $txt.TextLength
    $txt.SelectionLength = 0
    $txt.SelectionColor = [System.Drawing.Color]::$c
    $txt.AppendText("[$(Get-Date -f HH:mm:ss)] $m`n")
    $txt.ScrollToCaret()
}

function LogD($lines) {
    foreach ($l in $lines) {
        $l = "$l".Trim()
        if (!$l) { continue }
        if ($l -match "error|fail|fatal") { Log $l Salmon }
        elseif ($l -match "warn") { Log $l Gold }
        else { Log $l LightGray }
    }
}

function TestD { docker info 2>$null | Out-Null; $LASTEXITCODE -eq 0 }
function GetSt { (docker inspect --format "{{.State.Status}}" $container 2>$null).Trim() }

function UpdUI {
    if (!(TestD)) {
        $dot.ForeColor = $cOrange
        $lblSt.Text = "Docker 未运行"
        $lblSt.ForeColor = $cOrange
        $lblDk.Text = "请启动 Docker Desktop"
        $lblDk.ForeColor = $cOrange
        return
    }
    $lblDk.Text = "Docker: 运行中"
    $lblDk.ForeColor = $cGreen
    switch (GetSt) {
        "running" {
            $dot.ForeColor = $cGreen
            $lblSt.Text = "服务运行中"
            $lblSt.ForeColor = $cGreen
        }
        { $_ -in "exited", "created" } {
            $dot.ForeColor = $cRed
            $lblSt.Text = "服务已停止"
            $lblSt.ForeColor = $cRed
        }
        default {
            $dot.ForeColor = $cDim
            $lblSt.Text = "未部署"
            $lblSt.ForeColor = $cDim
        }
    }
}

function EnsD {
    @("auths", "logs", "plugins") | ForEach-Object {
        $p = Join-Path $scriptDir $_
        if (!(Test-Path $p)) {
            New-Item -Type Directory $p | Out-Null
            Log "已创建: $_" Cyan
        }
    }
}

function RunC($a, $label) {
    Log "$label..." Cyan
    $form.Enabled = $false
    Set-Location $scriptDir
    $o = & docker compose @a 2>&1
    LogD $o
    Start-Sleep -Milliseconds 1200
    UpdUI
    $form.Enabled = $true
}

# ── Button events ───────────────────────────────────────────────────────────
$btnStart.Add_Click({
    if (!(TestD)) { Log "Docker 未运行" Salmon; return }
    RunC @("up", "-d") "启动服务"
})

$btnStop.Add_Click({
    RunC @("down") "停止服务"
})

$btnRestart.Add_Click({
    if (!(TestD)) { Log "Docker 未运行" Salmon; return }
    RunC @("restart") "重启服务"
})

$btnDeploy.Add_Click({
    if (!(TestD)) { Log "Docker 未运行" Salmon; return }
    Log "=== 开始部署 ===" Cyan
    EnsD
    if (!(Test-Path (Join-Path $scriptDir "config.yaml"))) {
        Log "未找到 config.yaml，请先创建配置文件" Salmon
        [System.Windows.Forms.MessageBox]::Show(
            "请先创建 config.yaml 配置文件。`n可运行 scripts\deploy.ps1 自动生成。",
            "缺少配置", "OK", "Warning") | Out-Null
        return
    }
    RunC @("pull") "拉取镜像"
    RunC @("up", "-d") "启动服务"
    Log "=== 部署完成 ===" LimeGreen
    Start-Process $mgmtUrl
})

$btnPull.Add_Click({
    if (!(TestD)) { Log "Docker 未运行" Salmon; return }
    RunC @("pull") "拉取最新镜像"
})

$btnPanel.Add_Click({ Start-Process $mgmtUrl })

$btnCP.Add_Click({
    [System.Windows.Forms.Clipboard]::SetText($apiUrl)
    $btnCP.Text = "已复制!"
    $tmr = New-Object System.Windows.Forms.Timer
    $tmr.Interval = 1500
    $tmr.Add_Tick({ $btnCP.Text = "复制地址"; $tmr.Stop() })
    $tmr.Start()
})

$btnCL.Add_Click({ $txt.Clear() })

# ── Auto-refresh & startup ─────────────────────────────────────────────────
$ar = New-Object System.Windows.Forms.Timer
$ar.Interval = 8000
$ar.Add_Tick({ UpdUI })

$form.Add_Shown({
    UpdUI
    if ((GetSt) -eq "running") { LogD (docker logs --tail 20 $container 2>&1) }
    $ar.Start()
})

$form.Add_FormClosed({ $ar.Stop() })
[void]$form.ShowDialog()
