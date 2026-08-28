from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re

MESSAGE_MARKER = "ZB_AGENT_MESSAGE_V1"
MESSAGE_ROLES = {"JINGO", "LESTER", "DUNCAN", "DJANGO"}
MESSAGE_KINDS = {"ASSIGN", "RETURN", "QC_REQUEST", "QC_VERDICT", "ARCH_REVIEW", "ARCH_VERDICT", "CLOSE_REQUEST"}
TARGET_REPOSITORY = "Lester-Sparx/zorr-blatt-shared-hq"
MESSAGE_KEYS = (
    "MESSAGE_ID", "EVENT_ID", "CORRELATION_ID", "CAUSATION_MESSAGE_ID", "TASK_ID",
    "FROM_ROLE", "TO_ROLE", "MESSAGE_KIND", "TARGET_REPO", "TARGET_ISSUE", "TARGET_PR",
    "BASE_SHA", "TARGET_HEAD_SHA", "TASK_REVISION", "EVIDENCE_REF", "EVIDENCE_SHA256",
    "EXPECTED_GATE", "NO_AUTO_MERGE",
)
_SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_TASK_ID = re.compile(r"^[A-Z0-9_-]+$")
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA64 = re.compile(r"^[0-9a-f]{64}$")
_SYMBOL = re.compile(r"^[A-Z0-9_-]+$")


class CommunicationProtocolError(ValueError):
    def __init__(self, code: str = "MESSAGE_PROTOCOL_INVALID"):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class AgentMessage:
    message_id: str
    event_id: str
    correlation_id: str
    causation_message_id: str | None
    task_id: str
    from_role: str
    to_role: str
    message_kind: str
    target_repo: str
    target_issue: int | None
    target_pr: int | None
    base_sha: str | None
    target_head_sha: str | None
    task_revision: int | None
    evidence_ref: str | None
    evidence_sha256: str | None
    expected_gate: str
    no_auto_merge: bool = True
    direction: str = ""


def _fail() -> None:
    raise CommunicationProtocolError()


def _single(value: object) -> str:
    if not isinstance(value, str) or not value or any(ch in value for ch in "\r\n\x00"):
        _fail()
    return value


def _id(value: str) -> str:
    value = _single(value)
    if not _SAFE_ID.fullmatch(value):
        _fail()
    return value


def _optional_id(value: str) -> str | None:
    return None if value == "NONE" else _id(value)


def _positive_or_none(value: str) -> int | None:
    if value == "NONE":
        return None
    if not value.isdigit() or int(value) <= 0:
        _fail()
    return int(value)


def _sha_or_none(value: str, pattern: re.Pattern[str]) -> str | None:
    if value == "NONE":
        return None
    if not pattern.fullmatch(value):
        _fail()
    return value


def _parse_fields(lines: list[str]) -> dict[str, str]:
    if len(lines) != len(MESSAGE_KEYS):
        _fail()
    fields: dict[str, str] = {}
    for expected, raw in zip(MESSAGE_KEYS, lines):
        if " = " not in raw:
            _fail()
        key, value = raw.split(" = ", 1)
        if key != expected or key in fields:
            _fail()
        fields[key] = _single(value)
    return fields


def parse_message(body: str) -> AgentMessage:
    if not isinstance(body, str):
        _fail()
    lines = body.splitlines()
    if not lines or lines[0] != MESSAGE_MARKER:
        _fail()
    machine_end = 1 + len(MESSAGE_KEYS)
    if len(lines) < machine_end:
        _fail()
    fields = _parse_fields(lines[1:machine_end])
    tail = lines[machine_end:]
    direction = ""
    if tail:
        if tail[0] != "":
            _fail()
        direction = "\n".join(tail[1:]).strip()

    message_id = _id(fields["MESSAGE_ID"])
    event_id = _id(fields["EVENT_ID"])
    correlation_id = _id(fields["CORRELATION_ID"])
    causation = _optional_id(fields["CAUSATION_MESSAGE_ID"])
    task_id = _single(fields["TASK_ID"])
    if not _TASK_ID.fullmatch(task_id):
        _fail()
    from_role = fields["FROM_ROLE"]
    to_role = fields["TO_ROLE"]
    if from_role not in MESSAGE_ROLES or to_role not in MESSAGE_ROLES:
        _fail()
    kind = fields["MESSAGE_KIND"]
    if kind not in MESSAGE_KINDS:
        _fail()
    if fields["TARGET_REPO"] != TARGET_REPOSITORY:
        _fail()
    target_issue = _positive_or_none(fields["TARGET_ISSUE"])
    target_pr = _positive_or_none(fields["TARGET_PR"])
    base_sha = _sha_or_none(fields["BASE_SHA"], _SHA40)
    head_sha = _sha_or_none(fields["TARGET_HEAD_SHA"], _SHA40)
    if target_pr is not None and head_sha is None:
        _fail()
    revision = _positive_or_none(fields["TASK_REVISION"])
    evidence_ref = None if fields["EVIDENCE_REF"] == "NONE" else _single(fields["EVIDENCE_REF"])
    evidence_sha = _sha_or_none(fields["EVIDENCE_SHA256"], _SHA64)
    if (evidence_ref is None) != (evidence_sha is None):
        _fail()
    expected_gate = _single(fields["EXPECTED_GATE"])
    if not _SYMBOL.fullmatch(expected_gate):
        _fail()
    if fields["NO_AUTO_MERGE"] != "TRUE":
        _fail()

    return AgentMessage(
        message_id, event_id, correlation_id, causation, task_id, from_role, to_role, kind,
        TARGET_REPOSITORY, target_issue, target_pr, base_sha, head_sha, revision,
        evidence_ref, evidence_sha, expected_gate, True, direction,
    )


def _none(value: object) -> str:
    return "NONE" if value is None else str(value)


def canonical_message_body(message: AgentMessage) -> str:
    values = {
        "MESSAGE_ID": _id(message.message_id),
        "EVENT_ID": _id(message.event_id),
        "CORRELATION_ID": _id(message.correlation_id),
        "CAUSATION_MESSAGE_ID": "NONE" if message.causation_message_id is None else _id(message.causation_message_id),
        "TASK_ID": _single(message.task_id),
        "FROM_ROLE": _single(message.from_role),
        "TO_ROLE": _single(message.to_role),
        "MESSAGE_KIND": _single(message.message_kind),
        "TARGET_REPO": _single(message.target_repo),
        "TARGET_ISSUE": _none(message.target_issue),
        "TARGET_PR": _none(message.target_pr),
        "BASE_SHA": _none(message.base_sha),
        "TARGET_HEAD_SHA": _none(message.target_head_sha),
        "TASK_REVISION": _none(message.task_revision),
        "EVIDENCE_REF": _none(message.evidence_ref),
        "EVIDENCE_SHA256": _none(message.evidence_sha256),
        "EXPECTED_GATE": _single(message.expected_gate),
        "NO_AUTO_MERGE": "TRUE" if message.no_auto_merge is True else "FALSE",
    }
    lines = [MESSAGE_MARKER] + [f"{key} = {values[key]}" for key in MESSAGE_KEYS]
    if message.direction:
        if "\x00" in message.direction:
            _fail()
        lines.extend(["", message.direction.strip()])
    text = "\n".join(lines)
    parse_message(text)
    return text


def message_body_digest(message: AgentMessage) -> str:
    return sha256(canonical_message_body(message).encode("utf-8")).hexdigest()
