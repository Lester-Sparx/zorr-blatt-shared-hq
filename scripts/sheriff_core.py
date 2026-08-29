from __future__ import annotations

import hashlib
import json
from typing import Any


INCIDENT_CLASSES = {
    "I0_SELF_CAUGHT",
    "I1_CORRECTNESS",
    "I2_PROCESS",
    "I3_CRITICAL_INTEGRITY",
    "I4_SAFETY_SECURITY",
}


class SheriffIntegrityError(RuntimeError):
    """Raised when durable event identity conflicts with previously recorded bytes."""


def canonical_body_hash(event: dict[str, Any]) -> str:
    payload = json.dumps(
        event,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def classify_replay(existing_hash: str, incoming_hash: str) -> str:
    if existing_hash == incoming_hash:
        return "IDEMPOTENT_REPLAY"
    raise SheriffIntegrityError("EVENT_ID_BODY_HASH_CONFLICT")


def apply_discipline(score: int, delta: int) -> int:
    return max(0, min(100, int(score) + int(delta)))


def discipline_status(score: int) -> str:
    bounded = apply_discipline(score, 0)
    if bounded >= 90:
        return "GREEN"
    if bounded >= 75:
        return "YELLOW"
    if bounded >= 50:
        return "ORANGE"
    return "RED"


def remediation_path(incident_class: str, repeat_count: int) -> tuple[str, ...]:
    if incident_class not in INCIDENT_CLASSES:
        raise ValueError(f"UNKNOWN_INCIDENT_CLASS: {incident_class}")
    if repeat_count < 0:
        raise ValueError("REPEAT_COUNT_MUST_BE_NONNEGATIVE")

    if incident_class == "I0_SELF_CAUGHT":
        return ()

    if incident_class in {"I3_CRITICAL_INTEGRITY", "I4_SAFETY_SECURITY"}:
        steps = [
            "HARD_HOLD",
            "EVIDENCE_REVIEW",
            "ROOT_CAUSE",
            "REGRESSION_TEST",
            "REMEDIATION_PROOF",
            "INDEPENDENT_QC",
        ]
        if incident_class == "I4_SAFETY_SECURITY":
            steps.append("OWNER_REINSTATEMENT")
        return tuple(steps)

    steps = ["ROOT_CAUSE", "REGRESSION_TEST", "FRESH_VERIFICATION"]
    if repeat_count >= 1:
        steps.extend(["MANDATORY_PREFLIGHT", "INDEPENDENT_QC"])
    if repeat_count >= 2:
        steps.extend(["RESTRICT_SIMILAR_WORK"])
    return tuple(steps)
