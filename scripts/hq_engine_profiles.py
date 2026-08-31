from __future__ import annotations

from typing import Any


_ROOT = "DUNCAN PRIME"
_LEARNING_GATE = [
    "SOURCE_OR_LESSON",
    "EXERCISE",
    "OBJECTIVE_CHECK",
    "REGRESSION",
    "CHANGED_OR_UNSEEN_TRANSFER",
    "DURABLE_EVIDENCE",
    "PROVEN_OR_PARTIAL_OR_FAILED",
]
_REQUIRED_RESTORE = [
    "DUNCAN_ROOT_AND_ZORR_LAWS",
    "ENGINE_PROFILE",
    "CURRENT_TASK_EVIDENCE",
    "UNIFIED_ARCHIVE_CONTEXT",
    "VERIFIED_LESSONS",
    "ACCEPTED_OPTIMIZED_POLICY",
    "ENGINE_SOURCE_LAWS_AND_SKILL_EVIDENCE",
]

ENGINE_PROFILES: dict[str, dict[str, Any]] = {
    "SALVADOR": {
        "engine_id": "SALVADOR",
        "root_identity": _ROOT,
        "scope": "DRAW",
        "source_refs": ["#199", "#214", "#206"],
        "skill_domains": [
            "IDENTITY", "FORM", "ANATOMY", "GESTURE", "SILHOUETTE", "LINE",
            "CONTOUR", "VALUE", "TONE", "PERSPECTIVE", "DRAWING_SIMPLIFICATION",
            "MODEL_SHEET_CONSISTENCY",
        ],
        "restore_query": "SALVADOR DRAW drawing identity silhouette line anatomy model sheet ZORR",
        "learning_query": "SALVADOR DRAW drawing identity drift silhouette line transfer",
    },
    "GAUZZ": {
        "engine_id": "GAUZZ",
        "root_identity": _ROOT,
        "scope": "MATH_QC",
        "source_refs": ["#229", "#233", "#231"],
        "skill_domains": [
            "GEOMETRY", "PROPORTION", "COORDINATES", "PROJECTIVE_GEOMETRY", "FOV",
            "TRAJECTORY", "TIMING", "STATISTICS", "ERROR", "UNCERTAINTY", "QC",
            "TRANSFER_MEASUREMENT",
        ],
        "restore_query": "GAUZZ MATH QC geometry proportion FOV trajectory error uncertainty ZORR",
        "learning_query": "GAUZZ MATH QC measurement regression transfer uncertainty",
    },
    "LYNCH": {
        "engine_id": "LYNCH",
        "root_identity": _ROOT,
        "scope": "SCENE_DIRECTING",
        "source_refs": ["#231", "#206"],
        "skill_domains": [
            "STAGING", "BLOCKING", "CAMERA", "SHOT_SCALE", "SCREEN_GEOGRAPHY", "ACTING",
            "ACTION_READABILITY", "CONTINUITY", "RHYTHM", "REVEAL", "MONTAGE", "PARALLAX", "DEPTH",
        ],
        "restore_query": "LYNCH scene directing staging camera blocking acting continuity montage ZORR",
        "learning_query": "LYNCH scene directing staging camera regression transfer action readability",
    },
    "HOKUSAI": {
        "engine_id": "HOKUSAI",
        "root_identity": _ROOT,
        "scope": "DESIGN",
        "source_refs": ["#233", "#199", "#206"],
        "skill_domains": [
            "SHAPE_LANGUAGE", "SILHOUETTE_SYSTEM", "COSTUME", "COLOR", "VALUE_HIERARCHY",
            "NEGATIVE_SPACE", "HATCH_LANGUAGE", "POSTER_LAYOUT", "TYPOGRAPHY",
            "GRAPHIC_HIERARCHY", "FX_RHYTHM", "VARIATION",
        ],
        "restore_query": "HOKUSAI design shape language color negative space poster typography ZORR",
        "learning_query": "HOKUSAI design variation layout color regression transfer",
    },
}


def resolve_engine_command(message: str) -> dict[str, Any] | None:
    if not isinstance(message, str):
        return None
    tokens = message.strip().split()
    if not tokens:
        return None
    engine_id = tokens[0].upper()
    profile = ENGINE_PROFILES.get(engine_id)
    return dict(profile) if profile is not None else None


def build_activation_contract(message: str) -> dict[str, Any]:
    profile = resolve_engine_command(message)
    if profile is None:
        return {
            "schema": "ZB_ENGINE_ACTIVATION_V1",
            "status": "NO_ENGINE_COMMAND",
            "engine_id": None,
            "root_identity": _ROOT,
        }
    return {
        "schema": "ZB_ENGINE_ACTIVATION_V1",
        "status": "ACTIVATE",
        "engine_id": profile["engine_id"],
        "root_identity": _ROOT,
        "scope": profile["scope"],
        "source_refs": list(profile["source_refs"]),
        "skill_domains": list(profile["skill_domains"]),
        "restore_query": profile["restore_query"],
        "learning_query": profile["learning_query"],
        "required_restore": list(_REQUIRED_RESTORE),
        "skill_state_authority": "VERIFIED_EVIDENCE_ONLY",
        "learning_gate": list(_LEARNING_GATE),
        "stale_derived_state_may_override_fresh_evidence": False,
    }
