from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from zb_hq_memory.archive import ArchiveStore
from zb_hq_memory.context import build_context_packet
from zb_hq_memory.index import SearchIndex
from zb_hq_memory.models import (
    DecisionRecord,
    ProgressEvent,
    Provenance,
    RecordStatus,
    SourceRecord,
    SourceType,
)
from zb_hq_memory.snapshot import build_current_snapshot


def _now() -> datetime:
    return datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc)


def _provenance(store: ArchiveStore, payload: bytes, *, source_id: str, source_type: SourceType) -> Provenance:
    raw = store.ingest_raw(payload)
    return Provenance(
        source_id=source_id,
        source_type=source_type,
        source_location=f"raw:{raw.sha256}",
        source_hash=raw.sha256,
        authority="SPARX" if source_type in {SourceType.OWNER_DIRECT, SourceType.OWNER_CORRECTION} else "DUNCAN",
        created_at=_now(),
    )


def test_training_rule_survives_restart_index_rebuild_and_context_packet(tmp_path: Path) -> None:
    store = ArchiveStore(tmp_path)
    provenance = _provenance(
        store,
        b"FAIL: mask overlaps locked region; learned: edit mask must not overlap higher authority lock",
        source_id="training-source-001",
        source_type=SourceType.QC_RESULT,
    )
    event = ProgressEvent(
        record_id="progress-001",
        entity_id="SALVADOR",
        status=RecordStatus.LOCKED,
        source=provenance,
        created_at=_now(),
        text="Mask-overlap failure produced a durable learned rule.",
        skill_id="mask_control",
        before_state="FAILED",
        task="preservation repair",
        inputs=["locked face region", "edit mask"],
        output_artifacts=[],
        qc_result="FAIL",
        failures=["mask overlaps locked region"],
        learned_rules=["edit_mask must not overlap higher_authority_lock"],
        progress_delta="POSITIVE",
        next_target="prove non-overlapping mask",
    )
    store.append_record(event)

    first_index = SearchIndex(tmp_path / "index" / "hq-memory.sqlite3")
    first_index.rebuild(store.iter_records())
    assert first_index.search("higher_authority_lock")

    # Simulate a new chat/process and a disposable index loss.
    (tmp_path / "index" / "hq-memory.sqlite3").unlink()
    restarted = ArchiveStore(tmp_path)
    rebuilt_index = SearchIndex(tmp_path / "index" / "hq-memory.sqlite3")
    rebuilt_index.rebuild(restarted.iter_records())

    packet = build_context_packet(restarted, "SALVADOR")
    assert "edit_mask must not overlap higher_authority_lock" in packet.learned_rules
    assert rebuilt_index.search("higher_authority_lock")


def test_owner_correction_supersedes_without_deleting_history(tmp_path: Path) -> None:
    store = ArchiveStore(tmp_path)
    old_source = _provenance(store, b"OWNER: height = 180", source_id="owner-001", source_type=SourceType.OWNER_DIRECT)
    old = DecisionRecord(
        record_id="decision-height-r1",
        entity_id="DUNCAN_BODY_CANON",
        status=RecordStatus.LOCKED,
        source=old_source,
        created_at=_now(),
        text="height = 180",
        key="height_cm",
        value="180",
    )
    store.append_record(old)

    new_source = _provenance(store, b"OWNER CORRECTION: height = 181", source_id="owner-002", source_type=SourceType.OWNER_CORRECTION)
    corrected = DecisionRecord(
        record_id="decision-height-r2",
        entity_id="DUNCAN_BODY_CANON",
        status=RecordStatus.LOCKED,
        source=new_source,
        created_at=datetime(2026, 8, 29, 5, 1, tzinfo=timezone.utc),
        text="height = 181",
        key="height_cm",
        value="181",
        supersedes="decision-height-r1",
    )
    store.append_record(corrected)

    snapshot = build_current_snapshot(store.iter_records())
    current = [record for record in snapshot.records if isinstance(record, DecisionRecord)]
    assert [(record.key, record.value) for record in current] == [("height_cm", "181")]
    assert store.get_record("decision-height-r1") == old
    assert store.get_record("decision-height-r2") == corrected
    assert "decision-height-r1" in snapshot.superseded_ids


def test_historical_contradiction_remains_searchable_but_not_current(tmp_path: Path) -> None:
    store = ArchiveStore(tmp_path)
    canonical_source = _provenance(store, b"OWNER: Black Stone = basalt", source_id="owner-black-stone", source_type=SourceType.OWNER_DIRECT)
    canonical = DecisionRecord(
        record_id="black-stone-current",
        entity_id="BLACK_STONE",
        status=RecordStatus.LOCKED,
        source=canonical_source,
        created_at=_now(),
        text="Black Stone material is basalt.",
        key="material",
        value="basalt",
    )
    store.append_record(canonical)

    old_source = _provenance(store, b"old archive says Black Stone is obsidian", source_id="old-black-stone", source_type=SourceType.SOURCE_QUOTE)
    historical = SourceRecord(
        record_id="black-stone-old-source",
        entity_id="BLACK_STONE",
        status=RecordStatus.SUPERSEDED,
        source=old_source,
        created_at=_now(),
        text="Old source says Black Stone is obsidian.",
    )
    store.append_record(historical)

    index = SearchIndex(tmp_path / "index" / "hq-memory.sqlite3")
    index.rebuild(store.iter_records())
    history_hits = index.search("obsidian", statuses={RecordStatus.SUPERSEDED})
    assert [hit.record_id for hit in history_hits] == ["black-stone-old-source"]

    packet = build_context_packet(store, "BLACK_STONE")
    assert packet.facts == {"material": "basalt"}


def test_context_never_autofills_unknown_fields(tmp_path: Path) -> None:
    store = ArchiveStore(tmp_path)
    fact_source = _provenance(store, b"OWNER: coat = black", source_id="owner-coat", source_type=SourceType.OWNER_DIRECT)
    store.append_record(
        DecisionRecord(
            record_id="coat-current",
            entity_id="CHAR_X",
            status=RecordStatus.LOCKED,
            source=fact_source,
            created_at=_now(),
            text="coat = black",
            key="coat",
            value="black",
        )
    )
    open_source = _provenance(store, b"OPEN: birthplace unknown", source_id="open-birthplace", source_type=SourceType.OWNER_DIRECT)
    store.append_record(
        SourceRecord(
            record_id="birthplace-open",
            entity_id="CHAR_X",
            status=RecordStatus.OPEN,
            source=open_source,
            created_at=_now(),
            text="birthplace unknown",
        )
    )

    packet = build_context_packet(store, "CHAR_X")
    assert packet.facts == {"coat": "black"}
    assert packet.open_items == ["birthplace unknown"]
    assert "birthplace" not in packet.facts
