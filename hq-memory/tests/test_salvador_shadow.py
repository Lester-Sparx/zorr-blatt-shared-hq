from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

import pytest

from zb_hq_memory import ArchiveStore, Provenance, SearchIndex, SourceType
from zb_hq_memory.salvador_shadow import (
    RuleState,
    ShadowLearningError,
    ShadowObservation,
    SkillState,
    build_salvador_context,
    make_progress_event,
    normalized_error,
    promote_rule,
)

NOW = datetime(2026, 8, 29, 8, 0, tzinfo=timezone.utc)


def source(kind: SourceType = SourceType.QC_RESULT) -> Provenance:
    return Provenance(
        source_id=f"src-{kind.value.lower()}",
        source_type=kind,
        source_location="github:pr:164",
        source_hash="a" * 64,
        authority="DUNCAN3" if kind == SourceType.QC_RESULT else "OWNER",
        created_at=NOW,
    )


def observation(**changes: object) -> ShadowObservation:
    data: dict[str, object] = {
        "task_id": "shadow-1",
        "run_id": "run-1",
        "skill_id": "mask_control",
        "before_state": SkillState.UNTESTED,
        "qc_result": "FAIL",
        "metric_set_version": "SALVADOR_METRICS_R01",
        "measurements": {"mask_overlap": 0.18, "silhouette_error": 0.01},
        "input_artifacts": ["source:sha256:aaa"],
        "output_artifacts": ["result:sha256:bbb"],
        "failure_ids": ["mask overlap with locked face"],
        "root_cause_hypotheses": ["edit mask crossed higher-authority lock"],
        "learned_rule_candidates": ["edit mask must not intersect locked face"],
        "next_target": "mask_control_retest",
        "hard_lock_fail": True,
        "independent_evidence": False,
    }
    data.update(changes)
    return ShadowObservation(**data)


def test_failure_archives_learning_without_mutating_observation() -> None:
    obs = observation()
    before = obs.model_dump(mode="json")
    event = make_progress_event("shadow-event-1", obs, source(), observed_at=NOW)
    assert obs.model_dump(mode="json") == before
    assert event.entity_id == "SALVADOR"
    assert event.qc_result == "FAIL"
    assert event.after_state == SkillState.FAILED.value
    assert event.learned_rules == ["edit mask must not intersect locked face"]
    assert event.rule_states == {"edit mask must not intersect locked face": RuleState.CANDIDATE.value}
    assert event.metric_set_version == "SALVADOR_METRICS_R01"
    assert event.measurements["mask_overlap"] == 0.18


def test_pass_needs_independent_evidence_to_become_proven() -> None:
    without_gate = make_progress_event(
        "shadow-event-2",
        observation(
            before_state=SkillState.PARTIAL,
            qc_result="PASS",
            hard_lock_fail=False,
            independent_evidence=False,
            failure_ids=[],
        ),
        source(),
        observed_at=NOW,
    )
    with_gate = make_progress_event(
        "shadow-event-3",
        observation(
            before_state=SkillState.PARTIAL,
            qc_result="PASS",
            hard_lock_fail=False,
            independent_evidence=True,
            failure_ids=[],
        ),
        source(),
        observed_at=NOW + timedelta(seconds=1),
    )
    assert without_gate.after_state == SkillState.PARTIAL.value
    assert with_gate.after_state == SkillState.PROVEN.value


def test_shadow_cannot_self_award_locked() -> None:
    with pytest.raises(ShadowLearningError, match="LOCKED_REQUIRES_AUTHORITY"):
        make_progress_event(
            "shadow-event-4",
            observation(
                qc_result="PASS",
                hard_lock_fail=False,
                independent_evidence=True,
                requested_after_state=SkillState.LOCKED,
            ),
            source(),
            observed_at=NOW,
        )


def test_rule_lifecycle_requires_retest_independent_evidence_and_authority() -> None:
    assert promote_rule(RuleState.CANDIDATE, retest_passed=True) == RuleState.RETESTED
    assert promote_rule(RuleState.RETESTED, independent_evidence=True) == RuleState.PROVEN
    with pytest.raises(ShadowLearningError, match="RULE_LOCK_REQUIRES_AUTHORITY"):
        promote_rule(RuleState.PROVEN)
    assert promote_rule(RuleState.PROVEN, authority_promoted=True) == RuleState.LOCKED
    with pytest.raises(ShadowLearningError, match="RULE_PROMOTION_GATE"):
        promote_rule(RuleState.CANDIDATE, independent_evidence=True)


def test_hard_lock_fail_overrides_good_metrics_and_pass_label() -> None:
    event = make_progress_event(
        "shadow-event-5",
        observation(
            before_state=SkillState.PARTIAL,
            qc_result="PASS",
            hard_lock_fail=True,
            independent_evidence=True,
            measurements={"silhouette_error": 0.001, "color_zone_error": 0.002},
        ),
        source(),
        observed_at=NOW,
    )
    assert event.qc_result == "FAIL"
    assert event.after_state == SkillState.PARTIAL.value
    assert event.hard_lock_fail is True


def test_owner_correction_supersedes_old_learning_and_restore_is_deterministic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = ArchiveStore(Path(tmp))
        old = make_progress_event(
            "shadow-old",
            observation(before_state=SkillState.UNTESTED),
            source(),
            observed_at=NOW,
        )
        corrected = make_progress_event(
            "shadow-corrected",
            observation(
                before_state=SkillState.FAILED,
                qc_result="PASS",
                hard_lock_fail=False,
                independent_evidence=True,
                failure_ids=[],
                learned_rule_candidates=["preserve locked face region"],
            ),
            source(SourceType.OWNER_CORRECTION),
            observed_at=NOW + timedelta(seconds=1),
            supersedes="shadow-old",
        )
        store.append_record(old)
        store.append_record(corrected)
        first = build_salvador_context(store)
        second = build_salvador_context(ArchiveStore(Path(tmp)))
        assert first == second
        assert first.skills["mask_control"] == SkillState.PROVEN
        assert first.proven_capabilities == ["mask_control"]
        assert first.locked_skills == []
        assert "shadow-old" not in first.current_record_ids
        assert "shadow-corrected" in first.current_record_ids


def test_existing_fts_search_indexes_shadow_learning_records_with_skill_and_version() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = ArchiveStore(root / "archive")
        store.append_record(make_progress_event("shadow-search", observation(), source(), observed_at=NOW))
        index = SearchIndex(root / "search.sqlite3")
        index.rebuild(store.iter_records())
        hits = index.search("mask overlap with locked face")
        assert hits
        assert hits[0].record_id == "shadow-search"
        assert hits[0].skill_id == "mask_control"
        assert hits[0].version == "SALVADOR_METRICS_R01"


def test_normalized_error_is_deterministic_and_scale_explicit() -> None:
    assert normalized_error(observed=11.0, expected=10.0, scale=10.0) == pytest.approx(0.1)
    assert normalized_error(observed=9.0, expected=10.0, scale=10.0) == pytest.approx(0.1)
    with pytest.raises(ShadowLearningError, match="MEASUREMENT_SCALE_INVALID"):
        normalized_error(observed=1.0, expected=1.0, scale=0.0)
