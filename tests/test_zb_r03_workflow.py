from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "zb-r03-production-router.yml"


class R03ProductionWorkflowTests(unittest.TestCase):
    def workflow(self) -> str:
        if not WORKFLOW.is_file():
            self.fail("R03_PRODUCTION_WORKFLOW_MISSING")
        return WORKFLOW.read_text(encoding="utf-8")

    def test_has_only_event_driven_bus_and_internal_dispatch_triggers(self):
        text = self.workflow()
        self.assertIn("issue_comment:", text)
        self.assertIn("types: [created]", text)
        self.assertIn("repository_dispatch:", text)
        self.assertIn("types: [zb-r03-execute]", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("workflow_dispatch:", text)
        self.assertNotIn("pull_request_target:", text)

    def test_root_admission_is_exact_pr111_actor_marker_and_writes_dispatch_before_api_handoff(self):
        text = self.workflow()
        self.assertIn("github.event.issue.number == 111", text)
        self.assertIn("github.event.issue.pull_request", text)
        self.assertIn("github.event.comment.user.login == 'Lester-Sparx'", text)
        self.assertIn("startsWith(github.event.comment.body, 'ZB_AGENT_TASK_R03_V1')", text)
        self.assertIn("admit_r03_event", text)
        self.assertIn("ZB_R03_DISPATCH_V1", text)
        self.assertIn("STATE = DISPATCHED", text)
        self.assertIn("/repos/Lester-Sparx/zorr-blatt-shared-hq/dispatches", text)
        self.assertIn('"event_type":"zb-r03-execute"', text)

    def test_repository_dispatch_handoff_uses_no_pat_and_is_payload_bounded(self):
        text = self.workflow()
        self.assertIn("contents: write", text)
        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", text)
        self.assertNotIn("COPILOT_GITHUB_TOKEN", text)
        self.assertNotIn("GH_AW_CI_TRIGGER_TOKEN", text)
        self.assertNotIn("secrets: inherit", text)
        for token in (
            "root_comment_id",
            "message_id",
            "correlation_id",
            "task_id",
            "task_revision",
            "base_sha",
            "task_spec_comment_id",
            "task_spec_sha256",
            "replay_key",
        ):
            self.assertIn(token, text)

    def test_execution_run_revalidates_remote_authority_before_lester(self):
        text = self.workflow()
        self.assertIn("revalidate_r03_repository_dispatch", text)
        self.assertIn("github.event_name == 'repository_dispatch'", text)
        self.assertIn("github.event.action == 'zb-r03-execute'", text)
        self.assertIn("dispatch_ready", text)
        self.assertIn("needs.revalidate.outputs.dispatch_ready == 'true'", text)

    def test_lester_is_reusable_lock_only_on_repository_dispatch_and_receives_exact_bindings(self):
        text = self.workflow()
        self.assertIn("uses: ./.github/workflows/zb-r03-lester-agent.lock.yml", text)
        self.assertIn("message-id: ${{ needs.revalidate.outputs.message_id }}", text)
        self.assertIn("base-sha: ${{ needs.revalidate.outputs.base_sha }}", text)
        self.assertIn("task-spec-b64: ${{ needs.revalidate.outputs.task_spec_b64 }}", text)
        self.assertIn("candidate_pr_number: ${{ needs.lester.outputs.created_pr_number }}", text)
        self.assertNotIn("uses: ./.github/workflows/zb-r03-lester-agent.md", text)

    def test_duncan_and_finalize_are_downstream_same_execution_run(self):
        text = self.workflow()
        self.assertIn("duncan_qc:", text)
        self.assertIn("needs: [revalidate, lester]", text)
        self.assertIn("finalize:", text)
        self.assertIn("needs: [revalidate, lester, duncan_qc]", text)
        self.assertIn("needs.lester.outputs.created_pr_number", text)
        self.assertIn("PRODUCTION_ACTIVE = NO", text)


if __name__ == "__main__":
    unittest.main()
