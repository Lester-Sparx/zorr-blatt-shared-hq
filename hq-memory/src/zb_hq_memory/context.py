from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .archive import ArchiveStore
from .models import DecisionRecord, ProgressEvent, RecordStatus
from .snapshot import build_current_snapshot


class ContextIntegrityError(RuntimeError):
    pass


class ContextPacket(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: str = Field(min_length=1)
    facts: dict[str, str]
    open_items: list[str]
    learned_rules: list[str]
    known_failures: list[str]
    current_record_ids: list[str]
    source_pointers: list[str]


def _append_unique(target: list[str], values: list[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def build_context_packet(store: ArchiveStore, entity_id: str) -> ContextPacket:
    snapshot = build_current_snapshot(store.iter_records())
    records = [record for record in snapshot.records if record.entity_id == entity_id]

    facts: dict[str, str] = {}
    open_items: list[str] = []
    learned_rules: list[str] = []
    known_failures: list[str] = []
    current_record_ids: list[str] = []
    source_pointers: list[str] = []

    for record in records:
        current_record_ids.append(record.record_id)
        if record.source.source_id not in source_pointers:
            source_pointers.append(record.source.source_id)

        if record.status == RecordStatus.OPEN:
            if record.text not in open_items:
                open_items.append(record.text)
            continue

        if isinstance(record, DecisionRecord) and record.status == RecordStatus.LOCKED:
            existing = facts.get(record.key)
            if existing is not None and existing != record.value:
                raise ContextIntegrityError("CURRENT_FACT_CONFLICT")
            facts[record.key] = record.value

        if isinstance(record, ProgressEvent):
            _append_unique(learned_rules, record.learned_rules)
            _append_unique(known_failures, record.failures)

    return ContextPacket(
        entity_id=entity_id,
        facts=facts,
        open_items=open_items,
        learned_rules=learned_rules,
        known_failures=known_failures,
        current_record_ids=current_record_ids,
        source_pointers=source_pointers,
    )
