from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Mapping, Protocol

from scripts.zb_execution_contract import ExecutionRequest
from scripts.zb_execution_profiles import OPENCODE_VERSION
from scripts.zb_execution_workspace import Completed


class WorkerError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkerOutcome:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool


class WorkerPort(Protocol):
    def execute(
        self,
        request: ExecutionRequest,
        *,
        worktree: Path,
        timeout_seconds: int,
    ) -> WorkerOutcome: ...


class CommandRunner(Protocol):
    def run(
        self,
        argv,
        *,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: Mapping[str, str] | None = None,
    ) -> Completed: ...


AUTH_ENV_KEYS = frozenset(
    {
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "GITHUB_PAT",
        "ACTIONS_ID_TOKEN_REQUEST_URL",
        "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
        "ACTIONS_RUNTIME_TOKEN",
        "ACTIONS_RESULTS_URL",
        "COPILOT_GITHUB_TOKEN",
        "COPILOT_PROVIDER_API_KEY",
        "COPILOT_PROVIDER_BASE_URL",
        "COPILOT_ALLOW_ALL",
        "COPILOT_MODEL",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
    }
)
_STRIP_ENV = AUTH_ENV_KEYS


def sanitized_execution_env(base: Mapping[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if base is None else base)
    for key in AUTH_ENV_KEYS:
        env.pop(key, None)
    return env


_PROJECT_CONFIG_PATHS = ("opencode.json", "opencode.jsonc", ".opencode")


class OpenCodeWorker:
    def __init__(
        self,
        *,
        command: CommandRunner,
        config_path: Path,
        binary: str = "opencode",
        expected_version: str = OPENCODE_VERSION,
    ):
        if binary != "opencode":
            raise WorkerError("OPENCODE_BINARY_OVERRIDE_REJECTED")
        if expected_version != OPENCODE_VERSION:
            raise WorkerError("OPENCODE_VERSION_AUTHORITY_MISMATCH")
        self._command = command
        self._config_path = Path(config_path).resolve()
        self._binary = binary
        self._expected_version = expected_version

    def _environment(self) -> dict[str, str]:
        env = sanitized_execution_env()
        env["OPENCODE_CONFIG"] = str(self._config_path)
        env["OPENCODE_DISABLE_AUTOUPDATE"] = "true"
        env["OPENCODE_AUTO_SHARE"] = "false"
        return env

    def _preflight_paths(self, worktree: Path) -> None:
        if not self._config_path.is_file() or self._config_path.is_symlink():
            raise WorkerError("OPENCODE_POLICY_MISSING")
        for relative in _PROJECT_CONFIG_PATHS:
            if (worktree / relative).exists():
                raise WorkerError("PROJECT_OPENCODE_CONFIG_PRESENT")

    def _verify_version(self, *, worktree: Path, env: Mapping[str, str]) -> None:
        try:
            result = self._command.run(
                [self._binary, "--version"],
                cwd=worktree,
                timeout=30,
                env=env,
            )
        except Exception as exc:
            raise WorkerError("OPENCODE_VERSION_CHECK_FAILED") from exc
        if result.returncode != 0:
            raise WorkerError("OPENCODE_VERSION_CHECK_FAILED")
        tokens = re.findall(r"\d+\.\d+\.\d+", result.stdout)
        if self._expected_version not in tokens:
            raise WorkerError("OPENCODE_VERSION_MISMATCH")

    @staticmethod
    def _prompt(request: ExecutionRequest) -> str:
        scope = ";".join(request.allowed_write_scope)
        source_refs = ";".join(request.source_refs)
        evidence_refs = ";".join(request.evidence_input_refs)
        return "\n".join(
            (
                "ZORR BLATT bounded substantive execution.",
                f"TASK_ID={request.task_id}",
                f"TASK_REVISION={request.task_revision}",
                f"BASE_SHA={request.base_sha}",
                f"DESIGN_HEAD={request.design_head}",
                f"SOURCE_REFS={source_refs}",
                f"EVIDENCE_INPUT_REFS={evidence_refs}",
                f"ALLOWED_WRITE_SCOPE={scope}",
                "Edit only files inside ALLOWED_WRITE_SCOPE.",
                "DO NOT commit.",
                "DO NOT push.",
                "DO NOT merge.",
                "DO NOT change production activation, canon, OWNER locks, repository secrets, or workflow authority.",
                "Run only verification commands permitted by the static execution profile.",
                "Leave the workspace with uncommitted candidate changes and no Git HEAD movement.",
            )
        )

    def execute(
        self,
        request: ExecutionRequest,
        *,
        worktree: Path,
        timeout_seconds: int,
    ) -> WorkerOutcome:
        worktree = Path(worktree).resolve()
        if timeout_seconds <= 0:
            raise WorkerError("INVALID_WORKER_TIMEOUT")
        self._preflight_paths(worktree)
        env = self._environment()
        self._verify_version(worktree=worktree, env=env)
        argv = [
            self._binary,
            "run",
            "--format",
            "json",
            "--agent",
            "build",
            self._prompt(request),
        ]
        try:
            result = self._command.run(argv, cwd=worktree, timeout=timeout_seconds, env=env)
        except TimeoutError:
            return WorkerOutcome(exit_code=124, stdout="", stderr="worker timeout", timed_out=True)
        except Exception as exc:
            raise WorkerError("OPENCODE_EXECUTION_ERROR") from exc
        return WorkerOutcome(
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=False,
        )
