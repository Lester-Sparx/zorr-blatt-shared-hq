from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any

from .backends.base import BackendError
from .events import format_event
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
    ):
        self.github = github
        self.inbox_root = Path(inbox_root)
        self.result_root = Path(result_root)
        self.backend_registry = dict(backend_registry)
        self.poll_interval_seconds = poll_interval_seconds
        self._active_task_id: str | None = None
        self._executions: dict[str, str] = {}

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

    def _valid_existing_result(self, task_id: str) -> bool:
        image_path, meta_path = result_paths(self.result_root, task_id)
        if not image_path.is_file() or not meta_path.is_file():
            return False
        try:
            content = image_path.read_bytes()
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            return False
        return (
            bool(content)
            and meta.get("taskId") == task_id
            and meta.get("state") == "RESULT_READY"
            and meta.get("sha256") == hashlib.sha256(content).hexdigest()
        )

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

    def _post(self, issue_number: int, task_id: str, state: str, execution_id: str | None = None, result_sha256: str | None = None, error_code: str | None = None) -> None:
        self.github.post_comment(issue_number, format_event(task_id, state, execution_id, result_sha256, error_code))

    def _finish_execution(self, issue: Any, task: Any, backend: Any, execution_id: str) -> bool:
        poll = backend.poll(execution_id)
        if poll.state == "RUNNING":
            return False
        if poll.state == "FAILED":
            self._post(issue.number, task.task_id, "FAILED", execution_id, error_code=poll.error_code or "BACKEND_EXECUTION_FAILED")
            self._active_task_id = None
            self._executions.pop(task.task_id, None)
            return True
        if poll.state != "COMPLETE":
            raise BackendError("BACKEND_POLL_INVALID")
        content = backend.collect(execution_id)
        digest = self._persist_result(task, execution_id, content)
        self._post(issue.number, task.task_id, "RESULT_READY", execution_id, digest)
        self._active_task_id = None
        self._executions.pop(task.task_id, None)
        return True

    def run_once(self) -> RunSummary:
        issues = self.github.list_candidate_issues()
        processed = submitted = skipped = 0
        for issue in issues:
            try:
                task = parse_task(issue.body)
            except TaskContractError:
                skipped += 1
                continue

            if self._valid_existing_result(task.task_id):
                skipped += 1
                continue
            durable_state, durable_execution = self._latest_event(issue, task.task_id)
            if durable_state == "RESULT_READY":
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

            if durable_state == "RUNNING" and durable_execution:
                self._active_task_id = task.task_id
                self._executions[task.task_id] = durable_execution
                try:
                    finished = self._finish_execution(issue, task, backend, durable_execution)
                except BackendError as exc:
                    self._post(issue.number, task.task_id, "FAILED", durable_execution, error_code=exc.code)
                    self._active_task_id = None
                    self._executions.pop(task.task_id, None)
                    finished = True
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
                submitted += 1
                self._post(issue.number, task.task_id, "RUNNING", execution_id)
                finished = self._finish_execution(issue, task, backend, execution_id)
                processed += 1
                if not finished:
                    break
            except BackendError as exc:
                self._post(issue.number, task.task_id, "FAILED", error_code=exc.code)
                self._active_task_id = None
                self._executions.pop(task.task_id, None)
                processed += 1
        return RunSummary(len(issues), processed, submitted, skipped)

    def run_forever(self) -> None:
        while True:
            self.run_once()
            time.sleep(self.poll_interval_seconds)
