from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


REPOSITORY = "Lester-Sparx/zorr-blatt-shared-hq"
BUS_PR = 111
TRACKER_ISSUE = 106
TRANSPORT_ACTOR = "Lester-Sparx"
STATE_WRITER = "github-actions[bot]"
ROOT_MARKER = "ZB_AGENT_TASK_R03_V1"
TASK_SPEC_MARKER = "ZB_TASK_SPEC_V1"
DISPATCH_MARKER = "ZB_R03_DISPATCH_V1"
BUS_ISSUE_URL = f"https://api.github.com/repos/{REPOSITORY}/issues/{BUS_PR}"
TRACKER_ISSUE_URL = f"https://api.github.com/repos/{REPOSITORY}/issues/{TRACKER_ISSUE}"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "config" / "zb-r03" / "tasks.json"

_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_ROOT_FIELDS = (
    "MESSAGE_ID",
    "EVENT_ID",
    "CORRELATION_ID",
    "TASK_ID",
    "TASK_REVISION",
    "BASE_SHA",
    "TASK_SPEC_COMMENT_ID",
)
_SPEC_FIELDS = ("TASK_SPEC_ID", "TASK_ID", "TASK_REVISION", "BASE_SHA")
_REPLAY_STATES = frozenset({"DISPATCHED", "IN_PROGRESS", "PASS", "FAIL", "BLOCKED"})
_DISPATCH_PAYLOAD_KEYS = frozenset(
    {
        "root_comment_id",
        "message_id",
        "correlation_id",
        "task_id",
        "task_revision",
        "base_sha",
        "task_spec_comment_id",
        "task_spec_sha256",
        "replay_key",
    }
)


class ProtocolError(ValueError):
    pass


class GitHubPort(Protocol):
    def read_comment(self, comment_id: int) -> dict[str, Any]: ...
    def list_tracker_comments(self) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class R03TaskPolicy:
    task_id: str
    revision: int
    profile: str
    allowed_files: tuple[str, ...]
    max_changed_files: int
    max_patch_kb: int
    timeout_minutes: int
    auto_merge_after_duncan: bool


@dataclass(frozen=True)
class R03TaskSpec:
    task_spec_id: str
    task_id: str
    task_revision: int
    base_sha: str
    instructions: str


@dataclass(frozen=True)
class R03Dispatch:
    message_id: str
    event_id: str
    correlation_id: str
    task_id: str
    task_revision: int
    base_sha: str
    task_spec_comment_id: int
    task_spec_sha256: str
    task_spec_b64: str
    authority_ref: str
    task: R03TaskPolicy
    replay_key: str


