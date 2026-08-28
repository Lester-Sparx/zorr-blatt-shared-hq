from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path, PurePosixPath
from typing import Mapping, MutableMapping, Sequence

from scripts.zb_execution_contract import (
    ExecutionRequest,
    ExecutionResult,
    parse_execution_request,
    parse_execution_result,
    render_execution_result,
)
from scripts.zb_execution_copilot import CopilotWorker
from scripts.zb_execution_evidence import EvidenceError, build_evidence_bundle, verify_evidence_manifest
from scripts.zb_execution_profiles import ExecutionProfile, ExecutionProfileError, resolve_profile
from scripts.zb_execution_worker import (
    AUTH_ENV_KEYS,
    OpenCodeWorker,
    WorkerError,
    WorkerPort,
    sanitized_execution_env,
)
from scripts.zb_execution_workspace import (
    CommandPort,
    SubprocessCommand,
    WorkspaceError,
    audit_workspace,
    create_detached_worktree,
    remove_worktree,
)


_PATH_ENV_KEYS = frozenset(
    {
        "ZB_EXECUTION_REQUEST_PATH",
        "ZB_EXECUTION_RESULT_PATH",
        "ZB_EVIDENCE_DIR",
        "ZB_CANDIDATE_EVIDENCE_DIR",
        "ZB_QC_RESULT_PATH",
    }
)
_ID_ENV_KEYS = frozenset(
    {
        "ZB_EXECUTION_ID",
        "ZB_WORKFLOW_RUN_ID",
        "ZB_WORKFLOW_RUN_ATTEMPT",
    }
)
_TRUSTED_ENV_KEYS = _PATH_ENV_KEYS | _ID_ENV_KEYS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _result(
    request: ExecutionRequest,
    *,
    execution_id: str,
    workflow_run_id: str,
    workflow_run_attempt: int,
    runner_provenance: str,
    terminal_state: str,
    result_code: str,
    process_exit_code: int,
    start_head: str,
    end_head: str,
    changed_files: tuple[str, ...],
    test_evidence_refs: tuple[str, ...],
    artifact_evidence_refs: tuple[str, ...],
    started_at: str,
    finished_at: str,
) -> ExecutionResult:
    return ExecutionResult(
        execution_request_id=request.execution_request_id,
        execution_id=execution_id,
        attempt=workflow_run_attempt,
        message_id=request.message_id,
        correlation_id=request.correlation_id,
        task_id=request.task_id,
        task_revision=request.task_revision,
        logical_role=request.logical_role,
        execution_profile=request.execution_profile,
        execution_profile_version=request.execution_profile_version,
        base_sha=request.base_sha,
        start_head=start_head,
        end_head=end_head,
        terminal_state=terminal_state,
        result_code=result_code,
        process_exit_code=process_exit_code,
        changed_files=changed_files,
        test_evidence_refs=test_evidence_refs,
        artifact_evidence_refs=artifact_evidence_refs,
        workflow_run_id=workflow_run_id,
        workflow_run_attempt=workflow_run_attempt,
        runner_provenance=runner_provenance,
        started_at=started_at,
        finished_at=finished_at,
        production_active=False,
    )


def trusted_paths_from_env(env: Mapping[str, str], *, workspace_root: Path) -> dict[str, Path]:
    workspace_root = Path(workspace_root).resolve()
    for key in env:
        if key.startswith("ZB_") and key not in _TRUSTED_ENV_KEYS:
            raise ValueError("FROM_ENV_UNKNOWN_KEY")

    resolved: dict[str, Path] = {}
    for key in _PATH_ENV_KEYS:
        raw = env.get(key)
        if raw is None:
            continue
        if not raw or "\x00" in raw:
            raise ValueError("FROM_ENV_PATH_INVALID")
        path = Path(raw).resolve()
        if path != workspace_root and workspace_root not in path.parents:
            raise ValueError("FROM_ENV_PATH_ESCAPES_WORKSPACE")
        resolved[key] = path
    return resolved


def capture_copilot_token_and_scrub(env: MutableMapping[str, str]) -> str:
    token = env.get("COPILOT_GITHUB_TOKEN", "")
    for key in AUTH_ENV_KEYS:
        env.pop(key, None)
    return token


def build_execution_worker(
    profile: ExecutionProfile,
    *,
    command: CommandPort,
    workspace_root: Path,
    job_root: Path,
    copilot_token: str,
) -> WorkerPort:
    if profile.worker_backend == "opencode":
        return OpenCodeWorker(
            command=command,
            config_path=Path(workspace_root).resolve() / "config" / "zb-execution" / "opencode-r01.json",
        )
    if profile.worker_backend == "copilot-cli":
        return CopilotWorker(
            command=command,
            auth_token=copilot_token,
            home_path=Path(job_root).resolve() / "copilot-home",
        )
    raise WorkerError("WORKER_BACKEND_REJECTED")


