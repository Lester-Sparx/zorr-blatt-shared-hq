from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


REPOSITORY = "Lester-Sparx/zorr-blatt-shared-hq"
COMMUNICATION_PR = 111
TRACKER_ISSUE = 106
TRANSPORT_ACTOR = "Lester-Sparx"
TASK_ID = "ZB_GITHUB_NATIVE_BASE_R01"
TASK_REVISION = 1
APPROVED_DESIGN_HEAD = "81c44232b72b4a98c8ad0ac2ea6a0a2876f988bc"
MARKER = "ZB_AGENT_MESSAGE_V1"
API_ROOT = "https://api.github.com"
TRACKER_ISSUE_URL = f"{API_ROOT}/repos/{REPOSITORY}/issues/{TRACKER_ISSUE}"

EXPECTED_STAGES = (
    ("JINGO", "LESTER", "ASSIGN"),
    ("LESTER", "JINGO", "RETURN"),
    ("JINGO", "DUNCAN", "QC_REQUEST"),
    ("DUNCAN", "JINGO", "QC_VERDICT"),
    ("JINGO", "DJANGO", "ARCH_REVIEW"),
    ("DJANGO", "JINGO", "ARCH_VERDICT"),
    ("JINGO", "JINGO", "CLOSE_REQUEST"),
)
_REPLAY_STATES = frozenset({"RECEIVED", "RUNNING", "RESULT", "BLOCKED"})

_FIELDS = (
    "MESSAGE_ID",
    "EVENT_ID",
    "CORRELATION_ID",
    "CAUSATION_MESSAGE_ID",
    "TASK_ID",
    "FROM_ROLE",
    "TO_ROLE",
    "MESSAGE_KIND",
    "BASE_SHA",
    "TASK_REVISION",
    "DESIGN_HEAD",
    "NO_AUTO_MERGE",
)
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class ProtocolError(ValueError):
    pass


class PersistenceError(RuntimeError):
    pass


@dataclass(frozen=True)
class RootMessage:
    message_id: str
    event_id: str
    correlation_id: str
    causation_message_id: str
    task_id: str
    from_role: str
    to_role: str
    message_kind: str
    base_sha: str
    task_revision: int
    design_head: str
    no_auto_merge: bool


@dataclass(frozen=True)
class EventContext:
    repository: str
    issue_number: int
    comment_id: int
    actor: str
    run_id: str
    run_attempt: str
    github_sha: str


class GitHubPort(Protocol):
    def create_tracker_comment(self, body: str) -> int: ...
    def read_comment(self, comment_id: int) -> dict[str, Any]: ...
    def list_tracker_comments(self) -> list[dict[str, Any]]: ...


class GitHubApi:
    def __init__(self, token: str, *, timeout_seconds: float = 10.0):
        if not token:
            raise PersistenceError("GITHUB_TOKEN is required")
        self._token = token
        self._timeout_seconds = timeout_seconds

    def _request_json(self, url: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> Any:
        data = None
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "zorr-blatt-communication-base",
        }
        if payload is not None:
            data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except Exception as exc:
            raise PersistenceError(f"GitHub API {method} failed") from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PersistenceError("GitHub API returned invalid JSON") from exc

    def create_tracker_comment(self, body: str) -> int:
        result = self._request_json(
            f"{TRACKER_ISSUE_URL}/comments",
            method="POST",
            payload={"body": body},
        )
        comment_id = result.get("id") if isinstance(result, dict) else None
        if not isinstance(comment_id, int) or isinstance(comment_id, bool) or comment_id <= 0:
            raise PersistenceError("GitHub API did not return a numeric comment ID")
        return comment_id

    def read_comment(self, comment_id: int) -> dict[str, Any]:
        if not isinstance(comment_id, int) or isinstance(comment_id, bool) or comment_id <= 0:
            raise PersistenceError("invalid comment ID")
        result = self._request_json(f"{API_ROOT}/repos/{REPOSITORY}/issues/comments/{comment_id}")
        if not isinstance(result, dict):
            raise PersistenceError("GitHub comment read returned non-object")
        return result

    def list_tracker_comments(self) -> list[dict[str, Any]]:
        comments: list[dict[str, Any]] = []
        for page in range(1, 21):
            result = self._request_json(f"{TRACKER_ISSUE_URL}/comments?per_page=100&page={page}")
            if not isinstance(result, list) or not all(isinstance(item, dict) for item in result):
                raise PersistenceError("GitHub tracker comment list returned invalid data")
            comments.extend(result)
            if len(result) < 100:
                return comments
        raise PersistenceError("tracker pagination exceeded safety bound")


