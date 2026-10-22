# CLIProxyAPI Bootstrap
# Usage: _bootstrap.ps1 -Dir <path> -Script <launcher.py|launcher.py>
param(
    [string]$Dir    = $PSScriptRoot,
    [string]$Script = "launcher.py"
)
$Dir = $Dir.TrimEnd([char]92, [char]47)

function Find-Python {
    # 1. System PATH
    foreach ($cmd in @("py","python","python3")) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($found -and $found.Source) { return $found.Source }
    }
    # 2. Common install dirs
    $roots = @(
        "$env:LOCALAPPDATA\Programs\Python",
        $env:ProgramFiles,
        ${env:"ProgramFiles(x86)"},
        "C:\"
    )
    foreach ($root in $roots) {
        if (-not $root -or -not (Test-Path $root)) { continue }
        $exe = Get-ChildItem $root -Directory -EA SilentlyContinue |
            Where-Object { $_.Name -match "^[Pp]ython\d" } |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName "python.exe" } |
            Where-Object { Test-Path $_ } |
            Select-Object -First 1
        if ($exe) { return $exe }
    }
    return $null
}

function Install-FromOffline {
    # Use the full Python installer (includes tkinter/tcl/tk)
    $inst = Join-Path $Dir "offline_deps\python-3.12-installer.exe"
    if (-not (Test-Path $inst)) { return $false }
    Write-Host "Installing Python from offline package (includes tkinter)..."
    Start-Process $inst -ArgumentList "/quiet","InstallAllUsers=0","PrependPath=1" -Wait
    Start-Sleep -Seconds 2
    return $true
}

function Install-PythonWinget {
    if (-not (Get-Command winget -EA SilentlyContinue)) { return $false }
    Write-Host "Installing Python via winget..."
    winget install Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements | Out-Null
    Start-Sleep -Seconds 3
    return $true
}

function Install-Customtkinter($pyExe) {
    $wheels = Join-Path $Dir "offline_deps\wheels"
    if (Test-Path $wheels) {
        & $pyExe -m pip install customtkinter --find-links $wheels --no-index -q 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { Write-Host "customtkinter: installed from cache"; return }
    }
    & $pyExe -m pip install customtkinter -q 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "WARNING: customtkinter install may have failed" }
}

function Get-PythonW($pyExe) {
    $dir  = Split-Path $pyExe
    $name = [IO.Path]::GetFileNameWithoutExtension($pyExe)
    if ($name -eq "py") { $pyw = Join-Path $dir "pyw.exe"; if (Test-Path $pyw) { return $pyw } }
    $pyw = Join-Path $dir "pythonw.exe"
    if (Test-Path $pyw) { return $pyw }
    return $pyExe
}

# ── Main ──────────────────────────────────────────────────────────────────

$py = Find-Python

if (-not $py) { Install-FromOffline | Out-Null; $py = Find-Python }
if (-not $py) { Install-PythonWinget | Out-Null; $py = Find-Python }

if ($py) {
    Write-Host "Python: $py"
    Install-Customtkinter $py
    $pyw    = Get-PythonW $py
    $script = Join-Path $Dir $Script
    Start-Process $pyw -ArgumentList "`"$script`""
} else {
    Write-Host ""
    Write-Host "ERROR: Python not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  1. Download a pre-built executable from:"
    Write-Host "     https://github.com/GameDevTurbo/CodeXX-Client/releases" -ForegroundColor Cyan
    Write-Host "  2. Install Python from https://python.org then re-run"
    Write-Host "  3. Run prepare_offline.bat (downloads Python installer)"
    Write-Host ""
    Read-Host "Press Enter to exit"
}