def _capture_patch(worktree: Path, command: CommandPort) -> bytes:
    completed = command.run(
        ["git", "-C", str(worktree), "diff", "--binary", "--no-ext-diff", "--no-renames"],
        cwd=None,
    )
    if completed.returncode != 0:
        raise WorkspaceError("PATCH_CAPTURE_FAILED")
    return completed.stdout.encode("utf-8", "surrogateescape")


def _run_verification_commands(
    worktree: Path,
    commands: Sequence[Sequence[str]],
    command: CommandPort,
) -> tuple[bool, str]:
    if not commands:
        return True, "NO_VERIFICATION_COMMANDS_CONFIGURED_FOR_TEST_SEAM\n"
    chunks: list[str] = []
    for argv in commands:
        if not argv or any(not isinstance(part, str) or "\x00" in part for part in argv):
            return False, "INVALID_VERIFICATION_COMMAND\n"
        completed = command.run(list(argv), cwd=worktree, env=sanitized_execution_env())
        chunks.append(f"$ {' '.join(argv)}\n")
        chunks.append(completed.stdout)
        chunks.append(completed.stderr)
        chunks.append(f"EXIT={completed.returncode}\n")
        if completed.returncode != 0:
            return False, "".join(chunks)
    return True, "".join(chunks)


def _load_verified_replay(evidence_dir: Path, request_body: str) -> ExecutionResult | None:
    if not evidence_dir.exists():
        return None
    verify_evidence_manifest(evidence_dir)
    stored_request_body = (evidence_dir / "request.txt").read_text(encoding="utf-8")
    if stored_request_body != request_body:
        raise EvidenceError("REPLAY_REQUEST_MISMATCH")
    stored_request = parse_execution_request(stored_request_body)
    stored_result = parse_execution_result((evidence_dir / "result.txt").read_text(encoding="utf-8"))
    if (
        stored_result.execution_request_id != stored_request.execution_request_id
        or stored_result.message_id != stored_request.message_id
        or stored_result.correlation_id != stored_request.correlation_id
        or stored_result.task_id != stored_request.task_id
        or stored_result.task_revision != stored_request.task_revision
        or stored_result.execution_profile != stored_request.execution_profile
        or stored_result.execution_profile_version != stored_request.execution_profile_version
        or stored_result.base_sha != stored_request.base_sha
    ):
        raise EvidenceError("REPLAY_BINDING_MISMATCH")
    return stored_result


