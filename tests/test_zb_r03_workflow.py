from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "zb-r03-production-router.yml"


class R03ProductionWorkflowRetirementTests(unittest.TestCase):
    def workflow(self) -> str:
        if not WORKFLOW.is_file():
            self.fail("R03_PRODUCTION_WORKFLOW_MISSING")
        return WORKFLOW.read_text(encoding="utf-8")

    def test_old_r03_copilot_path_is_not_event_triggered(self):
        text = self.workflow()
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("issue_comment:", text)
        self.assertNotIn("repository_dispatch:", text)
        self.assertNotIn("schedule:", text)

    def test_old_r03_copilot_and_lester_executor_are_out_of_critical_path(self):
        text = self.workflow()
        self.assertIn("R03_RETIRED_FROM_AUTOMATION", text)
        self.assertNotIn("zb-r03-lester-agent.lock.yml", text)
        self.assertNotIn("COPILOT_GITHUB_TOKEN", text)
        self.assertNotIn("needs.lester", text)
        self.assertNotIn("gh-aw", text.lower())


if __name__ == "__main__":
    unittest.main()
