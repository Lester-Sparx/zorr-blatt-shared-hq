from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

DEFAULT_REPOSITORY = "Lester-Sparx/zorr-blatt-shared-hq"
MAX_SOURCE_BYTES_V1 = 20 * 1024 * 1024
_ALLOWED_KEYS = {
    "repository",
    "driveSyncRoot",
    "driveDropFolderId",
    "inboxRoot",
    "runtimeRoot",
    "quarantineRoot",
    "pollIntervalSeconds",
    "cloudRetryTimeoutSeconds",
    "maxSourceBytes",
}


class BridgeConfigError(ValueError):
    def __init__(self, code: str = "BRIDGE_CONFIG_INVALID"):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class BridgeConfig:
    repository: str
    drive_sync_root: Path
    drive_drop_folder_id: str
    inbox_root: Path = Path(r"D:\BLATT2\ZB_AGENT_INBOX")
    runtime_root: Path = Path(r"D:\BLATT2\ZB_AGENT_RUNTIME\reference-bridge")
    quarantine_root: Path = Path(r"D:\BLATT2\ZB_REFERENCE_QUARANTINE")
    poll_interval_seconds: float = 5.0
    cloud_retry_timeout_seconds: float = 300.0
    max_source_bytes: int = MAX_SOURCE_BYTES_V1


def _nonempty_string(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BridgeConfigError()
    return value.strip()


def _positive_float(value: Any) -> float:
    if isinstance(value, bool):
        raise BridgeConfigError()
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise BridgeConfigError() from exc
    if parsed <= 0:
        raise BridgeConfigError()
    return parsed


def load_bridge_config(path: Path) -> BridgeConfig:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise BridgeConfigError() from exc
    if not isinstance(raw, dict) or set(raw) - _ALLOWED_KEYS:
        raise BridgeConfigError()
    try:
        repository = _nonempty_string(raw.get("repository", DEFAULT_REPOSITORY))
        drive_sync_root = Path(_nonempty_string(raw.get("driveSyncRoot")))
        drive_drop_folder_id = _nonempty_string(raw.get("driveDropFolderId"))
        inbox_root = Path(_nonempty_string(raw.get("inboxRoot", r"D:\BLATT2\ZB_AGENT_INBOX")))
        runtime_root = Path(_nonempty_string(raw.get("runtimeRoot", r"D:\BLATT2\ZB_AGENT_RUNTIME\reference-bridge")))
        quarantine_root = Path(_nonempty_string(raw.get("quarantineRoot", r"D:\BLATT2\ZB_REFERENCE_QUARANTINE")))
        poll_interval = _positive_float(raw.get("pollIntervalSeconds", 5.0))
        retry_timeout = _positive_float(raw.get("cloudRetryTimeoutSeconds", 300.0))
        max_source = raw.get("maxSourceBytes", MAX_SOURCE_BYTES_V1)
        if isinstance(max_source, bool) or not isinstance(max_source, int) or max_source != MAX_SOURCE_BYTES_V1:
            raise BridgeConfigError()
    except BridgeConfigError:
        raise
    except Exception as exc:
        raise BridgeConfigError() from exc
    return BridgeConfig(
        repository=repository,
        drive_sync_root=drive_sync_root,
        drive_drop_folder_id=drive_drop_folder_id,
        inbox_root=inbox_root,
        runtime_root=runtime_root,
        quarantine_root=quarantine_root,
        poll_interval_seconds=poll_interval,
        cloud_retry_timeout_seconds=retry_timeout,
        max_source_bytes=max_source,
    )
