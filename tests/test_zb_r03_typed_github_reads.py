from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".github" / "workflows" / "zb-r03-lester-agent.md"


class R03TypedGitHubReadsTests(unittest.TestCase):
    def test_agent_uses_typed_github_mcp_for_durable_context(self):
        text = SOURCE.read_text(encoding="utf-8")
        self.assertIn("github:\n    toolsets: [default, actions]", text)
        self.assertIn("allowed-repos: current", text)
        self.assertIn("actions: read", text)
        self.assertIn("issues: read", text)
        self.assertIn("pull-requests: read", text)
        self.assertIn("Do not use a generic `fetch` tool against GitHub REST API URLs", text)
        self.assertIn("fail closed", text)


if __name__ == "__main__":
    unittest.main()
