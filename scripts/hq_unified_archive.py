from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any


RECORD_SCHEMA = "ZB_UNIFIED_ARCHIVE_RECORD_V1"
CONTEXT_SCHEMA = "ZB_UNIFIED_CURRENT_CONTEXT_V1"
_URL_RE = re.compile(r"https?://[^\s<>'\"\)\]]+")
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_KEY_RE = re.compile(r"[A-Z][A-Z0-9_]{0,63}")
_FIELD_RE = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$")


class UnifiedArchiveError(RuntimeError):
    pass


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _event_subject(payload: dict[str, Any]) -> tuple[str, int | None, str, str]:
    issue = payload.get("issue")
    if isinstance(issue, dict):
        kind = "pull_request" if isinstance(issue.get("pull_request"), dict) else "issue"
        number = issue.get("number") if isinstance(issue.get("number"), int) else None
        title = str(issue.get("title") or "")
        url = str(issue.get("html_url") or "")
        return kind, number, title, url

    pull_request = payload.get("pull_request")
    if isinstance(pull_request, dict):
        number = pull_request.get("number") if isinstance(pull_request.get("number"), int) else None
        title = str(pull_request.get("title") or "")
        url = str(pull_request.get("html_url") or "")
        return "pull_request", number, title, url

    repository = payload.get("repository")
    if isinstance(repository, dict):
        return "repository", None, str(repository.get("full_name") or repository.get("name") or ""), str(repository.get("html_url") or "")
    return "event", None, "", ""


def _body_and_url(payload: dict[str, Any], fallback_url: str) -> tuple[str, str]:
    for key in ("comment", "review"):
        value = payload.get(key)
        if isinstance(value, dict):
            body = value.get("body")
            if isinstance(body, str):
                return body, str(value.get("html_url") or fallback_url)

    for key in ("issue", "pull_request"):
        value = payload.get(key)
        if isinstance(value, dict):
            body = value.get("body")
            if isinstance(body, str):
                return body, str(value.get("html_url") or fallback_url)

    commits = payload.get("commits")
    if isinstance(commits, list):
        messages = [str(item.get("message")) for item in commits if isinstance(item, dict) and item.get("message")]
        if messages:
            return "\n".join(messages), fallback_url
    return "", fallback_url


def _created_at(payload: dict[str, Any]) -> str:
    for key in ("comment", "review", "issue", "pull_request"):
        value = payload.get(key)
        if isinstance(value, dict):
            for field in ("created_at", "updated_at"):
                stamp = value.get(field)
                if isinstance(stamp, str) and stamp:
                    return stamp
    repository = payload.get("repository")
    if isinstance(repository, dict):
        stamp = repository.get("updated_at")
        if isinstance(stamp, str):
            return stamp
    return ""


def _attachment_urls(text: str) -> list[str]:
    return sorted(set(_URL_RE.findall(text)))


