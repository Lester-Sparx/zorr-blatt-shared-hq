from pathlib import Path
import json
import pytest

from zb_reference_bridge.config import BridgeConfig, BridgeConfigError, load_bridge_config


def test_load_bridge_config_requires_drive_sync_root(tmp_path: Path):
    p = tmp_path / "bridge.json"
    p.write_text(json.dumps({"repository": "Lester-Sparx/zorr-blatt-shared-hq"}), encoding="utf-8")
    with pytest.raises(BridgeConfigError) as exc:
        load_bridge_config(p)
    assert exc.value.code == "BRIDGE_CONFIG_INVALID"


def test_load_bridge_config_accepts_canonical_values(tmp_path: Path):
    p = tmp_path / "bridge.json"
    p.write_text(json.dumps({
        "repository": "Lester-Sparx/zorr-blatt-shared-hq",
        "driveSyncRoot": str(tmp_path / "drive"),
        "driveDropFolderId": "folder123",
        "inboxRoot": str(tmp_path / "inbox"),
        "runtimeRoot": str(tmp_path / "runtime"),
        "quarantineRoot": str(tmp_path / "quarantine"),
        "pollIntervalSeconds": 5,
        "cloudRetryTimeoutSeconds": 300,
        "maxSourceBytes": 20971520,
    }), encoding="utf-8")
    cfg = load_bridge_config(p)
    assert cfg.drive_sync_root == tmp_path / "drive"
    assert cfg.drive_drop_folder_id == "folder123"
    assert cfg.max_source_bytes == 20 * 1024 * 1024


def test_unknown_config_key_fails_closed(tmp_path: Path):
    p = tmp_path / "bridge.json"
    p.write_text(json.dumps({
        "driveSyncRoot": str(tmp_path / "drive"),
        "driveDropFolderId": "folder123",
        "surprise": True,
    }), encoding="utf-8")
    with pytest.raises(BridgeConfigError) as exc:
        load_bridge_config(p)
    assert exc.value.code == "BRIDGE_CONFIG_INVALID"


def test_v1_max_source_bytes_is_locked(tmp_path: Path):
    p = tmp_path / "bridge.json"
    p.write_text(json.dumps({
        "driveSyncRoot": str(tmp_path / "drive"),
        "driveDropFolderId": "folder123",
        "maxSourceBytes": 123,
    }), encoding="utf-8")
    with pytest.raises(BridgeConfigError) as exc:
        load_bridge_config(p)
    assert exc.value.code == "BRIDGE_CONFIG_INVALID"


def test_defaults_are_locked():
    cfg = BridgeConfig(repository="Lester-Sparx/zorr-blatt-shared-hq", drive_sync_root=Path("X"), drive_drop_folder_id="folder")
    assert cfg.inbox_root == Path(r"D:\BLATT2\ZB_AGENT_INBOX")
    assert cfg.runtime_root == Path(r"D:\BLATT2\ZB_AGENT_RUNTIME\reference-bridge")
    assert cfg.quarantine_root == Path(r"D:\BLATT2\ZB_REFERENCE_QUARANTINE")
    assert cfg.poll_interval_seconds == 5.0
    assert cfg.cloud_retry_timeout_seconds == 300.0
