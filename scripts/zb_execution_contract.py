from __future__ import annotations

from dataclasses import dataclass
import re


REQUEST_MARKER = "ZB_EXECUTION_REQUEST_V1"
RESULT_MARKER = "ZB_EXECUTION_RESULT_V1"
EMPTY_LIST_SENTINEL = "NONE"

REQUEST_FIELDS = (
    "EXECUTION_REQUEST_ID",
    "MESSAGE_ID",
    "EVENT_ID",
    "CORRELATION_ID",
    "CAUSATION_MESSAGE_ID",
    "TASK_ID",
    "TASK_REVISION",
    "LOGICAL_ROLE",
    "EXECUTION_PROFILE",
    "EXECUTION_PROFILE_VERSION",
    "BASE_SHA",
    "AUTHORITY_REF",
    "DESIGN_HEAD",
    "SOURCE_REFS",
    "EVIDENCE_INPUT_REFS",
    "ALLOWED_WRITE_SCOPE",
    "TIMEOUT_SECONDS",
    "NO_AUTO_MERGE",
    "PRODUCTION_ACTIVE",
)

RESULT_FIELDS = (
    "EXECUTION_REQUEST_ID",
    "EXECUTION_ID",
    "ATTEMPT",
    "MESSAGE_ID",
    "CORRELATION_ID",
    "TASK_ID",
    "TASK_REVISION",
    "LOGICAL_ROLE",
    "EXECUTION_PROFILE",
    "EXECUTION_PROFILE_VERSION",
    "BASE_SHA",
    "START_HEAD",
    "END_HEAD",
    "TERMINAL_STATE",
    "RESULT_CODE",
    "PROCESS_EXIT_CODE",
    "CHANGED_FILES",
    "TEST_EVIDENCE_REFS",
    "ARTIFACT_EVIDENCE_REFS",
    "WORKFLOW_RUN_ID",
    "WORKFLOW_RUN_ATTEMPT",
    "RUNNER_PROVENANCE",
    "STARTED_AT",
    "FINISHED_AT",
    "PRODUCTION_ACTIVE",
)

TERMINAL_STATES = frozenset({"PASS", "FAIL", "BLOCKED", "TIMEOUT", "EXECUTION_ERROR"})
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class ExecutionContractError(ValueError):
    pass


@dataclass(frozen=True)
class ExecutionRequest:
    execution_request_id: str
    message_id: str
    event_id: str
    correlation_id: str
    causation_message_id: str
    task_id: str
    task_revision: int
    logical_role: str
    execution_profile: str
    execution_profile_version: int
    base_sha: str
    authority_ref: str
    design_head: str
    source_refs: tuple[str, ...]
    evidence_input_refs: tuple[str, ...]
    allowed_write_scope: tuple[str, ...]
    timeout_seconds: int
    no_auto_merge: bool
    production_active: bool


@dataclass(frozen=True)
class ExecutionResult:
    execution_request_id: str
    execution_id: str
    attempt: int
    message_id: str
    correlation_id: str
    task_id: str
    task_revision: int
    logical_role: str
    execution_profile: str
    execution_profile_version: int
    base_sha: str
    start_head: str
    end_head: str
    terminal_state: str
    result_code: str
    process_exit_code: int
    changed_files: tuple[str, ...]
    test_evidence_refs: tuple[str, ...]
    artifact_evidence_refs: tuple[str, ...]
    workflow_run_id: str
    workflow_run_attempt: int
    runner_provenance: str
    started_at: str
    finished_at: str
    production_active: bool


def _parse_exact_fields(body: str, marker: str, expected_fields: tuple[str, ...]) -> dict[str, str]:
    if not isinstance(body, str):
        raise ExecutionContractError("INVALID_MARKER")
    lines = body.splitlines()
    if not lines or lines[0] != marker:
        raise ExecutionContractError("INVALID_MARKER")

    expected = set(expected_fields)
    values: dict[str, str] = {}
    for line in lines[1:]:
        if not line:
            continue
        if " = " not in line:
            raise ExecutionContractError("MALFORMED_FIELD")
        name, value = line.split(" = ", 1)
        if name not in expected:
            raise ExecutionContractError("UNKNOWN_FIELD")
        if name in values:
            raise ExecutionContractError("DUPLICATE_FIELD")
        if not value:
            raise ExecutionContractError("MISSING_FIELD")
        values[name] = value

    if any(name not in values for name in expected_fields):
        raise ExecutionContractError("MISSING_FIELD")
    return values


