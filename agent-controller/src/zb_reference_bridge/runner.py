from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
import time
import uuid

from .config import BridgeConfig


class BridgePreflightError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _volume_id(path: Path) -> int:
    return int(Path(path).stat().st_dev)


def _probe_writable_dir(path: Path, code: str, *, must_exist: bool = False) -> None:
    root = Path(path)
    try:
        if must_exist:
            if not root.is_dir():
                raise OSError(code)
        else:
            root.mkdir(parents=True, exist_ok=True)
        probe = root / f".zb-reference-bridge-probe-{uuid.uuid4().hex}"
        probe.write_bytes(b"")
        probe.unlink()
    except OSError as exc:
        raise BridgePreflightError(code) from exc


def run_preflight(config: BridgeConfig, github, *, health=None) -> None:
    try:
        try:
            github.ensure_authenticated()
        except Exception as exc:
            raise BridgePreflightError("REFERENCE_BRIDGE_GITHUB_UNAVAILABLE") from exc
        _probe_writable_dir(config.drive_sync_root, "REFERENCE_BRIDGE_DRIVE_ROOT_UNAVAILABLE", must_exist=True)
        _probe_writable_dir(config.inbox_root, "REFERENCE_BRIDGE_INBOX_UNWRITABLE")
        _probe_writable_dir(config.runtime_root, "REFERENCE_BRIDGE_RUNTIME_UNWRITABLE")
        if _volume_id(config.runtime_root) != _volume_id(config.inbox_root):
            raise BridgePreflightError("REFERENCE_BRIDGE_VOLUME_MISMATCH")
        _probe_writable_dir(config.quarantine_root, "REFERENCE_BRIDGE_QUARANTINE_UNWRITABLE")
    except BridgePreflightError as exc:
        if health is not None:
            health.write("FATAL", drive_root_reachable=config.drive_sync_root.is_dir(), github_reachable=False, last_error_code=exc.code)
        raise


def run_bridge_forever(bridge, config: BridgeConfig, health, *, sleep=time.sleep, logger: logging.Logger | None = None) -> int:
    logger = logger or logging.getLogger("zb_reference_bridge.runner")
    accepted = rejected = 0
    health.write("STARTING", drive_root_reachable=True, github_reachable=True, accepted_count=accepted, rejected_count=rejected)
    while True:
        try:
            summary = bridge.run_once()
            accepted += int(summary.accepted)
            rejected += int(summary.rejected)
            health.write(
                "HEALTHY",
                drive_root_reachable=True,
                github_reachable=True,
                last_poll_utc=_utc_now(),
                accepted_count=accepted,
                rejected_count=rejected,
                last_error_code=None,
            )
        except KeyboardInterrupt:
            logger.info("reference bridge stopping")
            health.write("STOPPING", drive_root_reachable=True, github_reachable=True, accepted_count=accepted, rejected_count=rejected)
            return 0
        except Exception as exc:
            code = getattr(exc, "code", exc.__class__.__name__)
            logger.warning("reference bridge degraded: %s", code)
            health.write(
                "DEGRADED",
                drive_root_reachable=True,
                github_reachable=False,
                last_poll_utc=_utc_now(),
                accepted_count=accepted,
                rejected_count=rejected,
                last_error_code=str(code),
            )
        try:
            sleep(config.poll_interval_seconds)
        except KeyboardInterrupt:
            logger.info("reference bridge stopping")
            health.write("STOPPING", drive_root_reachable=True, github_reachable=True, accepted_count=accepted, rejected_count=rejected)
            return 0
