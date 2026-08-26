from __future__ import annotations

from dataclasses import dataclass
import re

ALLOWED_AGENTS = {"SALVADOR"}
ALLOWED_TASK_KINDS = {"PRODUCTION_IMAGE_EDIT"}
ALLOWED_STATES = {"ASSIGNED", "WAITING_REFERENCE"}
ALLOWED_REFERENCE_MODES = {"LOCAL_INBOX"}
_MACHINE_KEYS = ("TASK_ID", "AGENT", "TASK_KIND", "STATE", "REFERENCE")
_TASK_ID_RE = re.compile(r"^[A-Z0-9_-]+$")


class TaskContractError(ValueError):
    def __init__(self, code: str, message: str | None = None):
        self.code = code
        super().__init__(message or code)


@dataclass(frozen=True)
class AgentTask:
    task_id: str
    agent: str
    task_kind: str
    state: str
    reference: str
    direction: str


def parse_task(body: str) -> AgentTask:
    if not isinstance(body, str):
        raise TaskContractError("MISSING_MARKER")
    lines = body.splitlines()
    try:
        marker_index = next(i for i, line in enumerate(lines) if line.strip() == "ZB_AGENT_TASK_V0")
    except StopIteration as exc:
        raise TaskContractError("MISSING_MARKER") from exc

    fields: dict[str, str] = {}
    direction_start = None
    for i in range(marker_index + 1, len(lines)):
        raw = lines[i]
        if not raw.strip():
            direction_start = i + 1
            break
        if "=" not in raw:
            raise TaskContractError("UNKNOWN_FIELD")
        key, value = (part.strip() for part in raw.split("=", 1))
        if key not in _MACHINE_KEYS:
            raise TaskContractError("UNKNOWN_FIELD")
        if key in fields:
            raise TaskContractError("DUPLICATE_FIELD")
        fields[key] = value

    missing = [key for key in _MACHINE_KEYS if key not in fields or not fields[key]]
    if missing:
        raise TaskContractError("MISSING_FIELD")

    direction = "\n".join(lines[direction_start or len(lines):]).strip()
    if not direction:
        raise TaskContractError("EMPTY_DIRECTION")

    if not _TASK_ID_RE.fullmatch(fields["TASK_ID"]):
        raise TaskContractError("INVALID_TASK_ID")
    if fields["AGENT"] not in ALLOWED_AGENTS:
        raise TaskContractError("INVALID_AGENT")
    if fields["TASK_KIND"] not in ALLOWED_TASK_KINDS:
        raise TaskContractError("INVALID_TASK_KIND")
    if fields["STATE"] not in ALLOWED_STATES:
        raise TaskContractError("INVALID_STATE")
    if fields["REFERENCE"] not in ALLOWED_REFERENCE_MODES:
        raise TaskContractError("INVALID_REFERENCE_MODE")

    return AgentTask(
        task_id=fields["TASK_ID"],
        agent=fields["AGENT"],
        task_kind=fields["TASK_KIND"],
        state=fields["STATE"],
        reference=fields["REFERENCE"],
        direction=direction,
    )
