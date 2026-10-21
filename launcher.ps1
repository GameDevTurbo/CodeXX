Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$container = "cli-proxy-api"
$port      = 8317
$mgmtUrl   = "http://localhost:$port/management.html"
$apiUrl    = "http://localhost:$port/v1"
$cfgPath   = Join-Path $scriptDir "config.yaml"
$cmpPath   = Join-Path $scriptDir "docker-compose.yml"

$cBg     = [Drawing.Color]::FromArgb(15,15,20)
$cPanel  = [Drawing.Color]::FromArgb(26,26,36)
$cCard   = [Drawing.Color]::FromArgb(22,22,32)
$cInput  = [Drawing.Color]::FromArgb(36,36,52)
$cBlue   = [Drawing.Color]::FromArgb(56,139,253)
$cGreen  = [Drawing.Color]::FromArgb(63,185,80)
$cRed    = [Drawing.Color]::FromArgb(218,54,51)
$cOrange = [Drawing.Color]::FromArgb(210,140,40)
$cText   = [Drawing.Color]::FromArgb(220,220,230)
$cDim    = [Drawing.Color]::FromArgb(100,100,120)
$cSuccess= [Drawing.Color]::FromArgb(40,60,40)

$form = New-Object Windows.Forms.Form
$form.Text = "CLIProxyAPI Manager"
$form.Size = [Drawing.Size]::new(560,700)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedSingle"
$form.MaximizeBox = $false
$form.BackColor = $cBg; $form.ForeColor = $cText
$form.Font = [Drawing.Font]::new("Segoe UI",9)

# Header
$lTitle = New-Object Windows.Forms.Label
$lTitle.Text = "CLIProxyAPI Manager"
$lTitle.Font = [Drawing.Font]::new("Segoe UI",15,[Drawing.FontStyle]::Bold)
$lTitle.ForeColor = $cBlue; $lTitle.Location = [Drawing.Point]::new(20,14)
$lTitle.Size = [Drawing.Size]::new(400,30); $form.Controls.Add($lTitle)
$lSub = New-Object Windows.Forms.Label; $lSub.Text = "AI Subscription API Gateway"
$lSub.ForeColor = $cDim; $lSub.Location = [Drawing.Point]::new(22,44)
$lSub.Size = [Drawing.Size]::new(300,18); $form.Controls.Add($lSub)

# Steps panel
$pSteps = New-Object Windows.Forms.Panel
$pSteps.Location = [Drawing.Point]::new(20,72); $pSteps.Size = [Drawing.Size]::new(514,136)
$pSteps.BackColor = $cCard; $form.Controls.Add($pSteps)

function MkStepRow($num,$name,$y){
    $row = New-Object Windows.Forms.Panel
    $row.Location = [Drawing.Point]::new(0,$y); $row.Size = [Drawing.Size]::new(514,44)
    $row.BackColor = $cCard; $pSteps.Controls.Add($row)

    $dot = New-Object Windows.Forms.Label; $dot.Text = [char]0x25CF
    $dot.Font = [Drawing.Font]::new("Segoe UI",16); $dot.ForeColor = $cDim
    $dot.Location = [Drawing.Point]::new(12,8); $dot.Size = [Drawing.Size]::new(24,28)
    $row.Controls.Add($dot)

    $lNum = New-Object Windows.Forms.Label; $lNum.Text = "Step $num"
    $lNum.ForeColor = $cDim; $lNum.Font = [Drawing.Font]::new("Segoe UI",7)
    $lNum.Location = [Drawing.Point]::new(42,6); $lNum.Size = [Drawing.Size]::new(56,14)
    $row.Controls.Add($lNum)

    $lName = New-Object Windows.Forms.Label; $lName.Text = $name
    $lName.Font = [Drawing.Font]::new("Segoe UI",9,[Drawing.FontStyle]::Bold)
    $lName.ForeColor = $cText
    $lName.Location = [Drawing.Point]::new(42,22); $lName.Size = [Drawing.Size]::new(150,18)
    $row.Controls.Add($lName)

    $lStat = New-Object Windows.Forms.Label; $lStat.Text = "Checking..."
    $lStat.ForeColor = $cDim
    $lStat.Location = [Drawing.Point]::new(200,15); $lStat.Size = [Drawing.Size]::new(170,18)
    $row.Controls.Add($lStat)

    $btn = New-Object Windows.Forms.Button; $btn.Text = ""
    $btn.Location = [Drawing.Point]::new(380,8); $btn.Size = [Drawing.Size]::new(124,28)
    $btn.FlatStyle = "Flat"; $btn.FlatAppearance.BorderSize = 0
    $btn.BackColor = $cBlue; $btn.ForeColor = [Drawing.Color]::White
    $btn.Font = [Drawing.Font]::new("Segoe UI",8,[Drawing.FontStyle]::Bold)
    $btn.Cursor = "Hand"; $btn.Visible = $false
    $row.Controls.Add($btn)

    return @{$"dot"=$dot; $"stat"=$lStat; $"btn"=$btn}
}

