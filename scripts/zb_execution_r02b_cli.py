from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from scripts.zb_execution_cli import (
    _TRUSTED_ENV_KEYS,
    _required_env,
    build_execution_worker,
    capture_copilot_token_and_scrub,
    run_lester_execution,
    trusted_paths_from_env,
)
from scripts.zb_execution_contract import parse_execution_request, render_execution_result
from scripts.zb_execution_profiles import resolve_profile
from scripts.zb_execution_workspace import SubprocessCommand


R02B_TASK_ID = "ZB_EXECUTION_PROOF_R01"
R02B_TASK_REVISION = 2
R02B_DESIGN_HEAD = "2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8"
R02B_PROFILE = "LESTER_IMPLEMENT_R02A"
R02B_SCOPE = ("tests/fixtures/zb-execution-proof/",)


def _require_r02b_request(request_body: str):
    request = parse_execution_request(request_body)
    if (
        request.task_id != R02B_TASK_ID
        or request.task_revision != R02B_TASK_REVISION
        or request.design_head != R02B_DESIGN_HEAD
        or request.logical_role != "LESTER"
        or request.execution_profile != R02B_PROFILE
        or request.execution_profile_version != 1
        or request.allowed_write_scope != R02B_SCOPE
        or request.no_auto_merge is not True
        or request.production_active is not False
    ):
        raise ValueError("R02B_EXECUTION_AUTHORITY_MISMATCH")
    return request


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    execute = parser.add_subparsers(dest="command_name", required=True).add_parser("execute")
    execute.add_argument("--from-env", action="store_true", required=True)
    args = parser.parse_args(argv)
    if args.command_name != "execute":
        raise ValueError("R02B_EXECUTE_ONLY")

    workspace_root = Path(_required_env(os.environ, "GITHUB_WORKSPACE")).resolve()
    paths = trusted_paths_from_env(
        {key: value for key, value in os.environ.items() if key in _TRUSTED_ENV_KEYS},
        workspace_root=workspace_root,
    )
    request_path = paths["ZB_EXECUTION_REQUEST_PATH"]
    result_path = paths["ZB_EXECUTION_RESULT_PATH"]
    evidence_dir = paths["ZB_EVIDENCE_DIR"]
    request_body = request_path.read_text(encoding="utf-8")
    request = _require_r02b_request(request_body)
    profile = resolve_profile(request)

    execution_id = _required_env(os.environ, "ZB_EXECUTION_ID")
    workflow_run_id = _required_env(os.environ, "ZB_WORKFLOW_RUN_ID")
    workflow_run_attempt = int(_required_env(os.environ, "ZB_WORKFLOW_RUN_ATTEMPT"))
    runner_temp = Path(_required_env(os.environ, "RUNNER_TEMP")).resolve()
    worktree_root = runner_temp / f"zb-r02b-{workflow_run_id}-{workflow_run_attempt}"
    runner_provenance = os.environ.get(
        "ZB_RUNNER_PROVENANCE",
        "github-actions:github-hosted:windows-2025",
    )

    copilot_token = capture_copilot_token_and_scrub(os.environ)
    command = SubprocessCommand()
    worker = build_execution_worker(
        profile=profile,
        command=command,
        workspace_root=workspace_root,
        job_root=evidence_dir.parent,
        copilot_token=copilot_token,
    )
    result = run_lester_execution(
        request_body,
        repo_root=workspace_root,
        job_root=evidence_dir.parent,
        worktree_root=worktree_root,
        execution_id=execution_id,
        workflow_run_id=workflow_run_id,
        workflow_run_attempt=workflow_run_attempt,
        runner_provenance=runner_provenance,
        worker=worker,
        command=command,
        verification_commands=((sys.executable, "-m", "scripts.zb_execution_proof_verify"),),
    )
    result_path.write_text(render_execution_result(result), encoding="utf-8")
    return 0 if result.terminal_state == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
