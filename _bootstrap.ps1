# CLIProxyAPI Bootstrap — Find Python and launch the GUI
# Usage: _bootstrap.ps1 <launcher_dir> [launcher.py|client.py]
param(
    [string]$Dir    = $PSScriptRoot,
    [string]$Script = "launcher.py"
)

$Dir = $Dir.TrimEnd('\','/')

function Find-Python {
    # 1. Check PATH first (py launcher, python, python3)
    foreach ($cmd in @("py","python","python3")) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($found -and $found.Source) { return $found.Source }
    }

    # 2. Scan common install directories
    $roots = @(
        "$env:LOCALAPPDATA\Programs\Python",
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)},
        "C:\",
        "$env:USERPROFILE\AppData\Local\Programs\Python"
    )
    foreach ($root in $roots) {
        if (-not $root -or -not (Test-Path $root)) { continue }
        $exe = Get-ChildItem $root -Directory -ErrorAction SilentlyContinue |
            Where-Object  { $_.Name -match '^[Pp]ython\d' } |
            Sort-Object   Name -Descending |
            ForEach-Object { Join-Path $_.FullName "python.exe" } |
            Where-Object  { Test-Path $_ } |
            Select-Object -First 1
        if ($exe) { return $exe }
    }

    return $null
}

function Install-PythonViaWinget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { return $false }
    Write-Host "Python not found. Installing via winget..."
    winget install Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements | Out-Null
    Start-Sleep -Seconds 3
    return $true
}

function Install-CustomTkinter($pyExe) {
    $wheelsDir = Join-Path $Dir "offline_deps\wheels"
    if (Test-Path $wheelsDir) {
        Write-Host "Installing customtkinter from offline cache..."
        & $pyExe -m pip install customtkinter --find-links $wheelsDir --no-index -q 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { return }
        Write-Host "Offline install failed, trying network..."
    }
    & $pyExe -m pip install customtkinter -q 2>$null | Out-Null
}

function Get-PythonW($pyExe) {
    $dir = Split-Path $pyExe
    $name = [IO.Path]::GetFileNameWithoutExtension($pyExe)
    # py.exe (Launcher) → pyw.exe
    if ($name -eq "py") {
        $pyw = Join-Path $dir "pyw.exe"
        if (Test-Path $pyw) { return $pyw }
        # fallback: ask py launcher to use pythonw
        return $pyExe  # py.exe itself will do
    }
    # python.exe → pythonw.exe
    $pyw = Join-Path $dir "pythonw.exe"
    if (Test-Path $pyw) { return $pyw }
    return $pyExe
}

# ── Main ──────────────────────────────────────────────────────────────────────

$py = Find-Python

if (-not $py) {
    # Check offline_deps first
    $offlinePy = Join-Path $Dir "offline_deps\python-3.12-installer.exe"
    if (Test-Path $offlinePy) {
        Write-Host "Installing Python from offline package..."
        Start-Process $offlinePy -ArgumentList "/quiet","InstallAllUsers=0","PrependPath=1" -Wait
        $py = Find-Python
    }
}

if (-not $py) {
    Install-PythonViaWinget | Out-Null
    $py = Find-Python
}

if ($py) {
    Write-Host "Found Python: $py"
    Install-CustomTkinter $py
    $pyw    = Get-PythonW $py
    $script = Join-Path $Dir $Script
    Write-Host "Launching: $pyw `"$script`""
    # py.exe needs -3 flag or just works directly with .py files
    if ([IO.Path]::GetFileNameWithoutExtension($pyw) -in @("py","pyw")) {
        Start-Process $pyw -ArgumentList "`"$script`""
    } else {
        Start-Process $pyw -ArgumentList "`"$script`""
    }
} else {
    # Ultimate fallback: PowerShell WinForms launcher
    Write-Host "No Python found. Using PowerShell launcher..."
    $ps1 = Join-Path $Dir "launcher.ps1"
    Start-Process powershell -ArgumentList "-ExecutionPolicy","Bypass","-WindowStyle","Normal","-File","`"$ps1`""
}
