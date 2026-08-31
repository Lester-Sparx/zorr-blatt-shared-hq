#!/usr/bin/env python3
"""Fail-closed validation for the ZORR three-chat SHERIFF and wake contracts."""

from __future__ import annotations

import re
import sys
from pathlib import Path


LAW_REL = Path("studio/ZORR_SHERIFF_THREE_CHAT_LAW_R01.md")
MORNING_REL = Path("studio/ZORR_MORNING_BOOTSTRAP_R01.md")
MASTER_REL = Path("studio/ZORR_MASTER_CHAT_BOOTSTRAP_R01.md")
ORCH_REL = Path("studio/ZORR_THREE_CHAT_ORCHESTRATION_R01.md")
LAW_REF = LAW_REL.as_posix()
MORNING_REF = MORNING_REL.as_posix()

REQUIRED_LAW_TOKENS = (
    "CHAT A = CHARACTER / COSTUME -> POSE",
    "CHAT B = WORLD / CAMERA / S001",
    "CHAT C = DUNCAN PRIME MASTER / INTEGRATOR",
    "DURABLE AUTHORITY = GITHUB",
    "DECLARED HEAD != CURRENT HEAD",
    "ONE ACTIVE GATE LAW",
    "PASS TYPE LAW",
    "SPEC_PASS",
    "STATIC_PASS",
    "CI_PASS",
    "RUNTIME_PASS",
    "VISUAL_PASS",
    "PHYSICAL_PASS",
    "PRODUCTION_PASS",
    "ARTIFACT > ACTIVITY LAW",
    "TWO-SAME-FAILS LAW",
    "THIRD SAME REPAIR = FORBIDDEN",
    "NO COMPETING LOCKS LAW",
    "DURABLE WRITE LAW",
    "WRITE -> READBACK -> IDENTITY/HASH MATCH",
    "CONFLICTING MEMORY LAW",
    "OWNER TASTE LAW",
    "PROTECTED AUTHORITY LAW",
    "MASTER PROMOTION LAW",
    "PROMOTION = DENIED",
)

REQUIRED_MORNING_TOKENS = (
    "ZORR MORNING A",
    "ZORR MORNING B",
    "ZORR MORNING C",
    "FRESH-READ GITHUB BEFORE ACTION",
    "DO NOT ASK OWNER TO REPEAT DURABLE CONTEXT",
    "DO NOT TRUST A HISTORICAL HEAD AS CURRENT",
    "OWNER MAY GO OFFLINE",
    "Tracker: `#249`",
    "Tracker: `#250`",
    "Tracker: `#251`",
)

CURRENT_HEAD_LITERAL = re.compile(
    r"(?im)^.*\bCURRENT\b[^\n]{0,96}\bHEAD\b\s*=\s*[0-9a-f]{40}\b.*$"
)


class ThreeChatSheriffError(RuntimeError):
    pass


def _read(root: Path, relative: Path, missing_code: str) -> str:
    path = root / relative
    if not path.is_file():
        raise ThreeChatSheriffError(missing_code)
    return path.read_text(encoding="utf-8")


def _require(text: str, token: str, code: str) -> None:
    if token not in text:
        raise ThreeChatSheriffError(code)


def _require_tracker_binding(text: str, chat_label: str, tracker: str, code: str) -> None:
    pattern = re.compile(
        rf"(?is){re.escape(chat_label)}.*?Tracker:\s*{re.escape(tracker)}\b"
    )
    if pattern.search(text) is None:
        raise ThreeChatSheriffError(code)


def validate_repository(root: Path) -> None:
    root = root.resolve()
    law = _read(root, LAW_REL, "SHERIFF_LAW_MISSING")
    morning = _read(root, MORNING_REL, "MORNING_BOOTSTRAP_MISSING")
    master = _read(root, MASTER_REL, "MASTER_BOOTSTRAP_MISSING")
    orchestration = _read(root, ORCH_REL, "ORCHESTRATION_CONTRACT_MISSING")

    _require(master, LAW_REF, "MASTER_SHERIFF_BINDING_MISSING")
    _require(orchestration, LAW_REF, "ORCHESTRATION_SHERIFF_BINDING_MISSING")
    _require(master, MORNING_REF, "MASTER_MORNING_BINDING_MISSING")
    _require(orchestration, MORNING_REF, "ORCHESTRATION_MORNING_BINDING_MISSING")
    _require(morning, "Lester-Sparx/zorr-blatt-shared-hq", "MORNING_REPOSITORY_BINDING_MISSING")
    _require(master, "DUNCAN PRIME", "MASTER_ROLE_BINDING_MISSING")

    _require_tracker_binding(orchestration, "CHAT A", "#249", "CHAT_A_TRACKER_BINDING_MISSING")
    _require_tracker_binding(orchestration, "CHAT B", "#250", "CHAT_B_TRACKER_BINDING_MISSING")
    _require_tracker_binding(orchestration, "CHAT C", "#251", "CHAT_C_TRACKER_BINDING_MISSING")

    for token in REQUIRED_LAW_TOKENS:
        _require(law, token, f"SHERIFF_INVARIANT_MISSING:{token}")

    for token in REQUIRED_MORNING_TOKENS:
        _require(morning, token, f"MORNING_INVARIANT_MISSING:{token}")

    for relative, text in (
        (LAW_REL, law),
        (MORNING_REL, morning),
        (MASTER_REL, master),
        (ORCH_REL, orchestration),
    ):
        if CURRENT_HEAD_LITERAL.search(text):
            raise ThreeChatSheriffError(
                f"CURRENT_HEAD_LITERAL_FORBIDDEN:{relative.as_posix()}"
            )


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1:
        print("usage: validate_three_chat_sheriff.py [ROOT]", file=sys.stderr)
        return 2
    root = Path(args[0]) if args else Path(__file__).resolve().parent.parent
    try:
        validate_repository(root)
    except (OSError, UnicodeError, ThreeChatSheriffError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("THREE CHAT SHERIFF VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
