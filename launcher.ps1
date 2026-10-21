Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$container = "cli-proxy-api"
$port      = 8317
$mgmtUrl   = "http://localhost:$port/management.html"
$apiUrl    = "http://localhost:$port/v1"
$cfgPath   = Join-Path $scriptDir "config.yaml"
$cmpPath   = Join-Path $scriptDir "docker-compose.yml"
$dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"

$cBg     = [Drawing.Color]::FromArgb(15,15,20)
$cPanel  = [Drawing.Color]::FromArgb(26,26,36)
$cInput  = [Drawing.Color]::FromArgb(36,36,50)
$cBlue   = [Drawing.Color]::FromArgb(56,139,253)
$cGreen  = [Drawing.Color]::FromArgb(63,185,80)
$cRed    = [Drawing.Color]::FromArgb(218,54,51)
$cOrange = [Drawing.Color]::FromArgb(210,140,40)
$cText   = [Drawing.Color]::FromArgb(220,220,230)
$cDim    = [Drawing.Color]::FromArgb(100,100,120)

$form = New-Object Windows.Forms.Form
$form.Text = "CLIProxyAPI Manager"
$form.Size = [Drawing.Size]::new(570,660)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedSingle"
$form.MaximizeBox = $false
$form.BackColor = $cBg; $form.ForeColor = $cText
$form.Font = [Drawing.Font]::new("Segoe UI",9)

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
$pSt.Location = [Drawing.Point]::new(20,74); $pSt.Size = [Drawing.Size]::new(520,70)
$pSt.BackColor = $cPanel; $form.Controls.Add($pSt)
$dot = New-Object Windows.Forms.Label; $dot.Text = [char]0x25CF
$dot.Font = [Drawing.Font]::new("Segoe UI",20); $dot.ForeColor = $cDim
$dot.Location = [Drawing.Point]::new(12,12); $dot.Size = [Drawing.Size]::new(32,38)
$pSt.Controls.Add($dot)
$lblSvc = New-Object Windows.Forms.Label; $lblSvc.Text = "Checking..."
$lblSvc.Font = [Drawing.Font]::new("Segoe UI",11,[Drawing.FontStyle]::Bold)
$lblSvc.ForeColor = $cDim; $lblSvc.Location = [Drawing.Point]::new(50,8)
$lblSvc.Size = [Drawing.Size]::new(320,24); $pSt.Controls.Add($lblSvc)
$lblDk = New-Object Windows.Forms.Label; $lblDk.Text = "Docker: checking..."
$lblDk.ForeColor = $cDim; $lblDk.Location = [Drawing.Point]::new(50,34)
$lblDk.Size = [Drawing.Size]::new(310,18); $pSt.Controls.Add($lblDk)
# Start Docker button (visible only when Docker is not running)
$btnDockerStart = New-Object Windows.Forms.Button
$btnDockerStart.Text = "Start Docker Desktop"
$btnDockerStart.Location = [Drawing.Point]::new(368,18)
$btnDockerStart.Size = [Drawing.Size]::new(142,34)
$btnDockerStart.FlatStyle = "Flat"; $btnDockerStart.FlatAppearance.BorderSize = 0
$btnDockerStart.BackColor = $cOrange; $btnDockerStart.ForeColor = [Drawing.Color]::White
$btnDockerStart.Font = [Drawing.Font]::new("Segoe UI",8,[Drawing.FontStyle]::Bold)
$btnDockerStart.Cursor = "Hand"; $btnDockerStart.Visible = $false
$pSt.Controls.Add($btnDockerStart)

function MkBtn($t,$x,$y,$w,$col){
    $b = New-Object Windows.Forms.Button; $b.Text = $t
    $b.Location = [Drawing.Point]::new($x,$y); $b.Size = [Drawing.Size]::new($w,36)
    $b.FlatStyle = "Flat"; $b.FlatAppearance.BorderSize = 0; $b.BackColor = $col
    $b.ForeColor = [Drawing.Color]::White
    $b.Font = [Drawing.Font]::new("Segoe UI",9,[Drawing.FontStyle]::Bold)
    $b.Cursor = "Hand"; $form.Controls.Add($b); return $b
}

