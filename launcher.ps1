Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$container = "cli-proxy-api"
$port      = 8317
$mgmtUrl   = "http://localhost:$port/management.html"
$apiUrl    = "http://localhost:$port/v1"
$cfgPath   = Join-Path $scriptDir "config.yaml"
$cmpPath   = Join-Path $scriptDir "docker-compose.yml"

# Colors
$cBg     = [Drawing.Color]::FromArgb(15,15,20)
$cPanel  = [Drawing.Color]::FromArgb(26,26,36)
$cInput  = [Drawing.Color]::FromArgb(36,36,50)
$cBlue   = [Drawing.Color]::FromArgb(56,139,253)
$cGreen  = [Drawing.Color]::FromArgb(63,185,80)
$cRed    = [Drawing.Color]::FromArgb(218,54,51)
$cOrange = [Drawing.Color]::FromArgb(210,140,40)
$cText   = [Drawing.Color]::FromArgb(220,220,230)
$cDim    = [Drawing.Color]::FromArgb(100,100,120)

# Form
$form = New-Object Windows.Forms.Form
$form.Text = "CLIProxyAPI Manager"
$form.Size = [Drawing.Size]::new(570,640)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedSingle"
$form.MaximizeBox = $false
$form.BackColor = $cBg; $form.ForeColor = $cText
$form.Font = [Drawing.Font]::new("Segoe UI",9)

# Title
$lTitle = New-Object Windows.Forms.Label
$lTitle.Text = "CLIProxyAPI Manager"
$lTitle.Font = [Drawing.Font]::new("Segoe UI",16,[Drawing.FontStyle]::Bold)
$lTitle.ForeColor = $cBlue; $lTitle.Location = [Drawing.Point]::new(20,14)
$lTitle.Size = [Drawing.Size]::new(400,32); $form.Controls.Add($lTitle)
$lSub = New-Object Windows.Forms.Label
$lSub.Text = "AI Subscription API Gateway"
$lSub.ForeColor = $cDim; $lSub.Location = [Drawing.Point]::new(22,46)
$lSub.Size = [Drawing.Size]::new(300,18); $form.Controls.Add($lSub)

# Status panel
$pSt = New-Object Windows.Forms.Panel
$pSt.Location = [Drawing.Point]::new(20,74); $pSt.Size = [Drawing.Size]::new(520,62)
$pSt.BackColor = $cPanel; $form.Controls.Add($pSt)
$dot = New-Object Windows.Forms.Label; $dot.Text = [char]0x25CF
$dot.Font = [Drawing.Font]::new("Segoe UI",20); $dot.ForeColor = $cDim
$dot.Location = [Drawing.Point]::new(12,10); $dot.Size = [Drawing.Size]::new(32,36); $pSt.Controls.Add($dot)
$lblSvc = New-Object Windows.Forms.Label; $lblSvc.Text = "Checking..."
$lblSvc.Font = [Drawing.Font]::new("Segoe UI",11,[Drawing.FontStyle]::Bold); $lblSvc.ForeColor = $cDim
$lblSvc.Location = [Drawing.Point]::new(50,8); $lblSvc.Size = [Drawing.Size]::new(250,24); $pSt.Controls.Add($lblSvc)
$lblDk = New-Object Windows.Forms.Label; $lblDk.Text = "Docker: checking..."
$lblDk.ForeColor = $cDim; $lblDk.Location = [Drawing.Point]::new(50,34)
$lblDk.Size = [Drawing.Size]::new(450,18); $pSt.Controls.Add($lblDk)

# Helper: make button
function MkBtn($t,$x,$y,$w,$col){
    $b = New-Object Windows.Forms.Button; $b.Text = $t
    $b.Location = [Drawing.Point]::new($x,$y); $b.Size = [Drawing.Size]::new($w,36)
    $b.FlatStyle = "Flat"; $b.FlatAppearance.BorderSize = 0; $b.BackColor = $col
    $b.ForeColor = [Drawing.Color]::White
    $b.Font = [Drawing.Font]::new("Segoe UI",9,[Drawing.FontStyle]::Bold)
    $b.Cursor = "Hand"; $form.Controls.Add($b); return $b
}

# Row 1: service control
$btnStart   = MkBtn "Start"   20 148 115 ([Drawing.Color]::FromArgb(35,105,55))
$btnStop    = MkBtn "Stop"   142 148  90 ([Drawing.Color]::FromArgb(130,35,35))
$btnRestart = MkBtn "Restart" 238 148 110 ([Drawing.Color]::FromArgb(70,60,20))
$btnOpen    = MkBtn "Management Panel" 354 148 186 ([Drawing.Color]::FromArgb(44,82,130))

