from __future__ import annotations

from pathlib import Path
import unittest


class UnifiedArchiveWorkflowTests(unittest.TestCase):
    def test_permanent_archive_runs_unified_ingest_without_new_trigger(self) -> None:
        text = Path(".github/workflows/zb-permanent-archive-v1.yml").read_text(encoding="utf-8")
        self.assertNotIn("schedule:", text)
        self.assertEqual(text.count("contents: write"), 1)
        self.assertIn("python3 source/scripts/hq_unified_archive.py ingest-event", text)
        self.assertIn('--event-path "$GITHUB_EVENT_PATH"', text)
        self.assertIn('--archive-root "$GITHUB_WORKSPACE/archive/hq/archive-v1"', text)
        self.assertIn('--event-name "$GITHUB_EVENT_NAME"', text)
        self.assertIn('--repository "$GITHUB_REPOSITORY"', text)
        self.assertIn('--actor "$GITHUB_ACTOR"', text)

    def test_agent_restart_map_names_single_unified_restore_entrypoint(self) -> None:
        text = Path("AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("hq/archive-v1/derived/unified-v1/CURRENT_CONTEXT.json", text)
        self.assertIn("derived restore state", text.lower())
        self.assertIn("exact task", text.lower())


if __name__ == "__main__":
    unittest.main()