$btnStart   = MkBtn "Start"            20  156  110  ([Drawing.Color]::FromArgb(35,105,55))
$btnStop    = MkBtn "Stop"            136  156   90  ([Drawing.Color]::FromArgb(130,35,35))
$btnRestart = MkBtn "Restart"         232  156  110  ([Drawing.Color]::FromArgb(70,60,20))
$btnOpen    = MkBtn "Management Panel" 348  156  192  ([Drawing.Color]::FromArgb(44,82,130))
$btnDeploy  = MkBtn "Setup and Deploy"  20  200  190  $cBlue
$btnUpdate  = MkBtn "Update Image"     216  200  150  ([Drawing.Color]::FromArgb(50,50,80))
$btnLogs    = MkBtn "Live Logs"        372  200  168  ([Drawing.Color]::FromArgb(55,40,80))

# Setup wizard panel
$pWiz = New-Object Windows.Forms.Panel
$pWiz.Location = [Drawing.Point]::new(20,248); $pWiz.Size = [Drawing.Size]::new(520,130)
$pWiz.BackColor = [Drawing.Color]::FromArgb(18,32,18); $pWiz.Visible = $false
$form.Controls.Add($pWiz)
$lWizT = New-Object Windows.Forms.Label; $lWizT.Text = "First-time Setup"
$lWizT.Font = [Drawing.Font]::new("Segoe UI",10,[Drawing.FontStyle]::Bold)
$lWizT.ForeColor = $cGreen; $lWizT.Location = [Drawing.Point]::new(12,10)
$lWizT.Size = [Drawing.Size]::new(300,22); $pWiz.Controls.Add($lWizT)
$lWizS = New-Object Windows.Forms.Label
$lWizS.Text = "config.yaml not found. Auto-generate credentials and deploy."
$lWizS.ForeColor = $cDim; $lWizS.Location = [Drawing.Point]::new(12,32)
$lWizS.Size = [Drawing.Size]::new(500,18); $pWiz.Controls.Add($lWizS)
$lPx = New-Object Windows.Forms.Label; $lPx.Text = "Local proxy port:"
$lPx.ForeColor = $cDim; $lPx.Location = [Drawing.Point]::new(12,60)
$lPx.Size = [Drawing.Size]::new(120,22); $pWiz.Controls.Add($lPx)
$txtPx = New-Object Windows.Forms.TextBox; $txtPx.Text = "7890"
$txtPx.Location = [Drawing.Point]::new(136,58); $txtPx.Size = [Drawing.Size]::new(60,22)
$txtPx.BackColor = $cInput; $txtPx.ForeColor = $cText; $txtPx.BorderStyle = "FixedSingle"
$pWiz.Controls.Add($txtPx)
$lPxNote = New-Object Windows.Forms.Label
$lPxNote.Text = "(enter 0 if no proxy needed, e.g. overseas server)"
$lPxNote.ForeColor = $cDim; $lPxNote.Location = [Drawing.Point]::new(204,60)
$lPxNote.Size = [Drawing.Size]::new(310,22); $pWiz.Controls.Add($lPxNote)
$btnGen = New-Object Windows.Forms.Button; $btnGen.Text = "Generate Config and Deploy"
$btnGen.Location = [Drawing.Point]::new(12,90); $btnGen.Size = [Drawing.Size]::new(226,32)
$btnGen.FlatStyle = "Flat"; $btnGen.FlatAppearance.BorderSize = 0
$btnGen.BackColor = $cGreen; $btnGen.ForeColor = [Drawing.Color]::White
$btnGen.Font = [Drawing.Font]::new("Segoe UI",9,[Drawing.FontStyle]::Bold)
$btnGen.Cursor = "Hand"; $pWiz.Controls.Add($btnGen)

# API bar
$pApi = New-Object Windows.Forms.Panel
$pApi.Location = [Drawing.Point]::new(20,390); $pApi.Size = [Drawing.Size]::new(520,34)
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
$lLog.ForeColor = $cDim; $lLog.Location = [Drawing.Point]::new(20,432)
$lLog.Size = [Drawing.Size]::new(60,18); $form.Controls.Add($lLog)
$btnClr = New-Object Windows.Forms.Button; $btnClr.Text = "Clear"
$btnClr.Location = [Drawing.Point]::new(470,428); $btnClr.Size = [Drawing.Size]::new(70,22)
$btnClr.FlatStyle = "Flat"; $btnClr.FlatAppearance.BorderSize = 0
$btnClr.BackColor = $cPanel; $btnClr.ForeColor = $cDim
$btnClr.Font = [Drawing.Font]::new("Segoe UI",8); $btnClr.Cursor = "Hand"
$form.Controls.Add($btnClr)
$txt = New-Object Windows.Forms.RichTextBox
$txt.Location = [Drawing.Point]::new(20,454); $txt.Size = [Drawing.Size]::new(520,162)
$txt.BackColor = [Drawing.Color]::FromArgb(10,10,14); $txt.ForeColor = $cText
$txt.Font = [Drawing.Font]::new("Consolas",8.5); $txt.ReadOnly = $true
$txt.BorderStyle = "None"; $txt.ScrollBars = "Vertical"; $form.Controls.Add($txt)

