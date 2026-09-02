from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class LegacyExecutionIngressRetirementTests(unittest.TestCase):
    def test_base_compatibility_ingress_is_hard_disabled(self) -> None:
        text = (WORKFLOWS / "zb-communication-base.yml").read_text(encoding="utf-8")
        self.assertIn("LEGACY_EXECUTION_ROUTE_RETIRED", text)
        self.assertIn("if: ${{ false }}", text)
        self.assertNotIn("runs-on: [self-hosted", text)
        self.assertNotIn("runs-on: windows-2025", text)
        self.assertNotIn("task zb:exec:", text)
        self.assertNotIn("COPILOT_GITHUB_TOKEN: ${{ secrets.", text)

    def test_r02b_ingresses_are_manual_only_retired_stubs(self) -> None:
        for name in ("zb-communication-r02b.yml", "zb-communication-r02b-v2.yml"):
            with self.subTest(workflow=name):
                text = (WORKFLOWS / name).read_text(encoding="utf-8")
                self.assertIn("LEGACY_EXECUTION_ROUTE_RETIRED", text)
                self.assertIn("workflow_dispatch:", text)
                self.assertNotIn("issue_comment:", text)
                self.assertNotIn("runs-on: windows-2025", text)
                self.assertNotIn("self-hosted", text)
                self.assertNotIn("COPILOT_GITHUB_TOKEN", text)
                self.assertNotIn("task zb:exec:", text)
                self.assertNotIn("secrets.", text)

    def test_gh_aw_lester_executor_toolchain_is_absent(self) -> None:
        for relative in (
            ".github/workflows/zb-r03-lester-agent.md",
            ".github/workflows/zb-r03-lester-agent.lock.yml",
            ".github/workflows/zb-r03-gh-aw-compile.yml",
            ".github/actionlint.yaml",
        ):
            with self.subTest(path=relative):
                self.assertFalse((ROOT / relative).exists())

    def test_retirement_router_remains_non_event_triggered(self) -> None:
        text = (WORKFLOWS / "zb-r03-production-router.yml").read_text(encoding="utf-8")
        self.assertIn("R03_RETIRED_FROM_AUTOMATION", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("issue_comment:", text)
        self.assertNotIn("repository_dispatch:", text)
        self.assertNotIn("schedule:", text)


if __name__ == "__main__":
    unittest.main()
