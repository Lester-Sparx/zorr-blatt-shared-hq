from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from scripts import zb_communication_base as r01
from scripts.zb_execution_contract import (
    ExecutionRequest,
    parse_execution_result,
    parse_execution_request,
    render_execution_request,
)

REPOSITORY = r01.REPOSITORY
COMMUNICATION_PR = r01.COMMUNICATION_PR
TRACKER_ISSUE_URL = r01.TRACKER_ISSUE_URL
CONSOLE_ISSUE_URL = r01.CONSOLE_ISSUE_URL
TRANSPORT_ACTOR = r01.TRANSPORT_ACTOR
STATE_WRITER = r01.STATE_WRITER
ProtocolError = r01.ProtocolError
PersistenceError = r01.PersistenceError
RootMessage = r01.RootMessage
DispatchDecision = r01.DispatchDecision
GitHubPort = r01.GitHubPort
GitHubApi = r01.GitHubApi

R02B_TASK_ID = "ZB_EXECUTION_PROOF_R01"
R02B_TASK_REVISION = 2
R02B_DESIGN_HEAD = "2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8"
R02B_IMPLEMENTATION_PR = 125
R02B_PROFILE = "LESTER_IMPLEMENT_R02A"
R02B_ALLOWED_WRITE_SCOPE = ("tests/fixtures/zb-execution-proof/",)
R02B_TIMEOUT_SECONDS = 600
_MARKER = "ZB_AGENT_MESSAGE_V1"
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


def _verify_comment(readback: dict[str, Any], *, comment_id: int, body: str, issue_url: str) -> None:
    if readback.get("id") != comment_id:
        raise PersistenceError("comment ID read-back mismatch")
    if readback.get("body") != body:
        raise PersistenceError("comment body read-back mismatch")
    if readback.get("issue_url") != issue_url:
        raise PersistenceError("comment container read-back mismatch")


def _write_console_and_verify(port: GitHubPort, body: str) -> int:
    comment_id = port.create_console_comment(body)
    _verify_comment(port.read_comment(comment_id), comment_id=comment_id, body=body, issue_url=CONSOLE_ISSUE_URL)
    return comment_id


def _trusted_tracker_comment(comment: dict[str, Any]) -> bool:
    return (
        comment.get("issue_url") == TRACKER_ISSUE_URL
        and ((comment.get("user") or {}).get("login") == STATE_WRITER)
    )


def _parse_r02b_root(body: str) -> RootMessage:
    if not isinstance(body, str):
        raise ProtocolError("body must be text")
    lines = body.splitlines()
    if not lines or lines[0] != _MARKER:
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
        if not _IDENTIFIER.fullmatch(values[name]):
            raise ProtocolError(f"invalid {name}")
    if values["CAUSATION_MESSAGE_ID"] != "NONE":
        raise ProtocolError("initial CAUSATION_MESSAGE_ID must be NONE")
    if values["TASK_ID"] != R02B_TASK_ID:
        raise ProtocolError("wrong TASK_ID")
    if (values["FROM_ROLE"], values["TO_ROLE"], values["MESSAGE_KIND"]) != r01.EXPECTED_STAGES[0]:
        raise ProtocolError("wrong initial logical transition")
    if not _SHA40.fullmatch(values["BASE_SHA"]):
        raise ProtocolError("invalid BASE_SHA")
    try:
        revision = int(values["TASK_REVISION"])
    except ValueError as exc:
        raise ProtocolError("invalid TASK_REVISION") from exc
    if revision != R02B_TASK_REVISION:
        raise ProtocolError("wrong TASK_REVISION")
    if values["DESIGN_HEAD"] != R02B_DESIGN_HEAD:
        raise ProtocolError("wrong DESIGN_HEAD")
    if values["NO_AUTO_MERGE"] != "TRUE":
        raise ProtocolError("NO_AUTO_MERGE must be TRUE")
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
        task_revision=revision,
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
) -> tuple[RootMessage, r01.EventContext]:
    body = ((event.get("comment") or {}).get("body"))
    revision_text = None
    if isinstance(body, str):
        for line in body.splitlines()[1:]:
            if line.startswith("TASK_REVISION = "):
                revision_text = line.removeprefix("TASK_REVISION = ")
                break
    if revision_text == "1":
        return r01.admit_event(
            event,
            expected_base_sha=expected_base_sha,
            run_id=run_id,
            run_attempt=run_attempt,
            github_sha=github_sha,
        )
    if event.get("action") != "created":
        raise ProtocolError("event action must be created")
    if (event.get("repository") or {}).get("full_name") != REPOSITORY:
        raise ProtocolError("wrong repository")
    issue = event.get("issue") or {}
    if issue.get("number") != COMMUNICATION_PR or not isinstance(issue.get("pull_request"), dict):
        raise ProtocolError("wrong communication PR")
    comment = event.get("comment") or {}
    if (comment.get("user") or {}).get("login") != TRANSPORT_ACTOR:
        raise ProtocolError("wrong transport actor")
    comment_id = comment.get("id")
    if not isinstance(comment_id, int) or isinstance(comment_id, bool) or comment_id <= 0:
        raise ProtocolError("invalid source comment ID")
    message = _parse_r02b_root(body)
    if message.base_sha != expected_base_sha:
        raise ProtocolError("BASE_SHA does not match active base")
    return message, r01.EventContext(
        REPOSITORY,
        COMMUNICATION_PR,
        comment_id,
        TRANSPORT_ACTOR,
        str(run_id),
        str(run_attempt),
        str(github_sha),
    )


