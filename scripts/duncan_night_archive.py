from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Mapping

from scripts.hq_archive_ingest import _canonical_json, _write_once


SCHEMA = "DUNCAN_NIGHT_PROGRESS_V1"
CONTEXT_SCHEMA = "DUNCAN_CONTEXT_NEXT_V1"
DERIVED_REL = Path("derived") / "duncan-night-v1"
EVENTS_REL = DERIVED_REL / "events"
CONTEXT_REL = DERIVED_REL / "DUNCAN_CONTEXT_NEXT.json"
ALLOWED_SKILL_STATES = {"UNTESTED", "FAILED", "PARTIAL", "PROVEN"}
REPORT_MARKER = "DUNCAN_NIGHT_REPORT_R01"
REPORT_ISSUE = 111
REPORT_ACTOR = "Lester-Sparx"


class DuncanNightArchiveError(RuntimeError):
    pass


def _field(body: str, name: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(name)}\s*=\s*(.*?)\s*$", body)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def _section_lines(body: str, name: str) -> list[str] | None:
    lines = body.splitlines()
    start: int | None = None
    header = f"{name} ="
    for index, line in enumerate(lines):
        if line.strip() == header:
            start = index + 1
            break
    if start is None:
        return None

    collected: list[str] = []
    section_header = re.compile(r"^[A-Z][A-Z0-9_]*\s*=")
    for line in lines[start:]:
        stripped = line.strip()
        if stripped and section_header.match(stripped) and not stripped.startswith("-"):
            break
        if stripped:
            collected.append(stripped)
    return collected


def _parse_skill_deltas(lines: list[str] | None) -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []
    parsed: list[dict[str, str]] = []
    if lines is None:
        return parsed, ["SKILL_DELTA_MISSING"]
    if not lines:
        return parsed, ["SKILL_DELTA_EMPTY"]

    pattern = re.compile(
        r"^-\s*([A-Za-z0-9_.-]+)\s*:\s*([A-Z0-9_+.-]+)\s*->\s*([A-Z0-9_+.-]+)\s*$"
    )
    seen: set[str] = set()
    for line in lines:
        match = pattern.fullmatch(line)
        if not match:
            errors.append(f"SKILL_DELTA_MALFORMED:{line}")
            continue
        skill, before, after = match.groups()
        if skill in seen:
            errors.append(f"SKILL_DUPLICATE:{skill}")
            continue
        seen.add(skill)
        if before not in ALLOWED_SKILL_STATES:
            errors.append(f"SKILL_STATE_INVALID:{before}")
        if after not in ALLOWED_SKILL_STATES:
            errors.append(f"SKILL_STATE_INVALID:{after}")
        parsed.append({"skill": skill, "before": before, "after": after})
    return parsed, errors


def _parse_model_entries(lines: list[str] | None, section: str) -> tuple[dict[str, str], list[str]]:
    if lines is None:
        return {}, [f"{section}_MISSING"]
    entries: dict[str, str] = {}
    errors: list[str] = []
    pattern = re.compile(r"^-\s*([A-Za-z0-9_.-]+)\s*=\s*(.+?)\s*$")
    for line in lines:
        match = pattern.fullmatch(line)
        if not match:
            errors.append(f"{section}_MALFORMED:{line}")
            continue
        key, value = match.groups()
        if key in entries:
            errors.append(f"{section}_DUPLICATE:{key}")
            continue
        entries[key] = value.strip()
    return entries, errors