def _require_identifier(value: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ExecutionContractError("INVALID_IDENTIFIER")
    return value


def _require_sha(value: str) -> str:
    if not _SHA40.fullmatch(value):
        raise ExecutionContractError("INVALID_SHA")
    return value


def _require_positive_int(value: str) -> int:
    try:
        parsed = int(value, 10)
    except (TypeError, ValueError) as exc:
        raise ExecutionContractError("INVALID_POSITIVE_INT") from exc
    if parsed <= 0:
        raise ExecutionContractError("INVALID_POSITIVE_INT")
    return parsed


def _require_int(value: str) -> int:
    try:
        return int(value, 10)
    except (TypeError, ValueError) as exc:
        raise ExecutionContractError("INVALID_INT") from exc


def _require_list(value: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if allow_empty and value == EMPTY_LIST_SENTINEL:
        return ()
    parts = tuple(part.strip() for part in value.split(";"))
    if not parts or any(not part or "\x00" in part or "\n" in part or "\r" in part for part in parts):
        raise ExecutionContractError("INVALID_LIST")
    return parts


def _render_list(values: tuple[str, ...], *, allow_empty: bool = False) -> str:
    if allow_empty and not values:
        return EMPTY_LIST_SENTINEL
    if not values:
        raise ExecutionContractError("INVALID_LIST")
    return ";".join(values)


def _require_nonempty(value: str) -> str:
    if not value or "\x00" in value or "\n" in value or "\r" in value:
        raise ExecutionContractError("INVALID_VALUE")
    return value


def _run_specific_test_evidence_matches_workflow(
    test_evidence_refs: tuple[str, ...], workflow_run_id: str
) -> bool:
    prefix = f"run:{workflow_run_id}"
    run_specific_refs = tuple(ref for ref in test_evidence_refs if ref.startswith("run:"))
    return all(ref == prefix or ref.startswith(prefix + ":") for ref in run_specific_refs)


def parse_execution_request(body: str) -> ExecutionRequest:
    values = _parse_exact_fields(body, REQUEST_MARKER, REQUEST_FIELDS)
    if values["NO_AUTO_MERGE"] != "TRUE":
        raise ExecutionContractError("NO_AUTO_MERGE_REQUIRED")
    if values["PRODUCTION_ACTIVE"] != "NO":
        raise ExecutionContractError("PRODUCTION_ACTIVE_FORBIDDEN")

    return ExecutionRequest(
        execution_request_id=_require_identifier(values["EXECUTION_REQUEST_ID"]),
        message_id=_require_identifier(values["MESSAGE_ID"]),
        event_id=_require_identifier(values["EVENT_ID"]),
        correlation_id=_require_identifier(values["CORRELATION_ID"]),
        causation_message_id=_require_identifier(values["CAUSATION_MESSAGE_ID"]),
        task_id=_require_identifier(values["TASK_ID"]),
        task_revision=_require_positive_int(values["TASK_REVISION"]),
        logical_role=_require_identifier(values["LOGICAL_ROLE"]),
        execution_profile=_require_identifier(values["EXECUTION_PROFILE"]),
        execution_profile_version=_require_positive_int(values["EXECUTION_PROFILE_VERSION"]),
        base_sha=_require_sha(values["BASE_SHA"]),
        authority_ref=_require_identifier(values["AUTHORITY_REF"]),
        design_head=_require_sha(values["DESIGN_HEAD"]),
        source_refs=_require_list(values["SOURCE_REFS"]),
        evidence_input_refs=_require_list(values["EVIDENCE_INPUT_REFS"]),
        allowed_write_scope=_require_list(values["ALLOWED_WRITE_SCOPE"]),
        timeout_seconds=_require_positive_int(values["TIMEOUT_SECONDS"]),
        no_auto_merge=True,
        production_active=False,
    )


def render_execution_request(request: ExecutionRequest) -> str:
    values = {
        "EXECUTION_REQUEST_ID": request.execution_request_id,
        "MESSAGE_ID": request.message_id,
        "EVENT_ID": request.event_id,
        "CORRELATION_ID": request.correlation_id,
        "CAUSATION_MESSAGE_ID": request.causation_message_id,
        "TASK_ID": request.task_id,
        "TASK_REVISION": str(request.task_revision),
        "LOGICAL_ROLE": request.logical_role,
        "EXECUTION_PROFILE": request.execution_profile,
        "EXECUTION_PROFILE_VERSION": str(request.execution_profile_version),
        "BASE_SHA": request.base_sha,
        "AUTHORITY_REF": request.authority_ref,
        "DESIGN_HEAD": request.design_head,
        "SOURCE_REFS": _render_list(request.source_refs),
        "EVIDENCE_INPUT_REFS": _render_list(request.evidence_input_refs),
        "ALLOWED_WRITE_SCOPE": _render_list(request.allowed_write_scope),
        "TIMEOUT_SECONDS": str(request.timeout_seconds),
        "NO_AUTO_MERGE": "TRUE" if request.no_auto_merge else "FALSE",
        "PRODUCTION_ACTIVE": "YES" if request.production_active else "NO",
    }
    return REQUEST_MARKER + "\n" + "\n".join(f"{name} = {values[name]}" for name in REQUEST_FIELDS) + "\n"


def parse_execution_result(body: str) -> ExecutionResult:
    values = _parse_exact_fields(body, RESULT_MARKER, RESULT_FIELDS)
    terminal_state = values["TERMINAL_STATE"]
    if terminal_state not in TERMINAL_STATES:
        raise ExecutionContractError("INVALID_TERMINAL_STATE")
    if values["PRODUCTION_ACTIVE"] != "NO":
        raise ExecutionContractError("PRODUCTION_ACTIVE_FORBIDDEN")

    process_exit_code = _require_int(values["PROCESS_EXIT_CODE"])
    test_evidence_refs = _require_list(values["TEST_EVIDENCE_REFS"], allow_empty=True)
    workflow_run_id = _require_identifier(values["WORKFLOW_RUN_ID"])
    if terminal_state == "PASS" and (
        process_exit_code != 0
        or not test_evidence_refs
        or not _run_specific_test_evidence_matches_workflow(test_evidence_refs, workflow_run_id)
    ):
        terminal_state = "FAIL"

    return ExecutionResult(
        execution_request_id=_require_identifier(values["EXECUTION_REQUEST_ID"]),
        execution_id=_require_identifier(values["EXECUTION_ID"]),
        attempt=_require_positive_int(values["ATTEMPT"]),
        message_id=_require_identifier(values["MESSAGE_ID"]),
        correlation_id=_require_identifier(values["CORRELATION_ID"]),
        task_id=_require_identifier(values["TASK_ID"]),
        task_revision=_require_positive_int(values["TASK_REVISION"]),
        logical_role=_require_identifier(values["LOGICAL_ROLE"]),
        execution_profile=_require_identifier(values["EXECUTION_PROFILE"]),
        execution_profile_version=_require_positive_int(values["EXECUTION_PROFILE_VERSION"]),
        base_sha=_require_sha(values["BASE_SHA"]),
        start_head=_require_sha(values["START_HEAD"]),
        end_head=_require_sha(values["END_HEAD"]),
        terminal_state=terminal_state,
        result_code=_require_identifier(values["RESULT_CODE"]),
        process_exit_code=process_exit_code,
        changed_files=_require_list(values["CHANGED_FILES"], allow_empty=True),
        test_evidence_refs=test_evidence_refs,
        artifact_evidence_refs=_require_list(values["ARTIFACT_EVIDENCE_REFS"], allow_empty=True),
        workflow_run_id=workflow_run_id,
        workflow_run_attempt=_require_positive_int(values["WORKFLOW_RUN_ATTEMPT"]),
        runner_provenance=_require_identifier(values["RUNNER_PROVENANCE"]),
        started_at=_require_nonempty(values["STARTED_AT"]),
        finished_at=_require_nonempty(values["FINISHED_AT"]),
        production_active=False,
    )


def render_execution_result(result: ExecutionResult) -> str:
    values = {
        "EXECUTION_REQUEST_ID": result.execution_request_id,
        "EXECUTION_ID": result.execution_id,
        "ATTEMPT": str(result.attempt),
        "MESSAGE_ID": result.message_id,
        "CORRELATION_ID": result.correlation_id,
        "TASK_ID": result.task_id,
        "TASK_REVISION": str(result.task_revision),
        "LOGICAL_ROLE": result.logical_role,
        "EXECUTION_PROFILE": result.execution_profile,
        "EXECUTION_PROFILE_VERSION": str(result.execution_profile_version),
        "BASE_SHA": result.base_sha,
        "START_HEAD": result.start_head,
        "END_HEAD": result.end_head,
        "TERMINAL_STATE": result.terminal_state,
        "RESULT_CODE": result.result_code,
        "PROCESS_EXIT_CODE": str(result.process_exit_code),
        "CHANGED_FILES": _render_list(result.changed_files, allow_empty=True),
        "TEST_EVIDENCE_REFS": _render_list(result.test_evidence_refs, allow_empty=True),
        "ARTIFACT_EVIDENCE_REFS": _render_list(result.artifact_evidence_refs, allow_empty=True),
        "WORKFLOW_RUN_ID": result.workflow_run_id,
        "WORKFLOW_RUN_ATTEMPT": str(result.workflow_run_attempt),
        "RUNNER_PROVENANCE": result.runner_provenance,
        "STARTED_AT": result.started_at,
        "FINISHED_AT": result.finished_at,
        "PRODUCTION_ACTIVE": "YES" if result.production_active else "NO",
    }
    return RESULT_MARKER + "\n" + "\n".join(f"{name} = {values[name]}" for name in RESULT_FIELDS) + "\n"


def execution_replay_key(request: ExecutionRequest) -> str:
    return f"{request.execution_request_id}:{request.execution_profile_version}:{request.base_sha}:{request.task_revision}"
