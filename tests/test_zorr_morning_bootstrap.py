from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MORNING = ROOT / "studio" / "ZORR_MORNING_BOOTSTRAP_R01.md"
MASTER = ROOT / "studio" / "ZORR_MASTER_CHAT_BOOTSTRAP_R01.md"
ORCH = ROOT / "studio" / "ZORR_THREE_CHAT_ORCHESTRATION_R01.md"
MORNING_REF = "studio/ZORR_MORNING_BOOTSTRAP_R01.md"


class ZorrMorningBootstrapTests(unittest.TestCase):
    def test_morning_bootstrap_exists_and_has_all_three_start_commands(self) -> None:
        self.assertTrue(MORNING.is_file(), "MORNING_BOOTSTRAP_MISSING")
        text = MORNING.read_text(encoding="utf-8")
        for token in (
            "ZORR MORNING A",
            "ZORR MORNING B",
            "ZORR MORNING C",
            "FRESH-READ GITHUB BEFORE ACTION",
            "DO NOT ASK OWNER TO REPEAT DURABLE CONTEXT",
            "DO NOT TRUST A HISTORICAL HEAD AS CURRENT",
            "OWNER MAY GO OFFLINE",
        ):
            self.assertIn(token, text)

    def test_master_and_orchestration_bind_the_morning_bootstrap(self) -> None:
        master = MASTER.read_text(encoding="utf-8")
        orchestration = ORCH.read_text(encoding="utf-8")
        self.assertIn(MORNING_REF, master, "MASTER_MORNING_BINDING_MISSING")
        self.assertIn(MORNING_REF, orchestration, "ORCHESTRATION_MORNING_BINDING_MISSING")


if __name__ == "__main__":
    unittest.main()
