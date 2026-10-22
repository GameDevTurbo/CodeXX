param(
    [ValidateSet("client", "server")][string]$Role = "client",
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$AppArguments
)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$candidates = @()
foreach ($name in @("python", "python3", "py")) {
    $found = Get-Command $name -ErrorAction SilentlyContinue
    if ($found) { $candidates += $found.Source }
}
$candidates += @(Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
foreach ($candidate in ($candidates | Select-Object -Unique)) {
    $version = & $candidate -c "import sys; print(sys.executable) if sys.version_info >= (3,10) else sys.exit(1)" 2>$null
    if ($LASTEXITCODE -eq 0 -and $version) {
        & $version "$PSScriptRoot\launch.py" --role $Role -- @AppArguments
        exit $LASTEXITCODE
    }
}
Write-Host "Python 3.10+ was not found. Prefer the prebuilt release, or install Python with tkinter."
Write-Host "Client: https://github.com/GameDevTurbo/CodeXX-Client/releases"
Write-Host "Server: https://github.com/GameDevTurbo/CodeXX/releases"
exit 1
