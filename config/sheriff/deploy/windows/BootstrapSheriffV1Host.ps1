[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Repository = "Lester-Sparx/zorr-blatt-shared-hq"
$DeployerCommit = "ab816ff383c74d1c72ee36df31bc381cf062f52b"
$ValidatedRuntimeCommit = "47a92fc4a0d685e1a892285c568a59dfc5ccac82"
$MinWindows10Build = 19043
$Windows11Build = 22000

$Podman5Version = "v5.8.5"
$Podman5InstallerName = "podman-installer-windows-amd64.msi"
$Podman5InstallerUrl = "https://github.com/podman-container-tools/podman/releases/download/v5.8.5/podman-installer-windows-amd64.msi"
$Podman5InstallerSha256 = "a2d78a2460dc4745684ee443ced8878fbf3a2fe4d8c620a290500e85367d2a33"

$Root = Join-Path $env:LOCALAPPDATA "ZORR\SHERIFF_V1_HOST_BOOTSTRAP"
$Deployer = Join-Path $Root "ZbSheriffV1.ps1"
$DeployerUrl = "https://raw.githubusercontent.com/$Repository/$DeployerCommit/config/sheriff/deploy/windows/ZbSheriffV1.ps1"

function Ensure-Directory([string]$PathValue) {
    if (-not (Test-Path -LiteralPath $PathValue -PathType Container)) {
        New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
    }
}

function Write-Utf8NoBom([string]$PathValue, [string]$Text) {
    $encoding = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($PathValue, $Text, $encoding)
}

function Assert-WslReady {
    $wsl = Get-Command wsl.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $wsl) {
        throw "WSL_NOT_READY"
    }

    & $wsl.Source --status *> $null
    if ($LASTEXITCODE -ne 0) {
        & $wsl.Source --list --quiet *> $null
        if ($LASTEXITCODE -ne 0) {
            throw "WSL_NOT_READY"
        }
    }
    Write-Output "WSL_STATUS = PASS"
}

function Patch-ForWindows10([string]$PathValue) {
    $raw = [IO.File]::ReadAllText($PathValue)

    if ($raw -notlike "*$ValidatedRuntimeCommit*") {
        throw "DEPLOYER_RUNTIME_PIN_MISMATCH"
    }

    $oldPins = @'
$PodmanVersion = "v6.1.0"
$PodmanInstallerName = "podman-installer-windows-amd64.msi"
$PodmanInstallerUrl = "https://github.com/podman-container-tools/podman/releases/download/v6.1.0/podman-installer-windows-amd64.msi"
$PodmanInstallerSha256 = "1958aac22abb3a9cf7b52626c71ba1a26015c323f0b5fa74671e303b22b043d3"
'@

    $newPins = @"
`$PodmanVersion = "$Podman5Version"
`$PodmanInstallerName = "$Podman5InstallerName"
`$PodmanInstallerUrl = "$Podman5InstallerUrl"
`$PodmanInstallerSha256 = "$Podman5InstallerSha256"
"@

    $oldGuard = @'
    if ([Environment]::OSVersion.Version.Build -lt 22000) {
        throw "PODMAN_V6_WINDOWS_VERSION_UNSUPPORTED"
    }
'@

    $newGuard = @'
    if ([Environment]::OSVersion.Version.Build -lt 19043) {
        throw "WINDOWS_BUILD_TOO_OLD_FOR_PODMAN5"
    }
'@

    $oldInstallArgs = '$args = "/i `"$installer`" /qn /norestart"'
    $newInstallArgs = '$args = "/i `"$installer`" /qn /norestart ALLUSERS=1 MACHINE_PROVIDER=wsl"'

    if (-not $raw.Contains($oldPins) -or -not $raw.Contains($oldGuard) -or -not $raw.Contains($oldInstallArgs)) {
        throw "DEPLOYER_PATCH_CONTRACT_MISMATCH"
    }

    $raw = $raw.Replace($oldPins, $newPins)
    $raw = $raw.Replace($oldGuard, $newGuard)
    $raw = $raw.Replace($oldInstallArgs, $newInstallArgs)
    Write-Utf8NoBom $PathValue $raw

    $patched = [IO.File]::ReadAllText($PathValue)
    if ($patched -notlike "*$Podman5Version*" -or $patched -like "*PODMAN_V6_WINDOWS_VERSION_UNSUPPORTED*") {
        throw "DEPLOYER_PATCH_VERIFY_FAILED"
    }
}

