from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".github" / "workflows" / "zb-r03-lester-agent.md"
LOCK = ROOT / ".github" / "workflows" / "zb-r03-lester-agent.lock.yml"


class R03CopilotModelSelectionTests(unittest.TestCase):
    def test_source_leaves_copilot_subscription_model_unpinned(self):
        source = SOURCE.read_text(encoding="utf-8")
        frontmatter = source.split("---", 2)[1]
        self.assertNotRegex(frontmatter, r"(?m)^model:\s*auto\s*$")

    def test_compiled_lock_does_not_pin_gh_aw_auto_alias(self):
        lock = LOCK.read_text(encoding="utf-8")
        metadata = lock.splitlines()[0]
        self.assertNotIn('"agent_model":"auto"', metadata)
        self.assertNotIn("COPILOT_MODEL: auto", lock)


if __name__ == "__main__":
    unittest.main()
