from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".github" / "workflows" / "zb-r03-lester-agent.md"
LOCK = ROOT / ".github" / "workflows" / "zb-r03-lester-agent.lock.yml"


class R03CopilotModelSelectionTests(unittest.TestCase):
    def test_source_uses_native_gh_aw_agent_alias(self):
        source = SOURCE.read_text(encoding="utf-8")
        frontmatter = source.split("---", 2)[1]
        self.assertIn("engine: copilot", frontmatter)
        self.assertIn("model: agent", frontmatter)
        self.assertNotIn("model: copilot/auto", frontmatter)
        self.assertIn("\nmodels:\n", frontmatter)
        self.assertIn("default-ai-credits-pricing:", frontmatter)
        self.assertIn("input: 3.0", frontmatter)
        self.assertIn("output: 15.0", frontmatter)
        self.assertIn("strict: true", frontmatter)

    def test_compiled_lock_passes_native_agent_alias_to_gh_aw_harness(self):
        lock = LOCK.read_text(encoding="utf-8")
        metadata = lock.splitlines()[0]
        self.assertIn('"agent_model":"agent"', metadata)
        self.assertIn("COPILOT_MODEL: agent", lock)
        self.assertNotIn('"agent_model":"copilot/auto"', metadata)
        self.assertNotIn("COPILOT_MODEL: copilot/auto", lock)
        self.assertNotIn("COPILOT_MODEL: auto\n", lock)

    def test_compiled_lock_contains_upstream_agent_resolution_chain(self):
        lock = LOCK.read_text(encoding="utf-8")
        self.assertIn('\\"agent\\":[\\"sonnet-6x\\",\\"gpt-5.4\\",\\"gpt-5.5\\",\\"gpt-5.6\\",\\"gpt-5.3\\",\\"gemini-pro\\",\\"any\\"]', lock)


if __name__ == "__main__":
    unittest.main()
