from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import DurableRecord, RecordStatus


class SnapshotIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True)
class CurrentSnapshot:
    records: tuple[DurableRecord, ...]
    superseded_ids: frozenset[str]


def build_current_snapshot(records: Iterable[DurableRecord]) -> CurrentSnapshot:
    ordered = tuple(records)
    by_id: dict[str, DurableRecord] = {}
    for record in ordered:
        if record.record_id in by_id:
            raise SnapshotIntegrityError("RECORD_ID_COLLISION")
        by_id[record.record_id] = record

    superseders: dict[str, str] = {}
    for record in ordered:
        if record.supersedes is None:
            continue
        if record.supersedes not in by_id:
            raise SnapshotIntegrityError("SUPERSEDES_TARGET_MISSING")
        previous = superseders.get(record.supersedes)
        if previous is not None and previous != record.record_id:
            raise SnapshotIntegrityError("SUPERSEDES_CONFLICT")
        superseders[record.supersedes] = record.record_id

    superseded_ids = frozenset(superseders)
    excluded_statuses = {RecordStatus.SUPERSEDED, RecordStatus.QUARANTINE, RecordStatus.DROP}
    current = tuple(
        sorted(
            (
                record
                for record in ordered
                if record.record_id not in superseded_ids and record.status not in excluded_statuses
            ),
            key=lambda record: (record.created_at, record.record_id),
        )
    )
    return CurrentSnapshot(records=current, superseded_ids=superseded_ids)
