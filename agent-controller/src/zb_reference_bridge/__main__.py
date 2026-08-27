from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any, Callable

from .bridge import ReferenceBridge
from .config import BridgeConfig, BridgeConfigError, load_bridge_config
from .github_cli import BridgeGitHubCLI, BridgeGitHubError
from .health import BRIDGE_HEALTH_SCHEMA, HEALTH_STATES, BridgeHealthWriter, config_sha256, configure_bridge_logger
from .instance_lock import BridgeInstanceBusy, BridgeInstanceLock, BridgeRuntimeUnwritable
from .runner import BridgePreflightError, run_bridge_forever, run_preflight

_STATUS_STATES = HEALTH_STATES | {"MISSING", "STALE"}


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("heartbeat missing")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _pid_alive(pid: int) -> str:
    try:
        pid = int(pid)
        if pid <= 0:
            return "NO"
        os.kill(pid, 0)
        return "YES"
    except ProcessLookupError:
        return "NO"
    except PermissionError:
        return "YES"
    except Exception:
        return "UNKNOWN"


def _read_status(config: BridgeConfig) -> dict[str, str]:
    result = {
        "HEALTH_STATE": "MISSING",
        "PID": "NONE",
        "PID_ALIVE": "UNKNOWN",
        "INSTANCE_ID": "NONE",
        "HEARTBEAT_AGE_SEC": "NONE",
        "CONFIG_SHA256": "NONE",
        "DRIVE_ROOT_REACHABLE": "UNKNOWN",
    }
    path = Path(config.runtime_root) / "health.json"
    if not path.is_file():
        return result
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema") != BRIDGE_HEALTH_SCHEMA:
            raise ValueError("schema")
        state = data.get("state")
        if state not in HEALTH_STATES:
            raise ValueError("state")
        heartbeat = _parse_utc(data.get("heartbeatUtc"))
        age = max(0.0, (datetime.now(timezone.utc) - heartbeat).total_seconds())
        threshold = max(60.0, 3.0 * float(config.poll_interval_seconds))
        result["HEALTH_STATE"] = "STALE" if age > threshold else state
        result["HEARTBEAT_AGE_SEC"] = f"{age:.1f}"
        pid = int(data.get("pid"))
        result["PID"] = str(pid)
        result["PID_ALIVE"] = _pid_alive(pid)
        instance = data.get("instanceId")
        if not isinstance(instance, str) or not instance.strip():
            raise ValueError("instance")
        result["INSTANCE_ID"] = instance.strip()
        sha = data.get("configSha256")
        if not isinstance(sha, str) or not sha.strip():
            raise ValueError("sha")
        result["CONFIG_SHA256"] = sha.strip()
        reachable = data.get("driveRootReachable")
        if not isinstance(reachable, bool):
            raise ValueError("drive")
        result["DRIVE_ROOT_REACHABLE"] = "YES" if reachable else "NO"
    except Exception:
        return {
            "HEALTH_STATE": "MISSING",
            "PID": "NONE",
            "PID_ALIVE": "UNKNOWN",
            "INSTANCE_ID": "NONE",
            "HEARTBEAT_AGE_SEC": "NONE",
            "CONFIG_SHA256": "NONE",
            "DRIVE_ROOT_REACHABLE": "UNKNOWN",
        }
    return result


def _print_status(config: BridgeConfig) -> None:
    status = _read_status(config)
    print("ZB_REFERENCE_BRIDGE_STATUS_V1")
    for key in ("HEALTH_STATE", "PID", "PID_ALIVE", "INSTANCE_ID", "HEARTBEAT_AGE_SEC", "CONFIG_SHA256", "DRIVE_ROOT_REACHABLE"):
        print(f"{key} = {status[key]}")


def main(
    argv: list[str] | None = None,
    *,
    github_factory: Callable[[str], Any] = BridgeGitHubCLI,
    bridge_factory: Callable[[BridgeConfig, Any], Any] = ReferenceBridge,
    lock_factory: Callable[[Path], Any] = BridgeInstanceLock,
    health_factory: Callable[..., Any] = BridgeHealthWriter,
) -> int:
    parser = argparse.ArgumentParser(prog="zb_reference_bridge")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--once", action="store_true")
    modes.add_argument("--daemon", action="store_true")
    modes.add_argument("--preflight", action="store_true")
    modes.add_argument("--status", action="store_true")
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        config = load_bridge_config(args.config)
        if args.status:
            _print_status(config)
            return 0

        github = github_factory(config.repository)
        if args.preflight:
            run_preflight(config, github)
            print("ZB_REFERENCE_BRIDGE_PREFLIGHT PASS")
            return 0

        with lock_factory(config.runtime_root):
            if args.once:
                summary = bridge_factory(config, github).run_once()
                print(
                    "BRIDGE_CYCLE_COMPLETE "
                    f"discovered={summary.discovered} waiting={summary.waiting} "
                    f"accepted={summary.accepted} rejected={summary.rejected} skipped={summary.skipped}"
                )
                return 0

            health = health_factory(config.runtime_root, config_sha256(args.config))
            logger = configure_bridge_logger(config.runtime_root)
            run_preflight(config, github, health=health)
            bridge = bridge_factory(config, github)
            return run_bridge_forever(bridge, config, health, logger=logger)
    except BridgeInstanceBusy:
        print("REFERENCE_BRIDGE_INSTANCE_BUSY", file=sys.stderr)
        return 3
    except (BridgeConfigError, BridgeGitHubError, BridgePreflightError, BridgeRuntimeUnwritable) as exc:
        code = getattr(exc, "code", exc.__class__.__name__)
        print(f"REFERENCE_BRIDGE_ERROR {code}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
