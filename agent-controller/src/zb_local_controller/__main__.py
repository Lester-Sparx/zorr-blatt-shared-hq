from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Callable, Any
import uuid

from .backends.canon_reference_edit import CanonReferenceEditBackend
from .backends.comfyui import ComfyUIBackend
from .config import ConfigurationError, ControllerConfig, load_config
from .controller import Controller
from .daemon_health import DaemonHealthWriter, configure_daemon_logger
from .daemon_runner import DaemonPreflightError, DaemonRunner, run_daemon_preflight
from .github_cli import GitHubCLI, GitHubConfigurationError
from .instance_lock import ControllerInstanceBusy, ControllerInstanceLock, ControllerRuntimeUnwritable


def _default_backend_registry(config: ControllerConfig):
    smoke = ComfyUIBackend(config.comfyui_url, config.workflow_path)
    canon = CanonReferenceEditBackend(
        base_url=config.comfyui_url,
        workflow_path=config.canon_reference_workflow_path,
        canon_prompt_path=config.canon_prompt_path,
        comfyui_input_root=config.comfyui_input_root,
        model_name=config.canon_model_name,
        denoise=config.canon_denoise,
        max_long_side=config.canon_max_long_side,
        negative_prompt=config.canon_negative_prompt,
    )
    return {
        ("SALVADOR", "PRODUCTION_IMAGE_EDIT"): smoke,
        ("SALVADOR", "CANON_REFERENCE_EDIT"): canon,
    }


def _build_controller(config: ControllerConfig, github: Any, backend_registry_factory: Callable[[ControllerConfig], dict[tuple[str, str], Any]]) -> Controller:
    backend_registry = backend_registry_factory(config)
    return Controller(
        github,
        config.inbox_root,
        config.result_root,
        backend_registry,
        poll_interval_seconds=config.poll_interval_seconds,
        max_execution_seconds=config.max_execution_seconds,
    )


def main(
    argv: list[str] | None = None,
    *,
    github_factory: Callable[[str], Any] = GitHubCLI,
    backend_registry_factory: Callable[[ControllerConfig], dict[tuple[str, str], Any]] = _default_backend_registry,
) -> int:
    parser = argparse.ArgumentParser(prog="zb_local_controller")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="process one polling cycle and exit")
    mode.add_argument("--daemon", action="store_true", help="run controller daemon")
    mode.add_argument("--daemon-preflight", action="store_true", help="validate daemon startup dependencies without task processing")
    parser.add_argument("--config", type=Path, help="optional controller JSON config")
    args = parser.parse_args(argv)

    if (args.daemon or args.daemon_preflight) and args.config is None:
        print("CONFIGURATION_ERROR DAEMON_CONFIG_REQUIRED", file=sys.stderr)
        return 2

    try:
        config = load_config(args.config) if args.config else ControllerConfig()
        github = github_factory(config.repository)

        if args.daemon_preflight:
            run_daemon_preflight(config, args.config, github)
            print("ZB_CONTROLLER_DAEMON_PREFLIGHT PASS")
            return 0

        with ControllerInstanceLock(config.daemon_runtime_root):
            if args.daemon:
                instance_id = str(uuid.uuid4())
                pid = os.getpid()
                health = DaemonHealthWriter(
                    config.daemon_runtime_root,
                    config.repository,
                    args.config,
                    config.poll_interval_seconds,
                    pid,
                    instance_id,
                )
                logger = configure_daemon_logger(config.daemon_runtime_root, instance_id, pid)
                health.write("STARTING")
                try:
                    run_daemon_preflight(config, args.config, github)
                except Exception as exc:
                    code = str(getattr(exc, "code", exc.__class__.__name__))
                    health.write("FATAL", last_error_code=code)
                    raise
                controller = _build_controller(config, github, backend_registry_factory)
                return DaemonRunner(controller, health, logger, config.poll_interval_seconds).run()

            controller = _build_controller(config, github, backend_registry_factory)
            if args.once:
                summary = controller.run_once()
                print(
                    "CYCLE_COMPLETE "
                    f"discovered={summary.discovered} processed={summary.processed} "
                    f"submitted={summary.submitted} skipped={summary.skipped}"
                )
                return 0
            controller.run_forever()
            return 0
    except ControllerInstanceBusy:
        print("CONTROLLER_INSTANCE_BUSY", file=sys.stderr)
        return 3
    except (ConfigurationError, GitHubConfigurationError, DaemonPreflightError, ControllerRuntimeUnwritable) as exc:
        code = getattr(exc, "code", exc.__class__.__name__)
        print(f"CONFIGURATION_ERROR {code}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