$s1 = MkStepRow 1 "Docker Desktop"  0
$s2 = MkStepRow 2 "Configuration"  46
$s3 = MkStepRow 3 "Service"        92

# Wizard panel (config generation)
$pWiz = New-Object Windows.Forms.Panel
$pWiz.Location = [Drawing.Point]::new(20,218); $pWiz.Size = [Drawing.Size]::new(514,118)
$pWiz.BackColor = [Drawing.Color]::FromArgb(18,32,18); $pWiz.Visible = $false
$form.Controls.Add($pWiz)
$lWT = New-Object Windows.Forms.Label; $lWT.Text = "Generate Configuration"
$lWT.Font = [Drawing.Font]::new("Segoe UI",10,[Drawing.FontStyle]::Bold)
$lWT.ForeColor = $cGreen; $lWT.Location = [Drawing.Point]::new(14,10)
$lWT.Size = [Drawing.Size]::new(400,22); $pWiz.Controls.Add($lWT)
$lWS = New-Object Windows.Forms.Label
$lWS.Text = "API keys and management password will be auto-generated."
$lWS.ForeColor = $cDim; $lWS.Location = [Drawing.Point]::new(14,32)
$lWS.Size = [Drawing.Size]::new(490,18); $pWiz.Controls.Add($lWS)
$lPx = New-Object Windows.Forms.Label; $lPx.Text = "Local proxy port:"
$lPx.ForeColor = $cDim; $lPx.Location = [Drawing.Point]::new(14,58)
$lPx.Size = [Drawing.Size]::new(118,22); $pWiz.Controls.Add($lPx)
$txtPx = New-Object Windows.Forms.TextBox; $txtPx.Text = "7890"
$txtPx.Location = [Drawing.Point]::new(136,56); $txtPx.Size = [Drawing.Size]::new(60,22)
$txtPx.BackColor = $cInput; $txtPx.ForeColor = $cText; $txtPx.BorderStyle = "FixedSingle"
$pWiz.Controls.Add($txtPx)
$lPN = New-Object Windows.Forms.Label
$lPN.Text = "(0 = no proxy, e.g. overseas server without VPN)"
$lPN.ForeColor = $cDim; $lPN.Location = [Drawing.Point]::new(204,58)
$lPN.Size = [Drawing.Size]::new(305,22); $pWiz.Controls.Add($lPN)
$btnGen = New-Object Windows.Forms.Button
$btnGen.Text = "Generate and Deploy"
$btnGen.Location = [Drawing.Point]::new(14,84); $btnGen.Size = [Drawing.Size]::new(180,28)
$btnGen.FlatStyle = "Flat"; $btnGen.FlatAppearance.BorderSize = 0
$btnGen.BackColor = $cGreen; $btnGen.ForeColor = [Drawing.Color]::White
$btnGen.Font = [Drawing.Font]::new("Segoe UI",9,[Drawing.FontStyle]::Bold)
$btnGen.Cursor = "Hand"; $pWiz.Controls.Add($btnGen)

