Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

 = Split-Path -Parent .MyCommand.Path
 = "cli-proxy-api"
   = "http://localhost:8317/management.html"
    = "http://localhost:8317/v1"

$cBg=[ Drawing.Color]::FromArgb(15,15,20);$cPanel=[Drawing.Color]::FromArgb(26,26,36)
$cBlue=[Drawing.Color]::FromArgb(56,139,253);$cGreen=[Drawing.Color]::FromArgb(63,185,80)
$cRed=[Drawing.Color]::FromArgb(218,54,51);$cOrange=[Drawing.Color]::FromArgb(210,140,40)
$cText=[Drawing.Color]::FromArgb(220,220,230);$cDim=[Drawing.Color]::FromArgb(100,100,120)

$form=New-Object Windows.Forms.Form
$form.Text="CLIProxyAPI Launcher";$form.Size=[Drawing.Size]::new(560,560)
$form.StartPosition="CenterScreen";$form.FormBorderStyle="FixedSingle"
$form.MaximizeBox=$false;$form.BackColor=$cBg;$form.ForeColor=$cText
$form.Font=[Drawing.Font]::new("Segoe UI",9)

# Title
$lbTitle=New-Object Windows.Forms.Label;$lbTitle.Text="CLIProxyAPI"
$lbTitle.Font=[Drawing.Font]::new("Segoe UI",18,[Drawing.FontStyle]::Bold)
$lbTitle.ForeColor=$cBlue;$lbTitle.Location=[Drawing.Point]::new(20,14)
$lbTitle.Size=[Drawing.Size]::new(320,38);$form.Controls.Add($lbTitle)
$lbSub=New-Object Windows.Forms.Label;$lbSub.Text="One-Click Deployment Manager"
$lbSub.ForeColor=$cDim;$lbSub.Location=[Drawing.Point]::new(23,52)
$lbSub.Size=[Drawing.Size]::new(300,18);$form.Controls.Add($lbSub)

# Status panel
$pSt=New-Object Windows.Forms.Panel;$pSt.Location=[Drawing.Point]::new(20,82)
$pSt.Size=[Drawing.Size]::new(510,68);$pSt.BackColor=$cPanel;$form.Controls.Add($pSt)
$dot=New-Object Windows.Forms.Label;$dot.Text=[char]0x25CF
$dot.Font=[Drawing.Font]::new("Segoe UI",20);$dot.ForeColor=$cDim
$dot.Location=[Drawing.Point]::new(14,12);$dot.Size=[Drawing.Size]::new(32,38);$pSt.Controls.Add($dot)
$lblSt=New-Object Windows.Forms.Label;$lblSt.Text="Checking..."
$lblSt.Font=[Drawing.Font]::new("Segoe UI",12,[Drawing.FontStyle]::Bold);$lblSt.ForeColor=$cDim
$lblSt.Location=[Drawing.Point]::new(52,10);$lblSt.Size=[Drawing.Size]::new(200,26);$pSt.Controls.Add($lblSt)
$lblDk=New-Object Windows.Forms.Label;$lblDk.Text="Docker: checking...";$lblDk.ForeColor=$cDim
$lblDk.Location=[Drawing.Point]::new(52,36);$lblDk.Size=[Drawing.Size]::new(440,18);$pSt.Controls.Add($lblDk)

# Buttons helper
function New-Btn($text,$x,$y,$w,$color){
    $b=New-Object Windows.Forms.Button;$b.Text=$text
    $b.Location=[Drawing.Point]::new($x,$y);$b.Size=[Drawing.Size]::new($w,38)
    $b.FlatStyle="Flat";$b.FlatAppearance.BorderSize=0;$b.BackColor=$color
    $b.ForeColor=[Drawing.Color]::White
    $b.Font=[Drawing.Font]::new("Segoe UI",9,[Drawing.FontStyle]::Bold)
    $b.Cursor="Hand";$form.Controls.Add($b);return $b
}

$btnA=New-Btn "Start Service"        20  162 155 ([Drawing.Color]::FromArgb(35,105,55))
$btnB=New-Btn "Stop Service"        182  162 155 ([Drawing.Color]::FromArgb(130,35,35))
$btnC=New-Btn "Restart Service"     344  162 186 ([Drawing.Color]::FromArgb(70,60,20))
$btnD=New-Btn "Deploy (first time)"  20  208 230 $cBlue
$btnE=New-Btn "Pull Latest Image"   258  208 180 ([Drawing.Color]::FromArgb(50,50,80))
$btnF=New-Btn "Management Panel"    444  208  86 ([Drawing.Color]::FromArgb(44,82,130))

# API copy bar
$pC=New-Object Windows.Forms.Panel;$pC.Location=[Drawing.Point]::new(20,258)
$pC.Size=[Drawing.Size]::new(510,36);$pC.BackColor=$cPanel;$form.Controls.Add($pC)
$lA=New-Object Windows.Forms.Label;$lA.Text="API: $apiUrl";$lA.ForeColor=$cDim
$lA.Location=[Drawing.Point]::new(10,10);$lA.Size=[Drawing.Size]::new(380,18);$pC.Controls.Add($lA)
$btnCP=New-Object Windows.Forms.Button;$btnCP.Text="Copy URL"
$btnCP.Location=[Drawing.Point]::new(400,5);$btnCP.Size=[Drawing.Size]::new(102,26)
$btnCP.FlatStyle="Flat";$btnCP.FlatAppearance.BorderSize=1
$btnCP.FlatAppearance.BorderColor=[Drawing.Color]::FromArgb(45,45,60)
$btnCP.BackColor=$cPanel;$btnCP.ForeColor=$cDim
$btnCP.Font=[Drawing.Font]::new("Segoe UI",8);$btnCP.Cursor="Hand";$pC.Controls.Add($btnCP)

