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
LESSON_SCHEMA = "ZB_REFLEXION_LESSON_V1"
CURRENT_LESSONS_SCHEMA = "ZB_CURRENT_LESSONS_V1"
LEARNING_POLICY_SCHEMA = "ZB_LEARNING_POLICY_V1"
TRAINING_EXAMPLE_SCHEMA = "ZB_LEARNING_EXAMPLE_V1"
OPTIMIZED_POLICY_SCHEMA = "ZB_OPTIMIZED_LEARNING_POLICY_V1"
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


def _learning_root(archive_root: Path) -> Path:
    return Path(archive_root) / "derived" / "unified-v1" / "learning"


def _safe_repo_path(repo_root: Path, relative_path: str) -> Path:
    relative = Path(relative_path)
    if not relative_path or relative.is_absolute() or ".." in relative.parts:
        raise UnifiedArchiveError("LESSON_REF_INVALID")
    root = Path(repo_root).resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise UnifiedArchiveError("LESSON_REF_INVALID") from exc
    return candidate


def _closed_verdict_to_lesson(verdict_bytes: bytes, *, repo_root: Path) -> dict[str, Any] | None:
    try:
        verdict = json.loads(verdict_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UnifiedArchiveError("SHERIFF_VERDICT_INVALID") from exc
    if not isinstance(verdict, dict) or verdict.get("schemaVersion") != "SHERIFF_VERDICT_V1":
        raise UnifiedArchiveError("SHERIFF_VERDICT_INVALID")
    if verdict.get("status") != "CLOSED":
        return None

    required_strings = (
        "verdictId",
        "agentId",
        "incidentClass",
        "errorSignature",
        "rootCause",
        "regressionTest",
        "lessonRef",
        "issuedAt",
    )
    for key in required_strings:
        value = verdict.get(key)
        if not isinstance(value, str) or not value.strip():
            raise UnifiedArchiveError(f"SHERIFF_VERDICT_{key.upper()}_INVALID")
    evidence = verdict.get("evidence")
    if not isinstance(evidence, list) or not evidence or not all(isinstance(item, str) and item for item in evidence):
        raise UnifiedArchiveError("SHERIFF_VERDICT_EVIDENCE_INVALID")

    lesson_ref = str(verdict["lessonRef"])
    lesson_path = _safe_repo_path(Path(repo_root), lesson_ref)
    if not lesson_path.is_file():
        raise UnifiedArchiveError("LESSON_REF_MISSING")
    try:
        lesson_text = lesson_path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise UnifiedArchiveError("LESSON_REF_UNREADABLE") from exc
    if not lesson_text:
        raise UnifiedArchiveError("LESSON_TEXT_EMPTY")
    if len(lesson_text) > 16000:
        raise UnifiedArchiveError("LESSON_TEXT_TOO_LARGE")

    verdict_sha256 = hashlib.sha256(verdict_bytes).hexdigest()
    return {
        "schema": LESSON_SCHEMA,
        "verdict_id": verdict["verdictId"],
        "verdict_sha256": verdict_sha256,
        "agent_id": verdict["agentId"],
        "incident_class": verdict["incidentClass"],
        "error_signature": verdict["errorSignature"],
        "root_cause": verdict["rootCause"],
        "lesson_ref": lesson_ref,
        "lesson_text": lesson_text,
        "regression_test": verdict["regressionTest"],
        "evidence": list(verdict["evidence"]),
        "issued_at": verdict["issuedAt"],
    }


def _load_lessons(archive_root: Path) -> list[dict[str, Any]]:
    root = _learning_root(Path(archive_root)) / "lessons"
    lessons: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        try:
            lesson = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise UnifiedArchiveError("LESSON_RECORD_INVALID") from exc
        if not isinstance(lesson, dict) or lesson.get("schema") != LESSON_SCHEMA:
            raise UnifiedArchiveError("LESSON_RECORD_INVALID")
        digest = str(lesson.get("verdict_sha256") or "")
        if path.name != f"{digest}.json" or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise UnifiedArchiveError("LESSON_RECORD_PATH_INVALID")
        lessons.append(lesson)
    return lessons


def _write_learning_corpus(archive_root: Path, lessons: list[dict[str, Any]]) -> Path:
    learning_root = _learning_root(Path(archive_root))
    learning_root.mkdir(parents=True, exist_ok=True)
    path = learning_root / "TRAINING_CORPUS.jsonl"
    examples = []
    for lesson in sorted(lessons, key=lambda item: (str(item.get("issued_at") or ""), str(item.get("verdict_id") or ""))):
        examples.append({
            "schema": TRAINING_EXAMPLE_SCHEMA,
            "verdict_id": lesson["verdict_id"],
            "error_signature": lesson["error_signature"],
            "root_cause": lesson["root_cause"],
            "lesson": lesson["lesson_text"],
            "regression_test": lesson["regression_test"],
            "evidence": lesson["evidence"],
            "issued_at": lesson["issued_at"],
        })
    data = b"".join(_canonical_json(example) for example in examples)
    path.write_bytes(data)
    return path


def _write_current_lessons(archive_root: Path, lessons: list[dict[str, Any]], *, limit: int = 100) -> Path:
    if limit < 1:
        raise UnifiedArchiveError("CURRENT_LESSONS_LIMIT_INVALID")
    learning_root = _learning_root(Path(archive_root))
    learning_root.mkdir(parents=True, exist_ok=True)
    ordered = sorted(
        lessons,
        key=lambda item: (str(item.get("issued_at") or ""), str(item.get("verdict_id") or "")),
        reverse=True,
    )
    current = {
        "schema": CURRENT_LESSONS_SCHEMA,
        "lesson_count": len(lessons),
        "lessons": [
            {
                "verdict_id": lesson["verdict_id"],
                "verdict_sha256": lesson["verdict_sha256"],
                "error_signature": lesson["error_signature"],
                "lesson_ref": lesson["lesson_ref"],
                "lesson_excerpt": str(lesson["lesson_text"])[:1200],
                "regression_test": lesson["regression_test"],
                "evidence": lesson["evidence"],
                "issued_at": lesson["issued_at"],
            }
            for lesson in ordered[:limit]
        ],
    }
    path = learning_root / "CURRENT_LESSONS.json"
    path.write_bytes(_canonical_json(current))
    return path


def _load_learning_corpus(archive_root: Path) -> tuple[list[dict[str, Any]], str]:
    path = _learning_root(Path(archive_root)) / "TRAINING_CORPUS.jsonl"
    if not path.exists():
        return [], hashlib.sha256(b"").hexdigest()
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise UnifiedArchiveError("TRAINING_CORPUS_UNREADABLE") from exc
    examples: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_line in data.splitlines():
        if not raw_line.strip():
            continue
        try:
            example = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise UnifiedArchiveError("TRAINING_CORPUS_INVALID") from exc
        if not isinstance(example, dict) or example.get("schema") != TRAINING_EXAMPLE_SCHEMA:
            raise UnifiedArchiveError("TRAINING_CORPUS_INVALID")
        for key in ("verdict_id", "error_signature", "lesson", "regression_test"):
            value = example.get(key)
            if not isinstance(value, str) or not value.strip():
                raise UnifiedArchiveError("TRAINING_CORPUS_INVALID")
        verdict_id = str(example["verdict_id"])
        if verdict_id in seen:
            raise UnifiedArchiveError("TRAINING_CORPUS_DUPLICATE_VERDICT")
        seen.add(verdict_id)
        examples.append(example)
    return examples, hashlib.sha256(data).hexdigest()


def _normalize_rule(text: str) -> str:
    return " ".join(text.split())


def _render_optimizer_policy(rules: list[dict[str, Any]]) -> str:
    if not rules:
        return ""
    rendered = [
        "DURABLE OPTIMIZED LESSON POLICY — verified regression coverage; fresher raw evidence always wins."
    ]
    for rule in rules:
        rendered.append("ERROR_SIGNATURES = " + " | ".join(rule["error_signatures"]))
        rendered.append("RULE = " + str(rule["lesson_text"]))
        rendered.append("SOURCE_VERDICTS = " + " | ".join(rule["verdict_ids"]))
    return "\n".join(rendered)


def _policy_coverage(examples: list[dict[str, Any]], rules: list[dict[str, Any]]) -> float:
    if not examples:
        return 0.0
    normalized_rules = {_normalize_rule(str(rule["lesson_text"])) for rule in rules}
    matched = sum(1 for example in examples if _normalize_rule(str(example["lesson"])) in normalized_rules)
    return matched / len(examples)


def optimize_learning_policy(archive_root: Path) -> dict[str, Any]:
    archive_root = Path(archive_root)
    learning_root = _learning_root(archive_root)
    learning_root.mkdir(parents=True, exist_ok=True)
    output_path = learning_root / "CURRENT_OPTIMIZED_POLICY.json"
    lessons = _load_lessons(archive_root)
    examples, corpus_sha256 = _load_learning_corpus(archive_root)
    source_verdict_ids = sorted(str(lesson.get("verdict_id") or "") for lesson in lessons)

    if not lessons or not examples:
        result = {
            "schema": OPTIMIZED_POLICY_SCHEMA,
            "status": "NOT_PROVEN",
            "accepted": False,
            "baseline_rule_count": len(lessons),
            "optimized_rule_count": 0,
            "training_coverage": 0.0,
            "holdout_coverage": 0.0,
            "baseline_bytes": 0,
            "optimized_bytes": 0,
            "policy_prefix": "",
            "source_verdict_ids": source_verdict_ids,
            "corpus_sha256": corpus_sha256,
            "conflicting_error_signatures": [],
        }
        output_path.write_bytes(_canonical_json(result))
        return result

    signature_rules: dict[str, set[str]] = {}
    for lesson in lessons:
        signature = str(lesson.get("error_signature") or "")
        normalized = _normalize_rule(str(lesson.get("lesson_text") or ""))
        signature_rules.setdefault(signature, set()).add(normalized)
    conflicts = sorted(signature for signature, rules in signature_rules.items() if len(rules) > 1)

    baseline_rules = [
        {
            "lesson_text": str(lesson["lesson_text"]),
            "error_signatures": [str(lesson["error_signature"])],
            "verdict_ids": [str(lesson["verdict_id"])],
        }
        for lesson in sorted(lessons, key=lambda item: (str(item.get("issued_at") or ""), str(item.get("verdict_id") or "")))
    ]
    baseline_prefix = _render_optimizer_policy(baseline_rules)
    baseline_bytes = len(baseline_prefix.encode("utf-8"))

    if conflicts:
        result = {
            "schema": OPTIMIZED_POLICY_SCHEMA,
            "status": "CONFLICT",
            "accepted": False,
            "baseline_rule_count": len(baseline_rules),
            "optimized_rule_count": 0,
            "training_coverage": 0.0,
            "holdout_coverage": 0.0,
            "baseline_bytes": baseline_bytes,
            "optimized_bytes": 0,
            "policy_prefix": "",
            "source_verdict_ids": source_verdict_ids,
            "corpus_sha256": corpus_sha256,
            "conflicting_error_signatures": conflicts,
        }
        output_path.write_bytes(_canonical_json(result))
        return result

    grouped: dict[str, dict[str, Any]] = {}
    for lesson in sorted(
        lessons,
        key=lambda item: (str(item.get("issued_at") or ""), str(item.get("verdict_id") or "")),
        reverse=True,
    ):
        normalized = _normalize_rule(str(lesson["lesson_text"]))
        entry = grouped.setdefault(
            normalized,
            {
                "lesson_text": str(lesson["lesson_text"]),
                "error_signatures": set(),
                "verdict_ids": set(),
            },
        )
        entry["error_signatures"].add(str(lesson["error_signature"]))
        entry["verdict_ids"].add(str(lesson["verdict_id"]))

    optimized_rules = [
        {
            "lesson_text": entry["lesson_text"],
            "error_signatures": sorted(entry["error_signatures"]),
            "verdict_ids": sorted(entry["verdict_ids"]),
        }
        for _, entry in sorted(grouped.items(), key=lambda item: item[0])
    ]
    optimized_prefix = _render_optimizer_policy(optimized_rules)
    optimized_bytes = len(optimized_prefix.encode("utf-8"))

    ordered_examples = sorted(examples, key=lambda item: str(item["verdict_id"]))
    if len(ordered_examples) == 1:
        training_examples = ordered_examples
        holdout_examples = ordered_examples
    else:
        training_examples = ordered_examples[::2]
        holdout_examples = ordered_examples[1::2]
        if not holdout_examples:
            holdout_examples = training_examples

    baseline_training = _policy_coverage(training_examples, baseline_rules)
    baseline_holdout = _policy_coverage(holdout_examples, baseline_rules)
    optimized_training = _policy_coverage(training_examples, optimized_rules)
    optimized_holdout = _policy_coverage(holdout_examples, optimized_rules)
    non_regression = optimized_training >= baseline_training and optimized_holdout >= baseline_holdout

    if non_regression and optimized_bytes < baseline_bytes:
        status = "IMPROVED"
        selected_rules = optimized_rules
        selected_prefix = optimized_prefix
    else:
        status = "BASELINE_KEPT"
        selected_rules = baseline_rules
        selected_prefix = baseline_prefix

    result = {
        "schema": OPTIMIZED_POLICY_SCHEMA,
        "status": status,
        "accepted": True,
        "baseline_rule_count": len(baseline_rules),
        "optimized_rule_count": len(selected_rules),
        "training_coverage": _policy_coverage(training_examples, selected_rules),
        "holdout_coverage": _policy_coverage(holdout_examples, selected_rules),
        "baseline_bytes": baseline_bytes,
        "optimized_bytes": len(selected_prefix.encode("utf-8")),
        "policy_prefix": selected_prefix,
        "source_verdict_ids": source_verdict_ids,
        "corpus_sha256": corpus_sha256,
        "conflicting_error_signatures": [],
    }
    output_path.write_bytes(_canonical_json(result))
    return result


def sync_sheriff_lessons(verdict_root: Path, repo_root: Path, archive_root: Path) -> dict[str, Any]:
    verdict_root = Path(verdict_root)
    repo_root = Path(repo_root)
    archive_root = Path(archive_root)
    pending: list[dict[str, Any]] = []
    skipped_open = 0
    if verdict_root.exists():
        for verdict_path in sorted(verdict_root.glob("*.json")):
            try:
                verdict_bytes = verdict_path.read_bytes()
            except OSError as exc:
                raise UnifiedArchiveError("SHERIFF_VERDICT_UNREADABLE") from exc
            lesson = _closed_verdict_to_lesson(verdict_bytes, repo_root=repo_root)
            if lesson is None:
                skipped_open += 1
            else:
                pending.append(lesson)

    lesson_root = _learning_root(archive_root) / "lessons"
    lesson_root.mkdir(parents=True, exist_ok=True)
    for old in lesson_root.glob("*.json"):
        old.unlink()
    for lesson in pending:
        path = lesson_root / f"{lesson['verdict_sha256']}.json"
        path.write_bytes(_canonical_json(lesson))
    corpus_path = _write_learning_corpus(archive_root, pending)
    current_path = _write_current_lessons(archive_root, pending)
    optimizer = optimize_learning_policy(archive_root)
    optimized_path = _learning_root(archive_root) / "CURRENT_OPTIMIZED_POLICY.json"
    return {
        "learned": len(pending),
        "skipped_open": skipped_open,
        "corpus_count": len(pending),
        "corpus_relpath": corpus_path.relative_to(archive_root).as_posix(),
        "current_lessons_relpath": current_path.relative_to(archive_root).as_posix(),
        "optimizer_status": optimizer["status"],
        "optimized_policy_relpath": optimized_path.relative_to(archive_root).as_posix(),
    }


def search_lessons(archive_root: Path, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
    if limit < 1:
        raise UnifiedArchiveError("SEARCH_LIMIT_INVALID")
    lessons = _load_lessons(Path(archive_root))
    if not lessons:
        return []
    by_id = {str(lesson["verdict_id"]): lesson for lesson in lessons}
    connection = sqlite3.connect(":memory:")
    try:
        try:
            connection.execute(
                "CREATE VIRTUAL TABLE lesson_fts USING fts5(verdict_id UNINDEXED, error_signature, root_cause, lesson_text, regression_test)"
            )
        except sqlite3.OperationalError as exc:
            raise UnifiedArchiveError("SQLITE_FTS5_UNAVAILABLE") from exc
        connection.executemany(
            "INSERT INTO lesson_fts(verdict_id, error_signature, root_cause, lesson_text, regression_test) VALUES (?, ?, ?, ?, ?)",
            [
                (
                    lesson["verdict_id"],
                    str(lesson.get("error_signature") or ""),
                    str(lesson.get("root_cause") or ""),
                    str(lesson.get("lesson_text") or ""),
                    str(lesson.get("regression_test") or ""),
                )
                for lesson in lessons
            ],
        )
        rows = connection.execute(
            "SELECT verdict_id FROM lesson_fts WHERE lesson_fts MATCH ? ORDER BY bm25(lesson_fts), rowid LIMIT ?",
            (_fts_query(query), limit),
        ).fetchall()
    finally:
        connection.close()
    return [by_id[str(row[0])] for row in rows]


def build_learning_policy(archive_root: Path, query: str, *, limit: int = 5) -> dict[str, Any]:
    lessons = search_lessons(Path(archive_root), query, limit=limit)
    if not lessons:
        return {
            "schema": LEARNING_POLICY_SCHEMA,
            "status": "NOT_PROVEN",
            "query": query,
            "lesson_count": 0,
            "policy_prefix": "",
            "lessons": [],
        }
    rendered: list[str] = [
        "DURABLE VERIFIED LESSONS — apply before answering; fresher raw evidence always wins."
    ]
    public_lessons: list[dict[str, Any]] = []
    for lesson in lessons:
        rendered.extend([
            f"VERDICT = {lesson['verdict_id']}",
            f"ERROR_SIGNATURE = {lesson['error_signature']}",
            f"RULE = {lesson['lesson_text']}",
            f"REGRESSION_TEST = {lesson['regression_test']}",
            "EVIDENCE = " + " | ".join(str(item) for item in lesson["evidence"]),
        ])
        public_lessons.append({
            "verdict_id": lesson["verdict_id"],
            "verdict_sha256": lesson["verdict_sha256"],
            "error_signature": lesson["error_signature"],
            "root_cause": lesson["root_cause"],
            "lesson": lesson["lesson_text"],
            "regression_test": lesson["regression_test"],
            "evidence": lesson["evidence"],
            "issued_at": lesson["issued_at"],
        })
    return {
        "schema": LEARNING_POLICY_SCHEMA,
        "status": "PROVEN",
        "query": query,
        "lesson_count": len(public_lessons),
        "policy_prefix": "\n".join(rendered),
        "lessons": public_lessons,
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

    sync_lessons = subparsers.add_parser("sync-lessons")
    sync_lessons.add_argument("--verdict-root", required=True, type=Path)
    sync_lessons.add_argument("--repo-root", required=True, type=Path)
    sync_lessons.add_argument("--archive-root", required=True, type=Path)

    learning_policy = subparsers.add_parser("learning-policy")
    learning_policy.add_argument("--archive-root", required=True, type=Path)
    learning_policy.add_argument("--query", required=True)
    learning_policy.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()
    if args.command == "ingest-event":
        result: Any = _ingest_event(args)
    elif args.command == "search":
        result = search_records(args.archive_root, args.query, limit=args.limit)
    elif args.command == "restore":
        result = build_restore_packet(args.archive_root, args.query, limit=args.limit)
    elif args.command == "resolve":
        result = resolve_assertion(args.archive_root, args.subject_kind, args.subject_number, args.key)
    elif args.command == "guard":
        result = guard_assertion(
            args.archive_root,
            args.subject_kind,
            args.subject_number,
            args.key,
            args.claimed_value,
        )
    elif args.command == "sync-lessons":
        result = sync_sheriff_lessons(args.verdict_root, args.repo_root, args.archive_root)
    else:
        result = build_learning_policy(args.archive_root, args.query, limit=args.limit)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())