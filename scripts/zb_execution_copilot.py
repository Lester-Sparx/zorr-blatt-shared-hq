from __future__ import annotations

from pathlib import Path
import re

from scripts.zb_execution_contract import ExecutionRequest
from scripts.zb_execution_profiles import COPILOT_CLI_VERSION, COPILOT_MODEL
from scripts.zb_execution_worker import (
    CommandRunner,
    WorkerError,
    WorkerOutcome,
    sanitized_execution_env,
)


_PROOF_TASK_ID = "ZB_EXECUTION_PROOF_R01"
_PROOF_TASK_REVISION = 2
_PROOF_DESIGN_HEAD = "2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8"
_PROOF_TARGET = "tests/fixtures/zb-execution-proof/result.txt"


class CopilotWorker:
    def __init__(
        self,
        *,
        command: CommandRunner,
        auth_token: str,
        home_path: Path,
        binary: str = "copilot",
        expected_version: str = COPILOT_CLI_VERSION,
        model: str = COPILOT_MODEL,
    ):
        if not auth_token or not auth_token.strip():
            raise WorkerError("COPILOT_TOKEN_MISSING")
        if binary != "copilot":
            raise WorkerError("COPILOT_BINARY_OVERRIDE_REJECTED")
        if expected_version != COPILOT_CLI_VERSION:
            raise WorkerError("COPILOT_VERSION_AUTHORITY_MISMATCH")
        if model != COPILOT_MODEL:
            raise WorkerError("COPILOT_MODEL_AUTHORITY_MISMATCH")
        self._command = command
        self._auth_token = auth_token
        self._home_path = Path(home_path).resolve()
        self._binary = binary
        self._expected_version = expected_version
        self._model = model

    @staticmethod
    def _prompt(request: ExecutionRequest) -> str:
        lines = [
            "ZORR BLATT bounded substantive edit.",
            f"WORK_ID={request.task_id}",
            f"REVISION={request.task_revision}",
            f"BASE_SHA={request.base_sha}",
            f"DESIGN_HEAD={request.design_head}",
            f"ALLOWED_WRITE_SCOPE={';'.join(request.allowed_write_scope)}",
            "Edit only an existing file inside ALLOWED_WRITE_SCOPE.",
            "Do not create files.",
            "Do not commit, push, merge, change repository settings, secrets, canon, or OWNER locks.",
            "Leave the candidate edit uncommitted for trusted verification.",
        ]
        if (
            request.task_id == _PROOF_TASK_ID
            and request.task_revision == _PROOF_TASK_REVISION
            and request.design_head == _PROOF_DESIGN_HEAD
        ):
            lines.extend(
                (
                    f"TARGET_FILE={_PROOF_TARGET}",
                    "Change exactly one existing file: TARGET_FILE.",
                    "The target starts with exactly: ZB_R02A_PROOF_TARGET_V1 followed by STATE = BEFORE.",
                    "Replace exactly STATE = BEFORE with STATE = AFTER.",
                    "Preserve ZB_R02A_PROOF_TARGET_V1 exactly and add no other content.",
                )
            )
        return "\n".join(lines)

    def _preflight_home(self, worktree: Path) -> None:
        try:
            self._home_path.relative_to(worktree)
        except ValueError:
            pass
        else:
            raise WorkerError("COPILOT_HOME_INSIDE_WORKTREE")
        if self._home_path.exists() and self._home_path.is_symlink():
            raise WorkerError("COPILOT_HOME_SYMLINK_REJECTED")
        self._home_path.mkdir(parents=True, exist_ok=True)

    def _verify_version(self, *, worktree: Path) -> None:
        env = sanitized_execution_env()
        try:
            result = self._command.run(
                [self._binary, "--version"],
                cwd=worktree,
                timeout=30,
                env=env,
            )
        except Exception as exc:
            raise WorkerError("COPILOT_VERSION_CHECK_FAILED") from exc
        if result.returncode != 0:
            raise WorkerError("COPILOT_VERSION_CHECK_FAILED")
        versions = re.findall(r"\d+\.\d+\.\d+", result.stdout)
        if self._expected_version not in versions:
            raise WorkerError("COPILOT_VERSION_MISMATCH")

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
        self._preflight_home(worktree)
        self._verify_version(worktree=worktree)

        env = sanitized_execution_env()
        env["COPILOT_GITHUB_TOKEN"] = self._auth_token
        env["COPILOT_HOME"] = str(self._home_path)
        argv = [
            self._binary,
            "-p",
            self._prompt(request),
            f"--model={self._model}",
            "--no-ask-user",
            "--available-tools=edit,view,grep,glob",
            "--allow-tool=write",
            "--disable-builtin-mcps",
            "--no-auto-update",
            "--no-custom-instructions",
            "--no-experimental",
            "--no-remote",
            "--no-remote-export",
            "--disallow-temp-dir",
            "--output-format=json",
            "--no-banner",
            "--no-color",
        ]
        try:
            result = self._command.run(argv, cwd=worktree, timeout=timeout_seconds, env=env)
        except TimeoutError:
            return WorkerOutcome(exit_code=124, stdout="", stderr="worker timeout", timed_out=True)
        except Exception as exc:
            raise WorkerError("COPILOT_EXECUTION_ERROR") from exc
        return WorkerOutcome(
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=False,
        )
