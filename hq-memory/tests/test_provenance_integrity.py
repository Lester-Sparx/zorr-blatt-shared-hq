from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from zb_hq_memory.archive import ArchiveIntegrityError, ArchiveStore
from zb_hq_memory.models import DecisionRecord, Provenance, RecordStatus, SourceType


def _record(store: ArchiveStore) -> DecisionRecord:
    raw = store.ingest_raw(b"owner durable source bytes")
    return DecisionRecord(
        record_id="durable-decision",
        entity_id="E1",
        status=RecordStatus.LOCKED,
        source=Provenance(
            source_id="owner-source",
            source_type=SourceType.OWNER_DIRECT,
            source_location=f"raw:{raw.sha256}",
            source_hash=raw.sha256,
            authority="SPARX",
            created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
        ),
        created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
        text="durable fact = yes",
        key="durable_fact",
        value="yes",
    )


def test_restore_fails_closed_when_bound_raw_bytes_are_tampered(tmp_path: Path) -> None:
    store = ArchiveStore(tmp_path)
    record = _record(store)
    store.append_record(record)

    raw_path = store.raw_root / record.source.source_hash[:2] / f"{record.source.source_hash}.bin"
    raw_path.write_bytes(b"tampered")

    restarted = ArchiveStore(tmp_path)
    with pytest.raises(ArchiveIntegrityError, match="SOURCE_RAW_HASH_MISMATCH"):
        restarted.iter_records()


def test_restore_fails_closed_when_bound_raw_bytes_are_missing(tmp_path: Path) -> None:
    store = ArchiveStore(tmp_path)
    record = _record(store)
    store.append_record(record)

    raw_path = store.raw_root / record.source.source_hash[:2] / f"{record.source.source_hash}.bin"
    raw_path.unlink()

    restarted = ArchiveStore(tmp_path)
    with pytest.raises(ArchiveIntegrityError, match="SOURCE_RAW_MISSING"):
        restarted.get_record(record.record_id)
