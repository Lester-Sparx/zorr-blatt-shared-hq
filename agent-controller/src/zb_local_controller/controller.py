from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Callable

from .backends.base import BackendError
from .events import format_event
from .github_cli import GitHubCLIError
from .local_paths import ReferenceValidationError, resolve_reference, result_paths
from .task_contract import TaskContractError, parse_task


@dataclass(frozen=True)
class RunSummary:
    discovered: int = 0
    processed: int = 0
    submitted: int = 0
    skipped: int = 0


class Controller:
    def __init__(
        self,
        github: Any,
        inbox_root: Path,
        result_root: Path,
        backend_registry: dict[tuple[str, str], Any],
        poll_interval_seconds: float = 15.0,
        max_execution_seconds: float = 900.0,
        clock: Callable[[], float] = time.time,
    ):
        self.github = github
        self.inbox_root = Path(inbox_root)
        self.result_root = Path(result_root)
        self.backend_registry = dict(backend_registry)
        self.poll_interval_seconds = poll_interval_seconds
        self.max_execution_seconds = float(max_execution_seconds)
        self._clock = clock
        self._active_task_id: str | None = None
        self._executions: dict[str, str] = {}
        self._execution_started_at: dict[str, float] = {}

    @staticmethod
    def _parse_event(body: str, task_id: str) -> tuple[str | None, str | None]:
        if "ZB_AGENT_EVENT_V0" not in body:
            return None, None
        values: dict[str, str] = {}
        for line in body.splitlines():
            if " = " in line:
                key, value = line.split(" = ", 1)
                values[key.strip()] = value.strip()
        if values.get("TASK_ID") != task_id:
            return None, None
        execution = values.get("EXECUTION_ID")
        if execution == "NONE":
            execution = None
        return values.get("STATE"), execution

    def _latest_event(self, issue: Any, task_id: str) -> tuple[str | None, str | None]:
        for comment in reversed(issue.comments):
            state, execution = self._parse_event(comment, task_id)
            if state:
                return state, execution
        return None, None

    def _existing_result_metadata(self, task_id: str) -> dict[str, Any] | None:
        image_path, meta_path = result_paths(self.result_root, task_id)
        if not image_path.is_file() or not meta_path.is_file():
            return None
        try:
            content = image_path.read_bytes()
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not (
            bool(content)
            and meta.get("taskId") == task_id
            and meta.get("state") == "RESULT_READY"
            and meta.get("sha256") == hashlib.sha256(content).hexdigest()
        ):
            return None
        return meta

    def _valid_existing_result(self, task_id: str) -> bool:
        return self._existing_result_metadata(task_id) is not None

    def _execution_journal_path(self, task_id: str) -> Path:
        _, meta_path = result_paths(self.result_root, task_id)
        return meta_path.parent / "execution.json"

    def _load_execution_journal(self, task_id: str) -> dict[str, Any] | None:
        path = self._execution_journal_path(task_id)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if data.get("taskId") != task_id or not isinstance(data.get("executionId"), str) or not data.get("executionId"):
            return None
        return data

    def _persist_execution_journal(self, task: Any, execution_id: str) -> None:
        path = self._execution_journal_path(task.task_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        payload = {
            "taskId": task.task_id,
            "executionId": execution_id,
            "startedAt": self._clock(),
        }
        tmp.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, path)
        self._execution_started_at[task.task_id] = float(payload["startedAt"])

    def _clear_execution_journal(self, task_id: str) -> None:
        self._execution_started_at.pop(task_id, None)
        try:
            self._execution_journal_path(task_id).unlink(missing_ok=True)
        except OSError:
            pass

    def _persist_result(self, task: Any, execution_id: str, content: bytes) -> str:
        if not content:
            raise BackendError("BACKEND_OUTPUT_INVALID")
        image_path, meta_path = result_paths(self.result_root, task.task_id)
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_tmp = image_path.with_suffix(".png.tmp")
        meta_tmp = meta_path.with_suffix(".json.tmp")
        image_tmp.write_bytes(content)
        os.replace(image_tmp, image_path)
        digest = hashlib.sha256(content).hexdigest()
        metadata = {
            "taskId": task.task_id,
            "agent": task.agent,
            "backend": "COMFYUI_LOCAL",
            "state": "RESULT_READY",
            "executionId": execution_id,
            "sha256": digest,
            "bytes": len(content),
            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        meta_tmp.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(meta_tmp, meta_path)
        return digest

    def _post(self, issue_number: int, task_id: str, state: str, execution_id: str | None = None, result_sha256: str | None = None, error_code: str | None = None) -> bool:
        try:
            self.github.post_comment(issue_number, format_event(task_id, state, execution_id, result_sha256, error_code))
        except GitHubCLIError:
            return False
        return True

    def _finish_execution(self, issue: Any, task: Any, backend: Any, execution_id: str) -> bool:
        started_at = self._execution_started_at.get(task.task_id)
        if started_at is not None and self._clock() - started_at > self.max_execution_seconds:
            posted = self._post(issue.number, task.task_id, "FAILED", execution_id, error_code="EXECUTION_TIMEOUT")
            if posted:
                self._active_task_id = None
                self._executions.pop(task.task_id, None)
                self._clear_execution_journal(task.task_id)
            return posted

        poll = backend.poll(execution_id)
        if poll.state == "RUNNING":
            return False
        if poll.state == "FAILED":
            posted = self._post(issue.number, task.task_id, "FAILED", execution_id, error_code=poll.error_code or "BACKEND_EXECUTION_FAILED")
            if posted:
                self._active_task_id = None
                self._executions.pop(task.task_id, None)
                self._clear_execution_journal(task.task_id)
            return posted
        if poll.state != "COMPLETE":
            raise BackendError("BACKEND_POLL_INVALID")
        content = backend.collect(execution_id)
        digest = self._persist_result(task, execution_id, content)
        posted = self._post(issue.number, task.task_id, "RESULT_READY", execution_id, digest)
        if posted:
            self._active_task_id = None
            self._executions.pop(task.task_id, None)
            self._clear_execution_journal(task.task_id)
        return posted

    def run_once(self) -> RunSummary:
        issues = self.github.list_candidate_issues()
        processed = submitted = skipped = 0

        # Reconstruct accepted/running execution before dispatching any new task.
        if self._active_task_id is None:
            for issue in issues:
                try:
                    candidate = parse_task(issue.body)
                except TaskContractError:
                    continue
                durable_state, durable_execution = self._latest_event(issue, candidate.task_id)
                if durable_state in {"FAILED", "RESULT_READY"}:
                    self._clear_execution_journal(candidate.task_id)
                    continue
                journal = self._load_execution_journal(candidate.task_id)
                execution_id = durable_execution if durable_state == "RUNNING" and durable_execution else None
                if execution_id is None and journal:
                    execution_id = str(journal["executionId"])
                if execution_id:
                    self._active_task_id = candidate.task_id
                    self._executions[candidate.task_id] = execution_id
                    if journal is None:
                        self._persist_execution_journal(candidate, execution_id)
                    else:
                        started_at = journal.get("startedAt")
                        if isinstance(started_at, (int, float)):
                            self._execution_started_at[candidate.task_id] = float(started_at)
                        else:
                            self._persist_execution_journal(candidate, execution_id)
                    break

        for issue in issues:
            try:
                task = parse_task(issue.body)
            except TaskContractError:
                skipped += 1
                continue

            durable_state, durable_execution = self._latest_event(issue, task.task_id)
            if durable_state in {"FAILED", "RESULT_READY"}:
                self._clear_execution_journal(task.task_id)
                skipped += 1
                continue

            existing_result = self._existing_result_metadata(task.task_id)
            if existing_result is not None:
                execution_id = existing_result.get("executionId")
                if isinstance(execution_id, str) and execution_id:
                    posted = self._post(
                        issue.number,
                        task.task_id,
                        "RESULT_READY",
                        execution_id,
                        str(existing_result["sha256"]),
                    )
                    processed += 1
                    if posted:
                        self._clear_execution_journal(task.task_id)
                        if self._active_task_id == task.task_id:
                            self._active_task_id = None
                            self._executions.pop(task.task_id, None)
                else:
                    skipped += 1
                continue

            if self._active_task_id and self._active_task_id != task.task_id:
                skipped += 1
                continue

            backend = self.backend_registry.get((task.agent, task.task_kind))
            if backend is None:
                self._post(issue.number, task.task_id, "FAILED", error_code="BACKEND_MAPPING_INVALID")
                processed += 1
                continue

            active_execution = self._executions.get(task.task_id) if self._active_task_id == task.task_id else None
            if active_execution:
                if durable_state != "RUNNING":
                    if not self._post(issue.number, task.task_id, "RUNNING", active_execution):
                        processed += 1
                        break
                try:
                    finished = self._finish_execution(issue, task, backend, active_execution)
                except BackendError as exc:
                    posted = self._post(issue.number, task.task_id, "FAILED", active_execution, error_code=exc.code)
                    if posted:
                        self._active_task_id = None
                        self._executions.pop(task.task_id, None)
                        self._clear_execution_journal(task.task_id)
                    finished = posted
                processed += 1
                if not finished:
                    break
                continue

            try:
                reference = resolve_reference(self.inbox_root, task.task_id)
            except ReferenceValidationError as exc:
                self._post(issue.number, task.task_id, "FAILED", error_code=exc.code)
                processed += 1
                continue
            if reference is None:
                if durable_state != "WAITING_REFERENCE":
                    self._post(issue.number, task.task_id, "WAITING_REFERENCE")
                    processed += 1
                else:
                    skipped += 1
                continue

            self._active_task_id = task.task_id
            try:
                backend.ensure_ready()
                execution_id = backend.submit(task, reference)
                self._executions[task.task_id] = execution_id
                self._persist_execution_journal(task, execution_id)
                submitted += 1
                if not self._post(issue.number, task.task_id, "RUNNING", execution_id):
                    processed += 1
                    break
                finished = self._finish_execution(issue, task, backend, execution_id)
                processed += 1
                if not finished:
                    break
            except BackendError as exc:
                execution_id = self._executions.get(task.task_id)
                posted = self._post(issue.number, task.task_id, "FAILED", execution_id, error_code=exc.code)
                if posted:
                    self._active_task_id = None
                    self._executions.pop(task.task_id, None)
                    self._clear_execution_journal(task.task_id)
                processed += 1
                if not posted and execution_id:
                    break
        return RunSummary(len(issues), processed, submitted, skipped)

    def run_forever(self) -> None:
        while True:
            self.run_once()
            time.sleep(self.poll_interval_seconds)
