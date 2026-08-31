#!/usr/bin/env python3
"""ZORR anti-fixation diversity gate.

Reject concept proposals that repeat recent surface solutions even when the
emotion label changes. Stdlib only; intended to run before any illustration or
image-generation step.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

DIMENSIONS = {
    "framing": 1.0,
    "camera": 1.0,
    "pose": 1.2,
    "hand_role": 1.2,
    "face_mechanism": 1.2,
    "body_effort": 1.2,
    "space_operator": 1.0,
    "lighting": 0.8,
    "palette": 0.7,
    "render_language": 0.8,
    "environment_logic": 1.0,
    "temporal_state": 1.0,
}

EMOTION_CHANNELS = (
    "face",
    "body",
    "hands",
    "space",
    "light_value",
    "environment",
    "temporal_rhythm",
)

DEFAULTS = {
    "min_weighted_distance": 0.58,
    "min_changed_dimensions": 7,
    "max_same_values_in_recent_window": 2,
    "recent_window": 4,
    "min_emotion_channels": 4,
    "max_signature_overlap": 2,
}

SIGNATURE = ("camera", "pose", "hand_role", "lighting", "palette")


@dataclass(frozen=True)
class GateResult:
    passed: bool
    reasons: Tuple[str, ...]
    min_weighted_distance: float
    min_changed_dimensions: int
    active_emotion_channels: int


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def weighted_distance(a: Dict[str, str], b: Dict[str, str]) -> Tuple[float, int]:
    total = 0.0
    changed = 0.0
    changed_dims = 0
    for dim, weight in DIMENSIONS.items():
        total += weight
        if a.get(dim) != b.get(dim):
            changed += weight
            changed_dims += 1
    return changed / total if total else 0.0, changed_dims


def active_emotion_channels(concept: Dict) -> int:
    channels = concept.get("emotion_channels", {})
    return sum(bool(channels.get(k)) for k in EMOTION_CHANNELS)


def value_frequency_violations(concept: Dict, history: List[Dict], cfg: Dict) -> List[str]:
    window = history[-int(cfg["recent_window"]):]
    limit = int(cfg["max_same_values_in_recent_window"])
    out: List[str] = []
    for dim in DIMENSIONS:
        value = concept.get(dim)
        if value is None:
            continue
        count = sum(1 for h in window if h.get(dim) == value)
        if count >= limit:
            out.append(f"cooldown:{dim}={value!r} already used {count}x")
    return out


def signature_overlap(a: Dict, b: Dict) -> int:
    return sum(a.get(dim) == b.get(dim) for dim in SIGNATURE)


def validate_schema(concept: Dict) -> List[str]:
    reasons: List[str] = []
    for dim in DIMENSIONS:
        if not concept.get(dim):
            reasons.append(f"missing:{dim}")
    if not concept.get("emotion_goal"):
        reasons.append("missing:emotion_goal")
    if not concept.get("far_analogy"):
        reasons.append("missing:far_analogy")
    if not isinstance(concept.get("emotion_channels"), dict):
        reasons.append("missing:emotion_channels")
    return reasons


def gate(concept: Dict, history: List[Dict], cfg: Dict | None = None) -> GateResult:
    cfg = {**DEFAULTS, **(cfg or {})}
    reasons = validate_schema(concept)

    distances = [weighted_distance(concept, h) for h in history]
    if distances:
        min_dist, min_changed = min(distances, key=lambda x: x[0])
    else:
        min_dist, min_changed = 1.0, len(DIMENSIONS)

    if min_dist < float(cfg["min_weighted_distance"]):
        reasons.append(
            f"fixation:weighted_distance={min_dist:.3f} < {float(cfg['min_weighted_distance']):.3f}"
        )
    if min_changed < int(cfg["min_changed_dimensions"]):
        reasons.append(
            f"fixation:changed_dimensions={min_changed} < {int(cfg['min_changed_dimensions'])}"
        )

    reasons.extend(value_frequency_violations(concept, history, cfg))

    if history:
        overlap = max(
            signature_overlap(concept, h)
            for h in history[-int(cfg["recent_window"]):]
        )
        if overlap > int(cfg["max_signature_overlap"]):
            reasons.append(
                f"surface_signature_overlap={overlap} > {int(cfg['max_signature_overlap'])}"
            )

    channels = active_emotion_channels(concept)
    if channels < int(cfg["min_emotion_channels"]):
        reasons.append(
            f"weak_emotion:active_channels={channels} < {int(cfg['min_emotion_channels'])}"
        )

    far = str(concept.get("far_analogy", "")).lower()
    if any(tok in far for tok in ("anime", "manga", "jojo", "bleach", "berserk")):
        reasons.append("far_analogy_not_far:use a non-anime functional domain")

    return GateResult(
        passed=not reasons,
        reasons=tuple(reasons),
        min_weighted_distance=min_dist,
        min_changed_dimensions=min_changed,
        active_emotion_channels=channels,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--concept", required=True, type=Path)
    ap.add_argument("--history", required=True, type=Path)
    ap.add_argument("--config", type=Path)
    args = ap.parse_args()

    concept = load_json(args.concept)
    history = load_json(args.history)
    cfg = load_json(args.config) if args.config else None
    result = gate(concept, history, cfg)
    print(json.dumps({
        "status": "PASS" if result.passed else "REJECT",
        "min_weighted_distance": round(result.min_weighted_distance, 4),
        "min_changed_dimensions": result.min_changed_dimensions,
        "active_emotion_channels": result.active_emotion_channels,
        "reasons": list(result.reasons),
    }, indent=2, ensure_ascii=False))
    return 0 if result.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
