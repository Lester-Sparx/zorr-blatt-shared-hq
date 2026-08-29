from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "zb-r03-production-router.yml"


class R03LegacyRetirementTests(unittest.TestCase):
    def workflow(self) -> str:
        if not WORKFLOW.is_file():
            self.fail("R03_PRODUCTION_WORKFLOW_MISSING")
        return WORKFLOW.read_text(encoding="utf-8")

    def test_legacy_r03_is_manual_only_and_cannot_auto_trigger(self):
        text = self.workflow()
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("issue_comment:", text)
        self.assertNotIn("repository_dispatch:", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("pull_request_target:", text)

    def test_legacy_r03_has_no_nested_ai_executor_in_live_workflow(self):
        text = self.workflow()
        self.assertNotIn("zb-r03-lester-agent.lock.yml", text)
        self.assertNotIn("COPILOT_GITHUB_TOKEN", text)
        self.assertNotIn("needs.lester", text)
        self.assertNotIn("lester:", text)
        self.assertNotIn("duncan_qc:", text)

    def test_legacy_r03_is_a_deterministic_retirement_notice_only(self):
        text = self.workflow()
        self.assertIn("name: zb-r03-production-router-legacy-retired", text)
        self.assertIn("legacy_retired:", text)
        self.assertIn("R03_LEGACY_AUTOMATION_RETIRED", text)
        self.assertIn("DUNCAN_CHATGPT_ORCHESTRATOR_ACTIVE", text)
        self.assertIn("PRODUCTION_ACTIVE=NO", text)


if __name__ == "__main__":
    unittest.main()
