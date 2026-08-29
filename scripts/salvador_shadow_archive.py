from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Mapping

from scripts.hq_archive_ingest import _canonical_json, _write_once


SCHEMA = "SALVADOR_SHADOW_PROGRESS_V1"
_RUNTIME_STATES = {"WAITING_REFERENCE", "RUNNING", "RESULT_READY", "FAILED"}
_SKILL_STATES = {"UNTESTED", "FAILED", "PARTIAL", "PROVEN", "LOCKED"}


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


def _field(body: str, name: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(name)}\s*=\s*(.+?)\s*$", body)
    return match.group(1).strip() if match else None


def _count(body: str, name: str) -> int | None:
    value = _field(body, name)
    if value is None:
        return None
    token = value.split("/", 1)[0].strip()
    return int(token) if token.isdigit() else None


def _total(body: str) -> int | None:
    value = _field(body, "PASS")
    if value is None or "/" not in value:
        return None
    token = value.split("/", 1)[1].strip()
    return int(token) if token.isdigit() else None


def _sequence(metadata: Mapping[str, str], comment_id: object) -> list[int]:
    try:
        return [int(metadata.get("run_id", "0")), int(metadata.get("run_attempt", "0")), int(comment_id)]
    except (TypeError, ValueError):
        return [0, 0, 0]


def reduce_salvador_state(archive_root: Path) -> str:
    root = Path(archive_root) / "derived" / "salvador-shadow-v1" / "events"
    ordered: list[tuple[tuple[int, int, int], str]] = []
    if not root.is_dir():
        return "UNTESTED"
    for path in root.glob("*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(record, dict) or record.get("schema") != SCHEMA:
            continue
        sequence = record.get("sequence")
        state_after = record.get("state_after")
        if (
            not isinstance(sequence, list)
            or len(sequence) != 3
            or not all(isinstance(value, int) for value in sequence)
            or state_after not in _SKILL_STATES
        ):
            continue
        ordered.append(((sequence[0], sequence[1], sequence[2]), str(state_after)))
    if not ordered:
        return "UNTESTED"
    ordered.sort(key=lambda item: item[0])
    return ordered[-1][1]


def _write_record(event_bytes: bytes, archive_root: Path, record: dict[str, object]) -> dict[str, str]:
    digest = hashlib.sha256(event_bytes).hexdigest()
    record["source_raw_sha256"] = digest
    rel = Path("derived") / "salvador-shadow-v1" / "events" / f"{digest}.json"
    _write_once(
        Path(archive_root) / rel,
        _canonical_json(record),
        collision_code="SALVADOR_SHADOW_EVENT_COLLISION",
    )
    return {"shadow_relpath": rel.as_posix(), "source_raw_sha256": digest}


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
    if not isinstance(body, str):
        return None

    issue_number = issue.get("number")
    comment_id = comment.get("id")
    state_before = reduce_salvador_state(archive_root)
    sequence = _sequence(metadata, comment_id)

    if body.startswith("ZB_AGENT_EVENT_V0\n"):
        values = _fields(body)
        if values.get("AGENT") != "SALVADOR" or values.get("STATE") not in _RUNTIME_STATES:
            return None
        return _write_record(
            event_bytes,
            archive_root,
            {
                "schema": SCHEMA,
                "kind": "RUNTIME_OBSERVATION",
                "sequence": sequence,
                "issue": issue_number,
                "comment_id": comment_id,
                "task_id": values.get("TASK_ID", ""),
                "runtime_state": values["STATE"],
                "execution_id": values.get("EXECUTION_ID", ""),
                "result_sha256": values.get("RESULT_SHA256", ""),
                "state_before": state_before,
                "state_after": state_before,
                "training_eligible": False,
                "promotion_allowed": False,
            },
        )

    if body.startswith("JINGO_TARGETED_STRESS_R02_EVALUATION\n"):
        if _field(body, "LOGICAL_EVALUATOR") != "JINGO":
            return None
        if _field(body, "CLASS") != "TRAINING DIAGNOSIS / SAME-RUNTIME":
            return None
        passed = _count(body, "PASS")
        total = _total(body)
        major = _count(body, "MAJOR")
        critical = _count(body, "CRITICAL")
        if None in {passed, total, major, critical} or total == 0:
            return None
        state_after = "FAILED" if critical > 0 else "PARTIAL"
        return _write_record(
            event_bytes,
            archive_root,
            {
                "schema": SCHEMA,
                "kind": "TRAINING_EVALUATION",
                "sequence": sequence,
                "issue": issue_number,
                "comment_id": comment_id,
                "measurements": {
                    "pass": passed,
                    "total": total,
                    "major": major,
                    "critical": critical,
                },
                "state_before": state_before,
                "state_after": state_after,
                "training_eligible": True,
                "certification": False,
                "holdout": False,
                "promotion_allowed": False,
            },
        )

    return None
