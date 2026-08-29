from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .hq_archive_ingest import SCHEMA, ArchiveError
    from .duncan_night_archive import DuncanNightArchiveError, verify_duncan_archive
except ImportError:
    from hq_archive_ingest import SCHEMA, ArchiveError
    from duncan_night_archive import DuncanNightArchiveError, verify_duncan_archive


def verify_archive(archive_root: Path) -> dict[str, int]:
    root = Path(archive_root).resolve()
    raw_root = root / "raw" / "sha256"
    events_root = root / "events"

    raw_count = 0
    for raw_path in sorted(raw_root.glob("*/*.json")):
        raw_count += 1
        digest = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        if raw_path.stem != digest or raw_path.parent.name != digest[:2]:
            raise ArchiveError("RAW_FILENAME_HASH_MISMATCH")

    event_count = 0
    for event_path in sorted(events_root.glob("*/*.json")):
        event_count += 1
        try:
            envelope = json.loads(event_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ArchiveError("EVENT_ENVELOPE_INVALID") from exc
        if envelope.get("schema") != SCHEMA:
            raise ArchiveError("EVENT_SCHEMA_INVALID")
        digest = str(envelope.get("raw_sha256", ""))
        expected_rel = Path("raw") / "sha256" / digest[:2] / f"{digest}.json"
        if str(envelope.get("raw_relpath", "")) != expected_rel.as_posix():
            raise ArchiveError("EVENT_RAW_POINTER_INVALID")
        raw_path = (root / expected_rel).resolve()
        try:
            raw_path.relative_to(root)
        except ValueError as exc:
            raise ArchiveError("EVENT_RAW_POINTER_ESCAPE") from exc
        if not raw_path.is_file():
            raise ArchiveError("EVENT_RAW_MISSING")
        if hashlib.sha256(raw_path.read_bytes()).hexdigest() != digest:
            raise ArchiveError("EVENT_RAW_HASH_MISMATCH")

    try:
        duncan = verify_duncan_archive(root)
    except DuncanNightArchiveError as exc:
        raise ArchiveError(str(exc)) from exc

    return {
        "events": event_count,
        "raw_objects": raw_count,
        **duncan,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ZB Permanent Archive V1 integrity.")
    parser.add_argument("--archive-root", required=True, type=Path)
    args = parser.parse_args()
    result = verify_archive(args.archive_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
