from __future__ import annotations

_ALLOWED = {
    "ASSIGNED": {"WAITING_REFERENCE", "STARTING_BACKEND"},
    "WAITING_REFERENCE": {"STARTING_BACKEND"},
    "STARTING_BACKEND": {"RUNNING", "FAILED"},
    "RUNNING": {"RESULT_READY", "FAILED"},
    "RESULT_READY": set(),
    "FAILED": set(),
}


def can_transition(current: str, target: str) -> bool:
    return target in _ALLOWED.get(current, set())
