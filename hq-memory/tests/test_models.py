from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from zb_hq_memory.models import (
    DecisionRecord,
    Provenance,
    RecordStatus,
    SourceType,
    parse_record,
)


def _source() -> Provenance:
    return Provenance(
        source_id="src-1",
        source_type=SourceType.OWNER_DIRECT,
        source_location="raw:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        source_hash="a" * 64,
        authority="SPARX",
        created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
    )


def test_provenance_rejects_naive_timestamp_and_bad_hash() -> None:
    with pytest.raises(ValidationError):
        Provenance(
            source_id="src-1",
            source_type=SourceType.OWNER_DIRECT,
            source_location="chat",
            source_hash="not-a-sha",
            authority="SPARX",
            created_at=datetime(2026, 8, 29, 5, 0),
        )


def test_records_forbid_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        DecisionRecord(
            record_id="d1",
            entity_id="E1",
            status=RecordStatus.LOCKED,
            source=_source(),
            created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
            text="height = 180",
            key="height",
            value="180",
            surprise="invented",
        )


def test_parse_record_restores_discriminated_subtype() -> None:
    record = DecisionRecord(
        record_id="d1",
        entity_id="E1",
        status=RecordStatus.LOCKED,
        source=_source(),
        created_at=datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc),
        text="height = 180",
        key="height",
        value="180",
    )
    restored = parse_record(record.model_dump(mode="json"))
    assert restored == record
    assert restored.record_type == "DECISION_RECORD"
    assert DecisionRecord.model_json_schema()["type"] == "object"
