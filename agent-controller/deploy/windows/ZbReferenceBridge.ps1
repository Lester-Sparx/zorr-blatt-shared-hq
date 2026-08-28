[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Install","Uninstall","Status","Start","Stop","Restart","Enable","Disable")]
    [string]$Action,
    [string]$ConfigPath,
    [string]$WorkingDirectory,
    [string]$PythonExe
)

$ErrorActionPreference = "Stop"
$TaskName = "ZB Reference Bridge v1"
$DefaultRuntimeRoot = "D:\BLATT2\ZB_AGENT_RUNTIME\reference-bridge"
$DefaultPollIntervalSeconds = 5.0
$ExpectedHealthSchema = "zb-reference-bridge-v1"
$AllowedHealthStates = @("STARTING","HEALTHY","DEGRADED","FATAL","STOPPING","MISSING","STALE")

function Resolve-ExistingFile([string]$PathValue, [string]$Code) {
    if ([string]::IsNullOrWhiteSpace($PathValue)) { throw $Code }
    $item = Get-Item -LiteralPath $PathValue -ErrorAction Stop
    if ($item.PSIsContainer) { throw $Code }
    return $item.FullName
}
function Resolve-ExistingDirectory([string]$PathValue, [string]$Code) {
    if ([string]::IsNullOrWhiteSpace($PathValue)) { throw $Code }
    $item = Get-Item -LiteralPath $PathValue -ErrorAction Stop
    if (-not $item.PSIsContainer) { throw $Code }
    return $item.FullName
}
function Resolve-Python([string]$PathValue) {
    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        $command = Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1
        return (Resolve-ExistingFile $command.Source "PYTHON_EXE_INVALID")
    }
    return (Resolve-ExistingFile $PathValue "PYTHON_EXE_INVALID")
}
function Get-CanonicalTask { return Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue }
function Require-Task {
    $task = Get-CanonicalTask
    if ($null -eq $task) { throw "REFERENCE_BRIDGE_TASK_NOT_INSTALLED" }
    return $task
}
function Stop-CanonicalTaskBounded {
    $task = Get-CanonicalTask
    if ($null -eq $task) { return }
    if ([string]$task.State -eq "Running") {
        Stop-ScheduledTask -TaskName $TaskName
        $deadline = [DateTime]::UtcNow.AddSeconds(30)
        do {
            Start-Sleep -Milliseconds 250
            $task = Get-CanonicalTask
            if ($null -eq $task -or [string]$task.State -ne "Running") { return }
        } while ([DateTime]::UtcNow -lt $deadline)
        throw "REFERENCE_BRIDGE_TASK_STOP_TIMEOUT"
    }
}
function Get-StatusConfig([string]$PathValue) {
    $runtimeRoot = $DefaultRuntimeRoot
    $poll = $DefaultPollIntervalSeconds
    if (-not [string]::IsNullOrWhiteSpace($PathValue)) {
        $resolved = Resolve-ExistingFile $PathValue "CONFIG_PATH_INVALID"
        $raw = Get-Content -LiteralPath $resolved -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($null -ne $raw.runtimeRoot -and -not [string]::IsNullOrWhiteSpace([string]$raw.runtimeRoot)) { $runtimeRoot = [string]$raw.runtimeRoot }
        if ($null -ne $raw.pollIntervalSeconds) { $poll = [double]$raw.pollIntervalSeconds }
    }
    return @{ RuntimeRoot = $runtimeRoot; PollIntervalSeconds = $poll }
}
function Write-BridgeStatus([string]$PathValue) {
    $task = Get-CanonicalTask
    $registered = "NO"; $enabled = "NO"; $taskState = "MISSING"
    if ($null -ne $task) {
        $registered = "YES"
        $enabled = if ([string]$task.State -eq "Disabled") { "NO" } else { "YES" }
        $taskState = [string]$task.State
    }
    $statusConfig = Get-StatusConfig $PathValue
    $healthPath = Join-Path ([string]$statusConfig.RuntimeRoot) "health.json"
    $healthState = "MISSING"; $pidValue = "NONE"; $pidAlive = "UNKNOWN"; $instanceId = "NONE"; $heartbeatAge = "NONE"; $configSha = "NONE"; $driveReachable = "UNKNOWN"
    if (Test-Path -LiteralPath $healthPath -PathType Leaf) {
        try {
            $health = Get-Content -LiteralPath $healthPath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ([string]$health.schema -ne $ExpectedHealthSchema) { throw "HEALTH_SCHEMA_INVALID" }
            $healthState = [string]$health.state
            if ([string]::IsNullOrWhiteSpace($healthState) -or $AllowedHealthStates -notcontains $healthState) { throw "HEALTH_STATE_INVALID" }
            if ($null -eq $health.heartbeatUtc -or [string]::IsNullOrWhiteSpace([string]$health.heartbeatUtc)) { throw "HEALTH_HEARTBEAT_INVALID" }
            $heartbeat = [DateTimeOffset]::Parse([string]$health.heartbeatUtc).ToUniversalTime()
            $age = [Math]::Max(0.0, ([DateTimeOffset]::UtcNow - $heartbeat).TotalSeconds)
            $heartbeatAge = [Math]::Round($age, 1).ToString([Globalization.CultureInfo]::InvariantCulture)
            $threshold = [Math]::Max(60.0, 3.0 * [double]$statusConfig.PollIntervalSeconds)
            if ($age -gt $threshold) { $healthState = "STALE" }
            if ($null -ne $health.pid) {
                $pidValue = [string][int]$health.pid
                $process = Get-Process -Id ([int]$health.pid) -ErrorAction SilentlyContinue
                $pidAlive = if ($null -ne $process) { "YES" } else { "NO" }
            }
            if (-not [string]::IsNullOrWhiteSpace([string]$health.instanceId)) { $instanceId = [string]$health.instanceId }
            if (-not [string]::IsNullOrWhiteSpace([string]$health.configSha256)) { $configSha = [string]$health.configSha256 }
            if ($health.driveRootReachable -is [bool]) { $driveReachable = if ([bool]$health.driveRootReachable) { "YES" } else { "NO" } } else { throw "HEALTH_DRIVE_INVALID" }
        } catch {
            $healthState = "MISSING"; $pidValue = "NONE"; $pidAlive = "UNKNOWN"; $instanceId = "NONE"; $heartbeatAge = "NONE"; $configSha = "NONE"; $driveReachable = "UNKNOWN"
        }
    }
    Write-Output "ZB_REFERENCE_BRIDGE_STATUS_V1"
    Write-Output "TASK_REGISTERED = $registered"
    Write-Output "TASK_ENABLED = $enabled"
    Write-Output "TASK_STATE = $taskState"
    Write-Output "HEALTH_STATE = $healthState"
    Write-Output "PID = $pidValue"
    Write-Output "PID_ALIVE = $pidAlive"
    Write-Output "INSTANCE_ID = $instanceId"
    Write-Output "HEARTBEAT_AGE_SEC = $heartbeatAge"
    Write-Output "CONFIG_SHA256 = $configSha"
    Write-Output "DRIVE_ROOT_REACHABLE = $driveReachable"
}

