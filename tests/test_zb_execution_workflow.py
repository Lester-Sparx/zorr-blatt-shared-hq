from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "zb-communication-base.yml"
TASKFILE = ROOT / "Taskfile.yml"

CHECKOUT = "11d5960a326750d5838078e36cf38b85af677262"
UPLOAD = "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
DOWNLOAD = "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c"


def job_section(text: str, name: str, next_name: str | None) -> str:
    start = text.index(f"  {name}:\n")
    if next_name is None:
        return text[start:]
    end = text.index(f"  {next_name}:\n", start + 1)
    return text[start:end]


class ExecutionWorkflowShapeTests(unittest.TestCase):
    def test_substantive_path_has_four_trust_separated_jobs(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        for name in ("admit", "lester_execute", "duncan_qc", "finalize"):
            self.assertIn(f"  {name}:\n", text)
        self.assertNotIn("  route:\n", text)

        admit = job_section(text, "admit", "lester_execute")
        lester = job_section(text, "lester_execute", "duncan_qc")
        duncan = job_section(text, "duncan_qc", "finalize")
        finalize = job_section(text, "finalize", None)

        self.assertIn("runs-on: ubuntu-latest", admit)
        self.assertIn("runs-on: [self-hosted, Windows, X64, zorr-blatt-exec-r01]", lester)
        self.assertIn("runs-on: [self-hosted, Windows, X64, zorr-blatt-exec-r01]", duncan)
        self.assertIn("runs-on: ubuntu-latest", finalize)
        self.assertIn("github.event.repository.private == true", lester)
        self.assertIn("github.event.repository.private == true", duncan)
        self.assertIn("needs: admit", lester)
        self.assertIn("needs: [admit, lester_execute]", duncan)
        self.assertIn("needs: [admit, lester_execute, duncan_qc]", finalize)

        self.assertIn("issues: write", admit)
        self.assertNotIn("issues: write", lester)
        self.assertNotIn("issues: write", duncan)
        self.assertIn("issues: write", finalize)
        self.assertNotIn("pull-requests: write", text)
        self.assertNotIn("contents: write", text)

    def test_actions_artifacts_and_checkouts_are_exactly_pinned(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertGreaterEqual(text.count(f"actions/checkout@{CHECKOUT}"), 4)
        self.assertGreaterEqual(text.count(f"actions/upload-artifact@{UPLOAD}"), 3)
        self.assertGreaterEqual(text.count(f"actions/download-artifact@{DOWNLOAD}"), 4)
        self.assertNotIn("actions/checkout@v4", text)
        self.assertNotIn("actions/upload-artifact@v", text)
        self.assertNotIn("actions/download-artifact@v", text)
        self.assertGreaterEqual(text.count("persist-credentials: false"), 2)
        self.assertGreaterEqual(text.count("artifact-id"), 3)
        self.assertGreaterEqual(text.count("artifact-digest"), 3)
        self.assertGreaterEqual(text.count("retention-days: 7"), 3)
        self.assertGreaterEqual(text.count("if-no-files-found: error"), 3)

    def test_execution_identity_and_artifact_flow_are_static(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("github-actions:${{ github.run_id }}:${{ github.run_attempt }}:lester_execute", text)
        self.assertIn("github-actions:${{ github.run_id }}:${{ github.run_attempt }}:duncan_qc", text)
        self.assertIn("artifact-ids: ${{ needs.admit.outputs.request_artifact_id }}", text)
        self.assertIn("artifact-ids: ${{ needs.lester_execute.outputs.lester_artifact_id }}", text)
        self.assertIn("artifact-ids: ${{ needs.duncan_qc.outputs.duncan_artifact_id }}", text)
        self.assertIn("GATE = SUBSTANTIVE_EXECUTION", (ROOT / "scripts" / "zb_communication_base.py").read_text(encoding="utf-8"))

        for forbidden in (
            "pull_request_target:",
            "workflow_dispatch:",
            "schedule:",
            "secrets.",
            "GH_PAT",
            "GITHUB_PAT",
            "PERSONAL_ACCESS_TOKEN",
            "runs-on: ${{",
            "github.event.comment.body }}",
        ):
            self.assertNotIn(forbidden, text)

    def test_taskfile_uses_python_module_mode_not_script_path(self) -> None:
        text = TASKFILE.read_text(encoding="utf-8")
        self.assertIn("python -m scripts.zb_execution_cli execute --from-env", text)
        self.assertIn("python -m scripts.zb_execution_cli qc --from-env", text)
        self.assertNotIn("python scripts/zb_execution_cli.py", text)


if __name__ == "__main__":
    unittest.main()
