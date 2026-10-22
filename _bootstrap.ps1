param([string]$Dir=$PSScriptRoot, [string]$Script="launcher.py", [Parameter(ValueFromRemainingArguments=$true)][string[]]$AppArguments)
& "$PSScriptRoot\scripts\start.ps1" -Role server @AppArguments
exit $LASTEXITCODE