# Row 2: deploy
$btnDeploy = MkBtn "Setup and Deploy"  20 192 190 $cBlue
$btnUpdate = MkBtn "Update Image"     218 192 150 ([Drawing.Color]::FromArgb(50,50,80))
$btnLogs   = MkBtn "Live Logs"        374 192 166 ([Drawing.Color]::FromArgb(55,40,80))

# Setup wizard panel (shown when config.yaml missing)
$pWiz = New-Object Windows.Forms.Panel
$pWiz.Location = [Drawing.Point]::new(20,238); $pWiz.Size = [Drawing.Size]::new(520,130)
$pWiz.BackColor = [Drawing.Color]::FromArgb(20,30,20); $pWiz.Visible = $false
$form.Controls.Add($pWiz)

$lWizTitle = New-Object Windows.Forms.Label
$lWizTitle.Text = "First-time Setup"
$lWizTitle.Font = [Drawing.Font]::new("Segoe UI",10,[Drawing.FontStyle]::Bold)
$lWizTitle.ForeColor = $cGreen; $lWizTitle.Location = [Drawing.Point]::new(12,10)
$lWizTitle.Size = [Drawing.Size]::new(300,22); $pWiz.Controls.Add($lWizTitle)
$lWizSub = New-Object Windows.Forms.Label
$lWizSub.Text = "config.yaml not found. Generate credentials and deploy automatically."
$lWizSub.ForeColor = $cDim; $lWizSub.Location = [Drawing.Point]::new(12,32)
$lWizSub.Size = [Drawing.Size]::new(500,18); $pWiz.Controls.Add($lWizSub)

$lProxy = New-Object Windows.Forms.Label; $lProxy.Text = "Local proxy port:"
$lProxy.ForeColor = $cDim; $lProxy.Location = [Drawing.Point]::new(12,60)
$lProxy.Size = [Drawing.Size]::new(120,22); $pWiz.Controls.Add($lProxy)
$txtProxy = New-Object Windows.Forms.TextBox; $txtProxy.Text = "7890"
$txtProxy.Location = [Drawing.Point]::new(134,58); $txtProxy.Size = [Drawing.Size]::new(60,22)
$txtProxy.BackColor = $cInput; $txtProxy.ForeColor = $cText; $txtProxy.BorderStyle = "FixedSingle"
$pWiz.Controls.Add($txtProxy)
$lProxyNote = New-Object Windows.Forms.Label
$lProxyNote.Text = "(0 = no proxy, e.g. US server)"
$lProxyNote.ForeColor = $cDim; $lProxyNote.Location = [Drawing.Point]::new(202,60)
$lProxyNote.Size = [Drawing.Size]::new(250,22); $pWiz.Controls.Add($lProxyNote)

$btnGen = New-Object Windows.Forms.Button
$btnGen.Text = "Generate Config and Deploy"
$btnGen.Location = [Drawing.Point]::new(12,90); $btnGen.Size = [Drawing.Size]::new(220,32)
$btnGen.FlatStyle = "Flat"; $btnGen.FlatAppearance.BorderSize = 0
$btnGen.BackColor = $cGreen; $btnGen.ForeColor = [Drawing.Color]::White
$btnGen.Font = [Drawing.Font]::new("Segoe UI",9,[Drawing.FontStyle]::Bold)
$btnGen.Cursor = "Hand"; $pWiz.Controls.Add($btnGen)

# API copy bar
$pApi = New-Object Windows.Forms.Panel
$pApi.Location = [Drawing.Point]::new(20,378); $pApi.Size = [Drawing.Size]::new(520,34)
$pApi.BackColor = $cPanel; $form.Controls.Add($pApi)
$lApi = New-Object Windows.Forms.Label; $lApi.Text = "API: $apiUrl"
$lApi.ForeColor = $cDim; $lApi.Location = [Drawing.Point]::new(10,9)
$lApi.Size = [Drawing.Size]::new(380,18); $pApi.Controls.Add($lApi)
$btnCopy = New-Object Windows.Forms.Button; $btnCopy.Text = "Copy URL"
$btnCopy.Location = [Drawing.Point]::new(402,4); $btnCopy.Size = [Drawing.Size]::new(110,26)
$btnCopy.FlatStyle = "Flat"; $btnCopy.FlatAppearance.BorderSize = 1
$btnCopy.FlatAppearance.BorderColor = [Drawing.Color]::FromArgb(45,45,60)
$btnCopy.BackColor = $cPanel; $btnCopy.ForeColor = $cDim
$btnCopy.Font = [Drawing.Font]::new("Segoe UI",8); $btnCopy.Cursor = "Hand"
$pApi.Controls.Add($btnCopy)

