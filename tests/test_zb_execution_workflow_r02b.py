from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "zb-communication-r02b.yml"
R01_WORKFLOW = ROOT / ".github" / "workflows" / "zb-communication-base.yml"

CHECKOUT = "11d5960a326750d5838078e36cf38b85af677262"
UPLOAD = "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
DOWNLOAD = "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c"
DESIGN_HEAD = "2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8"
TASK_SHA256 = "27c0cd248c12cba03d8958d954a3df981c900be885ec9ce5f6a3cdc4e9a19316"


def section(text: str, name: str, next_name: str | None) -> str:
    start = text.index(f"  {name}:\n")
    if next_name is None:
        return text[start:]
    return text[start:text.index(f"  {next_name}:\n", start + 1)]


class R02BWorkflowTests(unittest.TestCase):
    def test_r02b_is_separate_hosted_four_job_pipeline(self) -> None:
        self.assertTrue(WORKFLOW.is_file())
        text = WORKFLOW.read_text(encoding="utf-8")
        for name in ("admit", "lester_execute", "duncan_qc", "finalize"):
            self.assertIn(f"  {name}:\n", text)
        lester = section(text, "lester_execute", "duncan_qc")
        duncan = section(text, "duncan_qc", "finalize")
        self.assertIn("runs-on: windows-2025", lester)
        self.assertIn("runs-on: windows-2025", duncan)
        self.assertNotIn("self-hosted", text)
        self.assertIn("needs: admit", lester)
        self.assertIn("needs: [admit, lester_execute]", duncan)
        self.assertIn("needs: [admit, lester_execute, duncan_qc]", section(text, "finalize", None))

    def test_event_gate_is_exact_r02b_authority_and_r01_ignores_revision_two(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("issue_comment:", text)
        self.assertIn("types: [created]", text)
        self.assertIn("TASK_REVISION = 2", text)
        self.assertIn(DESIGN_HEAD, text)
        self.assertIn("Lester-Sparx", text)
        self.assertIn("scripts.zb_communication_r02b", text)
        r01 = R01_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("TASK_REVISION = 1", r01)

    def test_only_lester_receives_pat_and_no_workflow_token_write_escalation(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        admit = section(text, "admit", "lester_execute")
        lester = section(text, "lester_execute", "duncan_qc")
        duncan = section(text, "duncan_qc", "finalize")
        finalize = section(text, "finalize", None)
        secret_line = "COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT_GITHUB_TOKEN }}"
        self.assertIn(secret_line, lester)
        self.assertNotIn("COPILOT_GITHUB_TOKEN", admit)
        self.assertNotIn("COPILOT_GITHUB_TOKEN", duncan)
        self.assertNotIn("COPILOT_GITHUB_TOKEN", finalize)
        self.assertEqual(text.count("COPILOT_GITHUB_TOKEN"), 1)
        self.assertNotIn("copilot-requests: write", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("pull-requests: write", text)
        self.assertNotIn("GH_TOKEN", text)
        self.assertNotIn("GITHUB_PAT", text)

    def test_exact_toolchain_and_pinned_artifact_actions(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertGreaterEqual(text.count(f"actions/checkout@{CHECKOUT}"), 4)
        self.assertGreaterEqual(text.count(f"actions/upload-artifact@{UPLOAD}"), 3)
        self.assertGreaterEqual(text.count(f"actions/download-artifact@{DOWNLOAD}"), 4)
        self.assertGreaterEqual(text.count("persist-credentials: false"), 4)
        self.assertIn("@github/copilot@1.0.80", text)
        self.assertIn("task_windows_amd64.zip", text)
        self.assertIn(TASK_SHA256, text)
        self.assertIn("LESTER_IMPLEMENT_R02A", text)
        self.assertIn("task zb:exec:lester:implement-r02a", text)
        self.assertIn("task zb:exec:duncan:qc-r01", text)
        self.assertIn("github-actions:github-hosted:windows-2025", text)

    def test_artifact_and_terminal_failure_flow_remain_fail_closed(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        finalize = section(text, "finalize", None)
        self.assertIn("always()", finalize.split("steps:\n", 1)[0])
        self.assertIn("Verify immutable artifact metadata", finalize)
        self.assertIn("verify_artifact_metadata", finalize)
        self.assertIn("Record failed execution pipeline", finalize)
        self.assertIn("finalize_substantive_execution", finalize)
        self.assertIn("artifact-id", text)
        self.assertIn("artifact-digest", text)
        self.assertIn("if-no-files-found: error", text)
        self.assertIn("PRODUCTION_ACTIVE = NO", (ROOT / "scripts" / "zb_communication_r02b.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
