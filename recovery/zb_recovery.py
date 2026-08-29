from __future__ import annotations

import base64
import json
from typing import Callable, Mapping


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
