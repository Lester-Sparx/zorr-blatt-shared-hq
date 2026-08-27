import hashlib
import json
import logging.handlers
from pathlib import Path

import zb_local_controller.daemon_health as daemon_health
from zb_local_controller.daemon_health import DaemonHealthWriter, config_sha256, configure_daemon_logger


def test_config_sha256_hashes_raw_config_bytes(tmp_path):
    path = tmp_path / "config.json"
    path.write_bytes(b"{}\n")
    assert config_sha256(path) == hashlib.sha256(b"{}\n").hexdigest()


def test_health_schema_and_cycle_summary(tmp_path):
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    writer = DaemonHealthWriter(
        tmp_path / "runtime",
        "Lester-Sparx/zorr-blatt-shared-hq",
        config,
        15.0,
        1234,
        "11111111-1111-1111-1111-111111111111",
    )
    writer.write("HEALTHY", {"discovered": 4, "processed": 1, "submitted": 0, "skipped": 3})
    data = json.loads((tmp_path / "runtime" / "health.json").read_text(encoding="utf-8"))
    assert data["schemaVersion"] == "zb-controller-daemon-v1"
    assert data["state"] == "HEALTHY"
    assert data["pid"] == 1234
    assert data["lastCycle"] == {"discovered": 4, "processed": 1, "submitted": 0, "skipped": 3}
    assert data["lastErrorCode"] is None
    assert data["startedAtUtc"].endswith("Z")
    assert data["heartbeatAtUtc"].endswith("Z")
    assert data["configSha256"] == hashlib.sha256(b"{}").hexdigest()


def test_rotating_logger_has_locked_bounds(tmp_path):
    logger = configure_daemon_logger(tmp_path, "instance", 4321)
    handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
    assert len(handlers) == 1
    assert handlers[0].maxBytes == 2097152
    assert handlers[0].backupCount == 5


def test_health_write_uses_sibling_tmp_and_atomic_replace(tmp_path, monkeypatch):
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    runtime = tmp_path / "runtime"
    calls = []
    original_replace = daemon_health.os.replace

    def recording_replace(src, dst):
        calls.append((Path(src), Path(dst)))
        original_replace(src, dst)

    monkeypatch.setattr(daemon_health.os, "replace", recording_replace)
    writer = DaemonHealthWriter(runtime, "repo/name", config, 15.0, 7, "instance")
    writer.write("STARTING")
    assert calls == [(runtime / "health.json.tmp", runtime / "health.json")]
    assert not (runtime / "health.json.tmp").exists()
