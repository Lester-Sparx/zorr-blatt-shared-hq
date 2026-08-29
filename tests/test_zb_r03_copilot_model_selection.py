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

    def test_compiled_lock_does_not_pass_literal_auto_to_copilot(self):
        lock = LOCK.read_text(encoding="utf-8")
        metadata = lock.splitlines()[0]
        self.assertNotIn('"agent_model":"copilot/auto"', metadata)
        self.assertNotIn("COPILOT_MODEL: copilot/auto", lock)
        self.assertNotIn("COPILOT_MODEL: auto\n", lock)

    def test_compiled_lock_uses_a_concrete_model_not_an_alias_token(self):
        lock = LOCK.read_text(encoding="utf-8")
        self.assertNotIn("COPILOT_MODEL: agent\n", lock)
        self.assertRegex(lock, r"COPILOT_MODEL: (?:claude-|gpt-|gemini-|kimi-|mai-code-)")


if __name__ == "__main__":
    unittest.main()
