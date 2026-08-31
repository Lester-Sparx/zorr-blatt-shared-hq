from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_three_chat_sheriff.py"
LAW_PATH = "studio/ZORR_SHERIFF_THREE_CHAT_LAW_R01.md"

VALID_LAW = f"""# ZORR SHERIFF — UNIVERSAL THREE-CHAT LAW R01

CHAT A = CHARACTER / COSTUME -> POSE
CHAT B = WORLD / CAMERA / S001
CHAT C = DUNCAN PRIME MASTER / INTEGRATOR
DURABLE AUTHORITY = GITHUB
DECLARED HEAD != CURRENT HEAD
ONE ACTIVE GATE LAW
PASS TYPE LAW
SPEC_PASS
STATIC_PASS
CI_PASS
RUNTIME_PASS
VISUAL_PASS
PHYSICAL_PASS
PRODUCTION_PASS
ARTIFACT > ACTIVITY LAW
TWO-SAME-FAILS LAW
THIRD SAME REPAIR = FORBIDDEN
NO COMPETING LOCKS LAW
DURABLE WRITE LAW
WRITE -> READBACK -> IDENTITY/HASH MATCH
CONFLICTING MEMORY LAW
OWNER TASTE LAW
PROTECTED AUTHORITY LAW
MASTER PROMOTION LAW
PROMOTION = DENIED
"""

VALID_MASTER = f"""# ZORR MASTER CHAT BOOTSTRAP R01

ROOT = DUNCAN PRIME
ROLE = DUNCAN PRIME MASTER / INTEGRATOR
SHERIFF LAW = `{LAW_PATH}`
BOOT = fresh-read `{LAW_PATH}` before promotion
OUTPUT = RESULT / DELTA / EVIDENCE / GATE DECISION / NEXT
"""


def orchestration(chat_c_tracker: str = "#251", extra: str = "") -> str:
    return f"""# ZORR THREE-CHAT ORCHESTRATION R01

SHERIFF LAW = `{LAW_PATH}`
CHAT A — CHARACTER MECHANICS
Tracker: #249
CHAT B — WORLD / CAMERA / SHOT CONTRACT
Tracker: #250
CHAT C — MASTER / DUNCAN PRIME INTEGRATOR
Tracker: {chat_c_tracker}
No two chats may independently redefine the same lock.
STOP LOCAL PROMOTION -> RECORD CONFLICT -> CHAT C MASTER ARBITRATION -> ONE AUTHORITY DECISION -> CONTINUE
{extra}
"""


def run_validator(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(root)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_fixture(root: Path, *, chat_c_tracker: str = "#251", extra_orchestration: str = "") -> None:
    studio = root / "studio"
    studio.mkdir(parents=True)
    (studio / "ZORR_SHERIFF_THREE_CHAT_LAW_R01.md").write_text(VALID_LAW, encoding="utf-8")
    (studio / "ZORR_MASTER_CHAT_BOOTSTRAP_R01.md").write_text(VALID_MASTER, encoding="utf-8")
    (studio / "ZORR_THREE_CHAT_ORCHESTRATION_R01.md").write_text(
        orchestration(chat_c_tracker, extra_orchestration), encoding="utf-8"
    )


class ThreeChatSheriffLawTests(unittest.TestCase):
    def test_current_repository_satisfies_three_chat_sheriff_contract(self) -> None:
        result = run_validator(ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("THREE CHAT SHERIFF VALIDATION PASS", result.stdout)

    def test_hardcoded_current_head_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(
                root,
                extra_orchestration=(
                    "CURRENT STUDIO HEAD = 0123456789abcdef0123456789abcdef01234567\n"
                ),
            )
            result = run_validator(root)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("CURRENT_HEAD_LITERAL_FORBIDDEN", result.stderr)

    def test_chat_c_tracker_role_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture(root, chat_c_tracker="#252")
            result = run_validator(root)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("CHAT_C_TRACKER_BINDING_MISSING", result.stderr)


if __name__ == "__main__":
    unittest.main()