# Log
$lLog = New-Object Windows.Forms.Label; $lLog.Text = "Log"
$lLog.ForeColor = $cDim; $lLog.Location = [Drawing.Point]::new(20,420)
$lLog.Size = [Drawing.Size]::new(60,18); $form.Controls.Add($lLog)
$btnClr = New-Object Windows.Forms.Button; $btnClr.Text = "Clear"
$btnClr.Location = [Drawing.Point]::new(470,416); $btnClr.Size = [Drawing.Size]::new(70,22)
$btnClr.FlatStyle = "Flat"; $btnClr.FlatAppearance.BorderSize = 0
$btnClr.BackColor = $cPanel; $btnClr.ForeColor = $cDim
$btnClr.Font = [Drawing.Font]::new("Segoe UI",8); $btnClr.Cursor = "Hand"
$form.Controls.Add($btnClr)
$txt = New-Object Windows.Forms.RichTextBox
$txt.Location = [Drawing.Point]::new(20,440); $txt.Size = [Drawing.Size]::new(520,154)
$txt.BackColor = [Drawing.Color]::FromArgb(10,10,14); $txt.ForeColor = $cText
$txt.Font = [Drawing.Font]::new("Consolas",8.5); $txt.ReadOnly = $true
$txt.BorderStyle = "None"; $txt.ScrollBars = "Vertical"; $form.Controls.Add($txt)

# Helper functions
function Log($m,$c="LightGray"){
    $txt.SelectionStart=$txt.TextLength; $txt.SelectionLength=0
    $txt.SelectionColor=[Drawing.Color]::$c
    $txt.AppendText("[$(Get-Date -f HH:mm:ss)] $m`n"); $txt.ScrollToCaret()
}
function LogD($lines){ foreach($l in $lines){$l="$l".Trim(); if(!$l){continue}
    if($l -match "error|fail|fatal"){Log $l Salmon} elseif($l -match "warn"){Log $l Gold} else{Log $l LightGray}} }
function TestD{ docker info 2>$null|Out-Null; $LASTEXITCODE -eq 0 }
function GetSt{ (docker inspect --format "{{.State.Status}}" $container 2>$null).Trim() }
function UpdUI{
    if(!(TestD)){$dot.ForeColor=$cOrange;$lblSvc.Text="Docker not running";$lblSvc.ForeColor=$cOrange
        $lblDk.Text="Please start Docker Desktop"; $lblDk.ForeColor=$cOrange; return}
    $lblDk.Text="Docker: running"; $lblDk.ForeColor=$cGreen
    switch(GetSt){
        "running"{$dot.ForeColor=$cGreen;$lblSvc.Text="Service running";$lblSvc.ForeColor=$cGreen}
        {unsetenv -in "exited","created"}{$dot.ForeColor=$cRed;$lblSvc.Text="Service stopped";$lblSvc.ForeColor=$cRed}
        default{$dot.ForeColor=$cDim;$lblSvc.Text="Not deployed";$lblSvc.ForeColor=$cDim}
    }
}
function RandHex{ -join ((1..16)|%{[byte[]]::new(1)|%{[System.Security.Cryptography.RandomNumberGenerator]::Fill($_); $_}|%{"{0:x2}" -f $_}}) }
function RandPwd{
    $c="ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
    $b=New-Object byte[] 20; [System.Security.Cryptography.RandomNumberGenerator]::Fill($b)
    -join ($b|%{$c[$_ % $c.Length]})
}
function EnsureDirs{
    @("auths","logs","plugins")|%{$p=Join-Path $scriptDir $_
        if(!(Test-Path $p)){New-Item -Type Directory $p|Out-Null; Log "Created dir: $_" Cyan}}
}
function RunC($a,$label){
    Log "$label..." Cyan; $form.Enabled=$false; Set-Location $scriptDir
    $o=& docker compose @a 2>&1; LogD $o; Start-Sleep -ms 1000; UpdUI; $form.Enabled=$true
}

# Generate config and deploy
function DoSetupAndDeploy{
    if(!(TestD)){Log "Docker not running - please start Docker Desktop" Salmon; return}
    EnsureDirs
    if(!(Test-Path $cfgPath)){$pWiz.Visible=$true; Log "Fill in the setup panel." Gold; return}
    $pWiz.Visible=$false
    RunC @("pull") "Pulling latest image"
    RunC @("up","-d","--pull","never") "Starting service"
    Log "Deploy complete - open Management Panel to add accounts." LimeGreen
    Start-Process $mgmtUrl
}

