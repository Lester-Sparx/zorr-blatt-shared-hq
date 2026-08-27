from __future__ import annotations

from dataclasses import dataclass
import re

_DELIVERY_MARKER = "ZB_REFERENCE_DELIVERY_V1"
_REFERENCE_MARKER = "ZB_REFERENCE_EVENT_V1"
_AGENT_MARKER = "ZB_AGENT_EVENT_V0"
_DELIVERY_KEYS = (
    "TASK_ID",
    "DELIVERY_ID",
    "DRIVE_FOLDER_ID",
    "DRIVE_FILE_ID",
    "SOURCE_FILE_NAME",
    "SIZE_BYTES",
    "SOURCE_SHA256",
    "MIME_TYPE",
    "SOURCE_STATUS",
    "TRANSPORT",
)
_TASK_ID_RE = re.compile(r"^[A-Z0-9_-]+$")
_DELIVERY_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


class ReferenceContractError(ValueError):
    def __init__(self, code: str = "REFERENCE_DELIVERY_EVENT_INVALID"):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ReferenceDelivery:
    task_id: str
    delivery_id: str
    drive_folder_id: str
    drive_file_id: str
    source_file_name: str
    size_bytes: int
    source_sha256: str
    mime_type: str
    source_status: str
    transport: str


@dataclass(frozen=True)
class ReferenceEvent:
    task_id: str
    delivery_id: str
    state: str
    source_sha256: str | None = None
    error_code: str | None = None
    transport: str = "GOOGLE_DRIVE"


def _parse_exact_fields(lines: list[str], keys: tuple[str, ...]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw in lines:
        if not raw.strip() or "=" not in raw:
            raise ReferenceContractError()
        key, value = (part.strip() for part in raw.split("=", 1))
        if key not in keys or key in fields or not value:
            raise ReferenceContractError()
        fields[key] = value
    if tuple(fields.keys()) != keys or set(fields) != set(keys):
        raise ReferenceContractError()
    return fields


def parse_delivery_event(body: str) -> ReferenceDelivery | None:
    if not isinstance(body, str):
        return None
    lines = body.splitlines()
    if not lines or lines[0].strip() != _DELIVERY_MARKER:
        return None
    try:
        fields = _parse_exact_fields(lines[1:], _DELIVERY_KEYS)
        if not _TASK_ID_RE.fullmatch(fields["TASK_ID"]):
            raise ReferenceContractError()
        if not _DELIVERY_ID_RE.fullmatch(fields["DELIVERY_ID"]):
            raise ReferenceContractError()
        size_bytes = int(fields["SIZE_BYTES"])
        if size_bytes < 0:
            raise ReferenceContractError()
        if not _SHA_RE.fullmatch(fields["SOURCE_SHA256"]):
            raise ReferenceContractError()
        if fields["SOURCE_STATUS"] != "OWNER_PROVIDED_REFERENCE":
            raise ReferenceContractError()
        if fields["TRANSPORT"] != "GOOGLE_DRIVE":
            raise ReferenceContractError()
    except (ValueError, ReferenceContractError) as exc:
        if isinstance(exc, ReferenceContractError):
            raise
        raise ReferenceContractError() from exc
    return ReferenceDelivery(
        task_id=fields["TASK_ID"],
        delivery_id=fields["DELIVERY_ID"],
        drive_folder_id=fields["DRIVE_FOLDER_ID"],
        drive_file_id=fields["DRIVE_FILE_ID"],
        source_file_name=fields["SOURCE_FILE_NAME"],
        size_bytes=size_bytes,
        source_sha256=fields["SOURCE_SHA256"],
        mime_type=fields["MIME_TYPE"],
        source_status=fields["SOURCE_STATUS"],
        transport=fields["TRANSPORT"],
    )


def format_reference_ready(task_id: str, delivery_id: str, source_sha256: str) -> str:
    if not _TASK_ID_RE.fullmatch(task_id) or not delivery_id.strip() or not _SHA_RE.fullmatch(source_sha256):
        raise ValueError("REFERENCE_EVENT_INVALID")
    return "\n".join((
        _REFERENCE_MARKER,
        f"TASK_ID = {task_id}",
        f"DELIVERY_ID = {delivery_id}",
        "STATE = REFERENCE_READY",
        f"SOURCE_SHA256 = {source_sha256}",
        "TRANSPORT = GOOGLE_DRIVE",
    ))


def format_reference_failed(task_id: str, delivery_id: str, error_code: str) -> str:
    if not _TASK_ID_RE.fullmatch(task_id) or not delivery_id.strip() or not error_code.strip():
        raise ValueError("REFERENCE_EVENT_INVALID")
    return "\n".join((
        _REFERENCE_MARKER,
        f"TASK_ID = {task_id}",
        f"DELIVERY_ID = {delivery_id}",
        "STATE = REFERENCE_FAILED",
        f"ERROR_CODE = {error_code}",
        "TRANSPORT = GOOGLE_DRIVE",
    ))


def latest_agent_terminal_state(comments: tuple[str, ...], task_id: str) -> str | None:
    terminal: str | None = None
    for body in comments:
        if not isinstance(body, str):
            continue
        lines = body.splitlines()
        if not lines or lines[0].strip() != _AGENT_MARKER:
            continue
        fields: dict[str, str] = {}
        for raw in lines[1:]:
            if not raw.strip():
                break
            if "=" not in raw:
                continue
            key, value = (part.strip() for part in raw.split("=", 1))
            if key not in fields:
                fields[key] = value
        if fields.get("TASK_ID") == task_id and fields.get("STATE") in {"FAILED", "RESULT_READY"}:
            terminal = fields["STATE"]
    return terminal
