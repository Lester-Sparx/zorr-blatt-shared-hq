from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from zb_hq_memory.index import SearchIndex
from zb_hq_memory.models import DecisionRecord, Provenance, RecordStatus, SourceRecord, SourceType


def _source(source_id: str) -> Provenance:
    return Provenance(
        source_id=source_id,
        source_type=SourceType.TEST_RESULT,
        source_location="test",
        source_hash="e" * 64,
        authority="TEST",
        created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
    )


def test_exact_record_id_beats_fts_and_index_is_rebuildable(tmp_path: Path) -> None:
    records = [
        DecisionRecord(
            record_id="alpha-current",
            entity_id="ALPHA",
            status=RecordStatus.LOCKED,
            source=_source("s1"),
            created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
            text="alpha current material basalt",
            key="material",
            value="basalt",
        ),
        SourceRecord(
            record_id="alpha-old",
            entity_id="ALPHA",
            status=RecordStatus.SUPERSEDED,
            source=_source("s2"),
            created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
            text="alpha old material obsidian",
        ),
    ]
    db_path = tmp_path / "index.sqlite3"
    index = SearchIndex(db_path)
    index.rebuild(records)
    assert index.search("alpha-current")[0].record_id == "alpha-current"
    assert index.search("obsidian", statuses={RecordStatus.SUPERSEDED})[0].record_id == "alpha-old"

    db_path.unlink()
    rebuilt = SearchIndex(db_path)
    rebuilt.rebuild(records)
    assert rebuilt.search("basalt")[0].record_id == "alpha-current"


def test_locked_ranks_before_open_for_same_lexical_match(tmp_path: Path) -> None:
    records = [
        SourceRecord(
            record_id="open-hit",
            entity_id="E1",
            status=RecordStatus.OPEN,
            source=_source("s-open"),
            created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
            text="shared phrase",
        ),
        SourceRecord(
            record_id="locked-hit",
            entity_id="E1",
            status=RecordStatus.LOCKED,
            source=_source("s-locked"),
            created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
            text="shared phrase",
        ),
    ]
    index = SearchIndex(tmp_path / "index.sqlite3")
    index.rebuild(records)
    assert [hit.record_id for hit in index.search("shared phrase")][:2] == ["locked-hit", "open-hit"]