$btnGen.Add_Click({
    $proxyPort = $txtProxy.Text.Trim()
    $key1 = "sk-$(RandHex)"
    $key2 = "sk-$(RandHex)"
    $mgmtPwd = RandPwd
    $nl = [Environment]::NewLine
    $cfg = "config-version: 8" + $nl +
            "host: 0.0.0.0" + $nl +
            "port: $port" + $nl +
            "access:" + $nl +
            "  api-keys:" + $nl +
            "    - $key1" + $nl +
            "    - $key2" + $nl +
            "oauth:" + $nl +
            "  auth-dir: /root/.cli-proxy-api" + $nl +
            "routing:" + $nl +
            "  strategy: round-robin" + $nl +
            "remote-management:" + $nl +
            "  allow-remote: true" + $nl +
            "  secret-key: $mgmtPwd" + $nl +
            "  disable-control-panel: false" + $nl
    [IO.File]::WriteAllText($cfgPath, $cfg, [Text.UTF8Encoding]::new($false))
    Log "config.yaml generated" Cyan
    if($proxyPort -and $proxyPort -ne "0"){
        $cmp = Get-Content $cmpPath -Raw
        if($cmp -notmatch "HTTP_PROXY"){
            $envLines = "    environment:" + $nl +
                         "      - HTTP_PROXY=http://host.docker.internal:$proxyPort" + $nl +
                         "      - HTTPS_PROXY=http://host.docker.internal:$proxyPort" + $nl +
                         "      - NO_PROXY=localhost,127.0.0.1" + $nl
            $cmp = $cmp.Replace("    restart:", $envLines + "    restart:")
            [IO.File]::WriteAllText($cmpPath, $cmp, [Text.UTF8Encoding]::new($false))
            Log "Proxy set: host.docker.internal:$proxyPort" Cyan
        }
    }
    Log "=== Save these credentials! ===" Gold
    Log "API Key 1:     $key1" LimeGreen
    Log "API Key 2:     $key2" LimeGreen
    Log "Mgmt password: $mgmtPwd" LimeGreen
    Log "Management URL: $mgmtUrl" LimeGreen
    $pWiz.Visible=$false
    RunC @("pull") "Pulling latest image"
    RunC @("up","-d","--pull","never") "Starting service"
    Log "Setup complete!" LimeGreen
    Start-Process $mgmtUrl
})

# Button events
$btnStart.Add_Click({if(!(TestD)){Log "Docker not running" Salmon;return}; RunC @("up","-d","--pull","never") "Starting service"})
$btnStop.Add_Click({RunC @("down") "Stopping service"})
$btnRestart.Add_Click({if(!(TestD)){Log "Docker not running" Salmon;return}; RunC @("restart") "Restarting service"})
$btnOpen.Add_Click({Start-Process $mgmtUrl})
$btnDeploy.Add_Click({DoSetupAndDeploy})
$btnUpdate.Add_Click({
    if(!(TestD)){Log "Docker not running" Salmon;return}
    RunC @("pull") "Pulling latest image"
    RunC @("up","-d","--pull","never") "Restarting with new image"
    Log "Update complete" LimeGreen
})
$btnLogs.Add_Click({
    $st = GetSt
    if($st -ne "running"){Log "Service not running" Salmon;return}
    Start-Process powershell -ArgumentList "-NoExit","-Command","cd $scriptDir; docker compose logs -f"
})
$btnCopy.Add_Click({
    [Windows.Forms.Clipboard]::SetText($apiUrl); $btnCopy.Text="Copied!"
    $tmr=New-Object Windows.Forms.Timer; $tmr.Interval=1500
    $tmr.Add_Tick({$btnCopy.Text="Copy URL";$tmr.Stop()}); $tmr.Start()
})
$btnClr.Add_Click({$txt.Clear()})

# Auto-refresh
$ar = New-Object Windows.Forms.Timer; $ar.Interval = 8000; $ar.Add_Tick({UpdUI})
$form.Add_Shown({
    UpdUI
    if(!(Test-Path $cfgPath)){
        $pWiz.Visible = $true
        Log "Welcome! config.yaml not found. Use the setup panel to get started." Gold
    } elseif((GetSt) -eq "running"){
        LogD(docker logs --tail 15 $container 2>&1)
    }
    $ar.Start()
})
$form.Add_FormClosed({$ar.Stop()})
[void]$form.ShowDialog()
