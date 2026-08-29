from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import subprocess
from typing import Any, Callable

from zb_local_controller.task_contract import TaskContractError, parse_task

from .archive import ArchiveStore
from .models import Provenance, RecordStatus, SourceRecord, SourceType


_ALLOWED_EVENT_STATES = {"WAITING_REFERENCE", "RUNNING", "RESULT_READY", "FAILED"}
_REQUIRED_EVENT_KEYS = {
    "TASK_ID",
    "AGENT",
    "STATE",
    "BACKEND",
    "EXECUTION_ID",
    "RESULT_SHA256",
    "ERROR_CODE",
}


class ShadowIngressError(RuntimeError):
    pass


@dataclass(frozen=True)
class IngressSummary:
    issues_seen: int = 0
    events_archived: int = 0


def _default_runner(args: list[str], **kwargs: Any):
    return subprocess.run(args, **kwargs)


class GitHubShadowReader:
    """Read-only GitHub adapter for durable SALVADOR task/event evidence."""

    def __init__(
        self,
        repository: str,
        *,
        runner: Callable[..., Any] | None = None,
    ) -> None:
        self.repository = str(repository)
        self._runner = runner or _default_runner

    def list_candidate_issues(self) -> list[dict[str, object]]:
        args = [
            "gh",
            "issue",
            "list",
            "--repo",
            self.repository,
            "--state",
            "open",
            "--search",
            "ZB_AGENT_TASK_V0",
            "--limit",
            "100",
            "--json",
            "number,title,body,comments",
        ]
        try:
            result = self._runner(args, capture_output=True, text=True, shell=False)
        except FileNotFoundError as exc:
            raise ShadowIngressError("GH_CLI_UNAVAILABLE") from exc
        if result.returncode != 0:
            raise ShadowIngressError("GH_ISSUE_LIST_FAILED")
        try:
            payload = json.loads(result.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise ShadowIngressError("GH_OUTPUT_INVALID") from exc
        if not isinstance(payload, list):
            raise ShadowIngressError("GH_OUTPUT_INVALID")
        return [item for item in payload if isinstance(item, dict)]


def _parse_created_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        created = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if created.tzinfo is None or created.utcoffset() is None:
        return None
    return created


def _parse_event(body: object, *, task_id: str) -> dict[str, str] | None:
    if not isinstance(body, str):
        return None
    lines = body.splitlines()
    if not lines or lines[0].strip() != "ZB_AGENT_EVENT_V0":
        return None

    values: dict[str, str] = {}
    for line in lines[1:]:
        if not line.strip():
            break
        if " = " not in line:
            return None
        key, value = line.split(" = ", 1)
        key = key.strip()
        value = value.strip()
        if key in values:
            return None
        values[key] = value

    if not _REQUIRED_EVENT_KEYS.issubset(values):
        return None
    if values["TASK_ID"] != task_id:
        return None
    if values["AGENT"] != "SALVADOR":
        return None
    if values["STATE"] not in _ALLOWED_EVENT_STATES:
        return None
    if values["BACKEND"] != "COMFYUI_LOCAL":
        return None
    return values


def _comment_actor(comment: dict[str, object]) -> str | None:
    author = comment.get("author")
    if not isinstance(author, dict):
        return None
    login = author.get("login")
    return str(login) if isinstance(login, str) and login else None


def _source_record(
    *,
    store: ArchiveStore,
    issue_number: int,
    comment_id: str,
    comment_body: str,
    actor: str,
    created_at: datetime,
    event: dict[str, str],
) -> SourceRecord:
    raw = store.ingest_raw(comment_body.encode("utf-8"))
    record_id = f"salvador.github.comment.{comment_id}"
    source = Provenance(
        source_id=record_id,
        source_type=SourceType.SOURCE_QUOTE,
        source_location=f"raw:{raw.sha256}",
        source_hash=raw.sha256,
        authority=f"ZB_CONTROLLER_RUNTIME:{actor}",
        created_at=created_at,
    )
    text = " | ".join(
        [
            "SALVADOR RUNTIME",
            f"ISSUE={issue_number}",
            f"TASK_ID={event['TASK_ID']}",
            f"STATE={event['STATE']}",
            f"EXECUTION_ID={event['EXECUTION_ID']}",
            f"RESULT_SHA256={event['RESULT_SHA256']}",
            f"ERROR_CODE={event['ERROR_CODE']}",
        ]
    )
    return SourceRecord(
        record_id=record_id,
        entity_id="SALVADOR",
        status=RecordStatus.OPEN,
        source=source,
        created_at=created_at,
        text=text,
    )


def ingest_salvador_events(
    store: ArchiveStore,
    reader: GitHubShadowReader,
    *,
    expected_actor: str,
) -> IngressSummary:
    issues = reader.list_candidate_issues()
    archived = 0

    for issue in issues:
        body = issue.get("body")
        try:
            task = parse_task(str(body or ""))
        except TaskContractError:
            continue
        if task.agent != "SALVADOR":
            continue

        try:
            issue_number = int(issue.get("number"))
        except (TypeError, ValueError):
            continue
        comments = issue.get("comments")
        if not isinstance(comments, list):
            continue

        for comment in comments:
            if not isinstance(comment, dict):
                continue
            actor = _comment_actor(comment)
            if actor != expected_actor:
                continue
            event = _parse_event(comment.get("body"), task_id=task.task_id)
            if event is None:
                continue
            created_at = _parse_created_at(comment.get("createdAt"))
            if created_at is None:
                continue
            comment_id_value = comment.get("id")
            if not isinstance(comment_id_value, (str, int)):
                continue
            comment_id = str(comment_id_value).strip()
            if not comment_id:
                continue
            comment_body = comment.get("body")
            if not isinstance(comment_body, str):
                continue

            record = _source_record(
                store=store,
                issue_number=issue_number,
                comment_id=comment_id,
                comment_body=comment_body,
                actor=actor,
                created_at=created_at,
                event=event,
            )
            store.append_record(record)
            archived += 1

    return IngressSummary(issues_seen=len(issues), events_archived=archived)