function Log($m,$c="LightGray"){
    $txt.SelectionStart=$txt.TextLength; $txt.SelectionLength=0
    $txt.SelectionColor=[Drawing.Color]::$c
    $txt.AppendText("[$(Get-Date -f HH:mm:ss)] $m`n"); $txt.ScrollToCaret()
}
function LogD($lines){ foreach($l in $lines){$l="$l".Trim();if(!$l){continue}
    if($l -match "error|fail|fatal"){Log $l Salmon}elseif($l -match "warn"){Log $l Gold}else{Log $l LightGray}} }
function TestD{ docker info 2>$null|Out-Null; $LASTEXITCODE -eq 0 }
function GetSt{ (docker inspect --format "{{.State.Status}}" $container 2>$null).Trim() }

function UpdUI{
    if(!(TestD)){
        $dot.ForeColor=$cOrange; $lblSvc.Text="Docker not running"; $lblSvc.ForeColor=$cOrange
        $lblDk.Text="Click the button to start Docker Desktop"
        $lblDk.ForeColor=$cOrange; $btnDockerStart.Visible=$true; return
    }
    $btnDockerStart.Visible=$false
    $lblDk.Text="Docker: running"; $lblDk.ForeColor=$cGreen
    switch(GetSt){
        "running"{$dot.ForeColor=$cGreen;$lblSvc.Text="Service running";$lblSvc.ForeColor=$cGreen}
        {unsetenv -in "exited","created"}{$dot.ForeColor=$cRed;$lblSvc.Text="Service stopped";$lblSvc.ForeColor=$cRed}
        default{$dot.ForeColor=$cDim;$lblSvc.Text="Not deployed";$lblSvc.ForeColor=$cDim}
    }
}

function RandHex{ 
    $b=New-Object byte[] 16; [Security.Cryptography.RandomNumberGenerator]::Fill($b)
    -join ($b|%{"{0:x2}" -f $_}) }
function RandPwd{
    $c="ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
    $b=New-Object byte[] 20; [Security.Cryptography.RandomNumberGenerator]::Fill($b)
    -join ($b|%{$c[$_ % $c.Length]}) }
function EnsureDirs{
    @("auths","logs","plugins")|%{$p=Join-Path $scriptDir $_
        if(!(Test-Path $p)){New-Item -Type Directory $p|Out-Null;Log "Created: $_" Cyan}} }
function RunC($a,$label){
    Log "$label..." Cyan; $form.Enabled=$false; Set-Location $scriptDir
    $o=& docker compose @a 2>&1; LogD $o; Start-Sleep -ms 1000; UpdUI; $form.Enabled=$true }

# Start Docker Desktop button handler
$btnDockerStart.Add_Click({
    Log "Starting Docker Desktop..." Cyan
    $exe = $dockerExe
    if(!(Test-Path $exe)){
        $exe = (Get-ItemProperty -Path "HKLM:\SOFTWARE\Docker Inc.\Docker Desktop" -Name "AppPath" -EA SilentlyContinue).AppPath
        if(!$exe){ Log "Cannot find Docker Desktop executable" Salmon; return }
        $exe = Join-Path $exe "Docker Desktop.exe"
    }
    Start-Process $exe
    Log "Waiting for Docker to start (may take 30-60 seconds)..." Gold
    $form.Enabled = $false
    $wait = New-Object Windows.Forms.Timer; $wait.Interval = 3000
    $wait.Add_Tick({
        if(TestD){
            $wait.Stop(); $form.Enabled = $true
            Log "Docker is ready!" LimeGreen
            UpdUI
            if(!(Test-Path $cfgPath)){$pWiz.Visible=$true; Log "Now fill in the setup panel." Gold}
        } else { Log "Still waiting for Docker..." DimGray }
    })
    $wait.Start()
})

