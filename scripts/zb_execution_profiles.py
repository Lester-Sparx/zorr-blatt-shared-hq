from __future__ import annotations

from dataclasses import dataclass
import json
from types import MappingProxyType
from typing import Mapping

from scripts.zb_execution_contract import ExecutionRequest


TASK_VERSION = "3.53.1"
OPENCODE_VERSION = "1.18.17"


class ExecutionProfileError(ValueError):
    pass


@dataclass(frozen=True)
class ExecutionProfile:
    name: str
    version: int
    logical_role: str
    task_name: str
    worker_backend: str
    max_timeout_seconds: int
    max_write_prefixes: tuple[str, ...]


_PROFILES = {
    "LESTER_IMPLEMENT_R01": ExecutionProfile(
        name="LESTER_IMPLEMENT_R01",
        version=1,
        logical_role="LESTER",
        task_name="zb:exec:lester:implement-r01",
        worker_backend="opencode",
        max_timeout_seconds=1800,
        max_write_prefixes=("scripts/", "tests/", "config/zb-execution/", ".github/workflows/", "Taskfile.yml"),
    ),
    "DUNCAN_QC_R01": ExecutionProfile(
        name="DUNCAN_QC_R01",
        version=1,
        logical_role="DUNCAN",
        task_name="zb:exec:duncan:qc-r01",
        worker_backend="deterministic-qc",
        max_timeout_seconds=900,
        max_write_prefixes=("evidence/",),
    ),
}
PROFILES: Mapping[str, ExecutionProfile] = MappingProxyType(_PROFILES)


def _scope_is_safe(scope: str) -> bool:
    if not scope or scope.startswith("/") or scope.startswith("~") or "\\" in scope or "\x00" in scope:
        return False
    parts = scope.split("/")
    return all(part not in {"..", "."} for part in parts if part)


def _scope_allowed(scope: str, trusted: tuple[str, ...]) -> bool:
    if not _scope_is_safe(scope):
        return False
    for prefix in trusted:
        if prefix.endswith("/"):
            if scope == prefix or scope.startswith(prefix):
                return True
        elif scope == prefix:
            return True
    return False


def resolve_profile(request: ExecutionRequest) -> ExecutionProfile:
    profile = PROFILES.get(request.execution_profile)
    if profile is None:
        raise ExecutionProfileError("EXECUTION_PROFILE_REJECTED")
    if request.logical_role != profile.logical_role:
        raise ExecutionProfileError("EXECUTION_ROLE_MISMATCH")
    if request.execution_profile_version != profile.version:
        raise ExecutionProfileError("EXECUTION_PROFILE_VERSION_MISMATCH")
    if request.timeout_seconds > profile.max_timeout_seconds:
        raise ExecutionProfileError("EXECUTION_TIMEOUT_ESCALATION")
    if not all(_scope_allowed(scope, profile.max_write_prefixes) for scope in request.allowed_write_scope):
        raise ExecutionProfileError("EXECUTION_WRITE_SCOPE_ESCALATION")
    return profile


def validate_task_inventory(task_json: str, profile: ExecutionProfile) -> None:
    try:
        payload = json.loads(task_json)
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
        "python scripts/zb_execution_cli.py execute --from-env",
        "python scripts/zb_execution_cli.py qc --from-env",
    )
    if any(token not in text for token in required):
        raise ExecutionProfileError("TASKFILE_INVENTORY_MISMATCH")


def validate_toolchain_versions(*, task_version: str, opencode_version: str | None) -> None:
    if task_version != TASK_VERSION:
        raise ExecutionProfileError("TASK_VERSION_MISMATCH")
    if opencode_version is not None and opencode_version != OPENCODE_VERSION:
        raise ExecutionProfileError("OPENCODE_VERSION_MISMATCH")
