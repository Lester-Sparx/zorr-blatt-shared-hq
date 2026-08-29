[CmdletBinding()]
param(
    [ValidateSet("Auto", "Resume")]
    [string]$Stage = "Auto"
)

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
$OpenSshClientCapability = "OpenSSH.Client~~~~0.0.1.0"

$Root = Join-Path $env:LOCALAPPDATA "ZORR\SHERIFF_V1_HOST_BOOTSTRAP"
$Deployer = Join-Path $Root "ZbSheriffV1.ps1"
$DeployerUrl = "https://raw.githubusercontent.com/$Repository/$DeployerCommit/config/sheriff/deploy/windows/ZbSheriffV1.ps1"
$ResumeTaskName = "ZORR SHERIFF V1 WSL Resume"
$WslRebootMarker = Join-Path $Root "wsl-reboot-requested.marker"

function Ensure-Directory([string]$PathValue) {
    if (-not (Test-Path -LiteralPath $PathValue -PathType Container)) {
        New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
    }
}

function Write-Utf8NoBom([string]$PathValue, [string]$Text) {
    $encoding = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($PathValue, $Text, $encoding)
}

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Invoke-ElevatedSelf {
    if (Test-IsAdministrator) { return }
    Write-Output "ELEVATION_REQUIRED_FOR_WSL"
    $args = '-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -Stage ' + $Stage
    $process = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $args -Wait -PassThru
    exit $process.ExitCode
}

function Test-WslCommandReady {
    $wsl = Get-Command wsl.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $wsl) { return $false }

    & $wsl.Source --status *> $null
    if ($LASTEXITCODE -eq 0) { return $true }

    & $wsl.Source --list --quiet *> $null
    return ($LASTEXITCODE -eq 0)
}

function Assert-VirtualizationFirmware {
    $processors = @(Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue)
    $signals = @($processors | ForEach-Object { $_.VirtualizationFirmwareEnabled } | Where-Object { $null -ne $_ })
    if ($signals.Count -gt 0 -and -not ($signals -contains $true)) {
        throw "CPU_VIRTUALIZATION_DISABLED_IN_FIRMWARE"
    }
    Write-Output "CPU_VIRTUALIZATION = PASS_OR_UNAVAILABLE"
}

function Register-WslResume {
    $existing = Get-ScheduledTask -TaskName $ResumeTaskName -ErrorAction SilentlyContinue
    if ($null -ne $existing) {
        Unregister-ScheduledTask -TaskName $ResumeTaskName -Confirm:$false
    }

    $arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -Stage Resume'
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments -WorkingDirectory $Root
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    $userId = if ($env:USERDOMAIN) { "$env:USERDOMAIN\$env:USERNAME" } else { $env:USERNAME }
    $principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero)
    $task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings
    Register-ScheduledTask -TaskName $ResumeTaskName -InputObject $task -Force | Out-Null
    Write-Output "WSL_RESUME_TASK = REGISTERED"
}

function Unregister-WslResume {
    $existing = Get-ScheduledTask -TaskName $ResumeTaskName -ErrorAction SilentlyContinue
    if ($null -ne $existing) {
        Unregister-ScheduledTask -TaskName $ResumeTaskName -Confirm:$false
    }
}

function Enable-WslFeature([string]$FeatureName) {
    $feature = Get-WindowsOptionalFeature -Online -FeatureName $FeatureName -ErrorAction Stop
    if ([string]$feature.State -eq "Enabled") { return $false }

    $result = Enable-WindowsOptionalFeature -Online -FeatureName $FeatureName -All -NoRestart -ErrorAction Stop
    if ([string]$result.State -ne "Enabled" -and -not $result.RestartNeeded) {
        throw "WINDOWS_FEATURE_ENABLE_FAILED:$FeatureName"
    }
    return $true
}

