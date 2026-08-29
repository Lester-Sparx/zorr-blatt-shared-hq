from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping


SCHEMA = "ZB_ARCHIVE_EVENT_V1"


class ArchiveError(RuntimeError):
    pass


def _write_once(path: Path, data: bytes, *, collision_code: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        if path.read_bytes() != data:
            raise ArchiveError(collision_code)
        return False

    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return True


def _canonical_json(payload: Mapping[str, object]) -> bytes:
    return (json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def archive_event(event_bytes: bytes, archive_root: Path, metadata: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(event_bytes, bytes):
        raise TypeError("EVENT_BYTES_REQUIRED")

    event_name = metadata.get("event_name", "").strip()
    run_id = metadata.get("run_id", "").strip()
    run_attempt = metadata.get("run_attempt", "").strip()
    if not event_name or not run_id or not run_attempt:
        raise ArchiveError("EVENT_IDENTITY_MISSING")

    root = Path(archive_root)
    digest = hashlib.sha256(event_bytes).hexdigest()
    raw_rel = Path("raw") / "sha256" / digest[:2] / f"{digest}.json"
    raw_path = root / raw_rel
    _write_once(raw_path, event_bytes, collision_code="RAW_HASH_COLLISION")

    try:
        parsed = json.loads(event_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArchiveError("EVENT_JSON_INVALID") from exc

    action = parsed.get("action") if isinstance(parsed, dict) else None
    envelope: dict[str, object] = {
        "schema": SCHEMA,
        "event_key": f"{run_id}.{run_attempt}",
        "event_name": event_name,
        "action": action,
        "raw_sha256": digest,
        "raw_relpath": raw_rel.as_posix(),
        "repository": metadata.get("repository", ""),
        "actor": metadata.get("actor", ""),
        "run_id": run_id,
        "run_attempt": run_attempt,
        "workflow": metadata.get("workflow", ""),
        "source_sha": metadata.get("source_sha", ""),
        "source_ref": metadata.get("source_ref", ""),
    }
    envelope_bytes = _canonical_json(envelope)
    event_rel = Path("events") / event_name / f"{run_id}-{run_attempt}.json"
    event_path = root / event_rel
    _write_once(event_path, envelope_bytes, collision_code="EVENT_ID_COLLISION")

    if hashlib.sha256(raw_path.read_bytes()).hexdigest() != digest:
        raise ArchiveError("RAW_READBACK_HASH_MISMATCH")
    if event_path.read_bytes() != envelope_bytes:
        raise ArchiveError("EVENT_READBACK_MISMATCH")

    return {
        "raw_sha256": digest,
        "raw_relpath": raw_rel.as_posix(),
        "event_relpath": event_rel.as_posix(),
    }


def _metadata_from_env() -> dict[str, str]:
    return {
        "event_name": os.environ.get("GITHUB_EVENT_NAME", ""),
        "run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", ""),
        "repository": os.environ.get("GITHUB_REPOSITORY", ""),
        "actor": os.environ.get("GITHUB_ACTOR", ""),
        "workflow": os.environ.get("GITHUB_WORKFLOW", ""),
        "source_sha": os.environ.get("GITHUB_SHA", ""),
        "source_ref": os.environ.get("GITHUB_REF", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive one GitHub event byte-for-byte.")
    parser.add_argument("--event-path", required=True, type=Path)
    parser.add_argument("--archive-root", required=True, type=Path)
    args = parser.parse_args()

    result = archive_event(args.event_path.read_bytes(), args.archive_root, _metadata_from_env())
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
