from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from zb_hq_memory.archive import ArchiveStore
from zb_hq_memory.context import build_context_packet
from zb_hq_memory.models import DecisionRecord, ProgressEvent, Provenance, RecordStatus, SourceRecord, SourceType


def _source(source_id: str, source_type: SourceType = SourceType.TEST_RESULT) -> Provenance:
    return Provenance(
        source_id=source_id,
        source_type=source_type,
        source_location=f"source:{source_id}",
        source_hash="f" * 64,
        authority="SPARX" if source_type in {SourceType.OWNER_DIRECT, SourceType.OWNER_CORRECTION} else "TEST",
        created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
    )


def test_context_packet_is_bounded_current_and_provenance_backed(tmp_path: Path) -> None:
    store = ArchiveStore(tmp_path)
    old = DecisionRecord(
        record_id="old",
        entity_id="E1",
        status=RecordStatus.LOCKED,
        source=_source("owner-old", SourceType.OWNER_DIRECT),
        created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
        text="color = red",
        key="color",
        value="red",
    )
    new = DecisionRecord(
        record_id="new",
        entity_id="E1",
        status=RecordStatus.LOCKED,
        source=_source("owner-new", SourceType.OWNER_CORRECTION),
        created_at=datetime(2026, 8, 29, 5, 1, tzinfo=timezone.utc),
        text="color = black",
        key="color",
        value="black",
        supersedes="old",
    )
    open_item = SourceRecord(
        record_id="open-1",
        entity_id="E1",
        status=RecordStatus.OPEN,
        source=_source("open-src", SourceType.OWNER_DIRECT),
        created_at=datetime(2026, 8, 29, 5, 2, tzinfo=timezone.utc),
        text="weapon length unresolved",
    )
    progress = ProgressEvent(
        record_id="progress-1",
        entity_id="E1",
        status=RecordStatus.LOCKED,
        source=_source("qc-1", SourceType.QC_RESULT),
        created_at=datetime(2026, 8, 29, 5, 3, tzinfo=timezone.utc),
        text="learned mask rule",
        skill_id="mask_control",
        before_state="FAILED",
        task="repair",
        inputs=[],
        output_artifacts=[],
        qc_result="FAIL",
        failures=["overlap"],
        learned_rules=["never overlap lock"],
        progress_delta="POSITIVE",
        next_target="retry",
    )
    for record in (old, new, open_item, progress):
        store.append_record(record)

    packet = build_context_packet(ArchiveStore(tmp_path), "E1")
    assert packet.facts == {"color": "black"}
    assert packet.open_items == ["weapon length unresolved"]
    assert packet.learned_rules == ["never overlap lock"]
    assert "owner-new" in packet.source_pointers
    assert "old" not in packet.current_record_ids