# Log box
$lblL=New-Object Windows.Forms.Label;$lblL.Text="Log";$lblL.ForeColor=$cDim
$lblL.Location=[Drawing.Point]::new(20,304);$lblL.Size=[Drawing.Size]::new(60,18);$form.Controls.Add($lblL)
$btnCL=New-Object Windows.Forms.Button;$btnCL.Text="Clear"
$btnCL.Location=[Drawing.Point]::new(462,300);$btnCL.Size=[Drawing.Size]::new(68,22)
$btnCL.FlatStyle="Flat";$btnCL.FlatAppearance.BorderSize=0;$btnCL.BackColor=$cPanel
$btnCL.ForeColor=$cDim;$btnCL.Font=[Drawing.Font]::new("Segoe UI",8);$btnCL.Cursor="Hand"
$form.Controls.Add($btnCL)
$txt=New-Object Windows.Forms.RichTextBox
$txt.Location=[Drawing.Point]::new(20,324);$txt.Size=[Drawing.Size]::new(510,174)
$txt.BackColor=[Drawing.Color]::FromArgb(10,10,14);$txt.ForeColor=$cText
$txt.Font=[Drawing.Font]::new("Consolas",8.5);$txt.ReadOnly=$true
$txt.BorderStyle="None";$txt.ScrollBars="Vertical";$form.Controls.Add($txt)

# Helper functions
function Log($m,$c="LightGray"){
    $txt.SelectionStart=$txt.TextLength;$txt.SelectionLength=0
    $txt.SelectionColor=[Drawing.Color]::$c
    $txt.AppendText("[$(Get-Date -f HH:mm:ss)] $m`n");$txt.ScrollToCaret()
}
function LogD($lines){
    foreach($l in $lines){$l="$l".Trim();if(!$l){continue}
        if($l -match "error|fail|fatal"){Log $l Salmon}
        elseif($l -match "warn"){Log $l Gold}
        else{Log $l LightGray}}
}
function TestD{docker info 2>$null|Out-Null;$LASTEXITCODE -eq 0}
function GetSt{(docker inspect --format "{{.State.Status}}" $container 2>$null).Trim()}
function UpdUI{
    if(!(TestD)){$dot.ForeColor=$cOrange;$lblSt.Text="Docker not running";$lblSt.ForeColor=$cOrange
        $lblDk.Text="Please start Docker Desktop";$lblDk.ForeColor=$cOrange;return}
    $lblDk.Text="Docker: running";$lblDk.ForeColor=$cGreen
    switch(GetSt){
        "running"{$dot.ForeColor=$cGreen;$lblSt.Text="Service running";$lblSt.ForeColor=$cGreen}
        {$_ -in "exited","created"}{$dot.ForeColor=$cRed;$lblSt.Text="Service stopped";$lblSt.ForeColor=$cRed}
        default{$dot.ForeColor=$cDim;$lblSt.Text="Not deployed";$lblSt.ForeColor=$cDim}
    }
}
function EnsD{
    @("auths","logs","plugins")|ForEach-Object{
        $p=Join-Path $scriptDir $_
        if(!(Test-Path $p)){New-Item -Type Directory $p|Out-Null;Log "Created: $_" Cyan}}
}
function RunC($a,$label){
    Log "$label..." Cyan;$form.Enabled=$false;Set-Location $scriptDir
    $o=& docker compose @a 2>&1;LogD $o;Start-Sleep -ms 1200;UpdUI;$form.Enabled=$true
}

# Button events
$btnA.Add_Click({if(!(TestD)){Log "Docker not running" Salmon;return};RunC @("up","-d") "Starting service"})
$btnB.Add_Click({RunC @("down") "Stopping service"})
$btnC.Add_Click({if(!(TestD)){Log "Docker not running" Salmon;return};RunC @("restart") "Restarting service"})
$btnD.Add_Click({
    if(!(TestD)){Log "Docker not running" Salmon;return}
    Log "=== Deploy start ===" Cyan;EnsD
    if(!(Test-Path(Join-Path $scriptDir "config.yaml"))){
        Log "config.yaml not found - please create it first" Salmon
        [Windows.Forms.MessageBox]::Show("Please create config.yaml first","Missing config","OK","Warning")|Out-Null;return}
    RunC @("pull") "Pulling latest image"
    RunC @("up","-d") "Starting service"
    Log "=== Deploy complete ===" LimeGreen
    Start-Process $mgmtUrl
})
$btnE.Add_Click({if(!(TestD)){Log "Docker not running" Salmon;return};RunC @("pull") "Pulling latest image"})
$btnF.Add_Click({Start-Process $mgmtUrl})
$btnCP.Add_Click({
    [Windows.Forms.Clipboard]::SetText($apiUrl);$btnCP.Text="Copied!"
    $tmr=New-Object Windows.Forms.Timer;$tmr.Interval=1500
    $tmr.Add_Tick({$btnCP.Text="Copy URL";$tmr.Stop()});$tmr.Start()
})
$btnCL.Add_Click({$txt.Clear()})

# Auto-refresh + startup
$ar=New-Object Windows.Forms.Timer;$ar.Interval=8000;$ar.Add_Tick({UpdUI})
$form.Add_Shown({
    UpdUI
    if((GetSt) -eq "running"){LogD(docker logs --tail 20 $container 2>&1)}
    $ar.Start()
})
$form.Add_FormClosed({$ar.Stop()})
[void]$form.ShowDialog()