# Quick actions
function MkBtn($t,$x,$y,$w,$col){
    $b=New-Object Windows.Forms.Button; $b.Text=$t
    $b.Location=[Drawing.Point]::new($x,$y); $b.Size=[Drawing.Size]::new($w,34)
    $b.FlatStyle="Flat"; $b.FlatAppearance.BorderSize=0; $b.BackColor=$col
    $b.ForeColor=[Drawing.Color]::White
    $b.Font=[Drawing.Font]::new("Segoe UI",8,[Drawing.FontStyle]::Bold)
    $b.Cursor="Hand"; $form.Controls.Add($b); return $b
}
$btnOpen    = MkBtn "Management Panel"  20  346  168  ([Drawing.Color]::FromArgb(44,82,130))
$btnStart   = MkBtn "Start Service"    194  346  118  ([Drawing.Color]::FromArgb(35,105,55))
$btnStop    = MkBtn "Stop"             318  346   74  ([Drawing.Color]::FromArgb(100,30,30))
$btnLogs    = MkBtn "Live Logs"        398  346  136  ([Drawing.Color]::FromArgb(55,40,80))
$btnUpdate  = MkBtn "Update Image"      20  386  175  ([Drawing.Color]::FromArgb(45,45,75))
$btnRestart = MkBtn "Restart Service"  200  386  155  ([Drawing.Color]::FromArgb(70,60,20))

# API bar
$pApi = New-Object Windows.Forms.Panel
$pApi.Location = [Drawing.Point]::new(20,430); $pApi.Size = [Drawing.Size]::new(514,32)
$pApi.BackColor = $cPanel; $form.Controls.Add($pApi)
$lApi = New-Object Windows.Forms.Label; $lApi.Text = "API: $apiUrl"
$lApi.ForeColor = $cDim; $lApi.Location = [Drawing.Point]::new(10,8)
$lApi.Size = [Drawing.Size]::new(370,18); $pApi.Controls.Add($lApi)
$btnCopy = New-Object Windows.Forms.Button; $btnCopy.Text = "Copy URL"
$btnCopy.Location = [Drawing.Point]::new(390,3); $btnCopy.Size = [Drawing.Size]::new(116,26)
$btnCopy.FlatStyle = "Flat"; $btnCopy.FlatAppearance.BorderSize = 1
$btnCopy.FlatAppearance.BorderColor = [Drawing.Color]::FromArgb(50,50,70)
$btnCopy.BackColor = $cPanel; $btnCopy.ForeColor = $cDim
$btnCopy.Font = [Drawing.Font]::new("Segoe UI",8); $btnCopy.Cursor = "Hand"
$pApi.Controls.Add($btnCopy)

# Log
$lLog = New-Object Windows.Forms.Label; $lLog.Text = "Log"
$lLog.ForeColor = $cDim; $lLog.Location = [Drawing.Point]::new(20,470)
$lLog.Size = [Drawing.Size]::new(50,18); $form.Controls.Add($lLog)
$btnClr = New-Object Windows.Forms.Button; $btnClr.Text = "Clear"
$btnClr.Location = [Drawing.Point]::new(464,466); $btnClr.Size = [Drawing.Size]::new(70,22)
$btnClr.FlatStyle = "Flat"; $btnClr.FlatAppearance.BorderSize = 0
$btnClr.BackColor = $cPanel; $btnClr.ForeColor = $cDim
$btnClr.Font = [Drawing.Font]::new("Segoe UI",8); $btnClr.Cursor = "Hand"
$form.Controls.Add($btnClr)
$txt = New-Object Windows.Forms.RichTextBox
$txt.Location = [Drawing.Point]::new(20,490); $txt.Size = [Drawing.Size]::new(514,166)
$txt.BackColor = [Drawing.Color]::FromArgb(10,10,14); $txt.ForeColor = $cText
$txt.Font = [Drawing.Font]::new("Consolas",8.5); $txt.ReadOnly = $true
$txt.BorderStyle = "None"; $txt.ScrollBars = "Vertical"; $form.Controls.Add($txt)

function Log($m,$c="LightGray"){
    $txt.SelectionStart=$txt.TextLength; $txt.SelectionLength=0
    $txt.SelectionColor=[Drawing.Color]::$c
    $txt.AppendText("[$(Get-Date -f HH:mm:ss)] $m`n"); $txt.ScrollToCaret()}
