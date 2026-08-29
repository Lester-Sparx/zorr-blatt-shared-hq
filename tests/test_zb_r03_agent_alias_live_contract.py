from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".github" / "workflows" / "zb-r03-lester-agent.md"


class R03AgentAliasLiveContractTests(unittest.TestCase):
    def test_lester_does_not_pass_literal_copilot_auto_through_byok_proxy(self):
        source = SOURCE.read_text(encoding="utf-8")
        frontmatter = source.split("---", 2)[1]
        self.assertIn("model: agent", frontmatter)
        self.assertNotIn("model: copilot/auto", frontmatter)


if __name__ == "__main__":
    unittest.main()