def _request_body(message: RootMessage, event: dict[str, Any]) -> str:
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
        execution_profile=R02B_PROFILE,
        execution_profile_version=1,
        base_sha=message.base_sha,
        authority_ref=f"pr:{COMMUNICATION_PR}:comment:{comment_id}",
        design_head=message.design_head,
        source_refs=(f"pr:{COMMUNICATION_PR}", f"source-comment:{comment_id}", "pr:123", "pr:124", "pr:125"),
        evidence_input_refs=("spec:123", "plan:124", "implementation:125"),
        allowed_write_scope=R02B_ALLOWED_WRITE_SCOPE,
        timeout_seconds=R02B_TIMEOUT_SECONDS,
        no_auto_merge=True,
        production_active=False,
    )
    return render_execution_request(request)


def prepare_substantive_dispatch(message: RootMessage, event: dict[str, Any], port: GitHubPort) -> DispatchDecision:
    if message.task_revision == 1:
        return r01.prepare_substantive_dispatch(message, event, port)
    if (
        message.task_id != R02B_TASK_ID
        or message.task_revision != R02B_TASK_REVISION
        or message.design_head != R02B_DESIGN_HEAD
    ):
        raise ProtocolError("wrong R02B substantive authority")
    request_body = _request_body(message, event)
    request_sha256 = hashlib.sha256(request_body.encode("utf-8")).hexdigest()
    for comment in port.list_tracker_comments():
        if _trusted_tracker_comment(comment) and comment.get("body") == request_body:
            return DispatchDecision("REQUEST_RECORDED", request_body, request_sha256)
    r01.write_and_verify(port, request_body)
    return DispatchDecision("REQUEST_RECORDED", request_body, request_sha256)


def _source_comment_id(request: ExecutionRequest) -> str:
    prefix = f"pr:{COMMUNICATION_PR}:comment:"
    if not request.authority_ref.startswith(prefix):
        return "UNKNOWN"
    value = request.authority_ref.removeprefix(prefix)
    return value if value.isdigit() else "UNKNOWN"


def _owner_view(request: ExecutionRequest, lester_id: str, duncan_id: str) -> str:
    return "\n".join(
        [
            "ZB_OWNER_VIEW_V0",
            f"MESSAGE_ID = {request.message_id}",
            f"CORRELATION_ID = {request.correlation_id}",
            f"SOURCE_COMMENT_ID = {_source_comment_id(request)}",
            f"TASK_ID = {request.task_id}",
            f"TASK_REVISION = {request.task_revision}",
            f"BASE_SHA = {request.base_sha}",
            f"DESIGN_HEAD = {request.design_head}",
            f"IMPLEMENTATION_PR = {R02B_IMPLEMENTATION_PR}",
            f"LESTER_EXECUTION_ID = {lester_id}",
            f"DUNCAN_EXECUTION_ID = {duncan_id}",
            "LAST_STAGE = DUNCAN / VERIFIED_QC_PASS",
            "OWNER_GATE_REQUIRED = TRUE",
            "OWNER_ACTION_REQUIRED = TRUE",
            "PRODUCTION_ACTIVE = NO",
        ]
    )


def _failure_record(request: ExecutionRequest, result_code: str) -> str:
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


