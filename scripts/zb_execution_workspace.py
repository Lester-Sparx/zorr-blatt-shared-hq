from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
import os
import subprocess
from typing import Mapping, Protocol, Sequence


class WorkspaceError(RuntimeError):
    pass


@dataclass(frozen=True)
class Completed:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class WorkspaceSnapshot:
    start_head: str
    end_head: str
    changed_files: tuple[str, ...]
    patch_sha256: str


class CommandPort(Protocol):
    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: Mapping[str, str] | None = None,
    ) -> Completed: ...


class SubprocessCommand:
    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: Mapping[str, str] | None = None,
    ) -> Completed:
        if not argv or any(not isinstance(part, str) or "\x00" in part for part in argv):
            raise WorkspaceError("INVALID_ARGV")
        try:
            result = subprocess.run(
                list(argv),
                cwd=str(cwd) if cwd is not None else None,
                timeout=timeout,
                env=dict(env) if env is not None else None,
                text=True,
                encoding="utf-8",
                errors="surrogateescape",
                capture_output=True,
                shell=False,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise WorkspaceError("COMMAND_EXECUTION_ERROR") from exc
        return Completed(tuple(argv), result.returncode, result.stdout, result.stderr)


def _checked(command: CommandPort, argv: Sequence[str], *, cwd: Path | None = None, timeout: int | None = None) -> Completed:
    result = command.run(argv, cwd=cwd, timeout=timeout)
    if result.returncode != 0:
        raise WorkspaceError(f"COMMAND_FAILED:{argv[0]}")
    return result


def _safe_repo_path(value: str, *, error_code: str) -> str:
    if not value or "\x00" in value or "\\" in value or value.startswith(("/", "~")):
        raise WorkspaceError(error_code)
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise WorkspaceError(error_code)
    normalized = path.as_posix()
    if normalized.startswith("../") or "/../" in normalized:
        raise WorkspaceError(error_code)
    return normalized


def _scope_allows(path: str, scope: str) -> bool:
    if scope.endswith("/"):
        return path.startswith(scope)
    return path == scope


def create_detached_worktree(
    repo_root: Path,
    base_sha: str,
    worktree: Path,
    command: CommandPort,
) -> None:
    repo_root = Path(repo_root).resolve()
    worktree = Path(worktree).resolve()
    if len(base_sha) != 40 or any(ch not in "0123456789abcdef" for ch in base_sha):
        raise WorkspaceError("INVALID_BASE_SHA")
    if worktree == repo_root or repo_root in worktree.parents:
        raise WorkspaceError("WORKTREE_INSIDE_SOURCE_REJECTED")
    if worktree.exists():
        raise WorkspaceError("WORKTREE_PATH_EXISTS")

    status = _checked(command, ["git", "status", "--porcelain"], cwd=repo_root).stdout
    if status.strip():
        raise WorkspaceError("SOURCE_CHECKOUT_DIRTY")

    _checked(command, ["git", "cat-file", "-e", f"{base_sha}^{{commit}}"], cwd=repo_root)
    _checked(command, ["git", "worktree", "add", "--detach", str(worktree), base_sha], cwd=repo_root)
    actual = _checked(command, ["git", "-C", str(worktree), "rev-parse", "HEAD"]).stdout.strip()
    if actual != base_sha:
        try:
            _checked(command, ["git", "worktree", "remove", "--force", str(worktree)], cwd=repo_root)
        finally:
            raise WorkspaceError("WORKTREE_BASE_MISMATCH")


def _changed_files(worktree: Path, command: CommandPort) -> tuple[str, ...]:
    tracked = _checked(
        command,
        ["git", "-C", str(worktree), "diff", "--name-only", "--no-renames"],
    ).stdout.splitlines()
    untracked = _checked(
        command,
        ["git", "-C", str(worktree), "ls-files", "--others", "--exclude-standard"],
    ).stdout.splitlines()
    normalized = {_safe_repo_path(item.strip(), error_code="INVALID_CHANGED_PATH") for item in (*tracked, *untracked) if item.strip()}
    return tuple(sorted(normalized))


def audit_workspace(
    worktree: Path,
    allowed_scope: tuple[str, ...],
    command: CommandPort,
    *,
    expected_base_sha: str | None = None,
) -> WorkspaceSnapshot:
    worktree = Path(worktree).resolve()
    if not worktree.is_dir():
        raise WorkspaceError("WORKTREE_MISSING")
    scopes = tuple(_safe_repo_path(scope.rstrip("/") if not scope.endswith("/") else scope[:-1], error_code="INVALID_WRITE_SCOPE") + ("/" if scope.endswith("/") else "") for scope in allowed_scope)
    if not scopes:
        raise WorkspaceError("INVALID_WRITE_SCOPE")

    head = _checked(command, ["git", "-C", str(worktree), "rev-parse", "HEAD"]).stdout.strip()
    if expected_base_sha is not None and head != expected_base_sha:
        raise WorkspaceError("HEAD_MOVED")

    changed = _changed_files(worktree, command)
    for path in changed:
        if not any(_scope_allows(path, scope) for scope in scopes):
            raise WorkspaceError("WRITE_SCOPE_VIOLATION")

    patch = _checked(
        command,
        ["git", "-C", str(worktree), "diff", "--binary", "--no-ext-diff", "--no-renames"],
    ).stdout.encode("utf-8", "surrogateescape")
    digest = hashlib.sha256(patch).hexdigest()
    end_head = _checked(command, ["git", "-C", str(worktree), "rev-parse", "HEAD"]).stdout.strip()
    if expected_base_sha is not None and end_head != expected_base_sha:
        raise WorkspaceError("HEAD_MOVED")
    return WorkspaceSnapshot(start_head=head, end_head=end_head, changed_files=changed, patch_sha256=digest)


def remove_worktree(repo_root: Path, worktree: Path, command: CommandPort) -> None:
    repo_root = Path(repo_root).resolve()
    worktree = Path(worktree).resolve()
    result = command.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=repo_root)
    if result.returncode != 0 and worktree.exists():
        raise WorkspaceError("WORKTREE_REMOVE_FAILED")