switch ($Action) {
    "Install" {
        $ConfigPath = Resolve-ExistingFile $ConfigPath "CONFIG_PATH_INVALID"
        $WorkingDirectory = Resolve-ExistingDirectory $WorkingDirectory "WORKING_DIRECTORY_INVALID"
        $PythonExe = Resolve-Python $PythonExe
        Push-Location $WorkingDirectory
        try {
            & $PythonExe -m zb_reference_bridge --preflight --config $ConfigPath
            if ($LASTEXITCODE -ne 0) { throw "REFERENCE_BRIDGE_PREFLIGHT_FAILED" }
        } finally { Pop-Location }
        $Arguments = '-m zb_reference_bridge --daemon --config "' + $ConfigPath + '"'
        $TaskAction = New-ScheduledTaskAction -Execute $PythonExe -Argument $Arguments -WorkingDirectory $WorkingDirectory
        $TaskTrigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
        $UserId = if ($env:USERDOMAIN) { "$env:USERDOMAIN\$env:USERNAME" } else { $env:USERNAME }
        $Principal = New-ScheduledTaskPrincipal -UserId $UserId -LogonType Interactive -RunLevel Limited
        $Settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
        $Task = New-ScheduledTask -Action $TaskAction -Trigger $TaskTrigger -Principal $Principal -Settings $Settings
        Register-ScheduledTask -TaskName $TaskName -InputObject $Task -Force | Out-Null
        Start-ScheduledTask -TaskName $TaskName
        Write-Output "ZB_REFERENCE_BRIDGE_INSTALL PASS"
    }
    "Uninstall" { Stop-CanonicalTaskBounded; if ($null -ne (Get-CanonicalTask)) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false }; Write-Output "ZB_REFERENCE_BRIDGE_UNINSTALL PASS" }
    "Status" { Write-BridgeStatus $ConfigPath }
    "Start" { $null = Require-Task; Start-ScheduledTask -TaskName $TaskName }
    "Stop" { $null = Require-Task; Stop-CanonicalTaskBounded }
    "Restart" { $null = Require-Task; Stop-CanonicalTaskBounded; Start-ScheduledTask -TaskName $TaskName }
    "Enable" { $null = Require-Task; Enable-ScheduledTask -TaskName $TaskName | Out-Null }
    "Disable" { $null = Require-Task; Disable-ScheduledTask -TaskName $TaskName | Out-Null }
}
