from __future__ import annotations

from datetime import datetime
from enum import StrEnum
import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .archive import ArchiveStore
from .models import ProgressEvent, Provenance, RecordStatus
from .snapshot import build_current_snapshot


class ShadowLearningError(RuntimeError):
    pass


class SkillState(StrEnum):
    UNTESTED = "UNTESTED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    PROVEN = "PROVEN"
    LOCKED = "LOCKED"


class ShadowObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    skill_id: str = Field(min_length=1)
    before_state: SkillState
    qc_result: Literal["PASS", "FAIL"]
    metric_set_version: str = Field(min_length=1)
    measurements: dict[str, float | int | bool | str | None] = Field(default_factory=dict)
    input_artifacts: list[str] = Field(default_factory=list)
    output_artifacts: list[str] = Field(default_factory=list)
    qc_evidence_refs: list[str] = Field(default_factory=list)
    failure_ids: list[str] = Field(default_factory=list)
    root_cause_hypotheses: list[str] = Field(default_factory=list)
    learned_rule_candidates: list[str] = Field(default_factory=list)
    next_target: str = Field(min_length=1)
    hard_lock_fail: bool = False
    independent_evidence: bool = False
    requested_after_state: SkillState | None = None
    authority_promoted: bool = False


class SalvadorContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    subject: Literal["SALVADOR"] = "SALVADOR"
    skills: dict[str, SkillState]
    learned_rules: list[str]
    known_failures: list[str]
    next_targets: list[str]
    current_record_ids: list[str]
    source_pointers: list[str]


def normalized_error(*, observed: float, expected: float, scale: float) -> float:
    values = (float(observed), float(expected), float(scale))
    if not all(math.isfinite(value) for value in values):
        raise ShadowLearningError("MEASUREMENT_VALUE_INVALID")
    if scale <= 0:
        raise ShadowLearningError("MEASUREMENT_SCALE_INVALID")
    return abs(observed - expected) / scale


def _effective_qc(observation: ShadowObservation) -> Literal["PASS", "FAIL"]:
    return "FAIL" if observation.hard_lock_fail else observation.qc_result


def _next_skill_state(observation: ShadowObservation) -> SkillState:
    requested = observation.requested_after_state
    if requested == SkillState.LOCKED and not observation.authority_promoted:
        raise ShadowLearningError("LOCKED_REQUIRES_AUTHORITY")

    qc_result = _effective_qc(observation)
    before = observation.before_state

    if requested == SkillState.LOCKED and observation.authority_promoted:
        if qc_result != "PASS" or not observation.independent_evidence:
            raise ShadowLearningError("LOCKED_REQUIRES_PROVEN_EVIDENCE")
        return SkillState.LOCKED

    if qc_result == "FAIL":
        if before == SkillState.UNTESTED:
            return SkillState.FAILED
        return before

    if before == SkillState.LOCKED:
        return SkillState.LOCKED
    if observation.independent_evidence:
        return SkillState.PROVEN
    if before in {SkillState.UNTESTED, SkillState.FAILED}:
        return SkillState.PARTIAL
    return before


def make_progress_event(
    record_id: str,
    observation: ShadowObservation,
    source: Provenance,
    *,
    observed_at: datetime,
    supersedes: str | None = None,
) -> ProgressEvent:
    after = _next_skill_state(observation)
    qc_result = _effective_qc(observation)
    details = [
        "SALVADOR SHADOW",
        f"run={observation.run_id}",
        f"skill={observation.skill_id}",
        f"qc={qc_result}",
        f"state={observation.before_state.value}->{after.value}",
    ]
    details.extend(observation.failure_ids)
    details.extend(observation.root_cause_hypotheses)
    details.extend(observation.learned_rule_candidates)

    return ProgressEvent(
        record_id=record_id,
        entity_id="SALVADOR",
        status=RecordStatus.OPEN,
        source=source,
        created_at=observed_at,
        text=" | ".join(details),
        supersedes=supersedes,
        skill_id=observation.skill_id,
        before_state=observation.before_state.value,
        after_state=after.value,
        task=observation.task_id,
        run_id=observation.run_id,
        inputs=list(observation.input_artifacts),
        output_artifacts=list(observation.output_artifacts),
        metric_set_version=observation.metric_set_version,
        measurements=dict(observation.measurements),
        qc_result=qc_result,
        qc_evidence_refs=list(observation.qc_evidence_refs),
        hard_lock_fail=observation.hard_lock_fail,
        failures=list(observation.failure_ids),
        root_cause_hypotheses=list(observation.root_cause_hypotheses),
        learned_rules=list(observation.learned_rule_candidates),
        progress_delta=f"{observation.before_state.value}->{after.value}",
        next_target=observation.next_target,
    )


def _append_unique(target: list[str], values: list[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def build_salvador_context(store: ArchiveStore) -> SalvadorContext:
    snapshot = build_current_snapshot(store.iter_records())
    skills: dict[str, SkillState] = {}
    learned_rules: list[str] = []
    known_failures: list[str] = []
    next_targets: list[str] = []
    current_record_ids: list[str] = []
    source_pointers: list[str] = []

    for record in snapshot.records:
        if not isinstance(record, ProgressEvent) or record.entity_id != "SALVADOR":
            continue
        current_record_ids.append(record.record_id)
        if record.source.source_id not in source_pointers:
            source_pointers.append(record.source.source_id)
        state_value = record.after_state or record.before_state
        try:
            skills[record.skill_id] = SkillState(state_value)
        except ValueError:
            continue
        _append_unique(learned_rules, record.learned_rules)
        _append_unique(known_failures, record.failures)
        if record.next_target and record.next_target not in next_targets:
            next_targets.append(record.next_target)

    return SalvadorContext(
        skills=skills,
        learned_rules=learned_rules,
        known_failures=known_failures,
        next_targets=next_targets,
        current_record_ids=current_record_ids,
        source_pointers=source_pointers,
    )