def write_and_verify(port: GitHubPort, body: str) -> int:
    comment_id = port.create_tracker_comment(body)
    readback = port.read_comment(comment_id)
    if readback.get("id") != comment_id:
        raise PersistenceError("comment ID read-back mismatch")
    if readback.get("body") != body:
        raise PersistenceError("comment body read-back mismatch")
    if readback.get("issue_url") != TRACKER_ISSUE_URL:
        raise PersistenceError("comment container read-back mismatch")
    return comment_id


def _parse_receipt_fields(body: Any) -> dict[str, str] | None:
    if not isinstance(body, str):
        return None
    lines = body.splitlines()
    if not lines or lines[0] != "ZB_AGENT_RECEIPT_V1":
        return None
    values: dict[str, str] = {}
    for line in lines[1:]:
        if not line or " = " not in line:
            continue
        name, value = line.split(" = ", 1)
        if name in values:
            return None
        values[name] = value
    return values


def _is_replay(message: RootMessage, context: EventContext, port: GitHubPort) -> bool:
    expected_source = str(context.comment_id)
    for comment in port.list_tracker_comments():
        fields = _parse_receipt_fields(comment.get("body"))
        if not fields:
            continue
        if fields.get("MESSAGE_ID") != message.message_id:
            continue
        if fields.get("SOURCE_COMMENT_ID") != expected_source:
            continue
        if fields.get("STATE") in _REPLAY_STATES:
            return True
    return False


def _receipt_body(
    message: RootMessage,
    context: EventContext,
    *,
    from_role: str,
    to_role: str,
    message_kind: str,
    state: str,
    result_code: str,
    execution_id: str,
) -> str:
    return "\n".join(
        [
            "ZB_AGENT_RECEIPT_V1",
            f"MESSAGE_ID = {message.message_id}",
            f"CORRELATION_ID = {message.correlation_id}",
            f"SOURCE_COMMENT_ID = {context.comment_id}",
            f"TASK_ID = {message.task_id}",
            f"TASK_REVISION = {message.task_revision}",
            f"BASE_SHA = {message.base_sha}",
            f"DESIGN_HEAD = {message.design_head}",
            f"SOURCE_ACTOR = {context.actor}",
            f"WORKFLOW_RUN_ID = {context.run_id}",
            f"WORKFLOW_RUN_ATTEMPT = {context.run_attempt}",
            f"LOGICAL_FROM_ROLE = {from_role}",
            f"LOGICAL_TO_ROLE = {to_role}",
            f"MESSAGE_KIND = {message_kind}",
            f"STATE = {state}",
            f"RESULT_CODE = {result_code}",
            f"EXECUTION_ID = {execution_id}",
            "PRODUCTION_ACTIVE = NO",
        ]
    )


def _owner_view_body(message: RootMessage, context: EventContext) -> str:
    return "\n".join(
        [
            "ZB_OWNER_VIEW_V0",
            f"MESSAGE_ID = {message.message_id}",
            f"CORRELATION_ID = {message.correlation_id}",
            f"SOURCE_COMMENT_ID = {context.comment_id}",
            f"TASK_ID = {message.task_id}",
            f"TASK_REVISION = {message.task_revision}",
            f"BASE_SHA = {message.base_sha}",
            f"DESIGN_HEAD = {message.design_head}",
            f"WORKFLOW_RUN_ID = {context.run_id}",
            f"WORKFLOW_RUN_ATTEMPT = {context.run_attempt}",
            "LAST_STAGE = JINGO -> JINGO / CLOSE_REQUEST",
            "OWNER_GATE_REQUIRED = TRUE",
            "OWNER_ACTION_REQUIRED = TRUE",
            "PRODUCTION_ACTIVE = NO",
        ]
    )


def run_base(message: RootMessage, context: EventContext, port: GitHubPort) -> str:
    if _is_replay(message, context, port):
        return "NOOP_REPLAY"

    initial_stage = EXPECTED_STAGES[0]
    write_and_verify(
        port,
        _receipt_body(
            message,
            context,
            from_role=initial_stage[0],
            to_role=initial_stage[1],
            message_kind=initial_stage[2],
            state="RECEIVED",
            result_code="NONE",
            execution_id="NONE",
        ),
    )

    execution_id = f"github-actions:{context.run_id}:{context.run_attempt}"
    write_and_verify(
        port,
        _receipt_body(
            message,
            context,
            from_role=initial_stage[0],
            to_role=initial_stage[1],
            message_kind=initial_stage[2],
            state="RUNNING",
            result_code="NONE",
            execution_id=execution_id,
        ),
    )

    for from_role, to_role, message_kind in EXPECTED_STAGES:
        write_and_verify(
            port,
            _receipt_body(
                message,
                context,
                from_role=from_role,
                to_role=to_role,
                message_kind=message_kind,
                state="RESULT",
                result_code="PASS",
                execution_id=execution_id,
            ),
        )

    write_and_verify(port, _owner_view_body(message, context))
    return "OWNER_GATE_REQUIRED"


