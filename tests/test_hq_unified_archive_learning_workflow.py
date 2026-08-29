from pathlib import Path
import unittest

from _support import ROOT


class UnifiedArchiveLearningWorkflowTests(unittest.TestCase):
    def test_main_push_rebuilds_verified_learning_state_in_existing_archive_workflow(self) -> None:
        workflow = (ROOT / ".github/workflows/zb-permanent-archive-v1.yml").read_text(encoding="utf-8")
        self.assertIn("sync-lessons", workflow)
        self.assertIn("source/hq/sheriff/verdicts", workflow)
        self.assertIn("$GITHUB_EVENT_NAME", workflow)
        self.assertIn('"push"', workflow)
        self.assertIn('refs/heads/main', workflow)
        self.assertNotIn("schedule:", workflow)

    def test_restart_map_requires_verified_learning_index_before_substantive_work(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("CURRENT_LESSONS.json", agents)
        self.assertIn("zb-archive-v1", agents)
        self.assertIn("verified lessons", agents.lower())
        self.assertIn("fresher", agents.lower())
        self.assertIn("evidence", agents.lower())

    def test_restart_map_consumes_only_accepted_optimized_policy(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("CURRENT_OPTIMIZED_POLICY.json", agents)
        self.assertIn("accepted = true", agents.lower())
        self.assertIn("BASELINE_KEPT", agents)
        self.assertIn("IMPROVED", agents)
        self.assertIn("CONFLICT", agents)
        self.assertIn("do not apply", agents.lower())
        self.assertIn("CURRENT_LESSONS.json", agents)


if __name__ == "__main__":
    unittest.main()
