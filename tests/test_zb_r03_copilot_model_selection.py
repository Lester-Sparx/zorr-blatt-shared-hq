from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".github" / "workflows" / "zb-r03-lester-agent.md"
LOCK = ROOT / ".github" / "workflows" / "zb-r03-lester-agent.lock.yml"


class R03CopilotModelSelectionTests(unittest.TestCase):
    def test_source_uses_provider_scoped_native_copilot_auto(self):
        source = SOURCE.read_text(encoding="utf-8")
        frontmatter = source.split("---", 2)[1]
        self.assertIn("engine: copilot", frontmatter)
        self.assertIn("model: copilot/auto", frontmatter)
        self.assertIn("\nmodels:\n", frontmatter)
        self.assertIn("default-ai-credits-pricing:", frontmatter)
        self.assertIn("input: 3.0", frontmatter)
        self.assertIn("output: 15.0", frontmatter)
        self.assertIn("strict: true", frontmatter)

    def test_compiled_lock_passes_provider_scoped_auto_to_gh_aw_harness(self):
        lock = LOCK.read_text(encoding="utf-8")
        metadata = lock.splitlines()[0]
        self.assertIn('"agent_model":"copilot/auto"', metadata)
        self.assertIn("COPILOT_MODEL: copilot/auto", lock)

    def test_provider_scoped_token_bypasses_builtin_auto_alias_key(self):
        lock = LOCK.read_text(encoding="utf-8")
        self.assertIn('\\"auto\\":[\\"copilot/auto\\",\\"large\\"]', lock)
        self.assertNotIn('COPILOT_MODEL: auto\n', lock)


if __name__ == "__main__":
    unittest.main()
