from __future__ import annotations

import os
from pathlib import Path
import sys
import time
from typing import Any, Callable
from uuid import uuid4

from .github_cli import GitHubCLIError


class DaemonPreflightError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def run_daemon_preflight(config: Any, config_path: Path, github: Any) -> None:
    config_path = Path(config_path)
    if not config_path.is_file():
        raise DaemonPreflightError("DAEMON_CONFIG_MISSING")
    if sys.version_info < (3, 12):
        raise DaemonPreflightError("DAEMON_PYTHON_UNSUPPORTED")

    runtime_root = Path(config.daemon_runtime_root)
    probe = runtime_root / f".daemon-preflight-{uuid4().hex}.tmp"
    try:
        runtime_root.mkdir(parents=True, exist_ok=True)
        with probe.open("xb") as handle:
            handle.write(b"ok")
            handle.flush()
        probe.unlink()
    except OSError as exc:
        try:
            probe.unlink(missing_ok=True)
        except OSError:
            pass
        raise DaemonPreflightError("DAEMON_RUNTIME_UNWRITABLE") from exc

    github.ensure_authenticated()


class DaemonRunner:
    def __init__(
        self,
        controller: Any,
        health: Any,
        logger: Any,
        poll_interval_seconds: float,
        sleep_fn: Callable[[float], None] = time.sleep,
    ):
        self.controller = controller
        self.health = health
        self.logger = logger
        self.poll_interval_seconds = float(poll_interval_seconds)
        self.sleep_fn = sleep_fn

    def run(self) -> int:
        while True:
            try:
                summary = self.controller.run_once()
                self.health.write("HEALTHY", last_cycle=summary)
                self.logger.info(
                    "controller cycle complete discovered=%s processed=%s submitted=%s skipped=%s",
                    summary.discovered,
                    summary.processed,
                    summary.submitted,
                    summary.skipped,
                )
            except GitHubCLIError as exc:
                code = str(exc) or exc.__class__.__name__
                self.logger.warning("controller cycle degraded: %s", code)
                self.health.write("DEGRADED", last_error_code=code)
            except KeyboardInterrupt:
                self.logger.info("controller daemon stopping")
                self.health.write("STOPPING")
                return 0
            except Exception as exc:
                code = str(getattr(exc, "code", exc.__class__.__name__))
                self.logger.exception("controller daemon fatal: %s", code)
                self.health.write("FATAL", last_error_code=code)
                return 1
            try:
                self.sleep_fn(self.poll_interval_seconds)
            except KeyboardInterrupt:
                self.logger.info("controller daemon stopping")
                self.health.write("STOPPING")
                return 0