function Ensure-WslReady {
    if (Test-WslCommandReady) {
        Write-Output "WSL_STATUS = PASS"
        return
    }

    Invoke-ElevatedSelf
    Assert-VirtualizationFirmware

    $changed = $false
    if (Enable-WslFeature "Microsoft-Windows-Subsystem-Linux") { $changed = $true }
    if (Enable-WslFeature "VirtualMachinePlatform") { $changed = $true }

    $wsl = Get-Command wsl.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $wsl) {
        & $wsl.Source --install --no-distribution
        $installExit = $LASTEXITCODE
        Write-Output "WSL_INSTALL_EXIT = $installExit"
    }

    if ($changed -and $Stage -eq "Auto" -and -not (Test-Path -LiteralPath $WslRebootMarker)) {
        Register-WslResume
        Set-Content -LiteralPath $WslRebootMarker -Value ([DateTime]::UtcNow.ToString("o")) -Encoding ASCII
        Write-Output "WSL_REBOOT_SCHEDULED = YES"
        Write-Output "WINDOWS_WILL_RESTART_IN_30_SECONDS"
        & shutdown.exe /r /t 30 /c "ZORR SHERIFF: WSL2 enabled. Installation resumes automatically after sign-in."
        exit 3010
    }

    if ($Stage -eq "Resume") {
        Write-Output "WSL_RESUME_STAGE = ACTIVE"
    }

    $wsl = Get-Command wsl.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $wsl) {
        throw "WSL_NOT_READY_AFTER_REPAIR"
    }

    & $wsl.Source --update --web-download *> $null
    if ($LASTEXITCODE -ne 0) {
        & $wsl.Source --update *> $null
    }

    & $wsl.Source --set-default-version 2 *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "WSL2_DEFAULT_VERSION_FAILED"
    }

    if (-not (Test-WslCommandReady)) {
        throw "WSL_NOT_READY_AFTER_REPAIR"
    }

    Unregister-WslResume
    Write-Output "WSL_STATUS = PASS"
}

function Ensure-OpenSshClient {
    $sshDir = Join-Path $env:WINDIR "System32\OpenSSH"
    $sshKeygenPath = Join-Path $sshDir "ssh-keygen.exe"

    $sshKeygen = Get-Command ssh-keygen.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $sshKeygen -and (Test-Path -LiteralPath $sshKeygenPath -PathType Leaf)) {
        $processPath = [Environment]::GetEnvironmentVariable("PATH", "Process")
        if (($processPath -split ';') -notcontains $sshDir) {
            [Environment]::SetEnvironmentVariable("PATH", ($processPath.TrimEnd(';') + ';' + $sshDir), "Process")
            $env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Process")
        }
        $sshKeygen = Get-Command ssh-keygen.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    }

    if ($null -eq $sshKeygen) {
        Invoke-ElevatedSelf
        $capability = Get-WindowsCapability -Online -Name $OpenSshClientCapability -ErrorAction Stop
        if ([string]$capability.State -ne "Installed") {
            Add-WindowsCapability -Online -Name $OpenSshClientCapability -ErrorAction Stop | Out-Null
        }

        if (-not (Test-Path -LiteralPath $sshKeygenPath -PathType Leaf)) {
            throw "OPENSSH_CLIENT_INSTALL_FAILED"
        }

        $processPath = [Environment]::GetEnvironmentVariable("PATH", "Process")
        if (($processPath -split ';') -notcontains $sshDir) {
            [Environment]::SetEnvironmentVariable("PATH", ($processPath.TrimEnd(';') + ';' + $sshDir), "Process")
            $env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Process")
        }

        $sshKeygen = Get-Command ssh-keygen.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -eq $sshKeygen) {
            throw "OPENSSH_CLIENT_PATH_NOT_READY"
        }
    }

    Write-Output "OPENSSH_CLIENT = PASS"
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

