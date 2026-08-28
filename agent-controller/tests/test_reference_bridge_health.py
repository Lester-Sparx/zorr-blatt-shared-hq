from pathlib import Path
import json
import logging

from zb_reference_bridge.health import BridgeHealthWriter, configure_bridge_logger


def test_health_write_is_atomic_and_schema_stable(tmp_path: Path, monkeypatch):
    calls = []
    import zb_reference_bridge.health as module
    real_replace = module.os.replace
    def recording_replace(src, dst):
        calls.append((Path(src), Path(dst)))
        return real_replace(src, dst)
    monkeypatch.setattr(module.os, "replace", recording_replace)

    writer = BridgeHealthWriter(tmp_path, "abc123")
    writer.write("HEALTHY", drive_root_reachable=True, github_reachable=True, accepted_count=2, rejected_count=1)

    payload = json.loads((tmp_path / "health.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "zb-reference-bridge-v1"
    assert payload["state"] == "HEALTHY"
    assert payload["configSha256"] == "abc123"
    assert payload["acceptedCount"] == 2
    assert payload["rejectedCount"] == 1
    assert calls and calls[-1][1] == tmp_path / "health.json"
    assert not (tmp_path / "health.json.tmp").exists()


def test_bridge_logger_is_bounded_1mib_x5(tmp_path: Path):
    logger = configure_bridge_logger(tmp_path)
    handlers = [h for h in logger.handlers if hasattr(h, "maxBytes")]
    assert len(handlers) == 1
    assert handlers[0].maxBytes == 1_048_576
    assert handlers[0].backupCount == 5
    for h in list(logger.handlers):
        h.close(); logger.removeHandler(h)
