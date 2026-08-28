from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from scripts.zb_execution_profiles import (
    ExecutionProfile,
    ExecutionProfileError,
    PROFILES,
    validate_task_inventory,
    validate_toolchain_versions,
)


RUNNER_VERSION = "2.337.0"
RUNNER_WINDOWS_X64_SHA256 = "1150692afa94e71f872017e254ea55b6eece1eece3fe7e3a6d4c93d0a1b85cfc"
TASK_VERSION = "3.53.1"
TASK_WINDOWS_AMD64_SHA256 = "27c0cd248c12cba03d8958d954a3df981c900be885ec9ce5f6a3cdc4e9a19316"
OPENCODE_VERSION = "1.18.25"
OPENCODE_WINDOWS_X64_SHA256 = "831e213e5f454d6e8b26f0fb24c7b3d42b40e47d73d154672a9192702eb08416"


class PreflightError(RuntimeError):
    pass


def _translate_profile_error(exc: ExecutionProfileError) -> PreflightError:
    return PreflightError(str(exc))


def run_implementation_preflight(
    *,
    profile: ExecutionProfile,
    task_version: str,
    task_inventory_json: str,
    opencode_version: str | None,
) -> None:
    try:
        validate_toolchain_versions(task_version=task_version, opencode_version=opencode_version)
        validate_task_inventory(task_inventory_json, profile)
    except ExecutionProfileError as exc:
        raise _translate_profile_error(exc) from exc
    if profile.worker_backend == "opencode" and opencode_version is None:
        raise PreflightError("OPENCODE_VERSION_MISSING")


def _static_policy() -> dict:
    path = Path(__file__).resolve().parents[1] / "config" / "zb-execution" / "opencode-r01.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreflightError("STATIC_OPENCODE_POLICY_INVALID") from exc
    if not isinstance(value, dict):
        raise PreflightError("STATIC_OPENCODE_POLICY_INVALID")
    return value


def validate_effective_opencode_config(config_json: str) -> None:
    try:
        config = json.loads(config_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise PreflightError("EFFECTIVE_CONFIG_INVALID") from exc
    if not isinstance(config, dict):
        raise PreflightError("EFFECTIVE_CONFIG_INVALID")

    if config.get("mcp"):
        raise PreflightError("UNAPPROVED_MCP")
    if config.get("plugin") or config.get("plugins"):
        raise PreflightError("UNAPPROVED_PLUGIN")
    if config.get("agent") or config.get("agents"):
        raise PreflightError("UNAPPROVED_AGENT_OVERRIDE")
    if config.get("command") or config.get("commands"):
        raise PreflightError("UNAPPROVED_COMMAND_OVERRIDE")

    permission = config.get("permission")
    if not isinstance(permission, dict) or permission.get("*") != "deny":
        raise PreflightError("EFFECTIVE_CONFIG_DENY_DEFAULT_MISSING")
    if permission.get("external_directory") != "deny":
        raise PreflightError("EXTERNAL_DIRECTORY_WIDENED")
    if permission.get("webfetch") != "deny" or permission.get("websearch") != "deny":
        raise PreflightError("NETWORK_PERMISSION_WIDENED")
    if permission.get("task") != "deny":
        raise PreflightError("SUBAGENT_PERMISSION_WIDENED")
    if permission.get("question") != "deny":
        raise PreflightError("QUESTION_PERMISSION_WIDENED")

    bash = permission.get("bash")
    if not isinstance(bash, dict) or bash.get("*") != "deny":
        raise PreflightError("SHELL_PERMISSION_WIDENED")

    approved = _static_policy().get("permission", {})
    approved_bash = approved.get("bash", {}) if isinstance(approved, dict) else {}
    for pattern, effect in bash.items():
        if effect == "allow" and approved_bash.get(pattern) != "allow":
            raise PreflightError("SHELL_PERMISSION_WIDENED")
    for forbidden in ("git push *", "git commit *", "git merge *"):
        if bash.get(forbidden) != "deny":
            raise PreflightError("SHELL_PERMISSION_WIDENED")


def run_activation_preflight(
    *,
    repository_private: bool,
    disposable_host: bool,
    runner_version: str,
    runner_sha256: str,
    task_version: str,
    task_sha256: str,
    opencode_version: str,
    opencode_sha256: str,
    task_inventory_json: str,
    profile: ExecutionProfile,
    effective_config_json: str,
) -> None:
    if not repository_private and not disposable_host:
        raise PreflightError("RUNNER_SECURITY_GATE_BLOCKED")
    if runner_version != RUNNER_VERSION:
        raise PreflightError("RUNNER_VERSION_MISMATCH")
    if runner_sha256 != RUNNER_WINDOWS_X64_SHA256:
        raise PreflightError("RUNNER_PROVENANCE_MISMATCH")
    if task_sha256 != TASK_WINDOWS_AMD64_SHA256:
        raise PreflightError("TASK_PROVENANCE_MISMATCH")
    if opencode_sha256 != OPENCODE_WINDOWS_X64_SHA256:
        raise PreflightError("OPENCODE_PROVENANCE_MISMATCH")
    run_implementation_preflight(
        profile=profile,
        task_version=task_version,
        task_inventory_json=task_inventory_json,
        opencode_version=opencode_version,
    )
    validate_effective_opencode_config(effective_config_json)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("implementation", "activation"), required=True)
    args = parser.parse_args(argv)
    profile_name = os.environ.get("ZB_EXECUTION_PROFILE", "LESTER_IMPLEMENT_R01")
    profile = PROFILES.get(profile_name)
    if profile is None:
        raise PreflightError("EXECUTION_PROFILE_REJECTED")
    task_version = os.environ.get("ZB_TASK_VERSION", "")
    inventory = os.environ.get("ZB_TASK_INVENTORY_JSON", "")
    opencode_version = os.environ.get("ZB_OPENCODE_VERSION")
    if args.mode == "implementation":
        run_implementation_preflight(
            profile=profile,
            task_version=task_version,
            task_inventory_json=inventory,
            opencode_version=opencode_version,
        )
        print("IMPLEMENTATION_PREFLIGHT = PASS")
        return 0
    run_activation_preflight(
        repository_private=os.environ.get("ZB_REPOSITORY_PRIVATE") == "true",
        disposable_host=os.environ.get("ZB_DISPOSABLE_HOST") == "true",
        runner_version=os.environ.get("ZB_RUNNER_VERSION", ""),
        runner_sha256=os.environ.get("ZB_RUNNER_SHA256", ""),
        task_version=task_version,
        task_sha256=os.environ.get("ZB_TASK_SHA256", ""),
        opencode_version=opencode_version or "",
        opencode_sha256=os.environ.get("ZB_OPENCODE_SHA256", ""),
        task_inventory_json=inventory,
        profile=profile,
        effective_config_json=os.environ.get("ZB_EFFECTIVE_OPENCODE_CONFIG_JSON", ""),
    )
    print("ACTIVATION_PREFLIGHT = PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
