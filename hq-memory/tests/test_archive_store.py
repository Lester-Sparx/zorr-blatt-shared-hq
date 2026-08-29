from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from zb_hq_memory.archive import ArchiveIntegrityError, ArchiveStore
from zb_hq_memory.models import DecisionRecord, Provenance, RecordStatus, SourceType


def _record(record_id: str, value: str) -> DecisionRecord:
    return DecisionRecord(
        record_id=record_id,
        entity_id="E1",
        status=RecordStatus.LOCKED,
        source=Provenance(
            source_id=f"src-{record_id}",
            source_type=SourceType.TEST_RESULT,
            source_location="test",
            source_hash="b" * 64,
            authority="TEST",
            created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
        ),
        created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
        text=f"k = {value}",
        key="k",
        value=value,
    )


def test_raw_is_content_addressed_and_idempotent(tmp_path: Path) -> None:
    store = ArchiveStore(tmp_path)
    first = store.ingest_raw(b"same bytes")
    second = store.ingest_raw(b"same bytes")
    assert first == second
    assert first.path.read_bytes() == b"same bytes"
    assert first.path.name == first.sha256 + ".bin"


def test_raw_existing_wrong_bytes_fail_closed(tmp_path: Path) -> None:
    store = ArchiveStore(tmp_path)
    raw = store.ingest_raw(b"trusted")
    raw.path.write_bytes(b"tampered")
    with pytest.raises(ArchiveIntegrityError, match="RAW_HASH_MISMATCH"):
        store.ingest_raw(b"trusted")


def test_same_record_is_idempotent_but_changed_body_collides(tmp_path: Path) -> None:
    store = ArchiveStore(tmp_path)
    first = _record("decision-1", "A")
    path = store.append_record(first)
    assert store.append_record(first) == path
    with pytest.raises(ArchiveIntegrityError, match="RECORD_ID_COLLISION"):
        store.append_record(_record("decision-1", "B"))


def test_iter_records_revalidates_corrupted_record(tmp_path: Path) -> None:
    store = ArchiveStore(tmp_path)
    path = store.append_record(_record("decision-1", "A"))
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(ArchiveIntegrityError, match="RECORD_INVALID"):
        store.iter_records()