def _require_identifier(value: str, code: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ProtocolError(code)
    return value


def _positive_int(value: Any, code: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ProtocolError(code) from exc
    if parsed <= 0 or isinstance(value, bool):
        raise ProtocolError(code)
    if isinstance(value, str) and str(parsed) != value:
        raise ProtocolError(code)
    return parsed


def _parse_exact_fields(lines: list[str], *, expected: tuple[str, ...], code: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in lines:
        if not line or " = " not in line:
            raise ProtocolError(code)
        name, value = line.split(" = ", 1)
        if name not in expected or name in values or not value:
            raise ProtocolError(code)
        values[name] = value
    if tuple(values.keys()) != expected:
        raise ProtocolError(code)
    return values


def _load_registry() -> dict[str, Any]:
    try:
        payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProtocolError("R03_TASK_REGISTRY_INVALID") from exc
    if not isinstance(payload, dict) or payload.get("schema") != "ZB_R03_TASK_REGISTRY_V1":
        raise ProtocolError("R03_TASK_REGISTRY_INVALID")
    tasks = payload.get("tasks")
    if not isinstance(tasks, dict) or not tasks:
        raise ProtocolError("R03_TASK_REGISTRY_INVALID")
    return tasks


def _valid_allowed_pattern(pattern: Any) -> bool:
    if not isinstance(pattern, str) or not pattern or pattern.startswith(("/", "~")) or "\\" in pattern or "\x00" in pattern:
        return False
    if ".." in pattern.split("/"):
        return False
    return pattern.endswith("/**") and pattern.count("*") == 2


def resolve_task(task_id: str, revision: int) -> R03TaskPolicy:
    _require_identifier(task_id, "R03_TASK_REJECTED")
    tasks = _load_registry()
    raw = tasks.get(task_id)
    if not isinstance(raw, dict):
        raise ProtocolError("R03_TASK_REJECTED")
    if raw.get("revision") != revision:
        raise ProtocolError("R03_TASK_REVISION_MISMATCH")
    expected_keys = {
        "revision",
        "profile",
        "allowed_files",
        "max_changed_files",
        "max_patch_kb",
        "timeout_minutes",
        "auto_merge_after_duncan",
    }
    if set(raw) != expected_keys:
        raise ProtocolError("R03_TASK_REGISTRY_INVALID")
    profile = raw.get("profile")
    allowed = raw.get("allowed_files")
    numeric = (raw.get("max_changed_files"), raw.get("max_patch_kb"), raw.get("timeout_minutes"))
    if not isinstance(profile, str) or not _IDENTIFIER.fullmatch(profile):
        raise ProtocolError("R03_TASK_REGISTRY_INVALID")
    if not isinstance(allowed, list) or not allowed or not all(_valid_allowed_pattern(item) for item in allowed):
        raise ProtocolError("R03_TASK_REGISTRY_INVALID")
    if len(allowed) != len(set(allowed)):
        raise ProtocolError("R03_TASK_REGISTRY_INVALID")
    if any(not isinstance(item, int) or isinstance(item, bool) or item <= 0 for item in numeric):
        raise ProtocolError("R03_TASK_REGISTRY_INVALID")
    auto_merge = raw.get("auto_merge_after_duncan")
    if not isinstance(auto_merge, bool):
        raise ProtocolError("R03_TASK_REGISTRY_INVALID")
    return R03TaskPolicy(
        task_id=task_id,
        revision=revision,
        profile=profile,
        allowed_files=tuple(allowed),
        max_changed_files=raw["max_changed_files"],
        max_patch_kb=raw["max_patch_kb"],
        timeout_minutes=raw["timeout_minutes"],
        auto_merge_after_duncan=auto_merge,
    )


def parse_task_spec_comment(body: Any, *, expected_comment_id: int, comment_id: int) -> R03TaskSpec:
    if comment_id != expected_comment_id:
        raise ProtocolError("R03_TASK_SPEC_COMMENT_ID_MISMATCH")
    if not isinstance(body, str):
        raise ProtocolError("R03_TASK_SPEC_INVALID")
    lines = body.splitlines()
    if not lines or lines[0] != TASK_SPEC_MARKER:
        raise ProtocolError("R03_TASK_SPEC_INVALID")
    try:
        blank = lines.index("")
    except ValueError as exc:
        raise ProtocolError("R03_TASK_SPEC_INVALID") from exc
    if blank != 5:
        raise ProtocolError("R03_TASK_SPEC_INVALID")
    values = _parse_exact_fields(lines[1:blank], expected=_SPEC_FIELDS, code="R03_TASK_SPEC_INVALID")
    task_spec_id = _require_identifier(values["TASK_SPEC_ID"], "R03_TASK_SPEC_INVALID")
    task_id = _require_identifier(values["TASK_ID"], "R03_TASK_SPEC_INVALID")
    revision = _positive_int(values["TASK_REVISION"], "R03_TASK_SPEC_INVALID")
    base_sha = values["BASE_SHA"]
    if not _SHA40.fullmatch(base_sha):
        raise ProtocolError("R03_TASK_SPEC_INVALID")
    instructions = "\n".join(lines[blank + 1 :]).strip()
    if not instructions:
        raise ProtocolError("R03_TASK_SPEC_INVALID")
    return R03TaskSpec(task_spec_id, task_id, revision, base_sha, instructions)


def _parse_root(body: Any) -> dict[str, Any]:
    if not isinstance(body, str):
        raise ProtocolError("R03_ROOT_INVALID")
    lines = body.splitlines()
    if not lines or lines[0] != ROOT_MARKER:
        raise ProtocolError("R03_ROOT_MARKER_REJECTED")
    if len(lines) != 1 + len(_ROOT_FIELDS):
        raise ProtocolError("R03_ROOT_INVALID")
    values = _parse_exact_fields(lines[1:], expected=_ROOT_FIELDS, code="R03_ROOT_INVALID")
    message_id = _require_identifier(values["MESSAGE_ID"], "R03_ROOT_INVALID")
    event_id = _require_identifier(values["EVENT_ID"], "R03_ROOT_INVALID")
    correlation_id = _require_identifier(values["CORRELATION_ID"], "R03_ROOT_INVALID")
    task_id = _require_identifier(values["TASK_ID"], "R03_ROOT_INVALID")
    task_revision = _positive_int(values["TASK_REVISION"], "R03_ROOT_INVALID")
    base_sha = values["BASE_SHA"]
    if not _SHA40.fullmatch(base_sha):
        raise ProtocolError("R03_ROOT_INVALID")
    task_spec_comment_id = _positive_int(values["TASK_SPEC_COMMENT_ID"], "R03_ROOT_INVALID")
    return {
        "message_id": message_id,
        "event_id": event_id,
        "correlation_id": correlation_id,
        "task_id": task_id,
        "task_revision": task_revision,
        "base_sha": base_sha,
        "task_spec_comment_id": task_spec_comment_id,
    }


def replay_key(message_id: str, task_id: str, task_revision: int, base_sha: str, task_spec_sha256: str) -> str:
    _require_identifier(message_id, "R03_REPLAY_KEY_INVALID")
    _require_identifier(task_id, "R03_REPLAY_KEY_INVALID")
    if not isinstance(task_revision, int) or isinstance(task_revision, bool) or task_revision <= 0:
        raise ProtocolError("R03_REPLAY_KEY_INVALID")
    if not _SHA40.fullmatch(base_sha) or not _SHA256.fullmatch(task_spec_sha256):
        raise ProtocolError("R03_REPLAY_KEY_INVALID")
    return f"{message_id}|{task_id}|{task_revision}|{base_sha}|{task_spec_sha256}"


def _trusted_comment(comment: Any) -> bool:
    if not isinstance(comment, dict) or comment.get("issue_url") != TRACKER_ISSUE_URL:
        return False
    user = comment.get("user") or {}
    return isinstance(user, dict) and user.get("login") == STATE_WRITER


def _body_fields(body: Any) -> dict[str, str]:
    if not isinstance(body, str):
        return {}
    fields: dict[str, str] = {}
    for line in body.splitlines()[1:]:
        if " = " in line:
            name, value = line.split(" = ", 1)
            if name in fields:
                return {}
            fields[name] = value
    return fields


def _trusted_replay_exists(key: str, port: GitHubPort) -> bool:
    for comment in port.list_tracker_comments():
        if not _trusted_comment(comment):
            continue
        fields = _body_fields(comment.get("body"))
        if fields.get("REPLAY_KEY") == key and fields.get("STATE") in _REPLAY_STATES:
            return True
    return False


def _build_dispatch(event: Any, *, expected_base_sha: str, port: GitHubPort, check_replay: bool) -> R03Dispatch:
    if not isinstance(event, dict):
        raise ProtocolError("R03_EVENT_REJECTED")
    repository = event.get("repository") or {}
    issue = event.get("issue") or {}
    comment = event.get("comment") or {}
    user = comment.get("user") or {}
    if repository.get("full_name") != REPOSITORY:
        raise ProtocolError("R03_REPOSITORY_REJECTED")
    if issue.get("number") != BUS_PR or not issue.get("pull_request"):
        raise ProtocolError("R03_PR_REJECTED")
    if user.get("login") != TRANSPORT_ACTOR:
        raise ProtocolError("R03_ACTOR_REJECTED")

    root = _parse_root(comment.get("body"))
    if root["base_sha"] != expected_base_sha:
        raise ProtocolError("R03_BASE_SHA_MISMATCH")
    task = resolve_task(root["task_id"], root["task_revision"])

    spec_comment = port.read_comment(root["task_spec_comment_id"])
    if not isinstance(spec_comment, dict):
        raise ProtocolError("R03_TASK_SPEC_READBACK_INVALID")
    if spec_comment.get("id") != root["task_spec_comment_id"]:
        raise ProtocolError("R03_TASK_SPEC_COMMENT_ID_MISMATCH")
    if spec_comment.get("issue_url") != BUS_ISSUE_URL:
        raise ProtocolError("R03_TASK_SPEC_CONTAINER_MISMATCH")
    spec_user = spec_comment.get("user") or {}
    if not isinstance(spec_user, dict) or spec_user.get("login") != TRANSPORT_ACTOR:
        raise ProtocolError("R03_TASK_SPEC_ACTOR_MISMATCH")
    spec_body = spec_comment.get("body")
    spec = parse_task_spec_comment(
        spec_body,
        expected_comment_id=root["task_spec_comment_id"],
        comment_id=spec_comment["id"],
    )
    if (spec.task_id, spec.task_revision, spec.base_sha) != (root["task_id"], root["task_revision"], root["base_sha"]):
        raise ProtocolError("R03_TASK_SPEC_BINDING_MISMATCH")

    spec_bytes = spec_body.encode("utf-8")
    spec_sha256 = hashlib.sha256(spec_bytes).hexdigest()
    encoded = base64.b64encode(spec_bytes).decode("ascii")
    key = replay_key(root["message_id"], root["task_id"], root["task_revision"], root["base_sha"], spec_sha256)
    if check_replay and _trusted_replay_exists(key, port):
        raise ProtocolError("R03_REPLAY_BLOCKED")

    return R03Dispatch(
        message_id=root["message_id"],
        event_id=root["event_id"],
        correlation_id=root["correlation_id"],
        task_id=root["task_id"],
        task_revision=root["task_revision"],
        base_sha=root["base_sha"],
        task_spec_comment_id=root["task_spec_comment_id"],
        task_spec_sha256=spec_sha256,
        task_spec_b64=encoded,
        authority_ref=f"pr:{BUS_PR}:comment:{root['task_spec_comment_id']}",
        task=task,
        replay_key=key,
    )


def admit_r03_event(event: Any, *, expected_base_sha: str, port: GitHubPort) -> R03Dispatch:
    return _build_dispatch(event, expected_base_sha=expected_base_sha, port=port, check_replay=True)


def render_dispatch_record(dispatch: R03Dispatch, *, root_comment_id: int) -> str:
    if not isinstance(root_comment_id, int) or isinstance(root_comment_id, bool) or root_comment_id <= 0:
        raise ProtocolError("R03_ROOT_COMMENT_ID_INVALID")
    return "\n".join(
        [
            DISPATCH_MARKER,
            f"ROOT_COMMENT_ID = {root_comment_id}",
            f"MESSAGE_ID = {dispatch.message_id}",
            f"CORRELATION_ID = {dispatch.correlation_id}",
            f"TASK_ID = {dispatch.task_id}",
            f"TASK_REVISION = {dispatch.task_revision}",
            f"BASE_SHA = {dispatch.base_sha}",
            f"TASK_SPEC_COMMENT_ID = {dispatch.task_spec_comment_id}",
            f"TASK_SPEC_SHA256 = {dispatch.task_spec_sha256}",
            f"REPLAY_KEY = {dispatch.replay_key}",
            "STATE = DISPATCHED",
            "PRODUCTION_ACTIVE = NO",
        ]
    )


def dispatch_payload(dispatch: R03Dispatch, *, root_comment_id: int) -> dict[str, Any]:
    if not isinstance(root_comment_id, int) or isinstance(root_comment_id, bool) or root_comment_id <= 0:
        raise ProtocolError("R03_ROOT_COMMENT_ID_INVALID")
    return {
        "root_comment_id": root_comment_id,
        "message_id": dispatch.message_id,
        "correlation_id": dispatch.correlation_id,
        "task_id": dispatch.task_id,
        "task_revision": dispatch.task_revision,
        "base_sha": dispatch.base_sha,
        "task_spec_comment_id": dispatch.task_spec_comment_id,
        "task_spec_sha256": dispatch.task_spec_sha256,
        "replay_key": dispatch.replay_key,
    }


def revalidate_r03_repository_dispatch(payload: Any, *, port: GitHubPort) -> R03Dispatch:
    if not isinstance(payload, dict) or set(payload) != _DISPATCH_PAYLOAD_KEYS:
        raise ProtocolError("R03_REPOSITORY_DISPATCH_INVALID")
    root_comment_id = _positive_int(payload.get("root_comment_id"), "R03_REPOSITORY_DISPATCH_INVALID")
    expected_base_sha = payload.get("base_sha")
    if not isinstance(expected_base_sha, str) or not _SHA40.fullmatch(expected_base_sha):
        raise ProtocolError("R03_REPOSITORY_DISPATCH_INVALID")

    root_comment = port.read_comment(root_comment_id)
    if not isinstance(root_comment, dict) or root_comment.get("id") != root_comment_id:
        raise ProtocolError("R03_ROOT_READBACK_INVALID")
    if root_comment.get("issue_url") != BUS_ISSUE_URL:
        raise ProtocolError("R03_ROOT_CONTAINER_MISMATCH")
    root_user = root_comment.get("user") or {}
    if not isinstance(root_user, dict) or root_user.get("login") != TRANSPORT_ACTOR:
        raise ProtocolError("R03_ROOT_ACTOR_MISMATCH")

    synthetic_event = {
        "repository": {"full_name": REPOSITORY},
        "issue": {"number": BUS_PR, "pull_request": {"url": f"https://api.github.com/repos/{REPOSITORY}/pulls/{BUS_PR}"}},
        "comment": root_comment,
    }
    dispatch = _build_dispatch(synthetic_event, expected_base_sha=expected_base_sha, port=port, check_replay=False)
    expected_payload = dispatch_payload(dispatch, root_comment_id=root_comment_id)
    if payload != expected_payload:
        raise ProtocolError("R03_REPOSITORY_DISPATCH_MISMATCH")

    expected_record = render_dispatch_record(dispatch, root_comment_id=root_comment_id)
    exact_records = [
        comment
        for comment in port.list_tracker_comments()
        if _trusted_comment(comment) and comment.get("body") == expected_record
    ]
    if not exact_records:
        raise ProtocolError("R03_DISPATCH_RECORD_MISSING")
    if len(exact_records) != 1:
        raise ProtocolError("R03_DISPATCH_RECORD_AMBIGUOUS")
    return dispatch