def _console_body(request: ExecutionRequest, *, phase: str, reason: str) -> str:
    updated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if phase == "DONE":
        overall, action, lester, duncan, owner, substantive = "WAITING", "OWNER_GATE_REQUIRED", "DONE", "DONE", "WAITING", "DONE"
    else:
        overall, action, lester, duncan, owner, substantive = "FAIL", "REVIEW_EXECUTION_FAILURE", "DONE", "FAIL", "BLOCKED", "FAIL"
    return "\n".join(
        [
            "ZB_OWNER_VIEW_V0",
            f"UPDATED_AT = {updated_at}",
            f"OVERALL_STATUS = {overall}",
            f"SPARX_ACTION = {action}",
            f"WHY = {reason}; source_comment_id={_source_comment_id(request)}; correlation_id={request.correlation_id}",
            "SCOUT_LAST_CHECK = UNKNOWN",
            "SCOUT_SUMMARY = NONE",
            "AGENT = JINGO | DONE | R02B hosted request authority resolved | NONE | NONE | await execution state",
            f"AGENT = LESTER | {lester} | GitHub-hosted Copilot execution | NONE | LESTER_IMPLEMENT_R02A | follow workflow gate",
            f"AGENT = DUNCAN | {duncan} | independent deterministic QC | NONE | DUNCAN_QC_R01 | follow workflow gate",
            "GATE = BASE_AUTOMATION | DONE | GitHub-native communication base retained",
            f"GATE = OWNER_GATE | {owner} | human OWNER only after verified DUNCAN PASS",
            f"GATE = SUBSTANTIVE_EXECUTION | {substantive} | {reason}",
        ]
    )


def finalize_substantive_execution(request_body: str, lester_result: str, duncan_result: str, port: GitHubPort) -> str:
    request = parse_execution_request(request_body)
    if request.task_revision == 1:
        return r01.finalize_substantive_execution(request_body, lester_result, duncan_result, port)
    if (
        request.task_id != R02B_TASK_ID
        or request.task_revision != R02B_TASK_REVISION
        or request.design_head != R02B_DESIGN_HEAD
        or request.execution_profile != R02B_PROFILE
    ):
        raise ProtocolError("wrong R02B request authority")
    lester = parse_execution_result(lester_result)
    duncan = parse_execution_result(duncan_result)
    common_lester = (
        lester.message_id == request.message_id
        and lester.correlation_id == request.correlation_id
        and lester.task_id == request.task_id
        and lester.task_revision == request.task_revision
        and lester.base_sha == request.base_sha
        and lester.logical_role == "LESTER"
        and lester.execution_profile == request.execution_profile
        and lester.execution_profile_version == request.execution_profile_version
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
        r01.write_and_verify(port, _failure_record(request, "LESTER_RESULT_REJECTED"))
        _write_console_and_verify(port, _console_body(request, phase="FAIL", reason="LESTER result verification failed"))
        return "LESTER_RESULT_REJECTED"
    if not common_duncan or duncan.terminal_state != "PASS":
        r01.write_and_verify(port, _failure_record(request, "DUNCAN_QC_FAIL"))
        _write_console_and_verify(port, _console_body(request, phase="FAIL", reason="DUNCAN QC did not pass"))
        return "DUNCAN_QC_FAIL"
    if duncan.execution_id == lester.execution_id:
        r01.write_and_verify(port, _failure_record(request, "DUNCAN_EXECUTION_ID_NOT_DISTINCT"))
        _write_console_and_verify(port, _console_body(request, phase="FAIL", reason="DUNCAN physical execution identity is not distinct"))
        return "DUNCAN_EXECUTION_ID_NOT_DISTINCT"
    r01.write_and_verify(port, _owner_view(request, lester.execution_id, duncan.execution_id))
    _write_console_and_verify(
        port,
        _console_body(request, phase="DONE", reason="verified GitHub-hosted LESTER result and independent DUNCAN PASS reached human OWNER gate"),
    )
    return "OWNER_GATE_REQUIRED"


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
    if not isinstance(body, str) or not body.splitlines() or body.splitlines()[0] != _MARKER:
        print("IGNORED_NON_PROTOCOL")
        return 0
    if _require_env(env, "GITHUB_REPOSITORY") != REPOSITORY:
        raise ProtocolError("environment repository mismatch")
    github_sha = _require_env(env, "GITHUB_SHA")
    if not _SHA40.fullmatch(github_sha):
        raise ProtocolError("invalid GITHUB_SHA")
    message, _ = admit_event(
        event,
        expected_base_sha=github_sha,
        run_id=_require_env(env, "GITHUB_RUN_ID"),
        run_attempt=_require_env(env, "GITHUB_RUN_ATTEMPT"),
        github_sha=github_sha,
    )
    port = port_factory(_require_env(env, "GITHUB_TOKEN"))
    if message.task_revision == 1:
        if message.task_id == r01.TASK_ID:
            result = r01.run_base(message, _, port)
        else:
            result = r01.prepare_substantive_dispatch(message, event, port).state
    else:
        result = prepare_substantive_dispatch(message, event, port).state
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
