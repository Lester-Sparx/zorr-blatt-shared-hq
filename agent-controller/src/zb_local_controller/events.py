from __future__ import annotations

_ALLOWED_STATES = {"WAITING_REFERENCE", "RUNNING", "RESULT_READY", "FAILED"}
_COMPAT = {
    "WAITING_REFERENCE": "SALVADOR_REFERENCE_REQUIRED",
    "RUNNING": "SALVADOR_RUNNING",
    "RESULT_READY": "SALVADOR_RESULT_READY",
}


class EventFormatError(ValueError):
    pass


def _clean(value: str | None) -> str:
    if value is None:
        return "NONE"
    text = str(value)
    if any(ch in text for ch in ("\n", "\r", "\x00")):
        raise EventFormatError("EVENT_METADATA_INVALID")
    return text or "NONE"


def format_event(
    task_id: str,
    state: str,
    execution_id: str | None,
    result_sha256: str | None,
    error_code: str | None,
) -> str:
    if state not in _ALLOWED_STATES:
        raise EventFormatError("EVENT_STATE_INVALID")
    lines = [
        "ZB_AGENT_EVENT_V0",
        f"TASK_ID = {_clean(task_id)}",
        "AGENT = SALVADOR",
        f"STATE = {state}",
        "BACKEND = COMFYUI_LOCAL",
        f"EXECUTION_ID = {_clean(execution_id)}",
        f"RESULT_SHA256 = {_clean(result_sha256)}",
        f"ERROR_CODE = {_clean(error_code)}",
    ]
    compat = _COMPAT.get(state)
    if compat:
        lines.extend(["", compat])
    return "\n".join(lines)
