"""Durable, append-only HQ memory for ZORR BLATT."""

from .archive import ArchiveIntegrityError, ArchiveStore, RawObject
from .context import ContextPacket, build_context_packet
from .index import SearchHit, SearchIndex, SearchIndexError
from .models import (
    ArtifactRecord,
    DecisionRecord,
    EntityProfile,
    ProgressEvent,
    Provenance,
    RecordStatus,
    SourceRecord,
    SourceType,
    TrainingProfile,
)
from .salvador_shadow import (
    RuleState,
    SalvadorContext,
    ShadowLearningError,
    ShadowObservation,
    SkillState,
    build_salvador_context,
    make_progress_event,
    normalized_error,
    promote_rule,
)
from .snapshot import CurrentSnapshot, SnapshotIntegrityError, build_current_snapshot

__all__ = [
    "ArchiveIntegrityError",
    "ArchiveStore",
    "ArtifactRecord",
    "ContextPacket",
    "CurrentSnapshot",
    "DecisionRecord",
    "EntityProfile",
    "ProgressEvent",
    "Provenance",
    "RawObject",
    "RecordStatus",
    "RuleState",
    "SalvadorContext",
    "SearchHit",
    "SearchIndex",
    "SearchIndexError",
    "ShadowLearningError",
    "ShadowObservation",
    "SkillState",
    "SnapshotIntegrityError",
    "SourceRecord",
    "SourceType",
    "TrainingProfile",
    "build_context_packet",
    "build_current_snapshot",
    "build_salvador_context",
    "make_progress_event",
    "normalized_error",
    "promote_rule",
]
