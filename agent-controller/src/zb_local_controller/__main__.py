from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Any

from .backends.comfyui import ComfyUIBackend
from .config import ConfigurationError, ControllerConfig, load_config
from .controller import Controller
from .github_cli import GitHubCLI, GitHubConfigurationError


def _default_backend_factory(config: ControllerConfig):
    return ComfyUIBackend(config.comfyui_url, config.workflow_path)


def main(
    argv: list[str] | None = None,
    *,
    github_factory: Callable[[str], Any] = GitHubCLI,
    backend_factory: Callable[[ControllerConfig], Any] = _default_backend_factory,
) -> int:
    parser = argparse.ArgumentParser(prog="zb_local_controller")
    parser.add_argument("--once", action="store_true", help="process one polling cycle and exit")
    parser.add_argument("--config", type=Path, help="optional controller JSON config")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config) if args.config else ControllerConfig()
        github = github_factory(config.repository)
        backend = backend_factory(config)
        controller = Controller(
            github,
            config.inbox_root,
            config.result_root,
            {("SALVADOR", "PRODUCTION_IMAGE_EDIT"): backend},
            poll_interval_seconds=config.poll_interval_seconds,
        )
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
    except (ConfigurationError, GitHubConfigurationError) as exc:
        code = getattr(exc, "code", exc.__class__.__name__)
        print(f"CONFIGURATION_ERROR {code}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
