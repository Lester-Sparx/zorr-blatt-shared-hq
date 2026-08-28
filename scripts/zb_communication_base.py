from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol

try:
    from scripts.zb_execution_contract import (
        ExecutionRequest,
        parse_execution_request,
        parse_execution_result,
        render_execution_request,
    )
except ModuleNotFoundError:  # direct script mode
    from zb_execution_contract import (
        ExecutionRequest,
        parse_execution_request,
        parse_execution_result,
        render_execution_request,
    )

REPOSITORY = "Lester-Sparx/zorr-blatt-shared-hq"
COMMUNICATION_PR = 111
TRACKER_ISSUE = 106
CONSOLE_ISSUE = 39
TRANSPORT_ACTOR = "Lester-Sparx"
STATE_WRITER = "github-actions[bot]"
TASK_ID = "ZB_GITHUB_NATIVE_BASE_R01"
TASK_REVISION = 1
IMPLEMENTATION_PR = 118
APPROVED_DESIGN_HEAD = "81c44232b72b4a98c8ad0ac2ea6a0a2876f988bc"
SUBSTANTIVE_TASK_ID = "ZB_EXECUTION_PROOF_R01"
SUBSTANTIVE_TASK_REVISION = 1
SUBSTANTIVE_DESIGN_HEAD = "7bac0b6c10dda0448a8792dd3c97f8cec76bbb03"
SUBSTANTIVE_IMPLEMENTATION_PR = 122
SUBSTANTIVE_ALLOWED_WRITE_SCOPE = ("tests/fixtures/zb-execution-proof/",)
MARKER = "ZB_AGENT_MESSAGE_V1"
API_ROOT = "https://api.github.com"
TRACKER_ISSUE_URL = f"{API_ROOT}/repos/{REPOSITORY}/issues/{TRACKER_ISSUE}"
CONSOLE_ISSUE_URL = f"{API_ROOT}/repos/{REPOSITORY}/issues/{CONSOLE_ISSUE}"

