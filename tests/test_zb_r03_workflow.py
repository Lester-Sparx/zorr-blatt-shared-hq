from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "zb-r03-production-router.yml"
LIVE_CALLER = ROOT / ".github" / "workflows" / "zb-r03-lester-live-caller.yml"


class R03ProductionWorkflowRetirementTests(unittest.TestCase):
    def workflow(self) -> str:
        if not WORKFLOW.is_file():
            self.fail("R03_PRODUCTION_WORKFLOW_MISSING")
        return WORKFLOW.read_text(encoding="utf-8")

    def test_old_r03_copilot_path_is_not_event_triggered(self):
        text = self.workflow()
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("issue_comment:", text)
        self.assertNotIn("repository_dispatch:", text)
        self.assertNotIn("schedule:", text)

    def test_old_r03_copilot_and_lester_executor_are_out_of_critical_path(self):
        text = self.workflow()
        self.assertIn("R03_RETIRED_FROM_AUTOMATION", text)
        self.assertNotIn("zb-r03-lester-agent.lock.yml", text)
        self.assertNotIn("COPILOT_GITHUB_TOKEN", text)
        self.assertNotIn("needs.lester", text)
        self.assertNotIn("gh-aw", text.lower())


class R03LesterLiveCallerTests(unittest.TestCase):
    def workflow(self) -> str:
        if not LIVE_CALLER.is_file():
            self.fail("R03_LESTER_LIVE_CALLER_MISSING")
        return LIVE_CALLER.read_text(encoding="utf-8")

    def test_exact_pr_comment_event_is_the_only_trigger(self):
        text = self.workflow()
        self.assertIn("issue_comment:", text)
        self.assertIn("types: [created]", text)
        self.assertNotIn("repository_dispatch:", text)
        self.assertNotIn("workflow_dispatch:", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("github.event.issue.number == 111", text)
        self.assertIn("github.event.issue.pull_request", text)
        self.assertIn("github.event.comment.user.login == 'Lester-Sparx'", text)
        self.assertIn("startsWith(github.event.comment.body, 'ZB_AGENT_TASK_R03_V1')", text)

    def test_admission_reuses_existing_router_and_persists_before_execution(self):
        text = self.workflow()
        self.assertIn("from scripts.zb_r03_router import admit_r03_event, render_dispatch_record", text)
        self.assertIn("dispatch = admit_r03_event(event, expected_base_sha=current_main, port=api)", text)
        self.assertIn("write_and_verify(api, record)", text)
        self.assertIn("dispatch_ready=true", text)
        self.assertLess(text.index("write_and_verify(api, record)"), text.index("dispatch_ready=true"))

    def test_separate_read_only_revalidation_is_mandatory_before_lester(self):
        text = self.workflow()
        self.assertIn("  revalidate:", text)
        self.assertIn("revalidate_r03_repository_dispatch", text)
        self.assertIn("dispatch = revalidate_r03_repository_dispatch(payload, port=api)", text)
        self.assertIn("if current_main != payload[\"base_sha\"]:", text)
        self.assertIn("raise SystemExit(\"R03_MAIN_MOVED_BEFORE_LESTER\")", text)
        self.assertIn("permissions:\\n      contents: read\\n      issues: read\\n      pull-requests: read", text)

    def test_lester_consumes_only_fresh_revalidated_bindings(self):
        text = self.workflow()
        lester = text[text.index("  lester:"):]
        self.assertIn("needs: revalidate", lester)
        self.assertIn("if: needs.revalidate.outputs.dispatch_ready == 'true'", lester)
        for binding in (
            "message-id: ${{ needs.revalidate.outputs.message_id }}",
            "correlation-id: ${{ needs.revalidate.outputs.correlation_id }}",
            "task-id: ${{ needs.revalidate.outputs.task_id }}",
            "task-revision: ${{ needs.revalidate.outputs.task_revision }}",
            "base-sha: ${{ needs.revalidate.outputs.base_sha }}",
            "authority-ref: ${{ needs.revalidate.outputs.authority_ref }}",
            "task-spec-b64: ${{ needs.revalidate.outputs.task_spec_b64 }}",
        ):
            self.assertIn(binding, lester)
        self.assertNotIn("needs.admit.outputs", lester)

    def test_caller_cannot_merge_finalize_or_mutate_production(self):
        text = self.workflow()
        self.assertNotIn("merge-pull-request", text)
        self.assertNotIn("enable-auto-merge", text)
        self.assertNotIn("zb_r03_finalize", text)
        self.assertNotIn("duncan_qc:", text)
        self.assertNotIn("PRODUCTION_ACTIVE=YES", text)
        self.assertNotIn("secrets: inherit", text)
        self.assertIn("COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT_GITHUB_TOKEN }}", text)


if __name__ == "__main__":
    unittest.main()