function LogD($lines){ foreach($l in $lines){$l="$l".Trim();if(!$l){continue}
    if($l -match "error|fail|fatal"){Log $l Salmon}elseif($l -match "warn"){Log $l Gold}else{Log $l LightGray}}}
function TestD{ docker info 2>$null|Out-Null; $LASTEXITCODE -eq 0 }
function GetSt{ (docker inspect --format "{{.State.Status}}" $container 2>$null).Trim() }
function RandHex{ $b=New-Object byte[] 16;[Security.Cryptography.RandomNumberGenerator]::Fill($b);-join($b|%{"{0:x2}" -f $_}) }
function RandPwd{ $c="ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789";$b=New-Object byte[] 20;[Security.Cryptography.RandomNumberGenerator]::Fill($b);-join($b|%{$c[$_ % $c.Length]}) }
function EnsureDirs{ @("auths","logs","plugins")|%{$p=Join-Path $scriptDir $_;if(!(Test-Path $p)){New-Item -Type Directory $p|Out-Null;Log "Created: $_" Cyan}} }
function RunC($a,$lbl){ Log "$lbl..." Cyan;$form.Enabled=$false;Set-Location $scriptDir;$o=& docker compose @a 2>&1;LogD $o;Start-Sleep -ms 1000;UpdUI;$form.Enabled=$true }

function UpdUI{
    # Step 1: Docker
    if(TestD){
        $s1.dot.ForeColor=$cGreen; $s1.stat.Text="Running"; $s1.stat.ForeColor=$cGreen
        $s1.btn.Visible=$false
    } else {
        $s1.dot.ForeColor=$cOrange; $s1.stat.Text="Not running"; $s1.stat.ForeColor=$cOrange
        $s1.btn.Text="Start Docker"; $s1.btn.BackColor=$cOrange; $s1.btn.Visible=$true
    }
    # Step 2: Config
    if(Test-Path $cfgPath){
        $s2.dot.ForeColor=$cGreen; $s2.stat.Text="Ready"; $s2.stat.ForeColor=$cGreen
        $s2.btn.Visible=$false; $pWiz.Visible=$false
    } else {
        $s2.dot.ForeColor=$cOrange; $s2.stat.Text="Not configured"; $s2.stat.ForeColor=$cOrange
        $s2.btn.Text="Setup"; $s2.btn.BackColor=$cBlue; $s2.btn.Visible=$true
    }
    # Step 3: Service
    switch(GetSt){
        "running"{ $s3.dot.ForeColor=$cGreen;$s3.stat.Text="Running";$s3.stat.ForeColor=$cGreen;$s3.btn.Visible=$false }
        {$_ -in "exited","created"}{ $s3.dot.ForeColor=$cRed;$s3.stat.Text="Stopped";$s3.stat.ForeColor=$cRed;$s3.btn.Text="Start";$s3.btn.BackColor=$cGreen;$s3.btn.Visible=$true }
        default{ $s3.dot.ForeColor=$cDim;$s3.stat.Text="Not deployed";$s3.stat.ForeColor=$cDim;$s3.btn.Text="Deploy";$s3.btn.BackColor=$cBlue;$s3.btn.Visible=$true }
    }
}

# Step button actions
$s1.btn.Add_Click({
    Log "Starting Docker Desktop..." Cyan
    $exe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if(!(Test-Path $exe)){$exe=(Get-ChildItem "C:\Program Files\Docker" -Recurse -Filter "Docker Desktop.exe" -EA SilentlyContinue|Select -First 1).FullName}
    if(!$exe){Log "Cannot find Docker Desktop" Salmon;return}
    Start-Process $exe
    Log "Waiting for Docker to start (up to 60s)..." Gold
    $form.Enabled=$false
    $wt=New-Object Windows.Forms.Timer;$wt.Interval=3000
    $wt.Add_Tick({if(TestD){$wt.Stop();$form.Enabled=$true;Log "Docker ready!" LimeGreen;UpdUI}else{Log "Waiting..." DimGray}})
    $wt.Start()
})
$s2.btn.Add_Click({ $pWiz.Visible=$true })
$s3.btn.Add_Click({
    if(!(TestD)){Log "Start Docker first" Salmon;return}
    if(!(Test-Path $cfgPath)){Log "Create config first" Salmon;$pWiz.Visible=$true;return}
    EnsureDirs; RunC @("up","-d","--pull","never") "Starting service"
    if((GetSt) -eq "running"){Start-Process $mgmtUrl}
})

