from __future__ import annotations

try:
    from scripts import zb_communication_r02b_core as _core
except ModuleNotFoundError:  # direct script mode
    import zb_communication_r02b_core as _core


for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)


PERMISSION_EVIDENCE_MARKER = "ZB_CONTEXT_E2_EVIDENCE_V1"
_original_finalize_substantive_execution = _core.finalize_substantive_execution


def _verified_terminal_pass_evidence_body(
    *,
    message_id: str,
    correlation_id: str,
    task_id: str,
    task_revision: int,
    base_sha: str,
    lester_execution_id: str,
    duncan_execution_id: str,
) -> str:
    return "\n".join(
        [
            PERMISSION_EVIDENCE_MARKER,
            "KEY = RESULT",
            'VALUE_JSON = "PASS"',
            "AUTHORITY = GITHUB",
            f"MESSAGE_ID = {message_id}",
            f"CORRELATION_ID = {correlation_id}",
            f"TASK_ID = {task_id}",
            f"TASK_REVISION = {task_revision}",
            f"BASE_SHA = {base_sha}",
            f"LESTER_EXECUTION_ID = {lester_execution_id}",
            f"DUNCAN_EXECUTION_ID = {duncan_execution_id}",
        ]
    )


def finalize_substantive_execution(request_body: str, lester_result: str, duncan_result: str, port):
    result = _original_finalize_substantive_execution(request_body, lester_result, duncan_result, port)
    if result == "OWNER_GATE_REQUIRED":
        request = _core.parse_execution_request(request_body)
        lester = _core.parse_execution_result(lester_result)
        duncan = _core.parse_execution_result(duncan_result)
        _core.r01.write_and_verify(
            port,
            _verified_terminal_pass_evidence_body(
                message_id=request.message_id,
                correlation_id=request.correlation_id,
                task_id=request.task_id,
                task_revision=request.task_revision,
                base_sha=request.base_sha,
                lester_execution_id=lester.execution_id,
                duncan_execution_id=duncan.execution_id,
            ),
        )
    return result