def run_lester_execution(
    request_body: str,
    *,
    repo_root: Path,
    job_root: Path,
    execution_id: str,
    workflow_run_id: str,
    workflow_run_attempt: int,
    runner_provenance: str,
    worker: WorkerPort,
    command: CommandPort,
    verification_commands: Sequence[Sequence[str]] = (),
) -> ExecutionResult:
    request = parse_execution_request(request_body)
    profile = resolve_profile(request)
    if profile.logical_role != "LESTER":
        raise ValueError("LESTER_PROFILE_REQUIRED")

    repo_root = Path(repo_root).resolve()
    job_root = Path(job_root).resolve()
    job_root.mkdir(parents=True, exist_ok=True)
    worktree = job_root / "worktree"
    evidence_dir = job_root / "evidence"
    replay = _load_verified_replay(evidence_dir, request_body)
    if replay is not None:
        return replay

    started_at = _now()
    terminal_state = "EXECUTION_ERROR"
    result_code = "EXECUTION_ERROR"
    process_exit_code = -1
    start_head = request.base_sha
    end_head = request.base_sha
    changed_files: tuple[str, ...] = ()
    patch_bytes = b""
    tests_text = ""
    worker_events = ""
    worktree_created = False

    try:
        create_detached_worktree(repo_root, request.base_sha, worktree, command)
        worktree_created = True
        try:
            outcome = worker.execute(request, worktree=worktree, timeout_seconds=request.timeout_seconds)
            process_exit_code = outcome.exit_code
            worker_events = outcome.stdout
            if outcome.stderr:
                worker_events += ("\n" if worker_events and not worker_events.endswith("\n") else "") + outcome.stderr
            if outcome.timed_out:
                terminal_state = "TIMEOUT"
                result_code = "WORKER_TIMEOUT"
            elif outcome.exit_code != 0:
                terminal_state = "FAIL"
                result_code = "WORKER_NONZERO_EXIT"
            else:
                terminal_state = "PASS"
                result_code = "OK"
        except WorkerError as exc:
            terminal_state = "EXECUTION_ERROR"
            result_code = "WORKER_EXECUTION_ERROR"
            process_exit_code = -1
            worker_events = f"{type(exc).__name__}:{exc}\n"

        verification_ok, tests_text = _run_verification_commands(worktree, verification_commands, command)
        if not verification_ok and terminal_state == "PASS":
            terminal_state = "FAIL"
            result_code = "VERIFICATION_FAILED"

        try:
            snapshot = audit_workspace(
                worktree,
                request.allowed_write_scope,
                command,
                expected_base_sha=request.base_sha,
            )
            start_head = snapshot.start_head
            end_head = snapshot.end_head
            changed_files = snapshot.changed_files
            patch_bytes = _capture_patch(worktree, command)
        except WorkspaceError as exc:
            if terminal_state == "PASS":
                terminal_state = "FAIL"
                result_code = "WORKSPACE_EVIDENCE_FAILED"
            tests_text += f"WORKSPACE_ERROR={exc}\n"
    except WorkspaceError as exc:
        terminal_state = "BLOCKED"
        result_code = "WORKSPACE_BLOCKED"
        process_exit_code = -1
        tests_text = f"WORKSPACE_BLOCKED={exc}\n"

    finished_at = _now()
    result = _result(
        request,
        execution_id=execution_id,
        workflow_run_id=workflow_run_id,
        workflow_run_attempt=workflow_run_attempt,
        runner_provenance=runner_provenance,
        terminal_state=terminal_state,
        result_code=result_code,
        process_exit_code=process_exit_code,
        start_head=start_head,
        end_head=end_head,
        changed_files=changed_files,
        test_evidence_refs=("tests.txt",),
        artifact_evidence_refs=("manifest.json", "patch.diff"),
        started_at=started_at,
        finished_at=finished_at,
    )
    rendered = render_execution_result(result)
    build_evidence_bundle(
        request_body=request_body,
        result_body=rendered,
        patch_bytes=patch_bytes,
        changed_files=changed_files,
        tests_text=tests_text or "NO_TEST_EVIDENCE\n",
        worker_events=worker_events,
        evidence_dir=evidence_dir,
    )
    if worktree_created:
        try:
            remove_worktree(repo_root, worktree, command)
        except WorkspaceError:
            pass
    return result


def _path_in_scope(path: str, scopes: tuple[str, ...]) -> bool:
    pure = PurePosixPath(path)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        return False
    normalized = pure.as_posix()
    for scope in scopes:
        if scope.endswith("/") and normalized.startswith(scope):
            return True
        if normalized == scope:
            return True
    return False


def run_duncan_qc(
    request_body: str,
    *,
    candidate_evidence_dir: Path,
    execution_id: str,
    workflow_run_id: str,
    workflow_run_attempt: int,
    runner_provenance: str,
) -> ExecutionResult:
    request = parse_execution_request(request_body)
    profile = resolve_profile(request)
    if profile.logical_role != "DUNCAN":
        raise ValueError("DUNCAN_PROFILE_REQUIRED")

    started_at = _now()
    terminal_state = "FAIL"
    result_code = "EVIDENCE_INVALID"
    process_exit_code = 0
    start_head = request.base_sha
    end_head = request.base_sha
    changed_files: tuple[str, ...] = ()
    candidate_dir = Path(candidate_evidence_dir).resolve()

    try:
        verify_evidence_manifest(candidate_dir)
        lester_request_body = (candidate_dir / "request.txt").read_text(encoding="utf-8")
        lester_result_body = (candidate_dir / "result.txt").read_text(encoding="utf-8")
        lester_request = parse_execution_request(lester_request_body)
        lester_result = parse_execution_result(lester_result_body)
        lester_profile = resolve_profile(lester_request)
        if lester_profile.logical_role != "LESTER" or lester_result.logical_role != "LESTER":
            raise ValueError("CANDIDATE_NOT_LESTER")

        if execution_id == lester_result.execution_id:
            terminal_state = "BLOCKED"
            result_code = "EXECUTION_ID_NOT_DISTINCT"
        else:
            bindings_match = (
                lester_result.execution_request_id == lester_request.execution_request_id
                and lester_result.message_id == lester_request.message_id
                and lester_result.correlation_id == lester_request.correlation_id
                and lester_result.task_id == lester_request.task_id
                and lester_result.task_revision == lester_request.task_revision
                and lester_result.execution_profile == lester_request.execution_profile
                and lester_result.execution_profile_version == lester_request.execution_profile_version
                and lester_result.base_sha == lester_request.base_sha
                and lester_result.start_head == lester_request.base_sha
                and lester_result.end_head == lester_request.base_sha
            )
            listed = tuple(
                line for line in (candidate_dir / "changed-files.txt").read_text(encoding="utf-8").splitlines() if line
            )
            tests_text = (candidate_dir / "tests.txt").read_text(encoding="utf-8")
            scope_ok = all(_path_in_scope(path, lester_request.allowed_write_scope) for path in lester_result.changed_files)
            if (
                not bindings_match
                or lester_result.terminal_state != "PASS"
                or listed != lester_result.changed_files
                or not scope_ok
                or not tests_text
            ):
                terminal_state = "FAIL"
                result_code = "EVIDENCE_BINDING_FAILED"
            else:
                terminal_state = "PASS"
                result_code = "QC_PASS"
            start_head = lester_result.start_head
            end_head = lester_result.end_head
            changed_files = lester_result.changed_files
    except (EvidenceError, OSError, ValueError, ExecutionProfileError):
        terminal_state = "FAIL"
        result_code = "EVIDENCE_INVALID"
        process_exit_code = 1

    finished_at = _now()
    return _result(
        request,
        execution_id=execution_id,
        workflow_run_id=workflow_run_id,
        workflow_run_attempt=workflow_run_attempt,
        runner_provenance=runner_provenance,
        terminal_state=terminal_state,
        result_code=result_code,
        process_exit_code=process_exit_code,
        start_head=start_head,
        end_head=end_head,
        changed_files=changed_files,
        test_evidence_refs=("tests.txt",),
        artifact_evidence_refs=("manifest.json", "patch.diff"),
        started_at=started_at,
        finished_at=finished_at,
    )