EXPECTED_STAGES = (
    ("JINGO", "LESTER", "ASSIGN"),
    ("LESTER", "JINGO", "RETURN"),
    ("JINGO", "DUNCAN", "QC_REQUEST"),
    ("DUNCAN", "JINGO", "QC_VERDICT"),
    ("JINGO", "DJANGO", "ARCH_REVIEW"),
    ("DJANGO", "JINGO", "ARCH_VERDICT"),
    ("JINGO", "JINGO", "CLOSE_REQUEST"),
)
_TASK_AUTHORITIES = {
    TASK_ID: (TASK_REVISION, APPROVED_DESIGN_HEAD),
    SUBSTANTIVE_TASK_ID: (SUBSTANTIVE_TASK_REVISION, SUBSTANTIVE_DESIGN_HEAD),
}
_REPLAY_STATES = frozenset({"RECEIVED", "RUNNING", "RESULT", "BLOCKED"})
_FIELDS = (
    "MESSAGE_ID", "EVENT_ID", "CORRELATION_ID", "CAUSATION_MESSAGE_ID",
    "TASK_ID", "FROM_ROLE", "TO_ROLE", "MESSAGE_KIND", "BASE_SHA",
    "TASK_REVISION", "DESIGN_HEAD", "NO_AUTO_MERGE",
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


@dataclass(frozen=True)
class DispatchDecision:
    state: str
    request_body: str | None
    request_sha256: str | None


class GitHubPort(Protocol):
    def create_tracker_comment(self, body: str) -> int: ...
    def create_console_comment(self, body: str) -> int: ...
    def read_comment(self, comment_id: int) -> dict[str, Any]: ...
    def list_tracker_comments(self) -> list[dict[str, Any]]: ...
    def list_console_comments(self) -> list[dict[str, Any]]: ...


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

    def _create_issue_comment(self, issue_url: str, body: str) -> int:
        result = self._request_json(f"{issue_url}/comments", method="POST", payload={"body": body})
        comment_id = result.get("id") if isinstance(result, dict) else None
        if not isinstance(comment_id, int) or isinstance(comment_id, bool) or comment_id <= 0:
            raise PersistenceError("GitHub API did not return a numeric comment ID")
        return comment_id

    def create_tracker_comment(self, body: str) -> int:
        return self._create_issue_comment(TRACKER_ISSUE_URL, body)

    def create_console_comment(self, body: str) -> int:
        return self._create_issue_comment(CONSOLE_ISSUE_URL, body)

    def read_comment(self, comment_id: int) -> dict[str, Any]:
        if not isinstance(comment_id, int) or isinstance(comment_id, bool) or comment_id <= 0:
            raise PersistenceError("invalid comment ID")
        result = self._request_json(f"{API_ROOT}/repos/{REPOSITORY}/issues/comments/{comment_id}")
        if not isinstance(result, dict):
            raise PersistenceError("GitHub comment read returned non-object")
        return result

    def _list_issue_comments(self, issue_url: str, label: str) -> list[dict[str, Any]]:
        comments: list[dict[str, Any]] = []
        for page in range(1, 21):
            result = self._request_json(f"{issue_url}/comments?per_page=100&page={page}")
            if not isinstance(result, list) or not all(isinstance(item, dict) for item in result):
                raise PersistenceError(f"GitHub {label} comment list returned invalid data")
            comments.extend(result)
            if len(result) < 100:
                return comments
        raise PersistenceError(f"{label} pagination exceeded safety bound")

    def list_tracker_comments(self) -> list[dict[str, Any]]:
        return self._list_issue_comments(TRACKER_ISSUE_URL, "tracker")

    def list_console_comments(self) -> list[dict[str, Any]]:
        return self._list_issue_comments(CONSOLE_ISSUE_URL, "console")


def _verify_comment(readback: dict[str, Any], *, comment_id: int, body: str, issue_url: str) -> None:
    if readback.get("id") != comment_id:
        raise PersistenceError("comment ID read-back mismatch")
    if readback.get("body") != body:
        raise PersistenceError("comment body read-back mismatch")
    if readback.get("issue_url") != issue_url:
        raise PersistenceError("comment container read-back mismatch")


def write_and_verify(port: GitHubPort, body: str) -> int:
    comment_id = port.create_tracker_comment(body)
    _verify_comment(port.read_comment(comment_id), comment_id=comment_id, body=body, issue_url=TRACKER_ISSUE_URL)
    return comment_id


def _write_console_and_verify(port: GitHubPort, body: str) -> int:
    comment_id = port.create_console_comment(body)
    _verify_comment(port.read_comment(comment_id), comment_id=comment_id, body=body, issue_url=CONSOLE_ISSUE_URL)
    return comment_id


def _parse_marker_fields(body: Any, marker: str) -> dict[str, str] | None:
    if not isinstance(body, str):
        return None
    lines = body.splitlines()
    if not lines or lines[0] != marker:
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


def _parse_receipt_fields(body: Any) -> dict[str, str] | None:
    return _parse_marker_fields(body, "ZB_AGENT_RECEIPT_V1")


def _trusted_comment(comment: dict[str, Any], issue_url: str) -> bool:
    if comment.get("issue_url") != issue_url:
        return False
    user = comment.get("user") or {}
    return user.get("login") == STATE_WRITER


def _is_replay(message: RootMessage, context: EventContext, port: GitHubPort) -> bool:
    expected_source = str(context.comment_id)
    for comment in port.list_tracker_comments():
        if not _trusted_comment(comment, TRACKER_ISSUE_URL):
            continue
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


def _terminal_owner_view_exists(message: RootMessage, context: EventContext, port: GitHubPort) -> bool:
    expected_source = str(context.comment_id)
    for comment in port.list_tracker_comments():
        if not _trusted_comment(comment, TRACKER_ISSUE_URL):
            continue
        fields = _parse_marker_fields(comment.get("body"), "ZB_OWNER_VIEW_V0")
        if not fields:
            continue
        if fields.get("MESSAGE_ID") != message.message_id:
            continue
        if fields.get("SOURCE_COMMENT_ID") != expected_source:
            continue
        if fields.get("OWNER_GATE_REQUIRED") == "TRUE":
            return True
    return False


def _projection_binding_line(message: RootMessage, context: EventContext) -> str:
    execution_id = f"github-actions:{context.run_id}:{context.run_attempt}"
    return f"GATE = PROJECTION_BINDING | DONE | source_comment_id={context.comment_id} correlation_id={message.correlation_id} run={execution_id}"


def _console_projection_exists(message: RootMessage, context: EventContext, port: GitHubPort) -> bool:
    binding = _projection_binding_line(message, context)
    for comment in port.list_console_comments():
        if not _trusted_comment(comment, CONSOLE_ISSUE_URL):
            continue
        body = comment.get("body")
        if isinstance(body, str) and body.startswith("ZB_OWNER_VIEW_V0\n") and binding in body.splitlines():
            return True
    return False


def _provenance_lines(context: EventContext) -> list[str]:
    return [f"IMPLEMENTATION_PR = {IMPLEMENTATION_PR}", f"RUNNER_SHA = {context.github_sha}"]


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
    lines = [
        "ZB_AGENT_RECEIPT_V1",
        f"MESSAGE_ID = {message.message_id}",
        f"CORRELATION_ID = {message.correlation_id}",
        f"SOURCE_COMMENT_ID = {context.comment_id}",
        f"TASK_ID = {message.task_id}",
        f"TASK_REVISION = {message.task_revision}",
        f"BASE_SHA = {message.base_sha}",
        f"DESIGN_HEAD = {message.design_head}",
        *_provenance_lines(context),
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
    return "\n".join(lines)


def _owner_view_body(message: RootMessage, context: EventContext) -> str:
    lines = [
        "ZB_OWNER_VIEW_V0",
        f"MESSAGE_ID = {message.message_id}",
        f"CORRELATION_ID = {message.correlation_id}",
        f"SOURCE_COMMENT_ID = {context.comment_id}",
        f"TASK_ID = {message.task_id}",
        f"TASK_REVISION = {message.task_revision}",
        f"BASE_SHA = {message.base_sha}",
        f"DESIGN_HEAD = {message.design_head}",
        *_provenance_lines(context),
        f"WORKFLOW_RUN_ID = {context.run_id}",
        f"WORKFLOW_RUN_ATTEMPT = {context.run_attempt}",
        "LAST_STAGE = JINGO -> JINGO / CLOSE_REQUEST",
        "OWNER_GATE_REQUIRED = TRUE",
        "OWNER_ACTION_REQUIRED = TRUE",
        "PRODUCTION_ACTIVE = NO",
    ]
    return "\n".join(lines)


def _console_projection_body(message: RootMessage, context: EventContext) -> str:
    updated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    execution_id = f"github-actions:{context.run_id}:{context.run_attempt}"
    lines = [
        "ZB_OWNER_VIEW_V0",
        f"UPDATED_AT = {updated_at}",
        "OVERALL_STATUS = WAITING",
        "SPARX_ACTION = OWNER_GATE_REQUIRED",
        f"WHY = formal GitHub-native workflow reached OWNER gate; source_comment_id={context.comment_id}; correlation_id={message.correlation_id}; run={execution_id}; substantive execution is not connected",
        "SCOUT_LAST_CHECK = UNKNOWN",
        "SCOUT_SUMMARY = NONE",
        "AGENT = JINGO | UNKNOWN | substantive execution not connected | NONE | execution adapter not connected | await authorized task adapter",
        "AGENT = LESTER | UNKNOWN | substantive execution not connected | NONE | execution adapter not connected | await authorized task adapter",
        "AGENT = DUNCAN | UNKNOWN | substantive independent QC not connected | NONE | QC execution adapter not connected | await authorized QC adapter",
        "AGENT = SALVADOR | UNKNOWN | not part of this base workflow | NONE | NONE | await authorized art task",
        "AGENT = LYNCH | UNKNOWN | not part of this base workflow | NONE | NONE | await authorized directing task",
        "AGENT = MAO | UNKNOWN | not part of this base workflow | NONE | NONE | await authorized task",
        "AGENT = CHARLIE | UNKNOWN | not part of this base workflow | NONE | NONE | await authorized task",
        "AGENT = MEMORO | UNKNOWN | not part of this base workflow | NONE | NONE | await authorized task",
        "GATE = BASE_AUTOMATION | DONE | formal workflow completed with durable OWNER gate",
        "GATE = OWNER_GATE | WAITING | human OWNER decision required; no automatic OWNER execution",
        "GATE = SUBSTANTIVE_EXECUTION | WAITING | real task execution adapter not connected",
        _projection_binding_line(message, context),
    ]
    return "\n".join(lines)


def run_base(message: RootMessage, context: EventContext, port: GitHubPort) -> str:
    if _is_replay(message, context, port):
        if _terminal_owner_view_exists(message, context, port) and not _console_projection_exists(message, context, port):
            _write_console_and_verify(port, _console_projection_body(message, context))
            return "OWNER_GATE_REQUIRED"
        return "NOOP_REPLAY"

    first = EXPECTED_STAGES[0]
    write_and_verify(port, _receipt_body(message, context, from_role=first[0], to_role=first[1], message_kind=first[2], state="RECEIVED", result_code="NONE", execution_id="NONE"))

    execution_id = f"github-actions:{context.run_id}:{context.run_attempt}"
    write_and_verify(port, _receipt_body(message, context, from_role=first[0], to_role=first[1], message_kind=first[2], state="RUNNING", result_code="NONE", execution_id=execution_id))

    for from_role, to_role, message_kind in EXPECTED_STAGES:
        write_and_verify(port, _receipt_body(message, context, from_role=from_role, to_role=to_role, message_kind=message_kind, state="RESULT", result_code="PASS", execution_id=execution_id))

    write_and_verify(port, _owner_view_body(message, context))
    _write_console_and_verify(port, _console_projection_body(message, context))
    return "OWNER_GATE_REQUIRED"


def _substantive_request_body(message: RootMessage, event: dict[str, Any]) -> str:
    comment_id = (event.get("comment") or {}).get("id")
    if not isinstance(comment_id, int) or isinstance(comment_id, bool) or comment_id <= 0:
        raise ProtocolError("invalid source comment ID")
    request = ExecutionRequest(
        execution_request_id=f"{message.message_id}-lester",
        message_id=message.message_id,
        event_id=message.event_id,
        correlation_id=message.correlation_id,
        causation_message_id=message.message_id,
        task_id=message.task_id,
        task_revision=message.task_revision,
        logical_role="LESTER",
        execution_profile="LESTER_IMPLEMENT_R01",
        execution_profile_version=1,
        base_sha=message.base_sha,
        authority_ref=f"pr:{COMMUNICATION_PR}:comment:{comment_id}",
        design_head=message.design_head,
        source_refs=(f"pr:{COMMUNICATION_PR}", f"source-comment:{comment_id}"),
        evidence_input_refs=("spec:120", "plan:121"),
        allowed_write_scope=SUBSTANTIVE_ALLOWED_WRITE_SCOPE,
        timeout_seconds=600,
        no_auto_merge=True,
        production_active=False,
    )
    return render_execution_request(request)


def _substantive_dispatch_record(message: RootMessage, event: dict[str, Any], result_code: str) -> str:
    comment_id = (event.get("comment") or {}).get("id")
    return "\n".join(
        [
            "ZB_SUBSTANTIVE_DISPATCH_V1",
            f"MESSAGE_ID = {message.message_id}",
            f"CORRELATION_ID = {message.correlation_id}",
            f"SOURCE_COMMENT_ID = {comment_id}",
            f"TASK_ID = {message.task_id}",
            f"TASK_REVISION = {message.task_revision}",
            f"BASE_SHA = {message.base_sha}",
            f"DESIGN_HEAD = {message.design_head}",
            f"IMPLEMENTATION_PR = {SUBSTANTIVE_IMPLEMENTATION_PR}",
            "STATE = BLOCKED",
            f"RESULT_CODE = {result_code}",
            "PRODUCTION_ACTIVE = NO",
        ]
    )


def _substantive_console_body(message: RootMessage, *, source_comment_id: str, phase: str, reason: str) -> str:
    updated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if phase == "DONE":
        overall = "WAITING"
        action = "OWNER_GATE_REQUIRED"
        lester = "DONE"
        duncan = "DONE"
        owner_gate = "WAITING"
        substantive = "DONE"
    elif phase == "FAIL":
        overall = "FAIL"
        action = "REVIEW_EXECUTION_FAILURE"
        lester = "DONE"
        duncan = "FAIL"
        owner_gate = "BLOCKED"
        substantive = "FAIL"
    else:
        overall = "BLOCKED"
        action = "RESOLVE_EXECUTION_HOST_GATE"
        lester = "BLOCKED"
        duncan = "WAITING"
        owner_gate = "BLOCKED"
        substantive = "BLOCKED"
    lines = [
        "ZB_OWNER_VIEW_V0",
        f"UPDATED_AT = {updated_at}",
        f"OVERALL_STATUS = {overall}",
        f"SPARX_ACTION = {action}",
        f"WHY = {reason}; source_comment_id={source_comment_id}; correlation_id={message.correlation_id}",
        "SCOUT_LAST_CHECK = UNKNOWN",
        "SCOUT_SUMMARY = NONE",
        "AGENT = JINGO | DONE | substantive request authority resolved | NONE | NONE | await execution state",
        f"AGENT = LESTER | {lester} | substantive execution | NONE | execution profile R01 | follow workflow gate",
        f"AGENT = DUNCAN | {duncan} | independent substantive QC | NONE | QC profile R01 | follow workflow gate",
        "AGENT = SALVADOR | UNKNOWN | not part of this execution path | NONE | NONE | await authorized art task",
        "AGENT = LYNCH | UNKNOWN | not part of this execution path | NONE | NONE | await authorized directing task",
        "AGENT = MAO | UNKNOWN | not part of this execution path | NONE | NONE | await authorized task",
        "AGENT = CHARLIE | UNKNOWN | not part of this execution path | NONE | NONE | await authorized task",
        "AGENT = MEMORO | UNKNOWN | not part of this execution path | NONE | NONE | await authorized task",
        "GATE = BASE_AUTOMATION | DONE | GitHub-native communication base retained",
        f"GATE = OWNER_GATE | {owner_gate} | human OWNER only after verified DUNCAN PASS",
        f"GATE = SUBSTANTIVE_EXECUTION | {substantive} | {reason}",
    ]
    return "\n".join(lines)


def prepare_substantive_dispatch(message: RootMessage, event: dict[str, Any], port: GitHubPort) -> DispatchDecision:
    if message.task_id != SUBSTANTIVE_TASK_ID:
        raise ProtocolError("wrong substantive task")
    repository = event.get("repository") or {}
    source_comment_id = str((event.get("comment") or {}).get("id"))
    if repository.get("private") is not True:
        write_and_verify(port, _substantive_dispatch_record(message, event, "RUNNER_SECURITY_GATE_BLOCKED"))
        _write_console_and_verify(
            port,
            _substantive_console_body(
                message,
                source_comment_id=source_comment_id,
                phase="BLOCKED",
                reason="public repository blocks persistent self-hosted execution",
            ),
        )
        return DispatchDecision("BLOCKED", None, None)

    request_body = _substantive_request_body(message, event)
    request_sha256 = hashlib.sha256(request_body.encode("utf-8")).hexdigest()
    for comment in port.list_tracker_comments():
        if _trusted_comment(comment, TRACKER_ISSUE_URL) and comment.get("body") == request_body:
            return DispatchDecision("REQUEST_RECORDED", request_body, request_sha256)
    write_and_verify(port, request_body)
    return DispatchDecision("REQUEST_RECORDED", request_body, request_sha256)


def _source_comment_id_from_request(request: ExecutionRequest) -> str:
    prefix = f"pr:{COMMUNICATION_PR}:comment:"
    if not request.authority_ref.startswith(prefix):
        return "UNKNOWN"
    value = request.authority_ref.removeprefix(prefix)
    return value if value.isdigit() else "UNKNOWN"


def _substantive_owner_view(request: ExecutionRequest, lester_execution_id: str, duncan_execution_id: str) -> str:
    return "\n".join(
        [
            "ZB_OWNER_VIEW_V0",
            f"MESSAGE_ID = {request.message_id}",
            f"CORRELATION_ID = {request.correlation_id}",
            f"SOURCE_COMMENT_ID = {_source_comment_id_from_request(request)}",
            f"TASK_ID = {request.task_id}",
            f"TASK_REVISION = {request.task_revision}",
            f"BASE_SHA = {request.base_sha}",
            f"DESIGN_HEAD = {request.design_head}",
            f"IMPLEMENTATION_PR = {SUBSTANTIVE_IMPLEMENTATION_PR}",
            f"LESTER_EXECUTION_ID = {lester_execution_id}",
            f"DUNCAN_EXECUTION_ID = {duncan_execution_id}",
            "LAST_STAGE = DUNCAN / VERIFIED_QC_PASS",
            "OWNER_GATE_REQUIRED = TRUE",
            "OWNER_ACTION_REQUIRED = TRUE",
            "PRODUCTION_ACTIVE = NO",
        ]
    )


def _substantive_failure_record(request: ExecutionRequest, result_code: str) -> str:
    return "\n".join(
        [
            "ZB_SUBSTANTIVE_FINALIZE_V1",
            f"MESSAGE_ID = {request.message_id}",
            f"CORRELATION_ID = {request.correlation_id}",
            f"TASK_ID = {request.task_id}",
            f"TASK_REVISION = {request.task_revision}",
            f"BASE_SHA = {request.base_sha}",
            "STATE = FAIL",
            f"RESULT_CODE = {result_code}",
            "OWNER_GATE_REQUIRED = FALSE",
            "PRODUCTION_ACTIVE = NO",
        ]
    )


def finalize_substantive_execution(request_body: str, lester_result: str, duncan_result: str, port: GitHubPort) -> str:
    request = parse_execution_request(request_body)
    lester = parse_execution_result(lester_result)
    duncan = parse_execution_result(duncan_result)
    source_comment_id = _source_comment_id_from_request(request)

    common_lester = (
        lester.message_id == request.message_id
        and lester.correlation_id == request.correlation_id
        and lester.task_id == request.task_id
        and lester.task_revision == request.task_revision
        and lester.base_sha == request.base_sha
        and lester.logical_role == "LESTER"
        and lester.execution_profile == "LESTER_IMPLEMENT_R01"
        and lester.execution_profile_version == 1
    )
    common_duncan = (
        duncan.message_id == request.message_id
        and duncan.correlation_id == request.correlation_id
        and duncan.task_id == request.task_id
        and duncan.task_revision == request.task_revision
        and duncan.base_sha == request.base_sha
        and duncan.logical_role == "DUNCAN"
        and duncan.execution_profile == "DUNCAN_QC_R01"
        and duncan.execution_profile_version == 1
    )
    if not common_lester or lester.terminal_state != "PASS":
        write_and_verify(port, _substantive_failure_record(request, "LESTER_RESULT_REJECTED"))
        _write_console_and_verify(
            port,
            _substantive_console_body(message=_root_from_request(request), source_comment_id=source_comment_id, phase="FAIL", reason="LESTER result verification failed"),
        )
        return "LESTER_RESULT_REJECTED"
    if not common_duncan or duncan.terminal_state != "PASS":
        write_and_verify(port, _substantive_failure_record(request, "DUNCAN_QC_FAIL"))
        _write_console_and_verify(
            port,
            _substantive_console_body(message=_root_from_request(request), source_comment_id=source_comment_id, phase="FAIL", reason="DUNCAN QC did not pass"),
        )
        return "DUNCAN_QC_FAIL"
    if duncan.execution_id == lester.execution_id:
        write_and_verify(port, _substantive_failure_record(request, "DUNCAN_EXECUTION_ID_NOT_DISTINCT"))
        _write_console_and_verify(
            port,
            _substantive_console_body(message=_root_from_request(request), source_comment_id=source_comment_id, phase="FAIL", reason="DUNCAN physical execution identity is not distinct"),
        )
        return "DUNCAN_EXECUTION_ID_NOT_DISTINCT"

    write_and_verify(port, _substantive_owner_view(request, lester.execution_id, duncan.execution_id))
    _write_console_and_verify(
        port,
        _substantive_console_body(
            message=_root_from_request(request),
            source_comment_id=source_comment_id,
            phase="DONE",
            reason="verified LESTER result and independent DUNCAN PASS reached human OWNER gate",
        ),
    )
    return "OWNER_GATE_REQUIRED"


def _root_from_request(request: ExecutionRequest) -> RootMessage:
    return RootMessage(
        message_id=request.message_id,
        event_id=request.event_id,
        correlation_id=request.correlation_id,
        causation_message_id="NONE",
        task_id=request.task_id,
        from_role="JINGO",
        to_role="LESTER",
        message_kind="ASSIGN",
        base_sha=request.base_sha,
        task_revision=request.task_revision,
        design_head=request.design_head,
        no_auto_merge=True,
    )


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
    for name in ("MESSAGE_ID", "EVENT_ID", "CORRELATION_ID"):
        _require_identifier(name, values[name])
    if values["CAUSATION_MESSAGE_ID"] != "NONE":
        raise ProtocolError("initial CAUSATION_MESSAGE_ID must be NONE")
    authority = _TASK_AUTHORITIES.get(values["TASK_ID"])
    if authority is None:
        raise ProtocolError("wrong TASK_ID")
    if (values["FROM_ROLE"], values["TO_ROLE"], values["MESSAGE_KIND"]) != EXPECTED_STAGES[0]:
        raise ProtocolError("wrong initial logical transition")
    if not _SHA40.fullmatch(values["BASE_SHA"]):
        raise ProtocolError("invalid BASE_SHA")
    expected_revision, expected_design_head = authority
    if values["DESIGN_HEAD"] != expected_design_head:
        raise ProtocolError("wrong DESIGN_HEAD")
    if values["NO_AUTO_MERGE"] != "TRUE":
        raise ProtocolError("NO_AUTO_MERGE must be TRUE")
    try:
        task_revision = int(values["TASK_REVISION"])
    except ValueError as exc:
        raise ProtocolError("invalid TASK_REVISION") from exc
    if task_revision != expected_revision:
        raise ProtocolError("wrong TASK_REVISION")

    return RootMessage(
        message_id=values["MESSAGE_ID"], event_id=values["EVENT_ID"], correlation_id=values["CORRELATION_ID"],
        causation_message_id=values["CAUSATION_MESSAGE_ID"], task_id=values["TASK_ID"], from_role=values["FROM_ROLE"],
        to_role=values["TO_ROLE"], message_kind=values["MESSAGE_KIND"], base_sha=values["BASE_SHA"],
        task_revision=task_revision, design_head=values["DESIGN_HEAD"], no_auto_merge=True,
    )


def admit_event(event: dict[str, Any], *, expected_base_sha: str, run_id: str, run_attempt: str, github_sha: str) -> tuple[RootMessage, EventContext]:
    if event.get("action") != "created":
        raise ProtocolError("event action must be created")
    if (event.get("repository") or {}).get("full_name") != REPOSITORY:
        raise ProtocolError("wrong repository")
    issue = event.get("issue") or {}
    if issue.get("number") != COMMUNICATION_PR:
        raise ProtocolError("wrong communication PR")
    if not isinstance(issue.get("pull_request"), dict):
        raise ProtocolError("source is not a pull request conversation")
    comment = event.get("comment") or {}
    if (comment.get("user") or {}).get("login") != TRANSPORT_ACTOR:
        raise ProtocolError("wrong transport actor")
    comment_id = comment.get("id")
    if not isinstance(comment_id, int) or isinstance(comment_id, bool) or comment_id <= 0:
        raise ProtocolError("invalid source comment ID")
    message = parse_root_message(comment.get("body"))
    if message.base_sha != expected_base_sha:
        raise ProtocolError("BASE_SHA does not match active base")
    return message, EventContext(REPOSITORY, COMMUNICATION_PR, comment_id, TRANSPORT_ACTOR, str(run_id), str(run_attempt), str(github_sha))


def _require_env(environ: dict[str, str], name: str) -> str:
    value = environ.get(name)
    if not value:
        raise ProtocolError(f"missing environment: {name}")
    return value


def main(*, environ: dict[str, str] | None = None, port_factory: Callable[[str], GitHubPort] = GitHubApi) -> int:
    env = os.environ if environ is None else environ
    event_path = Path(_require_env(env, "GITHUB_EVENT_PATH"))
    try:
        event = json.loads(event_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid GitHub event payload") from exc
    if not isinstance(event, dict):
        raise ProtocolError("GitHub event payload must be an object")

    body = (event.get("comment") or {}).get("body")
    if not isinstance(body, str) or not body.splitlines() or body.splitlines()[0] != MARKER:
        print("IGNORED_NON_PROTOCOL")
        return 0
    if _require_env(env, "GITHUB_REPOSITORY") != REPOSITORY:
        raise ProtocolError("environment repository mismatch")
    github_sha = _require_env(env, "GITHUB_SHA")
    if not _SHA40.fullmatch(github_sha):
        raise ProtocolError("invalid GITHUB_SHA")

    message, context = admit_event(
        event,
        expected_base_sha=github_sha,
        run_id=_require_env(env, "GITHUB_RUN_ID"),
        run_attempt=_require_env(env, "GITHUB_RUN_ATTEMPT"),
        github_sha=github_sha,
    )
    port = port_factory(_require_env(env, "GITHUB_TOKEN"))
    if message.task_id == TASK_ID:
        result = run_base(message, context, port)
    else:
        result = prepare_substantive_dispatch(message, event, port).state
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
