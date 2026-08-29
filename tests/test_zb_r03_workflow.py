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

    def test_root_admission_is_exact_pr111_actor_and_uses_trusted_dispatch_helpers_before_api_handoff(self):
        text = self.workflow()
        self.assertIn("github.event.issue.number == 111", text)
        self.assertIn("github.event.issue.pull_request", text)
        self.assertIn("github.event.comment.user.login == 'Lester-Sparx'", text)
        self.assertIn("startsWith(github.event.comment.body, 'ZB_AGENT_TASK_R03_V1')", text)
        self.assertIn("admit_r03_event", text)
        self.assertIn("render_dispatch_record", text)
        self.assertIn("r01.write_and_verify(api, record)", text)
        self.assertIn("dispatch_payload(dispatch, root_comment_id=root_comment_id)", text)
        self.assertIn("/repos/Lester-Sparx/zorr-blatt-shared-hq/dispatches", text)
        self.assertIn('"event_type": "zb-r03-execute"', text)

    def test_repository_dispatch_handoff_uses_no_pat_and_payload_is_built_only_by_typed_helper(self):
        text = self.workflow()
        self.assertIn("contents: write", text)
        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", text)
        self.assertIn('"client_payload": dispatch_payload(dispatch, root_comment_id=root_comment_id)', text)
        self.assertNotIn("COPILOT_GITHUB_TOKEN", text)
        self.assertNotIn("GH_AW_CI_TRIGGER_TOKEN", text)
        self.assertNotIn("secrets: inherit", text)

    def test_execution_run_revalidates_remote_authority_before_lester(self):
        text = self.workflow()
        self.assertIn("revalidate_r03_repository_dispatch", text)
        self.assertIn("github.event_name == 'repository_dispatch'", text)
        self.assertIn("github.event.action == 'zb-r03-execute'", text)
        self.assertIn("dispatch_ready", text)
        self.assertIn("needs.revalidate.outputs.dispatch_ready == 'true'", text)

    def test_revalidate_job_has_no_forward_reference_to_lester(self):
        text = self.workflow()
        revalidate = text.split("\n  revalidate:\n", 1)[1].split("\n  lester:\n", 1)[0]
        self.assertNotIn("needs.lester", revalidate)

    def test_lester_is_reusable_lock_only_on_repository_dispatch_and_receives_exact_bindings(self):
        text = self.workflow()
        self.assertIn("uses: ./.github/workflows/zb-r03-lester-agent.lock.yml", text)
        self.assertIn("message-id: ${{ needs.revalidate.outputs.message_id }}", text)
        self.assertIn("base-sha: ${{ needs.revalidate.outputs.base_sha }}", text)
        self.assertIn("task-spec-b64: ${{ needs.revalidate.outputs.task_spec_b64 }}", text)
        self.assertIn("candidate_pr_number: ${{ needs.lester.outputs.created_pr_number }}", text)
        self.assertNotIn("uses: ./.github/workflows/zb-r03-lester-agent.md", text)

    def test_duncan_is_metadata_then_exact_checkout_tests_then_fresh_record(self):
        text = self.workflow()
        duncan = text.split("\n  duncan_qc:\n", 1)[1].split("\n  finalize:\n", 1)[0]
        self.assertIn("R03_QC_PHASE: metadata", duncan)
        self.assertIn("id: metadata", duncan)
        self.assertIn("ref: ${{ steps.metadata.outputs.candidate_head_sha }}", duncan)
        self.assertIn("python3 scripts/hq_validate.py", duncan)
        self.assertIn("python3 -m unittest discover -s tests -v", duncan)
        self.assertIn("python3 -m compileall -q scripts tests", duncan)
        self.assertIn("R03_QC_PHASE: record", duncan)
        self.assertIn("R03_EXPECTED_CANDIDATE_HEAD: ${{ steps.metadata.outputs.candidate_head_sha }}", duncan)
        self.assertIn("qc_pass: ${{ steps.record.outputs.qc_pass }}", duncan)
        self.assertIn("candidate_head_sha: ${{ steps.record.outputs.candidate_head_sha }}", duncan)

    def test_duncan_and_finalize_are_downstream_same_execution_run(self):
        text = self.workflow()
        self.assertIn("duncan_qc:", text)
        self.assertIn("needs: [revalidate, lester]", text)
        self.assertIn("finalize:", text)
        self.assertIn("needs: [revalidate, lester, duncan_qc]", text)
        self.assertIn("needs.lester.outputs.created_pr_number", text)
        self.assertIn("PRODUCTION_ACTIVE: NO", text)


if __name__ == "__main__":
    unittest.main()
