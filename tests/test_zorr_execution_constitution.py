from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONSTITUTION = ROOT / "ZORR_EXECUTION_CONSTITUTION.md"
AGENTS = ROOT / "AGENTS.md"


class ZorrExecutionConstitutionTests(unittest.TestCase):
    def test_constitution_exists_with_core_laws(self):
        self.assertTrue(CONSTITUTION.is_file(), "ZORR_EXECUTION_CONSTITUTION.md is required")
        text = CONSTITUTION.read_text(encoding="utf-8")
        required = (
            "TRUTH LAW",
            "STUDY-FIRST LAW",
            "REUSE-FIRST / DO-NOT-WRITE-IT-YOURSELF LAW",
            "SIMPLEST-SUFFICIENT-SYSTEM LAW",
            "NO-TREADING-WATER LAW",
            "ROOT-CAUSE-BEFORE-FIX LAW",
            "BASE-FIRST LAW",
            "PRODUCT-FIRST LAW",
            "OWNER-IS-NOT-A-COURIER LAW",
            "FAIL-CLOSED LAW",
            "ZORR MODE shorthand",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_agent_bootstrap_requires_constitution(self):
        text = AGENTS.read_text(encoding="utf-8")
        self.assertIn("ZORR MODE — mandatory execution bootstrap", text)
        self.assertIn("ZORR_EXECUTION_CONSTITUTION.md", text)
        self.assertIn("DURABLE_CONTEXT_NOT_PROVEN", text)
        self.assertIn("Before claiming `PASS`", text)

    def test_owner_profile_is_not_part_of_execution_base(self):
        self.assertFalse((ROOT / "OWNER_WORKING_PROFILE.md").exists())


if __name__ == "__main__":
    unittest.main()
