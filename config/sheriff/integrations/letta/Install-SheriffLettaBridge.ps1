[CmdletBinding()]
param(
    [string]$SourcePath
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($SourcePath)) {
    $SourcePath = Join-Path $PSScriptRoot "zorr-sheriff-events.ts"
}

if ([string]::IsNullOrWhiteSpace($env:MEMORY_DIR)) {
    throw "MEMORY_DIR_REQUIRED"
}
if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
    throw "SHERIFF_LETTA_BRIDGE_SOURCE_MISSING:$SourcePath"
}

$modsRoot = Join-Path $env:MEMORY_DIR "mods"
$destination = Join-Path $modsRoot "zorr-sheriff-events.ts"
New-Item -ItemType Directory -Path $modsRoot -Force | Out-Null
Copy-Item -LiteralPath $SourcePath -Destination $destination -Force

$sourceHash = (Get-FileHash -LiteralPath $SourcePath -Algorithm SHA256).Hash
$destinationHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
if ($sourceHash -ne $destinationHash) {
    throw "SHERIFF_LETTA_BRIDGE_COPY_MISMATCH"
}

Write-Output "SHERIFF_LETTA_BRIDGE_INSTALLED=$destination"
Write-Output "SHA256=$destinationHash"
Write-Output "RELOAD_REQUIRED=YES"
