from pathlib import Path
import logging
import pytest

from zb_reference_bridge.bridge import BridgeCycleSummary
from zb_reference_bridge.config import BridgeConfig
from zb_reference_bridge.runner import BridgePreflightError, run_bridge_forever, run_preflight


class FakeGitHub:
    def __init__(self, fail=False): self.fail = fail; self.calls = 0
    def ensure_authenticated(self):
        self.calls += 1
        if self.fail: raise RuntimeError("auth")


class FakeHealth:
    def __init__(self): self.writes = []
    def write(self, state, **kwargs): self.writes.append((state, kwargs))


class FakeBridge:
    def __init__(self, outcomes): self.outcomes = list(outcomes)
    def run_once(self):
        value = self.outcomes.pop(0)
        if isinstance(value, BaseException): raise value
        return value


def cfg(tmp_path: Path):
    drive = tmp_path / "drive"; drive.mkdir()
    inbox = tmp_path / "inbox"; inbox.mkdir()
    return BridgeConfig(
        repository="Lester-Sparx/zorr-blatt-shared-hq",
        drive_sync_root=drive,
        drive_drop_folder_id="folder",
        inbox_root=inbox,
        runtime_root=tmp_path / "runtime",
        quarantine_root=tmp_path / "quarantine",
        poll_interval_seconds=1.0,
    )


def test_preflight_checks_auth_and_roots_without_moving_sources(tmp_path: Path):
    config = cfg(tmp_path)
    delivery = config.drive_sync_root / "DELIV-001"; delivery.mkdir()
    source = delivery / "source.png"; source.write_bytes(b"x")
    github = FakeGitHub()
    run_preflight(config, github)
    assert github.calls == 1
    assert source.read_bytes() == b"x"
    assert config.runtime_root.is_dir()
    assert config.quarantine_root.is_dir()


def test_preflight_invalid_drive_root_fails_closed(tmp_path: Path):
    config = cfg(tmp_path)
    config.drive_sync_root.rmdir()
    with pytest.raises(BridgePreflightError) as exc:
        run_preflight(config, FakeGitHub())
    assert exc.value.code == "REFERENCE_BRIDGE_DRIVE_ROOT_UNAVAILABLE"


def test_loop_updates_healthy_then_stopping_on_ctrl_c(tmp_path: Path):
    config = cfg(tmp_path)
    health = FakeHealth()
    bridge = FakeBridge([BridgeCycleSummary(1, 0, 1, 0, 0)])
    def stop(_seconds): raise KeyboardInterrupt
    code = run_bridge_forever(bridge, config, health, sleep=stop, logger=logging.getLogger("rb-test-stop"))
    assert code == 0
    assert [s for s, _ in health.writes] == ["STARTING", "HEALTHY", "STOPPING"]
    assert health.writes[1][1]["accepted_count"] == 1


def test_transient_scan_error_degrades_and_retries(tmp_path: Path):
    config = cfg(tmp_path)
    health = FakeHealth()
    bridge = FakeBridge([RuntimeError("temporary"), BridgeCycleSummary(0, 0, 0, 0, 0)])
    sleeps = []
    def sleep(_seconds):
        sleeps.append(1)
        if len(sleeps) == 2: raise KeyboardInterrupt
    code = run_bridge_forever(bridge, config, health, sleep=sleep, logger=logging.getLogger("rb-test-degrade"))
    assert code == 0
    states = [s for s, _ in health.writes]
    assert "DEGRADED" in states and "HEALTHY" in states and states[-1] == "STOPPING"


def test_unrecoverable_preflight_failure_can_be_written_fatal(tmp_path: Path):
    config = cfg(tmp_path)
    config.drive_sync_root.rmdir()
    health = FakeHealth()
    with pytest.raises(BridgePreflightError) as exc:
        run_preflight(config, FakeGitHub(), health=health)
    assert exc.value.code == "REFERENCE_BRIDGE_DRIVE_ROOT_UNAVAILABLE"
    assert health.writes[-1][0] == "FATAL"


def test_preflight_rejects_runtime_and_inbox_on_different_volumes(tmp_path: Path, monkeypatch):
    import zb_reference_bridge.runner as runner
    config = cfg(tmp_path)
    monkeypatch.setattr(runner, "_volume_id", lambda path: 1 if Path(path) == config.runtime_root else 2)
    with pytest.raises(BridgePreflightError) as exc:
        run_preflight(config, FakeGitHub())
    assert exc.value.code == "REFERENCE_BRIDGE_VOLUME_MISMATCH"