# Generate button
$btnGen.Add_Click({
    if(!(TestD)){Log "Start Docker first" Salmon;return}
    $px=$txtPx.Text.Trim(); $k1="sk-$(RandHex)"; $k2="sk-$(RandHex)"; $pw=RandPwd
    $nl=[Environment]::NewLine
    $cfg=@("config-version: 8","host: 0.0.0.0","port: $port","access:","  api-keys:",
           "    - $k1","    - $k2","oauth:","  auth-dir: /root/.cli-proxy-api",
           "routing:","  strategy: round-robin","remote-management:",
           "  allow-remote: true","  secret-key: $pw","  disable-control-panel: false") -join $nl
    [IO.File]::WriteAllText($cfgPath,$cfg+$nl,[Text.UTF8Encoding]::new($false))
    if($px -and $px -ne "0"){
        $cmp=Get-Content $cmpPath -Raw
        if($cmp -notmatch "HTTP_PROXY"){
            $ev="    environment:$nl      - HTTP_PROXY=http://host.docker.internal:$px$nl      - HTTPS_PROXY=http://host.docker.internal:$px$nl      - NO_PROXY=localhost,127.0.0.1$nl"
            [IO.File]::WriteAllText($cmpPath,$cmp.Replace("    restart:",$ev+"    restart:"),[Text.UTF8Encoding]::new($false))
        }
    }
    Log "" LightGray; Log "=== Save these credentials ===" Gold
    Log "API Key 1:     $k1" LimeGreen
    Log "API Key 2:     $k2" LimeGreen
    Log "Mgmt password: $pw" LimeGreen
    Log "Mgmt URL:      $mgmtUrl" Cyan
    EnsureDirs; UpdUI
    RunC @("pull") "Pulling latest image"
    RunC @("up","-d","--pull","never") "Starting service"
    Log "All done!" LimeGreen
    if((GetSt) -eq "running"){Start-Process $mgmtUrl}
})

$btnOpen.Add_Click({Start-Process $mgmtUrl})
$btnStart.Add_Click({if(!(TestD)){Log "Docker not running" Salmon;return};EnsureDirs;RunC @("up","-d","--pull","never") "Starting"})
$btnStop.Add_Click({RunC @("down") "Stopping"})
$btnRestart.Add_Click({if(!(TestD)){Log "Docker not running" Salmon;return};RunC @("restart") "Restarting"})
$btnUpdate.Add_Click({if(!(TestD)){Log "Docker not running" Salmon;return};RunC @("pull") "Pulling";RunC @("up","-d","--pull","never") "Restarting";Log "Updated" LimeGreen})
$btnLogs.Add_Click({if((GetSt) -ne "running"){Log "Service not running" Salmon;return};Start-Process powershell -ArgumentList "-NoExit","-Command","cd `"$scriptDir`"; docker compose logs -f"})
$btnCopy.Add_Click({[Windows.Forms.Clipboard]::SetText($apiUrl);$btnCopy.Text="Copied!";$t=New-Object Windows.Forms.Timer;$t.Interval=1500;$t.Add_Tick({$btnCopy.Text="Copy URL";$t.Stop()});$t.Start()})
$btnClr.Add_Click({$txt.Clear()})

$ar=New-Object Windows.Forms.Timer;$ar.Interval=8000;$ar.Add_Tick({UpdUI})
$form.Add_Shown({
    UpdUI
    if(!(Test-Path $cfgPath)){Log "Welcome! Complete the 3 steps above to get started." Gold}
    elseif((GetSt) -eq "running"){LogD(docker logs --tail 12 $container 2>&1)}
    $ar.Start()
})
$form.Add_FormClosed({$ar.Stop()})
[void]$form.ShowDialog()
