# CLIProxyAPI Bootstrap
# Usage: _bootstrap.ps1 -Dir <path> -Script <client.py|launcher.py>
param(
    [string]$Dir    = $PSScriptRoot,
    [string]$Script = "launcher.py"
)
$Dir = $Dir.TrimEnd([char]\'\', [char]\'/\')

function Find-Python {
    # 0. Bundled Python Embeddable (offline_deps\python-embed)
    $embed = Join-Path $Dir "offline_deps\python-embed\python.exe"
    if ((Test-Path $embed) -and (Get-Item $embed).Length -gt 10KB) { return $embed }

    # 1. PATH: py launcher, python, python3
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

function Setup-EmbedPython {
    # Detect architecture
    $arch = if ([Environment]::Is64BitOperatingSystem) { "amd64" } else { "win32" }
    $ver = "3.12.7"
    $url = "https://www.python.org/ftp/python/$ver/python-$ver-embed-$arch.zip"
    $embedDir = Join-Path $Dir "offline_deps\python-embed"
    $zip = Join-Path $env:TEMP "python-embed.zip"
    Write-Host "Downloading Python Embeddable (~10MB) for $arch..."
    try {
        (New-Object Net.WebClient).DownloadFile($url, $zip)
        if ((Get-Item $zip).Length -lt 1MB) { throw "Download incomplete" }
        Expand-Archive $zip -DestinationPath $embedDir -Force
        # Validate extraction
        $pyExe = Join-Path $embedDir "python.exe"
        if (-not (Test-Path $pyExe) -or (Get-Item $pyExe).Length -lt 10KB) {
            throw "python.exe missing or corrupt"
        }
        # Enable pip (uncomment import site in ._pth)
        $pth = Get-ChildItem $embedDir -Filter "*._pth" | Select-Object -First 1
        if ($pth) {
            (Get-Content $pth.FullName) -replace "^#import site","import site" |
                Set-Content $pth.FullName -Encoding UTF8
        }
        # Install pip
        $getpip = Join-Path $env:TEMP "get-pip.py"
        (New-Object Net.WebClient).DownloadFile("https://bootstrap.pypa.io/get-pip.py", $getpip)
        & $pyExe $getpip -q 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
        # Install customtkinter
        & $pyExe -m pip install customtkinter -q 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "customtkinter install failed" }
        Write-Host "Python Embeddable ready: $pyExe"
        return $pyExe
    } catch {
        Write-Host "Embeddable setup failed: $_"
        if (Test-Path $embedDir) { Remove-Item $embedDir -Recurse -Force -EA SilentlyContinue }
        return $null
    }
}

function Install-PythonWinget {
    if (-not (Get-Command winget -EA SilentlyContinue)) { return $false }
    Write-Host "Installing Python via winget..."
    winget install Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements | Out-Null
    return $true
}

function Install-Customtkinter($pyExe) {
    $wheels = Join-Path $Dir "offline_deps\wheels"
    if (Test-Path $wheels) {
        & $pyExe -m pip install customtkinter --find-links $wheels --no-index -q 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { Write-Host "customtkinter: installed from cache"; return }
    }
    & $pyExe -m pip install customtkinter -q 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "WARNING: customtkinter install failed - GUI may not start" }
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

if (-not $py) {
    # Try offline installer first
    $offInst = Join-Path $Dir "offline_deps\python-3.12-installer.exe"
    if (Test-Path $offInst) {
        Write-Host "Installing Python from offline package..."
        Start-Process $offInst -ArgumentList "/quiet","InstallAllUsers=0","PrependPath=1" -Wait
        $py = Find-Python
    }
}

if (-not $py) {
    # Try to download Python Embeddable (no install needed)
    $py = Setup-EmbedPython
}

if (-not $py) {
    Install-PythonWinget | Out-Null
    $py = Find-Python
}

if ($py) {
    Write-Host "Python: $py"
    Install-Customtkinter $py
    $pyw    = Get-PythonW $py
    $script = Join-Path $Dir $Script
    Start-Process $pyw -ArgumentList "`"$script`""
} else {
    Write-Host "ERROR: Could not find or install Python."
    Write-Host "Please download Python from https://python.org and re-run."
    Read-Host "Press Enter to exit"
}
