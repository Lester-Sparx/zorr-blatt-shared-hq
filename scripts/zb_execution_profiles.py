from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import PurePosixPath

from scripts.zb_execution_contract import ExecutionRequest


class ExecutionProfileError(ValueError):
    pass


TASK_VERSION = "3.53.1"
OPENCODE_VERSION = "1.18.17"


@dataclass(frozen=True)
class ExecutionProfile:
    name: str
    version: int
    logical_role: str
    task_name: str
    max_timeout_seconds: int
    allowed_write_scope: tuple[str, ...]


PROFILES = {
    "LESTER_IMPLEMENT_R01": ExecutionProfile(
        name="LESTER_IMPLEMENT_R01",
        version=1,
        logical_role="LESTER",
        task_name="zb:exec:lester:implement-r01",
        max_timeout_seconds=1800,
        allowed_write_scope=("scripts/", "tests/", "config/", ".github/workflows/", "Taskfile.yml"),
    ),
    "DUNCAN_QC_R01": ExecutionProfile(
        name="DUNCAN_QC_R01",
        version=1,
        logical_role="DUNCAN",
        task_name="zb:exec:duncan:qc-r01",
        max_timeout_seconds=900,
        allowed_write_scope=("evidence/",),
    ),
}


def _scope_is_within(candidate: str, allowed: str) -> bool:
    if candidate == allowed:
        return True
    if allowed.endswith("/"):
        return candidate.startswith(allowed)
    return False


def resolve_profile(request: ExecutionRequest) -> ExecutionProfile:
    profile = PROFILES.get(request.execution_profile)
    if profile is None:
        raise ExecutionProfileError("EXECUTION_PROFILE_REJECTED")
    if request.execution_profile_version != profile.version:
        raise ExecutionProfileError("EXECUTION_PROFILE_VERSION_REJECTED")
    if request.logical_role != profile.logical_role:
        raise ExecutionProfileError("EXECUTION_PROFILE_ROLE_REJECTED")
    if request.timeout_seconds > profile.max_timeout_seconds:
        raise ExecutionProfileError("EXECUTION_PROFILE_TIMEOUT_REJECTED")
    for path in request.allowed_write_scope:
        normalized = str(PurePosixPath(path))
        if normalized.startswith("../") or normalized == ".." or normalized.startswith("/"):
            raise ExecutionProfileError("EXECUTION_PROFILE_SCOPE_REJECTED")
        if not any(_scope_is_within(path, allowed) for allowed in profile.allowed_write_scope):
            raise ExecutionProfileError("EXECUTION_PROFILE_SCOPE_REJECTED")
    return profile


def validate_task_inventory(inventory_json: str, *, profile: ExecutionProfile) -> None:
    try:
        payload = json.loads(inventory_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ExecutionProfileError("TASK_INVENTORY_INVALID") from exc
    tasks = payload.get("tasks") if isinstance(payload, dict) else None
    if not isinstance(tasks, list):
        raise ExecutionProfileError("TASK_INVENTORY_INVALID")
    names: list[str] = []
    for item in tasks:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ExecutionProfileError("TASK_INVENTORY_INVALID")
        name = item["name"]
        if not name or "{{" in name or "}}" in name or "$" in name:
            raise ExecutionProfileError("TASK_INVENTORY_DYNAMIC")
        names.append(name)
    expected = {item.task_name for item in PROFILES.values()}
    if len(names) != len(set(names)) or set(names) != expected:
        raise ExecutionProfileError("TASK_INVENTORY_MISMATCH")
    if profile.task_name not in names:
        raise ExecutionProfileError("TASK_INVENTORY_MISMATCH")


def validate_taskfile_text(text: str) -> None:
    if not isinstance(text, str) or not text:
        raise ExecutionProfileError("TASKFILE_INVALID")
    forbidden = ("CLI_ARGS", "$ZB_", "{{", "}}", "http://", "https://", "includes:")
    if any(token in text for token in forbidden):
        raise ExecutionProfileError("TASKFILE_DYNAMIC_SURFACE")
    required = (
        "version: '3'",
        "zb:exec:lester:implement-r01",
        "zb:exec:duncan:qc-r01",
        "python -m scripts.zb_execution_cli execute --from-env",
        "python -m scripts.zb_execution_cli qc --from-env",
    )
    if any(token not in text for token in required):
        raise ExecutionProfileError("TASKFILE_INVENTORY_MISMATCH")


def validate_toolchain_versions(*, task_version: str, opencode_version: str | None) -> None:
    if task_version != TASK_VERSION:
        raise ExecutionProfileError("TASK_VERSION_MISMATCH")
    if opencode_version is not None and opencode_version != OPENCODE_VERSION:
        raise ExecutionProfileError("OPENCODE_VERSION_MISMATCH")