function Patch-PodmanMachineFirstInit([string]$PathValue) {
    $raw = [IO.File]::ReadAllText($PathValue)
    $old = @'
function Ensure-PodmanMachine([string]$PodmanExe) {
    # Reuse path: podman machine / podman compose. No custom container daemon.
    & $PodmanExe machine inspect *> $null
    if ($LASTEXITCODE -ne 0) {
        & $PodmanExe machine init
        if ($LASTEXITCODE -ne 0) { throw "PODMAN_MACHINE_INIT_FAILED" }
    }
    & $PodmanExe machine start *> $null
    if ($LASTEXITCODE -ne 0) {
        & $PodmanExe info *> $null
        if ($LASTEXITCODE -ne 0) { throw "PODMAN_MACHINE_START_FAILED" }
    }
    & $PodmanExe info *> $null
    if ($LASTEXITCODE -ne 0) { throw "PODMAN_NOT_READY" }
}
'@
    $new = @'
function Ensure-PodmanMachine([string]$PodmanExe) {
    # Windows PowerShell 5.1 turns native stderr into ErrorRecord under ErrorActionPreference=Stop.
    # Use Start-Process redirection so an expected "no machine yet" state cannot abort first install.
    function Invoke-PodmanMachineProcess([string[]]$Arguments) {
        $stdoutPath = [IO.Path]::GetTempFileName()
        $stderrPath = [IO.Path]::GetTempFileName()
        try {
            $process = Start-Process -FilePath $PodmanExe -ArgumentList $Arguments -Wait -PassThru -NoNewWindow -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
            return [pscustomobject]@{
                ExitCode = $process.ExitCode
                StdOut = [IO.File]::ReadAllText($stdoutPath)
                StdErr = [IO.File]::ReadAllText($stderrPath)
            }
        } finally {
            Remove-Item -LiteralPath $stdoutPath -Force -ErrorAction SilentlyContinue
            Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue
        }
    }

    $list = Invoke-PodmanMachineProcess @("machine", "list", "--format", "json")
    if ($list.ExitCode -ne 0) {
        throw "PODMAN_MACHINE_LIST_FAILED:$($list.StdErr.Trim())"
    }

    $machines = @()
    if (-not [string]::IsNullOrWhiteSpace($list.StdOut)) {
        try {
            $parsed = $list.StdOut | ConvertFrom-Json -ErrorAction Stop
            if ($null -ne $parsed) { $machines = @($parsed) }
        } catch {
            throw "PODMAN_MACHINE_LIST_PARSE_FAILED"
        }
    }

    $defaultMachine = $machines | Where-Object { $_.Name -eq "podman-machine-default" } | Select-Object -First 1
    if ($null -eq $defaultMachine) {
        $init = Invoke-PodmanMachineProcess @("machine", "init")
        if ($init.ExitCode -ne 0) {
            throw "PODMAN_MACHINE_INIT_FAILED:$($init.StdErr.Trim())"
        }
        Write-Output "PODMAN_MACHINE_FIRST_INIT_SAFE"
    }

    $start = Invoke-PodmanMachineProcess @("machine", "start")
    if ($start.ExitCode -ne 0) {
        $infoAfterStart = Invoke-PodmanMachineProcess @("info")
        if ($infoAfterStart.ExitCode -ne 0) {
            throw "PODMAN_MACHINE_START_FAILED:$($start.StdErr.Trim())"
        }
    }

    $info = Invoke-PodmanMachineProcess @("info")
    if ($info.ExitCode -ne 0) {
        throw "PODMAN_NOT_READY:$($info.StdErr.Trim())"
    }
}
'@

    if (-not $raw.Contains($old)) {
        throw "PODMAN_MACHINE_PATCH_CONTRACT_MISMATCH"
    }
    $raw = $raw.Replace($old, $new)
    Write-Utf8NoBom $PathValue $raw

    $patched = [IO.File]::ReadAllText($PathValue)
    if ($patched.Contains('& $PodmanExe machine inspect *> $null') -or -not $patched.Contains('machine", "list", "--format", "json')) {
        throw "PODMAN_MACHINE_PATCH_VERIFY_FAILED"
    }
    Write-Output "PODMAN_MACHINE_FIRST_INIT_PATCH = PASS"
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
Write-Output "BOOTSTRAP_STAGE = $Stage"

if ($Stage -eq "Resume") {
    Unregister-WslResume
}

if ($build -lt $MinWindows10Build) {
    throw "WINDOWS_BUILD_UNSUPPORTED:${build}:MIN=$MinWindows10Build"
}

if ($build -lt $Windows11Build) {
    Ensure-WslReady
}

Ensure-OpenSshClient

Invoke-WebRequest -UseBasicParsing -Uri $DeployerUrl -OutFile $Deployer
if (-not (Test-Path -LiteralPath $Deployer -PathType Leaf)) {
    throw "DEPLOYER_DOWNLOAD_MISSING"
}

if ($build -lt $Windows11Build) {
    Patch-ForWindows10 $Deployer
    Write-Output "HOST_RUNTIME = PODMAN_5_8_5_WIN10"
} else {
    $raw = [IO.File]::ReadAllText($Deployer)
    if ($raw -notlike "*$ValidatedRuntimeCommit*" -or $raw -notlike "*v6.1.0*") {
        throw "DEPLOYER_WIN11_CONTRACT_MISMATCH"
    }
    Write-Output "HOST_RUNTIME = PODMAN_6_1_0_WIN11"
}

Patch-PodmanMachineFirstInit $Deployer
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

Unregister-WslResume
if (Test-Path -LiteralPath $WslRebootMarker) {
    Remove-Item -LiteralPath $WslRebootMarker -Force -ErrorAction SilentlyContinue
}
Write-Output "SHERIFF_V1_HOST_BOOTSTRAP = PASS"
