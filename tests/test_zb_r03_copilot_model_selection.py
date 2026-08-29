from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".github" / "workflows" / "zb-r03-lester-agent.md"
LOCK = ROOT / ".github" / "workflows" / "zb-r03-lester-agent.lock.yml"


class R03CopilotModelSelectionTests(unittest.TestCase):
    def test_source_preserves_native_copilot_auto_without_large_fallback(self):
        source = SOURCE.read_text(encoding="utf-8")
        frontmatter = source.split("---", 2)[1]
        self.assertIn(
            "engine: copilot\nmodel: auto\nmodels:\n  auto:\n    - copilot/auto\nstrict: true",
            frontmatter,
        )
        self.assertNotIn("    - large", frontmatter)

    def test_compiled_lock_overrides_builtin_auto_alias_without_large_fallback(self):
        lock = LOCK.read_text(encoding="utf-8")
        metadata = lock.splitlines()[0]
        self.assertIn('"agent_model":"auto"', metadata)
        self.assertIn("COPILOT_MODEL:", lock)
        self.assertIn('\\"auto\\":[\\"copilot/auto\\"]', lock)
        self.assertNotIn('\\"auto\\":[\\"copilot/auto\\",\\"large\\"]', lock)


if __name__ == "__main__":
    unittest.main()
