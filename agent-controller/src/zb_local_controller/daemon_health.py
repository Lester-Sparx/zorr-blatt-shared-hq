from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from typing import Any


DAEMON_SCHEMA_VERSION = "zb-controller-daemon-v1"
HEALTH_STATES = {"STARTING", "HEALTHY", "DEGRADED", "FATAL", "STOPPING"}
LOG_MAX_BYTES = 2097152
LOG_BACKUP_COUNT = 5


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def config_sha256(path: Path) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def _cycle_payload(last_cycle: Any) -> dict[str, int] | None:
    if last_cycle is None:
        return None
    if is_dataclass(last_cycle):
        raw = asdict(last_cycle)
    elif isinstance(last_cycle, dict):
        raw = dict(last_cycle)
    else:
        raw = {
            "discovered": getattr(last_cycle, "discovered"),
            "processed": getattr(last_cycle, "processed"),
            "submitted": getattr(last_cycle, "submitted"),
            "skipped": getattr(last_cycle, "skipped"),
        }
    return {
        "discovered": int(raw["discovered"]),
        "processed": int(raw["processed"]),
        "submitted": int(raw["submitted"]),
        "skipped": int(raw["skipped"]),
    }


class DaemonHealthWriter:
    def __init__(
        self,
        runtime_root: Path,
        repository: str,
        config_path: Path,
        poll_interval_seconds: float,
        pid: int,
        instance_id: str,
    ):
        self.runtime_root = Path(runtime_root)
        self.path = self.runtime_root / "health.json"
        self.repository = str(repository)
        self.config_path = Path(config_path)
        self.poll_interval_seconds = float(poll_interval_seconds)
        self.pid = int(pid)
        self.instance_id = str(instance_id)
        self.started_at_utc = _utc_now()

    def write(self, state: str, last_cycle=None, last_error_code=None) -> None:
        if state not in HEALTH_STATES:
            raise ValueError("DAEMON_HEALTH_STATE_INVALID")
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        payload = {
            "schemaVersion": DAEMON_SCHEMA_VERSION,
            "state": state,
            "pid": self.pid,
            "instanceId": self.instance_id,
            "startedAtUtc": self.started_at_utc,
            "heartbeatAtUtc": _utc_now(),
            "repository": self.repository,
            "configSha256": config_sha256(self.config_path),
            "pollIntervalSeconds": self.poll_interval_seconds,
            "lastCycle": _cycle_payload(last_cycle),
            "lastErrorCode": None if last_error_code is None else str(last_error_code),
        }
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)


class _UtcFormatter(logging.Formatter):
    converter = staticmethod(lambda *args: __import__("time").gmtime(*args))


def configure_daemon_logger(runtime_root: Path, instance_id: str, pid: int) -> logging.Logger:
    runtime_root = Path(runtime_root)
    runtime_root.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(f"zb_local_controller.daemon.{instance_id}.{pid}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
    handler = RotatingFileHandler(
        runtime_root / "controller-daemon.log",
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(
        _UtcFormatter(
            f"%(asctime)sZ %(levelname)s pid={int(pid)} instance={instance_id} %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    return logger