def _require_identifier(name: str, value: str) -> None:
    if not _IDENTIFIER.fullmatch(value):
        raise ProtocolError(f"invalid {name}")


def parse_root_message(body: str) -> RootMessage:
    if not isinstance(body, str):
        raise ProtocolError("body must be text")

    lines = body.splitlines()
    if not lines or lines[0] != MARKER:
        raise ProtocolError("invalid marker")

    values: dict[str, str] = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        if " = " not in line:
            raise ProtocolError("invalid field syntax")
        name, value = line.split(" = ", 1)
        if name not in _FIELDS:
            raise ProtocolError(f"unknown field: {name}")
        if name in values:
            raise ProtocolError(f"duplicate field: {name}")
        if value == "":
            raise ProtocolError(f"empty field: {name}")
        values[name] = value

    missing = [name for name in _FIELDS if name not in values]
    if missing:
        raise ProtocolError("missing field: " + ",".join(missing))
    if len(values) != len(_FIELDS):
        raise ProtocolError("invalid field count")

    for name in ("MESSAGE_ID", "EVENT_ID", "CORRELATION_ID"):
        _require_identifier(name, values[name])

    if values["CAUSATION_MESSAGE_ID"] != "NONE":
        raise ProtocolError("initial CAUSATION_MESSAGE_ID must be NONE")
    if values["TASK_ID"] != TASK_ID:
        raise ProtocolError("wrong TASK_ID")
    if values["FROM_ROLE"] != "JINGO":
        raise ProtocolError("wrong FROM_ROLE")
    if values["TO_ROLE"] != "LESTER":
        raise ProtocolError("wrong TO_ROLE")
    if values["MESSAGE_KIND"] != "ASSIGN":
        raise ProtocolError("wrong MESSAGE_KIND")
    if not _SHA40.fullmatch(values["BASE_SHA"]):
        raise ProtocolError("invalid BASE_SHA")
    if values["DESIGN_HEAD"] != APPROVED_DESIGN_HEAD:
        raise ProtocolError("wrong DESIGN_HEAD")
    if values["NO_AUTO_MERGE"] != "TRUE":
        raise ProtocolError("NO_AUTO_MERGE must be TRUE")

    try:
        task_revision = int(values["TASK_REVISION"])
    except ValueError as exc:
        raise ProtocolError("invalid TASK_REVISION") from exc
    if task_revision != TASK_REVISION:
        raise ProtocolError("wrong TASK_REVISION")

    return RootMessage(
        message_id=values["MESSAGE_ID"],
        event_id=values["EVENT_ID"],
        correlation_id=values["CORRELATION_ID"],
        causation_message_id=values["CAUSATION_MESSAGE_ID"],
        task_id=values["TASK_ID"],
        from_role=values["FROM_ROLE"],
        to_role=values["TO_ROLE"],
        message_kind=values["MESSAGE_KIND"],
        base_sha=values["BASE_SHA"],
        task_revision=task_revision,
        design_head=values["DESIGN_HEAD"],
        no_auto_merge=True,
    )


def admit_event(
    event: dict[str, Any],
    *,
    expected_base_sha: str,
    run_id: str,
    run_attempt: str,
    github_sha: str,
) -> tuple[RootMessage, EventContext]:
    if event.get("action") != "created":
        raise ProtocolError("event action must be created")

    repository = event.get("repository") or {}
    if repository.get("full_name") != REPOSITORY:
        raise ProtocolError("wrong repository")

    issue = event.get("issue") or {}
    if issue.get("number") != COMMUNICATION_PR:
        raise ProtocolError("wrong communication PR")
    if not isinstance(issue.get("pull_request"), dict):
        raise ProtocolError("source is not a pull request conversation")

    comment = event.get("comment") or {}
    user = comment.get("user") or {}
    if user.get("login") != TRANSPORT_ACTOR:
        raise ProtocolError("wrong transport actor")

    comment_id = comment.get("id")
    if not isinstance(comment_id, int) or isinstance(comment_id, bool) or comment_id <= 0:
        raise ProtocolError("invalid source comment ID")

    message = parse_root_message(comment.get("body"))
    if message.base_sha != expected_base_sha:
        raise ProtocolError("BASE_SHA does not match active base")

    context = EventContext(
        repository=REPOSITORY,
        issue_number=COMMUNICATION_PR,
        comment_id=comment_id,
        actor=TRANSPORT_ACTOR,
        run_id=str(run_id),
        run_attempt=str(run_attempt),
        github_sha=str(github_sha),
    )
    return message, context
