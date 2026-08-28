from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "deploy" / "windows" / "ZbControllerDaemon.ps1"


def text():
    return SCRIPT.read_text(encoding="utf-8")


def test_canonical_name_and_commands_are_declared():
    source = text()
    assert "ZB Controller Daemon v1" in source
    assert "-m zb_local_controller --daemon --config" in source
    assert "--daemon-preflight" in source
    for action in ("Install", "Uninstall", "Status", "Start", "Stop", "Restart", "Enable", "Disable"):
        assert f'"{action}"' in source


def test_install_is_idempotent_and_current_user_scoped():
    source = text()
    assert "Register-ScheduledTask -TaskName $TaskName -InputObject $Task -Force" in source
    assert "New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME" in source
    assert "-LogonType Interactive -RunLevel Limited" in source


def test_locked_scheduler_policy_is_declared():
    source = text()
    for token in (
        "MultipleInstances IgnoreNew",
        "RestartCount 5",
        "New-TimeSpan -Minutes 1",
        "ExecutionTimeLimit ([TimeSpan]::Zero)",
        "DontStopIfGoingOnBatteries",
        "AllowStartIfOnBatteries",
        "StartWhenAvailable",
        "RunLevel Limited",
        "LogonType Interactive",
    ):
        assert token in source


def test_no_service_or_elevation_fallback():
    source = text().lower()
    assert "runlevel highest" not in source
    assert "new-service" not in source
    assert "nssm" not in source
    assert "-password" not in source


def test_status_rejects_wrong_health_schema_version():
    source = text()
    assert '$ExpectedHealthSchema = "zb-controller-daemon-v1"' in source
    assert '$health.schemaVersion -ne $ExpectedHealthSchema' in source


def test_status_rejects_health_state_outside_allowed_enum():
    source = text()
    assert '$AllowedHealthStates' in source
    assert '$AllowedHealthStates -notcontains $healthState' in source


def test_status_requires_valid_heartbeat_for_live_health():
    source = text()
    assert 'HEALTH_HEARTBEAT_INVALID' in source
    assert '$null -eq $health.heartbeatAtUtc' in source