function Patch-EvidenceTransport([string]$PathValue) {
    # Physical runtime proof must not depend on a separately installed/authenticated GitHub CLI.
    # If gh is unavailable, connected ChatGPT/GitHub relays the already-written evidence file.
    $raw = [IO.File]::ReadAllText($PathValue)
    $old = @'
function Post-Evidence {
    $gh = Get-Command gh -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $gh) { throw "GH_CLI_NOT_READY" }
    & $gh.Source auth status *> $null
    if ($LASTEXITCODE -ne 0) { throw "GH_AUTH_NOT_READY" }
    & $gh.Source issue comment $ActivationIssue --repo $Repository --body-file $ResultPath *> $null
    if ($LASTEXITCODE -ne 0) { throw "GITHUB_EVIDENCE_POST_FAILED" }
}
'@
    $new = @'
function Post-Evidence {
    $gh = Get-Command gh -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $gh) {
        Write-Output "GITHUB_EVIDENCE_POST = DEFERRED_TO_CONNECTED_CHAT"
        return
    }
    & $gh.Source auth status *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Output "GITHUB_EVIDENCE_POST = DEFERRED_TO_CONNECTED_CHAT"
        return
    }
    & $gh.Source issue comment $ActivationIssue --repo $Repository --body-file $ResultPath *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Output "GITHUB_EVIDENCE_POST = DEFERRED_TO_CONNECTED_CHAT"
        return
    }
    Write-Output "GITHUB_EVIDENCE_POST = PASS"
}
'@
    if (-not $raw.Contains($old)) {
        throw "EVIDENCE_TRANSPORT_PATCH_CONTRACT_MISMATCH"
    }
    $raw = $raw.Replace($old, $new)
    Write-Utf8NoBom $PathValue $raw
    Write-Output "PHYSICAL_RUNTIME_DOES_NOT_REQUIRE_GH_CLI"
}

Ensure-Directory $Root
$build = [Environment]::OSVersion.Version.Build
Write-Output "WINDOWS_BUILD = $build"

if ($build -lt $MinWindows10Build) {
    throw "WINDOWS_BUILD_UNSUPPORTED:${build}:MIN=$MinWindows10Build"
}

Invoke-WebRequest -UseBasicParsing -Uri $DeployerUrl -OutFile $Deployer
if (-not (Test-Path -LiteralPath $Deployer -PathType Leaf)) {
    throw "DEPLOYER_DOWNLOAD_MISSING"
}

if ($build -lt $Windows11Build) {
    Assert-WslReady
    Patch-ForWindows10 $Deployer
    Write-Output "HOST_RUNTIME = PODMAN_5_8_5_WIN10"
} else {
    $raw = [IO.File]::ReadAllText($Deployer)
    if ($raw -notlike "*$ValidatedRuntimeCommit*" -or $raw -notlike "*v6.1.0*") {
        throw "DEPLOYER_WIN11_CONTRACT_MISMATCH"
    }
    Write-Output "HOST_RUNTIME = PODMAN_6_1_0_WIN11"
}

Patch-EvidenceTransport $Deployer
Write-Output "DEPLOYER_HOST_COMPAT = PASS"

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Deployer -Action Install
if ($LASTEXITCODE -ne 0) {
    throw "INSTALL_FAILED:$LASTEXITCODE"
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Deployer -Action Verify
if ($LASTEXITCODE -ne 0) {
    throw "VERIFY_FAILED:$LASTEXITCODE"
}

Write-Output "SHERIFF_V1_HOST_BOOTSTRAP = PASS"
