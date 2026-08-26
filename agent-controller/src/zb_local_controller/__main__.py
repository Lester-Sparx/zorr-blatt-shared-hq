from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Any

from .backends.canon_reference_edit import CanonReferenceEditBackend
from .backends.comfyui import ComfyUIBackend
from .config import ConfigurationError, ControllerConfig, load_config
from .controller import Controller
from .github_cli import GitHubCLI, GitHubConfigurationError


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


def main(
    argv: list[str] | None = None,
    *,
    github_factory: Callable[[str], Any] = GitHubCLI,
    backend_registry_factory: Callable[[ControllerConfig], dict[tuple[str, str], Any]] = _default_backend_registry,
) -> int:
    parser = argparse.ArgumentParser(prog="zb_local_controller")
    parser.add_argument("--once", action="store_true", help="process one polling cycle and exit")
    parser.add_argument("--config", type=Path, help="optional controller JSON config")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config) if args.config else ControllerConfig()
        github = github_factory(config.repository)
        backend_registry = backend_registry_factory(config)
        controller = Controller(
            github,
            config.inbox_root,
            config.result_root,
            backend_registry,
            poll_interval_seconds=config.poll_interval_seconds,
            max_execution_seconds=config.max_execution_seconds,
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
