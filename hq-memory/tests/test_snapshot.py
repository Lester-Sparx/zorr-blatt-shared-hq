from __future__ import annotations

from datetime import datetime, timezone

import pytest

from zb_hq_memory.models import DecisionRecord, Provenance, RecordStatus, SourceType
from zb_hq_memory.snapshot import SnapshotIntegrityError, build_current_snapshot


def _decision(record_id: str, value: str, supersedes: str | None = None) -> DecisionRecord:
    return DecisionRecord(
        record_id=record_id,
        entity_id="E1",
        status=RecordStatus.LOCKED,
        source=Provenance(
            source_id=f"src-{record_id}",
            source_type=SourceType.OWNER_CORRECTION if supersedes else SourceType.OWNER_DIRECT,
            source_location="owner",
            source_hash=("c" if supersedes else "d") * 64,
            authority="SPARX",
            created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
        ),
        created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
        text=f"k = {value}",
        key="k",
        value=value,
        supersedes=supersedes,
    )


def test_missing_superseded_target_fails_closed() -> None:
    with pytest.raises(SnapshotIntegrityError, match="SUPERSEDES_TARGET_MISSING"):
        build_current_snapshot([_decision("new", "B", supersedes="missing")])


def test_two_records_cannot_supersede_same_target() -> None:
    old = _decision("old", "A")
    with pytest.raises(SnapshotIntegrityError, match="SUPERSEDES_CONFLICT"):
        build_current_snapshot([
            old,
            _decision("new-1", "B", supersedes="old"),
            _decision("new-2", "C", supersedes="old"),
        ])


def test_snapshot_keeps_only_effective_record_and_reports_history_id() -> None:
    old = _decision("old", "A")
    new = _decision("new", "B", supersedes="old")
    snapshot = build_current_snapshot([old, new])
    assert snapshot.records == (new,)
    assert snapshot.superseded_ids == frozenset({"old"})
