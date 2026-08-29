from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

from scripts.hq_archive_ingest import _canonical_json, _write_once


SCHEMA = "SALVADOR_SHADOW_PROGRESS_V1"
_RUNTIME_STATES = {"WAITING_REFERENCE", "RUNNING", "RESULT_READY", "FAILED"}


def _fields(body: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in body.splitlines()[1:]:
        if not line.strip():
            break
        if " = " not in line:
            return {}
        key, value = line.split(" = ", 1)
        key = key.strip()
        if key in values:
            return {}
        values[key] = value.strip()
    return values


def archive_salvador_shadow_event(
    event_bytes: bytes,
    archive_root: Path,
    metadata: Mapping[str, str],
) -> dict[str, str] | None:
    if metadata.get("event_name") != "issue_comment":
        return None
    try:
        payload = json.loads(event_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or payload.get("action") != "created":
        return None

    comment = payload.get("comment")
    issue = payload.get("issue")
    if not isinstance(comment, dict) or not isinstance(issue, dict):
        return None
    actor = comment.get("user")
    actor_login = actor.get("login") if isinstance(actor, dict) else None
    if actor_login != metadata.get("actor"):
        return None
    body = comment.get("body")
    if not isinstance(body, str) or not body.startswith("ZB_AGENT_EVENT_V0\n"):
        return None
    values = _fields(body)
    if values.get("AGENT") != "SALVADOR" or values.get("STATE") not in _RUNTIME_STATES:
        return None

    digest = hashlib.sha256(event_bytes).hexdigest()
    issue_number = issue.get("number")
    comment_id = comment.get("id")
    record = {
        "schema": SCHEMA,
        "kind": "RUNTIME_OBSERVATION",
        "source_raw_sha256": digest,
        "issue": issue_number,
        "comment_id": comment_id,
        "task_id": values.get("TASK_ID", ""),
        "runtime_state": values["STATE"],
        "execution_id": values.get("EXECUTION_ID", ""),
        "result_sha256": values.get("RESULT_SHA256", ""),
        "state_before": "UNTESTED",
        "state_after": "UNTESTED",
        "training_eligible": False,
        "promotion_allowed": False,
    }
    rel = Path("derived") / "salvador-shadow-v1" / "events" / f"{digest}.json"
    encoded = _canonical_json(record)
    _write_once(Path(archive_root) / rel, encoded, collision_code="SALVADOR_SHADOW_EVENT_COLLISION")
    return {"shadow_relpath": rel.as_posix(), "source_raw_sha256": digest}