# Setup and Deploy
function DoSetupAndDeploy{
    if(!(TestD)){Log "Docker not running - click Start Docker Desktop" Salmon; return}
    EnsureDirs
    if(!(Test-Path $cfgPath)){$pWiz.Visible=$true; Log "Fill in the setup panel above." Gold; return}
    $pWiz.Visible=$false
    RunC @("pull") "Pulling latest image"
    RunC @("up","-d","--pull","never") "Starting service"
    Log "Deploy complete - open Management Panel to add your AI accounts." LimeGreen
    Start-Process $mgmtUrl
}

$btnGen.Add_Click({
    $px=$txtPx.Text.Trim(); $k1="sk-$(RandHex)"; $k2="sk-$(RandHex)"; $pw=RandPwd
    $nl=[Environment]::NewLine
    $cfg=@("config-version: 8","host: 0.0.0.0","port: $port","access:","  api-keys:",
           "    - $k1","    - $k2","oauth:","  auth-dir: /root/.cli-proxy-api",
           "routing:","  strategy: round-robin","remote-management:",
           "  allow-remote: true","  secret-key: $pw","  disable-control-panel: false") -join $nl
    [IO.File]::WriteAllText($cfgPath,$cfg+$nl,[Text.UTF8Encoding]::new($false))
    Log "config.yaml generated" Cyan
    if($px -and $px -ne "0"){
        $cmp=Get-Content $cmpPath -Raw
        if($cmp -notmatch "HTTP_PROXY"){
            $env="    environment:$nl      - HTTP_PROXY=http://host.docker.internal:$px$nl      - HTTPS_PROXY=http://host.docker.internal:$px$nl      - NO_PROXY=localhost,127.0.0.1$nl"
            $cmp=$cmp.Replace("    restart:",$env+"    restart:")
            [IO.File]::WriteAllText($cmpPath,$cmp,[Text.UTF8Encoding]::new($false))
            Log "Proxy configured: port $px" Cyan
        }
    }
    Log "=== Save these credentials! ===" Gold
    Log "API Key 1:      $k1" LimeGreen
    Log "API Key 2:      $k2" LimeGreen
    Log "Mgmt password:  $pw" LimeGreen
    Log "Management URL: $mgmtUrl" LimeGreen
    $pWiz.Visible=$false
    RunC @("pull") "Pulling latest image"
    RunC @("up","-d","--pull","never") "Starting service"
    Log "Setup complete!" LimeGreen
    Start-Process $mgmtUrl
})

$btnStart.Add_Click({if(!(TestD)){Log "Docker not running" Salmon;return};RunC @("up","-d","--pull","never") "Starting"})
$btnStop.Add_Click({RunC @("down") "Stopping"})
$btnRestart.Add_Click({if(!(TestD)){Log "Docker not running" Salmon;return};RunC @("restart") "Restarting"})
$btnOpen.Add_Click({Start-Process $mgmtUrl})
$btnDeploy.Add_Click({DoSetupAndDeploy})
$btnUpdate.Add_Click({
    if(!(TestD)){Log "Docker not running" Salmon;return}
    RunC @("pull") "Pulling latest image"
    RunC @("up","-d","--pull","never") "Restarting with new image"
    Log "Update complete" LimeGreen
})
$btnLogs.Add_Click({
    if((GetSt) -ne "running"){Log "Service not running" Salmon;return}
    Start-Process powershell -ArgumentList "-NoExit","-Command","cd `"$scriptDir`"; docker compose logs -f"
})
$btnCopy.Add_Click({
    [Windows.Forms.Clipboard]::SetText($apiUrl);$btnCopy.Text="Copied!"
    $t=New-Object Windows.Forms.Timer;$t.Interval=1500
    $t.Add_Tick({$btnCopy.Text="Copy URL";$t.Stop()});$t.Start()
})
$btnClr.Add_Click({$txt.Clear()})

$ar=New-Object Windows.Forms.Timer;$ar.Interval=8000;$ar.Add_Tick({UpdUI})
$form.Add_Shown({
    UpdUI
    if(!(Test-Path $cfgPath)){
        $pWiz.Visible=$true
        if(TestD){Log "Welcome! Fill in the setup panel to get started." Gold}
        else{Log "Welcome! Start Docker Desktop first, then set up." Gold}
    } elseif((GetSt) -eq "running"){LogD(docker logs --tail 15 $container 2>&1)}
    $ar.Start()
})
$form.Add_FormClosed({$ar.Stop()})
[void]$form.ShowDialog()