def _required_env(env: Mapping[str, str], name: str) -> str:
    value = env.get(name)
    if not value:
        raise ValueError(f"MISSING_ENV:{name}")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command_name", required=True)
    execute = sub.add_parser("execute")
    execute.add_argument("--from-env", action="store_true", required=True)
    qc = sub.add_parser("qc")
    qc.add_argument("--from-env", action="store_true", required=True)
    args = parser.parse_args(argv)

    workspace_root = Path(_required_env(os.environ, "GITHUB_WORKSPACE")).resolve()
    paths = trusted_paths_from_env(
        {key: value for key, value in os.environ.items() if key in _TRUSTED_ENV_KEYS},
        workspace_root=workspace_root,
    )
    execution_id = _required_env(os.environ, "ZB_EXECUTION_ID")
    workflow_run_id = _required_env(os.environ, "ZB_WORKFLOW_RUN_ID")
    workflow_run_attempt = int(_required_env(os.environ, "ZB_WORKFLOW_RUN_ATTEMPT"))
    runner_provenance = os.environ.get("ZB_RUNNER_PROVENANCE", "github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01")

    if args.command_name == "execute":
        request_path = paths["ZB_EXECUTION_REQUEST_PATH"]
        result_path = paths["ZB_EXECUTION_RESULT_PATH"]
        evidence_dir = paths["ZB_EVIDENCE_DIR"]
        request_body = request_path.read_text(encoding="utf-8")
        profile = resolve_profile(parse_execution_request(request_body))
        copilot_token = capture_copilot_token_and_scrub(os.environ)
        command = SubprocessCommand()
        worker = build_execution_worker(
            profile,
            command=command,
            workspace_root=workspace_root,
            job_root=evidence_dir.parent,
            copilot_token=copilot_token,
        )
        result = run_lester_execution(
            request_body,
            repo_root=workspace_root,
            job_root=evidence_dir.parent,
            execution_id=execution_id,
            workflow_run_id=workflow_run_id,
            workflow_run_attempt=workflow_run_attempt,
            runner_provenance=runner_provenance,
            worker=worker,
            command=command,
            verification_commands=(),
        )
        result_path.write_text(render_execution_result(result), encoding="utf-8")
        return 0 if result.terminal_state == "PASS" else 1

    result = run_duncan_qc(
        paths["ZB_EXECUTION_REQUEST_PATH"].read_text(encoding="utf-8"),
        candidate_evidence_dir=paths["ZB_CANDIDATE_EVIDENCE_DIR"],
        execution_id=execution_id,
        workflow_run_id=workflow_run_id,
        workflow_run_attempt=workflow_run_attempt,
        runner_provenance=runner_provenance,
    )
    paths["ZB_QC_RESULT_PATH"].write_text(render_execution_result(result), encoding="utf-8")
    return 0 if result.terminal_state == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
