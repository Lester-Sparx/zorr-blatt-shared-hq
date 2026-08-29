from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping


class RecoveryError(RuntimeError):
    pass


def _dict(value: object, code: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise RecoveryError(code)
    return value


def _list(value: object, code: str) -> list[object]:
    if not isinstance(value, list):
        raise RecoveryError(code)
    return value


def _string(value: object, code: str) -> str:
    if not isinstance(value, str) or not value:
        raise RecoveryError(code)
    return value


def _require_sha(value: object, code: str) -> str:
    token = _string(value, code).lower()
    if len(token) != 40 or any(char not in "0123456789abcdef" for char in token):
        raise RecoveryError(code)
    return token


def _default_runner(args: list[str], **kwargs: Any):
    return subprocess.run(args, **kwargs)


def run_gh_json(
    endpoint: str,
    *,
    runner: Callable[..., Any] | None = None,
) -> object:
    command_runner = runner or _default_runner
    try:
        result = command_runner(
            ["gh", "api", endpoint],
            capture_output=True,
            text=True,
            shell=False,
        )
    except FileNotFoundError as exc:
        raise RecoveryError("RECOVERY_GH_CLI_UNAVAILABLE") from exc
    if result.returncode != 0:
        raise RecoveryError("RECOVERY_GH_API_FAILED")
    try:
        return json.loads(result.stdout or "null")
    except json.JSONDecodeError as exc:
        raise RecoveryError("RECOVERY_GH_OUTPUT_INVALID") from exc


def _branch_sha(payload: object, code: str) -> str:
    branch = _dict(payload, code)
    commit = _dict(branch.get("commit"), code)
    return _require_sha(commit.get("sha"), code)


def _pr_ref(payload: object, side: str, code: str) -> tuple[str, str]:
    pr = _dict(payload, code)
    node = _dict(pr.get(side), code)
    return _string(node.get("ref"), code), _require_sha(node.get("sha"), code)


def _comment_record(value: object) -> dict[str, object]:
    comment = _dict(value, "RECOVERY_BUS_COMMENT_INVALID")
    user = _dict(comment.get("user"), "RECOVERY_BUS_COMMENT_INVALID")
    comment_id = comment.get("id")
    if not isinstance(comment_id, int):
        raise RecoveryError("RECOVERY_BUS_COMMENT_INVALID")
    return {
        "id": comment_id,
        "body": _string(comment.get("body"), "RECOVERY_BUS_COMMENT_INVALID"),
        "created_at": _string(comment.get("created_at"), "RECOVERY_BUS_COMMENT_INVALID"),
        "actor": _string(user.get("login"), "RECOVERY_BUS_COMMENT_INVALID"),
    }


def _pr_record(value: object) -> dict[str, object]:
    pr = _dict(value, "RECOVERY_OPEN_PR_INVALID")
    number = pr.get("number")
    if not isinstance(number, int):
        raise RecoveryError("RECOVERY_OPEN_PR_INVALID")
    base_ref, base_sha = _pr_ref(pr, "base", "RECOVERY_OPEN_PR_INVALID")
    head_ref, head_sha = _pr_ref(pr, "head", "RECOVERY_OPEN_PR_INVALID")
    return {
        "number": number,
        "title": _string(pr.get("title"), "RECOVERY_OPEN_PR_INVALID"),
        "state": _string(pr.get("state"), "RECOVERY_OPEN_PR_INVALID"),
        "draft": bool(pr.get("draft", False)),
        "updated_at": _string(pr.get("updated_at"), "RECOVERY_OPEN_PR_INVALID"),
        "base_ref": base_ref,
        "base_sha": base_sha,
        "head_ref": head_ref,
        "head_sha": head_sha,
    }


def collect_recovery_state(
    manifest: Mapping[str, object],
    gh_json: Callable[[str], object],
) -> dict[str, object]:
    repository = _string(manifest.get("repository"), "RECOVERY_MANIFEST_INVALID")
    expected_actor = _string(manifest.get("expected_actor"), "RECOVERY_MANIFEST_INVALID")
    main_branch = _string(manifest.get("main_branch"), "RECOVERY_MANIFEST_INVALID")
    archive_branch = _string(manifest.get("archive_branch"), "RECOVERY_MANIFEST_INVALID")
    checkpoint_path = _string(manifest.get("checkpoint_path"), "RECOVERY_MANIFEST_INVALID")
    bus_number = manifest.get("communication_bus_pr")
    if not isinstance(bus_number, int) or bus_number <= 0:
        raise RecoveryError("RECOVERY_MANIFEST_INVALID")

    user = _dict(gh_json("user"), "RECOVERY_USER_UNREADABLE")
    actor = _string(user.get("login"), "RECOVERY_USER_UNREADABLE")
    if actor != expected_actor:
        raise RecoveryError(f"RECOVERY_ACTOR_MISMATCH:{actor}")

    prefix = f"repos/{repository}"
    repo = _dict(gh_json(prefix), "RECOVERY_REPOSITORY_UNREADABLE")
    if repo.get("full_name") != repository:
        raise RecoveryError("RECOVERY_REPOSITORY_MISMATCH")
    permissions = _dict(repo.get("permissions"), "RECOVERY_PERMISSIONS_UNREADABLE")
    required = manifest.get("required_permissions")
    if not isinstance(required, list) or not all(isinstance(item, str) and item for item in required):
        raise RecoveryError("RECOVERY_MANIFEST_INVALID")
    for permission in required:
        if permissions.get(permission) is not True:
            raise RecoveryError(f"RECOVERY_PERMISSION_MISSING:{permission}")

    main_sha = _branch_sha(
        gh_json(f"{prefix}/branches/{main_branch}"),
        "RECOVERY_MAIN_UNREADABLE",
    )
    archive_sha = _branch_sha(
        gh_json(f"{prefix}/branches/{archive_branch}"),
        "RECOVERY_ARCHIVE_UNREADABLE",
    )

    checkpoint_payload = _dict(
        gh_json(f"{prefix}/contents/{checkpoint_path}?ref={main_branch}"),
        "RECOVERY_CHECKPOINT_UNREADABLE",
    )
    checkpoint_blob_sha = _require_sha(
        checkpoint_payload.get("sha"), "RECOVERY_CHECKPOINT_SHA_INVALID"
    )
    if checkpoint_payload.get("encoding") != "base64":
        raise RecoveryError("RECOVERY_CHECKPOINT_ENCODING_INVALID")
    encoded = _string(checkpoint_payload.get("content"), "RECOVERY_CHECKPOINT_CONTENT_INVALID")
    try:
        checkpoint_text = base64.b64decode(encoded, validate=False).decode("utf-8")
        checkpoint = json.loads(checkpoint_text)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecoveryError("RECOVERY_CHECKPOINT_CONTENT_INVALID") from exc
    checkpoint = _dict(checkpoint, "RECOVERY_CHECKPOINT_CONTENT_INVALID")
    _string(checkpoint.get("checkpointId"), "RECOVERY_CHECKPOINT_ID_MISSING")

    bus_payload = _dict(
        gh_json(f"{prefix}/pulls/{bus_number}"), "RECOVERY_BUS_UNREADABLE"
    )
    if bus_payload.get("number") != bus_number:
        raise RecoveryError("RECOVERY_BUS_MISMATCH")
    bus_base_ref, bus_base_sha = _pr_ref(
        bus_payload, "base", "RECOVERY_BUS_UNREADABLE"
    )
    bus_head_ref, bus_head_sha = _pr_ref(
        bus_payload, "head", "RECOVERY_BUS_UNREADABLE"
    )
    bus = {
        "number": bus_number,
        "state": _string(bus_payload.get("state"), "RECOVERY_BUS_UNREADABLE"),
        "draft": bool(bus_payload.get("draft", False)),
        "base_ref": bus_base_ref,
        "base_sha": bus_base_sha,
        "head_ref": bus_head_ref,
        "head_sha": bus_head_sha,
    }

    comments = [
        _comment_record(item)
        for item in _list(
            gh_json(f"{prefix}/issues/{bus_number}/comments?per_page=100"),
            "RECOVERY_BUS_COMMENTS_UNREADABLE",
        )
    ]
    comments.sort(key=lambda item: (str(item["created_at"]), int(item["id"])))

    open_prs = [
        _pr_record(item)
        for item in _list(
            gh_json(f"{prefix}/pulls?state=open&per_page=100"),
            "RECOVERY_OPEN_PRS_UNREADABLE",
        )
    ]
    open_prs.sort(key=lambda item: (str(item["updated_at"]), int(item["number"])), reverse=True)

    return {
        "schema": "ZB_RECOVERY_STATE_V1",
        "actor": actor,
        "repository": repository,
        "permissions": {permission: True for permission in required},
        "main_sha": main_sha,
        "archive_sha": archive_sha,
        "checkpoint_blob_sha": checkpoint_blob_sha,
        "checkpoint": checkpoint,
        "bus": bus,
        "bus_comments": comments,
        "open_prs": open_prs,
    }


_STATE_KEYS = (
    "schema",
    "actor",
    "repository",
    "permissions",
    "main_sha",
    "archive_sha",
    "checkpoint_blob_sha",
    "checkpoint",
    "bus",
    "bus_comments",
    "open_prs",
)
_SENSITIVE_KEY_PARTS = ("token", "secret", "private_key", "authorization", "password")
_SENSITIVE_VALUE_MARKERS = (
    "ghp_",
    "github_pat_",
    "-----BEGIN PRIVATE KEY-----",
    "-----BEGIN RSA PRIVATE KEY-----",
    "-----BEGIN OPENSSH PRIVATE KEY-----",
)


def _safe_value(value: object) -> object:
    if isinstance(value, dict):
        clean: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                continue
            lowered = key.lower()
            if any(part in lowered for part in _SENSITIVE_KEY_PARTS):
                continue
            clean[key] = _safe_value(item)
        return clean
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        if any(marker in value for marker in _SENSITIVE_VALUE_MARKERS):
            return "[REDACTED_SECRET_MATERIAL]"
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def _safe_state(state: Mapping[str, object]) -> dict[str, object]:
    return {
        key: _safe_value(state[key])
        for key in _STATE_KEYS
        if key in state
    }


def render_recovery_state_json(state: Mapping[str, object]) -> str:
    return json.dumps(_safe_state(state), ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def render_resume_packet(
    manifest: Mapping[str, object],
    state: Mapping[str, object],
) -> str:
    safe = _safe_state(state)
    actor = _string(safe.get("actor"), "RECOVERY_STATE_INVALID")
    repository = _string(safe.get("repository"), "RECOVERY_STATE_INVALID")
    main_sha = _require_sha(safe.get("main_sha"), "RECOVERY_STATE_INVALID")
    archive_sha = _require_sha(safe.get("archive_sha"), "RECOVERY_STATE_INVALID")
    checkpoint_blob_sha = _require_sha(
        safe.get("checkpoint_blob_sha"), "RECOVERY_STATE_INVALID"
    )
    checkpoint = _dict(safe.get("checkpoint"), "RECOVERY_STATE_INVALID")
    checkpoint_id = _string(checkpoint.get("checkpointId"), "RECOVERY_STATE_INVALID")
    bus = _dict(safe.get("bus"), "RECOVERY_STATE_INVALID")
    bus_number = bus.get("number")
    if not isinstance(bus_number, int):
        raise RecoveryError("RECOVERY_STATE_INVALID")
    bus_head_sha = _require_sha(bus.get("head_sha"), "RECOVERY_STATE_INVALID")
    comments = _list(safe.get("bus_comments"), "RECOVERY_STATE_INVALID")
    open_prs = _list(safe.get("open_prs"), "RECOVERY_STATE_INVALID")

    lines = [
        "# ZORR BLATT — EMERGENCY RECOVERY RESUME PACKET",
        "",
        "NO CHAT IS PROJECT MEMORY. GITHUB DURABLE EVIDENCE IS PROJECT MEMORY.",
        "",
        f"GITHUB_ACTOR = {actor}",
        f"REPOSITORY = {repository}",
        f"MAIN_SHA = {main_sha}",
        f"ARCHIVE_SHA = {archive_sha}",
        f"CHECKPOINT_ID = {checkpoint_id}",
        f"CHECKPOINT_BLOB_SHA = {checkpoint_blob_sha}",
        f"COMMUNICATION_BUS_PR = {bus_number}",
        f"COMMUNICATION_BUS_HEAD = {bus_head_sha}",
        "",
        "## Active pull requests",
    ]
    for item in open_prs:
        pr = _dict(item, "RECOVERY_STATE_INVALID")
        number = pr.get("number")
        if not isinstance(number, int):
            raise RecoveryError("RECOVERY_STATE_INVALID")
        head_sha = _require_sha(pr.get("head_sha"), "RECOVERY_STATE_INVALID")
        lines.append(f"ACTIVE_PR_{number}_HEAD = {head_sha}")
        lines.append(f"ACTIVE_PR_{number}_TITLE = {_string(pr.get('title'), 'RECOVERY_STATE_INVALID')}")

    lines.extend(["", "## Latest permanent-bus evidence"])
    for item in comments:
        comment = _dict(item, "RECOVERY_STATE_INVALID")
        comment_id = comment.get("id")
        if not isinstance(comment_id, int):
            raise RecoveryError("RECOVERY_STATE_INVALID")
        body = _string(comment.get("body"), "RECOVERY_STATE_INVALID")
        lines.append(f"BUS_COMMENT_{comment_id} = {body}")

    lines.extend(
        [
            "",
            "## Mandatory continuation law",
            "1. Verify authenticated actor before any mutation.",
            "2. Fresh-read repository, main, zb-archive-v1, checkpoint, PR #111, and active PR heads before any mutation.",
            "3. Treat this packet as a bootstrap index, not authority over newer GitHub evidence.",
            "4. Never infer missing privileges; fail closed.",
            "5. Continue from the newest mutually consistent immutable GitHub evidence.",
            "",
            "This packet cannot grant privileges. The receiving client must already have an authorized GitHub connector or MCP connection.",
        ]
    )
    return "\n".join(lines) + "\n"


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def write_outputs(
    manifest: Mapping[str, object],
    state: Mapping[str, object],
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    state_path = output_dir / "RECOVERY_STATE.json"
    packet_path = output_dir / "RESUME_PACKET.md"
    _atomic_write(state_path, render_recovery_state_json(state))
    _atomic_write(packet_path, render_resume_packet(manifest, state))
    return state_path, packet_path


def load_manifest(path: Path) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecoveryError("RECOVERY_MANIFEST_INVALID") from exc
    return _dict(value, "RECOVERY_MANIFEST_INVALID")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        default="recovery/recovery_manifest.json",
    )
    parser.add_argument(
        "--output",
        default="recovery/.runtime",
    )
    args = parser.parse_args(argv)
    manifest = load_manifest(Path(args.manifest))
    state = collect_recovery_state(manifest, run_gh_json)
    state_path, packet_path = write_outputs(manifest, state, Path(args.output))
    print("ZB_RECOVERY_CAPSULE = PASS")
    print(f"RECOVERY_STATE = {state_path}")
    print(f"RESUME_PACKET = {packet_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
