$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
python -m pip install -e $repo
$cmd = Get-Command zb -ErrorAction Stop
& zb --help | Out-Null
Write-Host "ZB_CONSOLE_READY = $($cmd.Source)"