def _record_from_event(event_bytes: bytes, metadata: Mapping[str, str]) -> dict[str, object] | None:
    if not isinstance(event_bytes, bytes):
        raise TypeError("EVENT_BYTES_REQUIRED")
    event_name = metadata.get("event_name", "").strip()
    if event_name and event_name != "issue_comment":
        return None

    try:
        payload = json.loads(event_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or payload.get("action") != "created":
        return None

    issue = payload.get("issue")
    comment = payload.get("comment")
    if not isinstance(issue, dict) or not isinstance(comment, dict):
        return None
    if issue.get("number") != REPORT_ISSUE:
        return None

    actor = comment.get("user")
    actor_login = actor.get("login") if isinstance(actor, dict) else None
    if actor_login != REPORT_ACTOR:
        return None
    metadata_actor = metadata.get("actor", "").strip()
    if metadata_actor and metadata_actor != actor_login:
        return None

    body = comment.get("body")
    if not isinstance(body, str) or not body.startswith(REPORT_MARKER + "\n"):
        return None
    comment_id = comment.get("id")
    if not isinstance(comment_id, int) or comment_id <= 0:
        return None

    errors: list[str] = []
    cycle_id = _field(body, "CYCLE_ID")
    main_head = _field(body, "MAIN_HEAD_OBSERVED")
    prime_core_changed = _field(body, "PRIME_CORE_CHANGED")
    production_mutation = _field(body, "PRODUCTION_MUTATION")
    if not cycle_id:
        errors.append("CYCLE_ID_MISSING")
    if not main_head:
        errors.append("MAIN_HEAD_OBSERVED_MISSING")
    if prime_core_changed != "NO":
        errors.append("PRIME_CORE_MUTATION_FORBIDDEN")
    if production_mutation != "NO":
        errors.append("PRODUCTION_MUTATION_FORBIDDEN")

    skills, skill_errors = _parse_skill_deltas(_section_lines(body, "SKILL_DELTA"))
    self_model, self_errors = _parse_model_entries(
        _section_lines(body, "SELF_MODEL_DELTA"), "SELF_MODEL_DELTA"
    )
    owner_taste, taste_errors = _parse_model_entries(
        _section_lines(body, "OWNER_TASTE_MODEL_DELTA"), "OWNER_TASTE_MODEL_DELTA"
    )
    errors.extend(skill_errors)
    errors.extend(self_errors)
    errors.extend(taste_errors)

    digest = hashlib.sha256(event_bytes).hexdigest()
    return {
        "schema": SCHEMA,
        "source_raw_sha256": digest,
        "issue": REPORT_ISSUE,
        "comment_id": comment_id,
        "sequence": comment_id,
        "cycle_id": cycle_id or "",
        "main_head_observed": main_head or "",
        "prime_core_changed": prime_core_changed or "",
        "production_mutation": production_mutation or "",
        "skill_deltas": skills,
        "self_model_delta": self_model,
        "owner_taste_model_delta": owner_taste,
        "training_eligible": not errors,
        "validation_errors": sorted(set(errors)),
    }


def archive_duncan_night_event(
    event_bytes: bytes,
    archive_root: Path,
    metadata: Mapping[str, str],
) -> dict[str, object] | None:
    record = _record_from_event(event_bytes, metadata)
    if record is None:
        return None
    digest = str(record["source_raw_sha256"])
    rel = EVENTS_REL / f"{digest}.json"
    _write_once(
        Path(archive_root) / rel,
        _canonical_json(record),
        collision_code="DUNCAN_NIGHT_EVENT_COLLISION",
    )
    return {
        "event_relpath": rel.as_posix(),
        "source_raw_sha256": digest,
        "training_eligible": bool(record["training_eligible"]),
        "validation_errors": list(record["validation_errors"]),
    }


def _validated_records(archive_root: Path) -> list[dict[str, object]]:
    root = Path(archive_root) / EVENTS_REL
    records: list[dict[str, object]] = []
    if not root.is_dir():
        return records
    for path in sorted(root.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise DuncanNightArchiveError("DUNCAN_DERIVED_EVENT_INVALID") from exc
        if not isinstance(record, dict) or record.get("schema") != SCHEMA:
            raise DuncanNightArchiveError("DUNCAN_DERIVED_SCHEMA_INVALID")
        digest = record.get("source_raw_sha256")
        if not isinstance(digest, str) or path.stem != digest:
            raise DuncanNightArchiveError("DUNCAN_DERIVED_HASH_NAME_MISMATCH")
        if record.get("training_eligible") is True:
            records.append(record)
    records.sort(key=lambda item: (int(item["sequence"]), str(item["source_raw_sha256"])))
    return records


def _write_context(archive_root: Path, context: dict[str, object]) -> None:
    path = Path(archive_root) / CONTEXT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _canonical_json(context)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    if path.read_bytes() != data:
        raise DuncanNightArchiveError("DUNCAN_CONTEXT_READBACK_MISMATCH")


def rebuild_duncan_context(archive_root: Path) -> dict[str, object]:
    skills: dict[str, str] = {}
    self_model: dict[str, str] = {}
    owner_taste_model: dict[str, str] = {}
    source_events: list[dict[str, object]] = []
    latest_cycle_id = ""
    seen_cycles: dict[str, str] = {}

    for record in _validated_records(archive_root):
        cycle_id = str(record.get("cycle_id", ""))
        digest = str(record.get("source_raw_sha256", ""))
        previous_digest = seen_cycles.get(cycle_id)
        if previous_digest is not None and previous_digest != digest:
            raise DuncanNightArchiveError("DUNCAN_CYCLE_ID_COLLISION")
        seen_cycles[cycle_id] = digest

        for delta in record.get("skill_deltas", []):
            if not isinstance(delta, dict):
                raise DuncanNightArchiveError("DUNCAN_SKILL_DELTA_INVALID")
            skill = str(delta.get("skill", ""))
            after = str(delta.get("after", ""))
            if not skill or after not in ALLOWED_SKILL_STATES:
                raise DuncanNightArchiveError("DUNCAN_SKILL_STATE_INVALID")
            skills[skill] = after

        self_delta = record.get("self_model_delta", {})
        taste_delta = record.get("owner_taste_model_delta", {})
        if not isinstance(self_delta, dict) or not isinstance(taste_delta, dict):
            raise DuncanNightArchiveError("DUNCAN_MODEL_DELTA_INVALID")
        self_model.update({str(k): str(v) for k, v in self_delta.items()})
        owner_taste_model.update({str(k): str(v) for k, v in taste_delta.items()})
        source_events.append(
            {
                "cycle_id": cycle_id,
                "comment_id": int(record["comment_id"]),
                "source_raw_sha256": digest,
            }
        )
        latest_cycle_id = cycle_id

    context: dict[str, object] = {
        "schema": CONTEXT_SCHEMA,
        "prime_core_mutable": False,
        "skills": dict(sorted(skills.items())),
        "self_model": dict(sorted(self_model.items())),
        "owner_taste_model": dict(sorted(owner_taste_model.items())),
        "source_events": source_events,
        "latest_cycle_id": latest_cycle_id,
    }
    _write_context(archive_root, context)
    return context


def rebuild_duncan_from_raw(archive_root: Path) -> dict[str, object]:
    root = Path(archive_root)
    raw_root = root / "raw" / "sha256"
    for raw_path in sorted(raw_root.glob("*/*.json")):
        event_bytes = raw_path.read_bytes()
        digest = hashlib.sha256(event_bytes).hexdigest()
        if raw_path.stem != digest:
            raise DuncanNightArchiveError("DUNCAN_RAW_HASH_MISMATCH")
        archive_duncan_night_event(event_bytes, root, {})
    return rebuild_duncan_context(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="duncan_night_archive")
    parser.add_argument("--event-path", type=Path)
    parser.add_argument("--archive-root", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.event_path is not None:
        metadata = {
            "event_name": os.environ.get("GITHUB_EVENT_NAME", ""),
            "actor": os.environ.get("GITHUB_ACTOR", ""),
        }
        archive_duncan_night_event(args.event_path.read_bytes(), args.archive_root, metadata)
    context = rebuild_duncan_from_raw(args.archive_root)
    print(json.dumps(context, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
