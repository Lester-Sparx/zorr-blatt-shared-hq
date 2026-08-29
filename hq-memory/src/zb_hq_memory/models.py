from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
import re
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator

_ID_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class RecordStatus(StrEnum):
    LOCKED = "LOCKED"
    OPEN = "OPEN"
    QUARANTINE = "QUARANTINE"
    DROP = "DROP"
    SUPERSEDED = "SUPERSEDED"


class SourceType(StrEnum):
    OWNER_DIRECT = "OWNER_DIRECT"
    OWNER_CORRECTION = "OWNER_CORRECTION"
    LOCKED_REFERENCE = "LOCKED_REFERENCE"
    APPROVED_REFERENCE = "APPROVED_REFERENCE"
    WORKING_REFERENCE = "WORKING_REFERENCE"
    SOURCE_QUOTE = "SOURCE_QUOTE"
    TEST_RESULT = "TEST_RESULT"
    QC_RESULT = "QC_RESULT"
    MEASURED_DERIVATION = "MEASURED_DERIVATION"
    ASSISTANT_INFERENCE = "ASSISTANT_INFERENCE"
    ASSISTANT_GENERATED = "ASSISTANT_GENERATED"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Provenance(_FrozenModel):
    source_id: str = Field(min_length=1)
    source_type: SourceType
    source_location: str = Field(min_length=1)
    source_hash: str
    authority: str = Field(min_length=1)
    created_at: datetime

    @field_validator("source_id")
    @classmethod
    def _source_id_safe(cls, value: str) -> str:
        if not _ID_RE.fullmatch(value):
            raise ValueError("SOURCE_ID_INVALID")
        return value

    @field_validator("source_hash")
    @classmethod
    def _sha256(cls, value: str) -> str:
        if not _SHA256_RE.fullmatch(value):
            raise ValueError("SOURCE_HASH_INVALID")
        return value.lower()

    @field_validator("created_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("TIMESTAMP_NOT_AWARE")
        return value.astimezone(timezone.utc)


class DurableRecordBase(_FrozenModel):
    record_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    status: RecordStatus
    source: Provenance
    created_at: datetime
    text: str = Field(min_length=1)
    supersedes: str | None = None

    @field_validator("record_id", "entity_id")
    @classmethod
    def _id_safe(cls, value: str) -> str:
        if not _ID_RE.fullmatch(value):
            raise ValueError("RECORD_ID_INVALID")
        return value

    @field_validator("supersedes")
    @classmethod
    def _supersedes_safe(cls, value: str | None) -> str | None:
        if value is not None and not _ID_RE.fullmatch(value):
            raise ValueError("SUPERSEDES_ID_INVALID")
        return value

    @field_validator("created_at")
    @classmethod
    def _created_at_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("TIMESTAMP_NOT_AWARE")
        return value.astimezone(timezone.utc)


class EntityProfile(DurableRecordBase):
    record_type: Literal["ENTITY_PROFILE"] = "ENTITY_PROFILE"
    canonical_name: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)


class TrainingProfile(DurableRecordBase):
    record_type: Literal["TRAINING_PROFILE"] = "TRAINING_PROFILE"
    skills: dict[str, str] = Field(default_factory=dict)


class ProgressEvent(DurableRecordBase):
    record_type: Literal["PROGRESS_EVENT"] = "PROGRESS_EVENT"
    skill_id: str = Field(min_length=1)
    before_state: str = Field(min_length=1)
    after_state: str | None = None
    task: str = Field(min_length=1)
    run_id: str | None = None
    inputs: list[str] = Field(default_factory=list)
    output_artifacts: list[str] = Field(default_factory=list)
    metric_set_version: str | None = None
    measurements: dict[str, float | int | bool | str | None] = Field(default_factory=dict)
    qc_result: str = Field(min_length=1)
    qc_evidence_refs: list[str] = Field(default_factory=list)
    hard_lock_fail: bool = False
    failures: list[str] = Field(default_factory=list)
    root_cause_hypotheses: list[str] = Field(default_factory=list)
    learned_rules: list[str] = Field(default_factory=list)
    progress_delta: str = Field(min_length=1)
    next_target: str = Field(min_length=1)


class DecisionRecord(DurableRecordBase):
    record_type: Literal["DECISION_RECORD"] = "DECISION_RECORD"
    key: str = Field(min_length=1)
    value: str = Field(min_length=1)


class ArtifactRecord(DurableRecordBase):
    record_type: Literal["ARTIFACT_RECORD"] = "ARTIFACT_RECORD"
    object_ref: str = Field(min_length=1)
    sha256: str
    media_type: str = Field(min_length=1)

    @field_validator("sha256")
    @classmethod
    def _artifact_sha(cls, value: str) -> str:
        if not _SHA256_RE.fullmatch(value):
            raise ValueError("ARTIFACT_HASH_INVALID")
        return value.lower()


class SourceRecord(DurableRecordBase):
    record_type: Literal["SOURCE_RECORD"] = "SOURCE_RECORD"


DurableRecord = Annotated[
    Union[
        EntityProfile,
        TrainingProfile,
        ProgressEvent,
        DecisionRecord,
        ArtifactRecord,
        SourceRecord,
    ],
    Field(discriminator="record_type"),
]

_RECORD_ADAPTER = TypeAdapter(DurableRecord)


def parse_record(payload: object) -> DurableRecord:
    return _RECORD_ADAPTER.validate_python(payload)
