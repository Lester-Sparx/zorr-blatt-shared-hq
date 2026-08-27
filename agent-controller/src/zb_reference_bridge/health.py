from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import uuid

BRIDGE_HEALTH_SCHEMA = "zb-reference-bridge-v1"
HEALTH_STATES = {"STARTING", "HEALTHY", "DEGRADED", "FATAL", "STOPPING"}
LOG_MAX_BYTES = 1_048_576
LOG_BACKUP_COUNT = 5


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def config_sha256(path: Path) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


class BridgeHealthWriter:
    def __init__(self, runtime_root: Path, config_sha: str, *, pid: int | None = None, instance_id: str | None = None):
        self.runtime_root = Path(runtime_root)
        self.path = self.runtime_root / "health.json"
        self.config_sha = str(config_sha)
        self.pid = os.getpid() if pid is None else int(pid)
        self.instance_id = instance_id or str(uuid.uuid4())
        self.accepted_count = 0
        self.rejected_count = 0

    def write(
        self,
        state: str,
        *,
        drive_root_reachable: bool | None = None,
        github_reachable: bool | None = None,
        last_poll_utc: str | None = None,
        accepted_count: int | None = None,
        rejected_count: int | None = None,
        last_error_code: str | None = None,
    ) -> None:
        if state not in HEALTH_STATES:
            raise ValueError("REFERENCE_BRIDGE_HEALTH_STATE_INVALID")
        if accepted_count is not None:
            self.accepted_count = int(accepted_count)
        if rejected_count is not None:
            self.rejected_count = int(rejected_count)
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        heartbeat = _utc_now()
        payload = {
            "schema": BRIDGE_HEALTH_SCHEMA,
            "pid": self.pid,
            "instanceId": self.instance_id,
            "state": state,
            "heartbeatUtc": heartbeat,
            "configSha256": self.config_sha,
            "driveRootReachable": drive_root_reachable,
            "githubReachable": github_reachable,
            "lastPollUtc": last_poll_utc,
            "acceptedCount": self.accepted_count,
            "rejectedCount": self.rejected_count,
            "lastErrorCode": last_error_code,
        }
        tmp = self.runtime_root / "health.json.tmp"
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)


class _UtcFormatter(logging.Formatter):
    converter = staticmethod(lambda *args: __import__("time").gmtime(*args))


def configure_bridge_logger(runtime_root: Path) -> logging.Logger:
    root = Path(runtime_root)
    root.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(f"zb_reference_bridge.{root}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
    handler = RotatingFileHandler(root / "reference-bridge.log", maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8")
    handler.setFormatter(_UtcFormatter("%(asctime)sZ %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"))
    logger.addHandler(handler)
    return logger
