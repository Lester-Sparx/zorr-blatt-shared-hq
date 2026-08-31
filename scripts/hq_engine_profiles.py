from __future__ import annotations

from typing import Any


ROOT_IDENTITY = "DUNCAN PRIME"
COMMON_BASE_PATH = "hq/engine-profiles/FOUR_ENGINE_R01.md"
ENGINE_IDS = ("SALVADOR", "GAUZZ", "LYNCH", "HOKUSAI")

LEARNING_GATE = [
    "SOURCE_OR_LESSON",
    "EXERCISE",
    "OBJECTIVE_CHECK",
    "REGRESSION",
    "CHANGED_OR_UNSEEN_TRANSFER",
    "DURABLE_EVIDENCE",
    "PROVEN_OR_PARTIAL_OR_FAILED",
]

REQUIRED_RESTORE = [
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
        "command": "SALVADOR",
        "profile_path": "hq/engine-profiles/SALVADOR.md",
        "root_identity": ROOT_IDENTITY,
        "scope": "DRAW",
        "source_refs": ["#199", "#214", "#206"],
        "skill_domains": [
            "IDENTITY", "FORM", "ANATOMY", "GESTURE", "SILHOUETTE", "LINE",
            "CONTOUR", "VALUE", "TONE", "PERSPECTIVE", "DRAWING_SIMPLIFICATION",
            "MODEL_SHEET_CONSISTENCY",
        ],
        "restore_query": "SALVADOR drawing identity silhouette line anatomy model sheet ZORR",
        "learning_query": "SALVADOR drawing identity drift silhouette line regression transfer",
    },
    "GAUZZ": {
        "engine_id": "GAUZZ",
        "command": "GAUZZ",
        "profile_path": "hq/engine-profiles/GAUZZ.md",
        "root_identity": ROOT_IDENTITY,
        "scope": "MATH_QC",
        "source_refs": ["#229", "#233", "#231"],
        "skill_domains": [
            "GEOMETRY", "PROPORTION", "COORDINATES", "PROJECTIVE_GEOMETRY", "FOV",
            "TRAJECTORY", "TIMING", "STATISTICS", "ERROR", "UNCERTAINTY", "QC",
            "TRANSFER_MEASUREMENT",
        ],
        "restore_query": "GAUZZ math QC geometry proportion FOV trajectory uncertainty ZORR",
        "learning_query": "GAUZZ measurement error QC regression transfer uncertainty",
    },
    "LYNCH": {
        "engine_id": "LYNCH",
        "command": "LYNCH",
        "profile_path": "hq/engine-profiles/LYNCH.md",
        "root_identity": ROOT_IDENTITY,
        "scope": "SCENE_DIRECTING",
        "source_refs": ["#231", "#206"],
        "skill_domains": [
            "STAGING", "DIRECTING", "BLOCKING", "CAMERA", "SHOT_SCALE", "SCREEN_GEOGRAPHY",
            "ACTING", "ACTION_READABILITY", "CONTINUITY", "RHYTHM", "REVEAL", "MONTAGE",
            "PARALLAX", "DEPTH",
        ],
        "restore_query": "LYNCH scene directing staging camera blocking acting continuity montage ZORR",
        "learning_query": "LYNCH scene directing staging camera action readability regression transfer",
    },
    "HOKUSAI": {
        "engine_id": "HOKUSAI",
        "command": "HOKUSAI",
        "profile_path": "hq/engine-profiles/HOKUSAI.md",
        "root_identity": ROOT_IDENTITY,
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
    """Resolve only the four engine names; command == engine name, case-insensitive."""
    if not isinstance(message, str):
        return None
    tokens = message.strip().split()
    if not tokens:
        return None
    engine_id = tokens[0].upper()
    if engine_id not in ENGINE_IDS:
        return None
    return dict(ENGINE_PROFILES[engine_id])


def build_activation_contract(message: str) -> dict[str, Any]:
    profile = resolve_engine_command(message)
    if profile is None:
        return {
            "schema": "ZB_ENGINE_ACTIVATION_V1",
            "status": "NO_ENGINE_COMMAND",
            "engine_id": None,
            "root_identity": ROOT_IDENTITY,
            "engine_count": 4,
        }

    return {
        "schema": "ZB_ENGINE_ACTIVATION_V1",
        "status": "ACTIVATE",
        "engine_count": 4,
        "engine_id": profile["engine_id"],
        "command": profile["command"],
        "command_law": "COMMAND_EQUALS_ENGINE_NAME",
        "aliases": [],
        "root_identity": ROOT_IDENTITY,
        "common_base_path": COMMON_BASE_PATH,
        "profile_path": profile["profile_path"],
        "scope": profile["scope"],
        "source_refs": list(profile["source_refs"]),
        "skill_domains": list(profile["skill_domains"]),
        "restore_query": profile["restore_query"],
        "learning_query": profile["learning_query"],
        "required_restore": list(REQUIRED_RESTORE),
        "skill_state_authority": "VERIFIED_EVIDENCE_ONLY",
        "learning_gate": list(LEARNING_GATE),
        "stale_derived_state_may_override_fresh_evidence": False,
    }
