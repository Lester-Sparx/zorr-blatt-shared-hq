from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import pytest

from zb_reference_bridge.bridge import BridgeCycleSummary
from zb_reference_bridge.instance_lock import BridgeInstanceBusy
from zb_reference_bridge.__main__ import main


def write_config(tmp_path: Path):
    drive = tmp_path / "drive"; drive.mkdir()
    inbox = tmp_path / "inbox"; inbox.mkdir()
    p = tmp_path / "bridge.json"
    p.write_text(json.dumps({
        "repository": "Lester-Sparx/zorr-blatt-shared-hq",
        "driveSyncRoot": str(drive),
        "driveDropFolderId": "folder",
        "inboxRoot": str(inbox),
        "runtimeRoot": str(tmp_path / "runtime"),
        "quarantineRoot": str(tmp_path / "quarantine"),
        "pollIntervalSeconds": 5,
        "cloudRetryTimeoutSeconds": 300,
        "maxSourceBytes": 20971520,
    }), encoding="utf-8")
    return p


def test_cli_requires_exactly_one_processing_mode(tmp_path):
    p = write_config(tmp_path)
    with pytest.raises(SystemExit):
        main(["--config", str(p)])
    with pytest.raises(SystemExit):
        main(["--config", str(p), "--once", "--daemon"])


def test_once_acquires_lock_before_discovery(tmp_path, capsys):
    p = write_config(tmp_path)
    order = []
    class GH:
        def __init__(self, _repo): pass
    class Lock:
        def __init__(self, _root): pass
        def __enter__(self): order.append("lock"); return self
        def __exit__(self, *args): order.append("unlock")
    class Bridge:
        def __init__(self, _cfg, _gh): pass
        def run_once(self): order.append("discover"); return BridgeCycleSummary(1, 0, 0, 0, 1)
    code = main(["--config", str(p), "--once"], github_factory=GH, lock_factory=Lock, bridge_factory=Bridge)
    assert code == 0
    assert order[:2] == ["lock", "discover"]
    assert "BRIDGE_CYCLE_COMPLETE" in capsys.readouterr().out


def test_busy_lock_returns_stable_nonzero_code(tmp_path, capsys):
    p = write_config(tmp_path)
    class GH:
        def __init__(self, _repo): pass
    class BusyLock:
        def __init__(self, _root): pass
        def __enter__(self): raise BridgeInstanceBusy()
        def __exit__(self, *args): pass
    code = main(["--config", str(p), "--once"], github_factory=GH, lock_factory=BusyLock)
    assert code == 3
    assert "REFERENCE_BRIDGE_INSTANCE_BUSY" in capsys.readouterr().err


def test_status_malformed_health_fails_closed_to_missing(tmp_path, capsys):
    p = write_config(tmp_path)
    runtime = tmp_path / "runtime"; runtime.mkdir()
    (runtime / "health.json").write_text('{"schema":"wrong","state":"HEALTHY"}', encoding="utf-8")
    assert main(["--config", str(p), "--status"]) == 0
    out = capsys.readouterr().out
    assert "HEALTH_STATE = MISSING" in out
    assert "PID = NONE" in out


def test_status_stale_heartbeat_fails_closed_to_stale(tmp_path, capsys):
    p = write_config(tmp_path)
    runtime = tmp_path / "runtime"; runtime.mkdir()
    old = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
    (runtime / "health.json").write_text(json.dumps({
        "schema":"zb-reference-bridge-v1", "state":"HEALTHY", "pid":999999,
        "instanceId":"abc", "heartbeatUtc":old, "configSha256":"deadbeef",
        "driveRootReachable":True,
    }), encoding="utf-8")
    assert main(["--config", str(p), "--status"]) == 0
    out = capsys.readouterr().out
    assert "HEALTH_STATE = STALE" in out
    assert "INSTANCE_ID = abc" in out
    assert "DRIVE_ROOT_REACHABLE = YES" in out