def derive_record(
    event_bytes: bytes,
    *,
    raw_sha256: str,
    event_name: str,
    repository: str,
    actor: str,
) -> dict[str, Any]:
    if not isinstance(event_bytes, bytes):
        raise TypeError("EVENT_BYTES_REQUIRED")
    actual_digest = hashlib.sha256(event_bytes).hexdigest()
    if raw_sha256 != actual_digest:
        raise UnifiedArchiveError("RAW_SHA256_MISMATCH")
    try:
        payload = json.loads(event_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UnifiedArchiveError("EVENT_JSON_INVALID") from exc
    if not isinstance(payload, dict):
        raise UnifiedArchiveError("EVENT_OBJECT_REQUIRED")

    subject_kind, subject_number, subject_title, subject_url = _event_subject(payload)
    body_text, source_url = _body_and_url(payload, subject_url)
    action = str(payload.get("action") or "")
    search_text = "\n".join(part for part in (repository, actor, event_name, action, subject_title, body_text) if part)
    return {
        "schema": RECORD_SCHEMA,
        "raw_sha256": raw_sha256,
        "event_name": event_name,
        "action": action,
        "repository": repository,
        "actor": actor,
        "subject_kind": subject_kind,
        "subject_number": subject_number,
        "subject_title": subject_title,
        "body_text": body_text,
        "search_text": search_text,
        "source_url": source_url,
        "attachment_urls": _attachment_urls(body_text),
        "created_at": _created_at(payload),
    }


def _record_path(archive_root: Path, raw_sha256: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{64}", raw_sha256):
        raise UnifiedArchiveError("RAW_SHA256_INVALID")
    return Path(archive_root) / "derived" / "unified-v1" / "records" / raw_sha256[:2] / f"{raw_sha256}.json"


def write_record(record: dict[str, Any], archive_root: Path) -> Path:
    if record.get("schema") != RECORD_SCHEMA:
        raise UnifiedArchiveError("RECORD_SCHEMA_INVALID")
    digest = str(record.get("raw_sha256") or "")
    path = _record_path(Path(archive_root), digest)
    data = _canonical_json(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise UnifiedArchiveError("DERIVED_RECORD_COLLISION")
        return path
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        if path.read_bytes() != data:
            raise UnifiedArchiveError("DERIVED_RECORD_COLLISION")
        return path
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


def _load_records(archive_root: Path) -> list[dict[str, Any]]:
    root = Path(archive_root) / "derived" / "unified-v1" / "records"
    records: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise UnifiedArchiveError("DERIVED_RECORD_INVALID") from exc
        if not isinstance(record, dict) or record.get("schema") != RECORD_SCHEMA:
            raise UnifiedArchiveError("DERIVED_RECORD_SCHEMA_INVALID")
        digest = str(record.get("raw_sha256") or "")
        if path != _record_path(Path(archive_root), digest):
            raise UnifiedArchiveError("DERIVED_RECORD_PATH_INVALID")
        records.append(record)
    return records


def rebuild_current_context(archive_root: Path, *, limit: int = 50) -> dict[str, Any]:
    if limit < 1:
        raise UnifiedArchiveError("CONTEXT_LIMIT_INVALID")
    records = _load_records(Path(archive_root))
    records.sort(key=lambda item: (str(item.get("created_at") or ""), str(item.get("raw_sha256") or "")), reverse=True)
    latest: list[dict[str, Any]] = []
    for record in records[:limit]:
        latest.append({
            "raw_sha256": record["raw_sha256"],
            "event_name": record["event_name"],
            "action": record["action"],
            "subject_kind": record["subject_kind"],
            "subject_number": record["subject_number"],
            "subject_title": record["subject_title"],
            "body_excerpt": str(record["body_text"])[:1200],
            "source_url": record["source_url"],
            "attachment_urls": record["attachment_urls"],
            "created_at": record.get("created_at", ""),
        })
    context = {
        "schema": CONTEXT_SCHEMA,
        "record_count": len(records),
        "latest_records": latest,
    }
    path = Path(archive_root) / "derived" / "unified-v1" / "CURRENT_CONTEXT.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_json(context))
    return context


def _fts_query(query: str) -> str:
    tokens = _TOKEN_RE.findall(query)
    if not tokens:
        raise UnifiedArchiveError("SEARCH_QUERY_EMPTY")
    return " AND ".join('"' + token.replace('"', '""') + '"' for token in tokens)


def search_records(archive_root: Path, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
    if limit < 1:
        raise UnifiedArchiveError("SEARCH_LIMIT_INVALID")
    records = _load_records(Path(archive_root))
    if not records:
        return []
    by_digest = {str(record["raw_sha256"]): record for record in records}
    connection = sqlite3.connect(":memory:")
    try:
        try:
            connection.execute(
                "CREATE VIRTUAL TABLE archive_fts USING fts5(raw_sha256 UNINDEXED, subject_title, body_text, search_text)"
            )
        except sqlite3.OperationalError as exc:
            raise UnifiedArchiveError("SQLITE_FTS5_UNAVAILABLE") from exc
        connection.executemany(
            "INSERT INTO archive_fts(raw_sha256, subject_title, body_text, search_text) VALUES (?, ?, ?, ?)",
            [
                (
                    record["raw_sha256"],
                    str(record.get("subject_title") or ""),
                    str(record.get("body_text") or ""),
                    str(record.get("search_text") or ""),
                )
                for record in records
            ],
        )
        rows = connection.execute(
            "SELECT raw_sha256 FROM archive_fts WHERE archive_fts MATCH ? ORDER BY bm25(archive_fts), rowid LIMIT ?",
            (_fts_query(query), limit),
        ).fetchall()
    finally:
        connection.close()
    return [by_digest[str(row[0])] for row in rows]


def _structured_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = _FIELD_RE.fullmatch(line)
        if not match:
            continue
        key, value = match.groups()
        previous = fields.get(key)
        if previous is not None and previous != value:
            raise UnifiedArchiveError("STRUCTURED_FIELD_CONFLICT")
        fields[key] = value
    return fields


def resolve_assertion(
    archive_root: Path,
    subject_kind: str,
    subject_number: int | None,
    key: str,
) -> dict[str, Any]:
    if not _KEY_RE.fullmatch(key):
        raise UnifiedArchiveError("ASSERTION_KEY_INVALID")
    records = [
        record
        for record in _load_records(Path(archive_root))
        if record.get("subject_kind") == subject_kind and record.get("subject_number") == subject_number
    ]
    records.sort(key=lambda item: (str(item.get("created_at") or ""), str(item.get("raw_sha256") or "")), reverse=True)
    for record in records:
        fields = _structured_fields(str(record.get("body_text") or ""))
        if key not in fields:
            continue
        return {
            "status": "PROVEN",
            "key": key,
            "value": fields[key],
            "raw_sha256": record["raw_sha256"],
            "source_url": record.get("source_url", ""),
            "created_at": record.get("created_at", ""),
        }
    return {"status": "NOT_PROVEN", "key": key}


def guard_assertion(
    archive_root: Path,
    subject_kind: str,
    subject_number: int | None,
    key: str,
    claimed_value: str,
) -> dict[str, Any]:
    resolved = resolve_assertion(archive_root, subject_kind, subject_number, key)
    if resolved["status"] != "PROVEN":
        return resolved
    if resolved["value"] == claimed_value:
        return {
            "status": "MATCH",
            "key": key,
            "value": claimed_value,
            "raw_sha256": resolved["raw_sha256"],
            "source_url": resolved["source_url"],
            "created_at": resolved["created_at"],
        }
    return {
        "status": "CONFLICT",
        "key": key,
        "claimed_value": claimed_value,
        "corrected_value": resolved["value"],
        "raw_sha256": resolved["raw_sha256"],
        "source_url": resolved["source_url"],
        "created_at": resolved["created_at"],
    }


def build_restore_packet(archive_root: Path, query: str, *, limit: int = 10) -> dict[str, Any]:
    records = search_records(Path(archive_root), query, limit=limit)
    results = [
        {
            "raw_sha256": record["raw_sha256"],
            "event_name": record["event_name"],
            "action": record["action"],
            "subject_kind": record["subject_kind"],
            "subject_number": record["subject_number"],
            "subject_title": record["subject_title"],
            "body_excerpt": str(record.get("body_text") or "")[:1200],
            "source_url": record.get("source_url", ""),
            "attachment_urls": record.get("attachment_urls", []),
            "created_at": record.get("created_at", ""),
        }
        for record in records
    ]
    return {
        "status": "PROVEN" if results else "NOT_PROVEN",
        "query": query,
        "results": results,
    }


def _ingest_event(args: argparse.Namespace) -> dict[str, Any]:
    event_bytes = args.event_path.read_bytes()
    digest = hashlib.sha256(event_bytes).hexdigest()
    record = derive_record(
        event_bytes,
        raw_sha256=digest,
        event_name=args.event_name,
        repository=args.repository,
        actor=args.actor,
    )
    record_path = write_record(record, args.archive_root)
    context = rebuild_current_context(args.archive_root, limit=args.context_limit)
    return {
        "raw_sha256": digest,
        "record_relpath": record_path.relative_to(args.archive_root).as_posix(),
        "context_records": context["record_count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build/search the rebuildable Unified Archive V1 layer.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest-event")
    ingest.add_argument("--event-path", required=True, type=Path)
    ingest.add_argument("--archive-root", required=True, type=Path)
    ingest.add_argument("--event-name", required=True)
    ingest.add_argument("--repository", required=True)
    ingest.add_argument("--actor", required=True)
    ingest.add_argument("--context-limit", type=int, default=50)

    search = subparsers.add_parser("search")
    search.add_argument("--archive-root", required=True, type=Path)
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=10)

    restore = subparsers.add_parser("restore")
    restore.add_argument("--archive-root", required=True, type=Path)
    restore.add_argument("--query", required=True)
    restore.add_argument("--limit", type=int, default=10)

    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("--archive-root", required=True, type=Path)
    resolve.add_argument("--subject-kind", required=True)
    resolve.add_argument("--subject-number", type=int)
    resolve.add_argument("--key", required=True)

    guard = subparsers.add_parser("guard")
    guard.add_argument("--archive-root", required=True, type=Path)
    guard.add_argument("--subject-kind", required=True)
    guard.add_argument("--subject-number", type=int)
    guard.add_argument("--key", required=True)
    guard.add_argument("--claimed-value", required=True)

    args = parser.parse_args()
    if args.command == "ingest-event":
        result: Any = _ingest_event(args)
    elif args.command == "search":
        result = search_records(args.archive_root, args.query, limit=args.limit)
    elif args.command == "restore":
        result = build_restore_packet(args.archive_root, args.query, limit=args.limit)
    elif args.command == "resolve":
        result = resolve_assertion(args.archive_root, args.subject_kind, args.subject_number, args.key)
    else:
        result = guard_assertion(
            args.archive_root,
            args.subject_kind,
            args.subject_number,
            args.key,
            args.claimed_value,
        )
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
