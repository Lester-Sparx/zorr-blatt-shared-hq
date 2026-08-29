[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Install","Uninstall","Status","Start","Stop","Restart","Verify")]
    [string]$Action,
    [string]$RuntimeRoot
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$TaskName = "ZB Sheriff V1"
$Repository = "Lester-Sparx/zorr-blatt-shared-hq"
$ActivationIssue = 181
$ValidatedRuntimeCommit = "47a92fc4a0d685e1a892285c568a59dfc5ccac82"
$RequiredServices = @("forgejo","nats","opa","postgres","otel-collector","prometheus","loki","grafana","sheriff-worker")

# Open-code runtime pins. Podman is Apache-2.0. Docker Compose CLI is Apache-2.0.
$PodmanVersion = "v6.1.0"
$PodmanInstallerName = "podman-installer-windows-amd64.msi"
$PodmanInstallerUrl = "https://github.com/podman-container-tools/podman/releases/download/v6.1.0/podman-installer-windows-amd64.msi"
$PodmanInstallerSha256 = "1958aac22abb3a9cf7b52626c71ba1a26015c323f0b5fa74671e303b22b043d3"
$ComposeVersion = "v5.5.0"
$ComposeName = "docker-compose-windows-x86_64.exe"
$ComposeUrl = "https://github.com/docker/compose/releases/download/v5.5.0/docker-compose-windows-x86_64.exe"
$ComposeSha256 = "51e1e61195f3616896265487ed64551095f3bd27ac7fbd5758d3538c3bfa1b19"

if ([string]::IsNullOrWhiteSpace($RuntimeRoot)) {
    if (Test-Path -LiteralPath "D:\BLATT2" -PathType Container) {
        $RuntimeRoot = "D:\BLATT2\ZB_SHERIFF_V1"
    } else {
        $RuntimeRoot = Join-Path $env:LOCALAPPDATA "ZORR\ZB_SHERIFF_V1"
    }
}
$RuntimeRoot = [IO.Path]::GetFullPath($RuntimeRoot)
$ToolsRoot = Join-Path $RuntimeRoot "tools"
$SourceRoot = Join-Path $RuntimeRoot "source"
$StateRoot = Join-Path $RuntimeRoot "state"
$SecretsPath = Join-Path $StateRoot ".env"
$ComposeExe = Join-Path $ToolsRoot $ComposeName
$ComposeFile = Join-Path $SourceRoot "config\sheriff\docker-compose.yml"
$SmokeScript = Join-Path $StateRoot "production_smoke.py"
$ResultPath = Join-Path $StateRoot "SHERIFF_V1_PRODUCTION_RESULT.txt"
$PersistentScript = Join-Path $StateRoot "ZbSheriffV1.ps1"

function Ensure-Directory([string]$PathValue) {
    if (-not (Test-Path -LiteralPath $PathValue -PathType Container)) {
        New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
    }
}

function Get-Sha256([string]$PathValue) {
    return (Get-FileHash -LiteralPath $PathValue -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Download-Verified([string]$Url, [string]$Destination, [string]$ExpectedSha) {
    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        if ((Get-Sha256 $Destination) -eq $ExpectedSha.ToLowerInvariant()) { return }
        Remove-Item -LiteralPath $Destination -Force
    }
    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Destination
    $actual = Get-Sha256 $Destination
    if ($actual -ne $ExpectedSha.ToLowerInvariant()) {
        Remove-Item -LiteralPath $Destination -Force -ErrorAction SilentlyContinue
        throw "DOWNLOAD_SHA256_MISMATCH:${Destination}:$actual"
    }
}

function Find-Podman {
    $command = Get-Command podman -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $command) { return $command.Source }
    $candidates = @(
        (Join-Path $env:ProgramFiles "RedHat\Podman\podman.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Podman\podman.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    }
    return $null
}

function Ensure-Podman {
    $podman = Find-Podman
    if ($null -ne $podman) { return $podman }

    if ([Environment]::OSVersion.Version.Build -lt 22000) {
        throw "PODMAN_V6_WINDOWS_VERSION_UNSUPPORTED"
    }

    Ensure-Directory $ToolsRoot
    $installer = Join-Path $ToolsRoot $PodmanInstallerName
    Download-Verified $PodmanInstallerUrl $installer $PodmanInstallerSha256

    $args = "/i `"$installer`" /qn /norestart"
    $process = Start-Process -FilePath "msiexec.exe" -ArgumentList $args -Verb RunAs -Wait -PassThru
    if ($process.ExitCode -eq 3010) { throw "PODMAN_INSTALL_REBOOT_REQUIRED" }
    if ($process.ExitCode -ne 0) { throw "PODMAN_INSTALL_FAILED:$($process.ExitCode)" }

    $podman = Find-Podman
    if ($null -eq $podman) { throw "PODMAN_INSTALL_NOT_FOUND" }
    return $podman
}

function Ensure-ComposeProvider {
    Ensure-Directory $ToolsRoot
    Download-Verified $ComposeUrl $ComposeExe $ComposeSha256
    $env:PODMAN_COMPOSE_PROVIDER = $ComposeExe
    return $ComposeExe
}

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

function Materialize-ValidatedRuntime {
    Ensure-Directory $RuntimeRoot
    Ensure-Directory $StateRoot
    $marker = Join-Path $SourceRoot ".zorr-sheriff-runtime-commit"
    if ((Test-Path -LiteralPath $marker -PathType Leaf) -and ((Get-Content -LiteralPath $marker -Raw).Trim() -eq $ValidatedRuntimeCommit) -and (Test-Path -LiteralPath $ComposeFile -PathType Leaf)) {
        return
    }

    $tempRoot = Join-Path $RuntimeRoot ("materialize-" + [Guid]::NewGuid().ToString("N"))
    $archive = Join-Path $tempRoot "runtime.zip"
    $extract = Join-Path $tempRoot "extract"
    Ensure-Directory $tempRoot
    Ensure-Directory $extract
    try {
        $url = "https://github.com/$Repository/archive/$ValidatedRuntimeCommit.zip"
        Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $archive
        Expand-Archive -LiteralPath $archive -DestinationPath $extract -Force
        $candidate = Get-ChildItem -LiteralPath $extract -Directory | Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "config\sheriff\docker-compose.yml") -PathType Leaf
        } | Select-Object -First 1
        if ($null -eq $candidate) { throw "RUNTIME_ARCHIVE_LAYOUT_INVALID" }

        if (Test-Path -LiteralPath $SourceRoot) { Remove-Item -LiteralPath $SourceRoot -Recurse -Force }
        New-Item -ItemType Directory -Path $SourceRoot -Force | Out-Null

        foreach ($relative in @("config\sheriff", "scripts\sheriff_core.py", "scripts\sheriff_worker.py", "scripts\sheriff_runtime_e2e.py", "schemas\SHERIFF_AGENT_EVENT_V1.schema.json", "schemas\SHERIFF_VERDICT_V1.schema.json", "requirements-sheriff.txt")) {
            $from = Join-Path $candidate.FullName $relative
            if (-not (Test-Path -LiteralPath $from)) { throw "RUNTIME_FILE_MISSING:$relative" }
            $to = Join-Path $SourceRoot $relative
            $parent = Split-Path -Parent $to
            Ensure-Directory $parent
            Copy-Item -LiteralPath $from -Destination $to -Recurse -Force
        }
        Set-Content -LiteralPath $marker -Value $ValidatedRuntimeCommit -Encoding ASCII
    } finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function New-Secret {
    $bytes = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $rng.GetBytes($bytes)
    } finally {
        $rng.Dispose()
    }
    return (($bytes | ForEach-Object { $_.ToString("x2") }) -join "")
}

function Ensure-Secrets {
    Ensure-Directory $StateRoot
    if (-not (Test-Path -LiteralPath $SecretsPath -PathType Leaf)) {
        @(
            "NATS_PASSWORD=$(New-Secret)",
            "SHERIFF_DB_PASSWORD=$(New-Secret)",
            "GRAFANA_ADMIN_PASSWORD=$(New-Secret)"
        ) | Set-Content -LiteralPath $SecretsPath -Encoding ASCII
        try {
            $aclUser = $env:USERNAME + ":(R,W)"
            & icacls $SecretsPath /inheritance:r /grant:r $aclUser *> $null
        } catch { }
    }
}

function Import-Secrets {
    if (-not (Test-Path -LiteralPath $SecretsPath -PathType Leaf)) { throw "SECRETS_MISSING" }
    foreach ($line in Get-Content -LiteralPath $SecretsPath) {
        if ($line -match '^([^=]+)=(.+)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

function Write-SmokeScript {
    Ensure-Directory $StateRoot
    $python = @'
import asyncio, json, os, sys, time
from datetime import datetime, timezone
import nats
import psycopg

NATS_URL = os.environ["SHERIFF_NATS_URL"]
POSTGRES_DSN = os.environ["SHERIFF_POSTGRES_DSN"]
EVENT_ID = sys.argv[1]

async def scalar(conn, sql, params=()):
    async with conn.cursor() as cur:
        await cur.execute(sql, params)
        row = await cur.fetchone()
        return None if row is None else row[0]

async def main():
    conn = await psycopg.AsyncConnection.connect(POSTGRES_DSN)
    try:
        async with conn.cursor() as cur:
            await cur.execute("SELECT discipline_score, merit_points, active_gate, incident_count FROM sheriff_agent_scores WHERE agent_id='SHERIFF'")
            before = await cur.fetchone()
    finally:
        await conn.close()

    event = {
        "specversion": "1.0",
        "id": EVENT_ID,
        "source": "zb://sheriff/production-smoke",
        "type": "zb.agent.result",
        "subject": "task:SHERIFF-PRODUCTION-SMOKE",
        "time": datetime.now(timezone.utc).isoformat(),
        "datacontenttype": "application/json",
        "data": {
            "agentId": "SHERIFF",
            "taskRef": "SHERIFF-PRODUCTION-SMOKE",
            "executionId": EVENT_ID,
            "status": "FAIL",
            "evidence": ["production-smoke:issue-181"],
            "errorSignature": "PRODUCTION_SMOKE_UPSTREAM",
            "incidentAttribution": "SYSTEM_UPSTREAM",
            "selfCaught": False,
            "processViolation": False,
            "safetyViolation": False,
        },
    }

    nc = await nats.connect(NATS_URL, connect_timeout=5)
    try:
        js = nc.jetstream()
        ack = await js.publish("zb.agent.result", json.dumps(event, separators=(",", ":")).encode())
        if not ack:
            raise RuntimeError("PRODUCTION_SMOKE_PUBLISH_ACK_INVALID")
    finally:
        await nc.drain()

    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        conn = await psycopg.AsyncConnection.connect(POSTGRES_DSN)
        try:
            event_count = int(await scalar(conn, "SELECT COUNT(*) FROM sheriff_events WHERE event_id=%s", (EVENT_ID,)))
            incident_count = int(await scalar(conn, "SELECT COUNT(*) FROM sheriff_incidents WHERE event_id=%s", (EVENT_ID,)))
            async with conn.cursor() as cur:
                await cur.execute("SELECT discipline_score, merit_points, active_gate, incident_count FROM sheriff_agent_scores WHERE agent_id='SHERIFF'")
                after = await cur.fetchone()
            if event_count == 1:
                if incident_count != 0:
                    raise RuntimeError("PRODUCTION_SMOKE_CREATED_INCIDENT")
                if before != after:
                    raise RuntimeError(f"PRODUCTION_SMOKE_MUTATED_SCORE:{before!r}:{after!r}")
                print("SHERIFF_PRODUCTION_SMOKE = PASS")
                return
        finally:
            await conn.close()
        await asyncio.sleep(1)
    raise RuntimeError("PRODUCTION_SMOKE_TIMEOUT")

asyncio.run(main())
'@
    Set-Content -LiteralPath $SmokeScript -Value $python -Encoding UTF8
}

function Invoke-Compose([string]$PodmanExe, [Parameter(ValueFromRemainingArguments=$true)][string[]]$ComposeArgs) {
    $env:PODMAN_COMPOSE_PROVIDER = $ComposeExe
    & $PodmanExe compose -f $ComposeFile @ComposeArgs
    if ($LASTEXITCODE -ne 0) { throw "PODMAN_COMPOSE_FAILED:$($ComposeArgs -join ' ')" }
}

function Ensure-Task([string]$ScriptPath) {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -ne $existing) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    $arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $ScriptPath + '" -Action Start -RuntimeRoot "' + $RuntimeRoot + '"'
    $taskAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments -WorkingDirectory $StateRoot
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    $userId = if ($env:USERDOMAIN) { "$env:USERDOMAIN\$env:USERNAME" } else { $env:USERNAME }
    $principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
    $task = New-ScheduledTask -Action $taskAction -Trigger $trigger -Principal $principal -Settings $settings
    Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
}

function Start-Stack {
    Materialize-ValidatedRuntime
    Ensure-Secrets
    Import-Secrets
    $podman = Ensure-Podman
    $null = Ensure-ComposeProvider
    Ensure-PodmanMachine $podman
    Invoke-Compose $podman "up" "-d" "--build"
}

function Get-TaskState {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -eq $task) { return @{ Registered="NO"; Enabled="NO"; State="MISSING" } }
    return @{
        Registered = "YES"
        Enabled = if ([string]$task.State -eq "Disabled") { "NO" } else { "YES" }
        State = [string]$task.State
    }
}

function Get-RunningServices([string]$PodmanExe) {
    $env:PODMAN_COMPOSE_PROVIDER = $ComposeExe
    $lines = & $PodmanExe compose -f $ComposeFile ps --status running --services
    if ($LASTEXITCODE -ne 0) { throw "PODMAN_COMPOSE_PS_FAILED" }
    return @($lines | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ })
}

function Invoke-Health([string]$PodmanExe) {
    $harness = Join-Path $SourceRoot "scripts\sheriff_runtime_e2e.py"
    Invoke-Compose $PodmanExe "run" "--rm" "--no-deps" "-v" "${harness}:/tmp/sheriff_runtime_e2e.py:ro" "sheriff-worker" "python" "/tmp/sheriff_runtime_e2e.py" "health"
}

function Invoke-LiveSmoke([string]$PodmanExe) {
    Write-SmokeScript
    $smokeId = "PROD-SMOKE-" + [Guid]::NewGuid().ToString("N")
    Invoke-Compose $PodmanExe "run" "--rm" "--no-deps" "-v" "${SmokeScript}:/tmp/production_smoke.py:ro" "sheriff-worker" "python" "/tmp/production_smoke.py" $smokeId
}

function Write-Result([string[]]$Lines) {
    Ensure-Directory $StateRoot
    $Lines | Set-Content -LiteralPath $ResultPath -Encoding UTF8
    $Lines | ForEach-Object { Write-Output $_ }
}

function Post-Evidence {
    $gh = Get-Command gh -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $gh) { throw "GH_CLI_NOT_READY" }
    & $gh.Source auth status *> $null
    if ($LASTEXITCODE -ne 0) { throw "GH_AUTH_NOT_READY" }
    & $gh.Source issue comment $ActivationIssue --repo $Repository --body-file $ResultPath *> $null
    if ($LASTEXITCODE -ne 0) { throw "GITHUB_EVIDENCE_POST_FAILED" }
}

function Verify-Production {
    $taskState = Get-TaskState
    $stack = "FAIL"
    $live = "FAIL"
    $blocker = "NONE"
    try {
        if ($taskState.Registered -ne "YES") { throw "TASK_NOT_REGISTERED" }
        if ($taskState.Enabled -ne "YES") { throw "TASK_NOT_ENABLED" }
        Materialize-ValidatedRuntime
        Ensure-Secrets
        Import-Secrets
        $podman = Ensure-Podman
        $null = Ensure-ComposeProvider
        Ensure-PodmanMachine $podman
        $running = Get-RunningServices $podman
        foreach ($service in $RequiredServices) {
            if ($running -notcontains $service) { throw "SERVICE_NOT_RUNNING:$service" }
        }
        $stack = "PASS"

        Invoke-Health $podman
        Invoke-LiveSmoke $podman
        Invoke-Compose $podman "restart" "sheriff-worker"
        Start-Sleep -Seconds 3
        Invoke-Health $podman
        Invoke-LiveSmoke $podman
        $live = "PASS"

        $lines = @(
            "SHERIFF_V1_PRODUCTION_EVIDENCE_V1",
            "RUNTIME_COMMIT = $ValidatedRuntimeCommit",
            "OPEN_CODE_ONLY = TRUE",
            "HOST = $env:COMPUTERNAME",
            "TASK_REGISTERED = $($taskState.Registered)",
            "TASK_ENABLED = $($taskState.Enabled)",
            "TASK_STATE = $($taskState.State)",
            "STACK_SERVICES_RUNNING = $stack",
            "SHERIFF_LIVE_PATH = $live",
            "WORKER_RESTART = PASS",
            "SHERIFF_V1_24_7_PRODUCTION_ACTIVE = YES",
            "BLOCKER = NONE"
        )
        Write-Result $lines
        Post-Evidence
        return
    } catch {
        $blocker = $_.Exception.Message
        $lines = @(
            "SHERIFF_V1_PRODUCTION_EVIDENCE_V1",
            "RUNTIME_COMMIT = $ValidatedRuntimeCommit",
            "OPEN_CODE_ONLY = TRUE",
            "TASK_REGISTERED = $($taskState.Registered)",
            "TASK_ENABLED = $($taskState.Enabled)",
            "TASK_STATE = $($taskState.State)",
            "STACK_SERVICES_RUNNING = $stack",
            "SHERIFF_LIVE_PATH = $live",
            "SHERIFF_V1_24_7_PRODUCTION_ACTIVE = NO",
            "BLOCKER = $blocker"
        )
        Write-Result $lines
        throw
    }
}

switch ($Action) {
    "Install" {
        Ensure-Directory $RuntimeRoot
        Ensure-Directory $StateRoot
        Copy-Item -LiteralPath $PSCommandPath -Destination $PersistentScript -Force
        Start-Stack
        Ensure-Task $PersistentScript
        Start-ScheduledTask -TaskName $TaskName
        Write-Output "ZB_SHERIFF_V1_INSTALL = PASS"
    }
    "Uninstall" {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($null -ne $task) {
            if ([string]$task.State -eq "Running") { Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue }
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        }
        try {
            Import-Secrets
            $podman = Find-Podman
            if ($null -ne $podman -and (Test-Path -LiteralPath $ComposeFile -PathType Leaf)) {
                $null = Ensure-ComposeProvider
                Invoke-Compose $podman "stop"
            }
        } catch { }
        Write-Output "ZB_SHERIFF_V1_UNINSTALL = PASS"
    }
    "Status" {
        $state = Get-TaskState
        Write-Output "ZB_SHERIFF_V1_STATUS"
        Write-Output "TASK_REGISTERED = $($state.Registered)"
        Write-Output "TASK_ENABLED = $($state.Enabled)"
        Write-Output "TASK_STATE = $($state.State)"
        try {
            $podman = Find-Podman
            if ($null -eq $podman) { throw "PODMAN_MISSING" }
            $null = Ensure-ComposeProvider
            $running = Get-RunningServices $podman
            $missing = @($RequiredServices | Where-Object { $running -notcontains $_ })
            Write-Output ("STACK_SERVICES_RUNNING = " + $(if ($missing.Count -eq 0) { "PASS" } else { "FAIL" }))
            Write-Output ("BLOCKER = " + $(if ($missing.Count -eq 0) { "NONE" } else { "MISSING:" + ($missing -join ',') }))
        } catch {
            Write-Output "STACK_SERVICES_RUNNING = FAIL"
            Write-Output "BLOCKER = $($_.Exception.Message)"
        }
    }
    "Start" {
        Start-Stack
        Write-Output "ZB_SHERIFF_V1_START = PASS"
    }
    "Stop" {
        Import-Secrets
        $podman = Find-Podman
        if ($null -eq $podman) { throw "PODMAN_MISSING" }
        $null = Ensure-ComposeProvider
        Invoke-Compose $podman "stop"
        Write-Output "ZB_SHERIFF_V1_STOP = PASS"
    }
    "Restart" {
        Import-Secrets
        $podman = Find-Podman
        if ($null -eq $podman) { throw "PODMAN_MISSING" }
        $null = Ensure-ComposeProvider
        Ensure-PodmanMachine $podman
        Invoke-Compose $podman "restart"
        Write-Output "ZB_SHERIFF_V1_RESTART = PASS"
    }
    "Verify" {
        Verify-Production
    }
}
