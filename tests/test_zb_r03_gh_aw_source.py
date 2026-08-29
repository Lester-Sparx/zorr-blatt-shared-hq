from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".github" / "workflows" / "zb-r03-lester-agent.md"
COMPILE_WORKFLOW = ROOT / ".github" / "workflows" / "zb-r03-gh-aw-compile.yml"
LOCK = ROOT / ".github" / "workflows" / "zb-r03-lester-agent.lock.yml"


class R03GhAwSourceTests(unittest.TestCase):
    def source(self) -> str:
        if not SOURCE.is_file():
            self.fail("R03_GH_AW_SOURCE_MISSING")
        return SOURCE.read_text(encoding="utf-8")

    def test_source_is_reusable_strict_copilot_only(self):
        text = self.source()
        self.assertIn("workflow_call:", text)
        self.assertIn("engine: copilot", text)
        self.assertIn("model: auto", text)
        self.assertIn("strict: true", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("issue_comment:", text)
        self.assertNotIn("pull_request:", text)

    def test_checkout_is_pinned_to_exact_authorized_base_not_pr_context(self):
        text = self.source()
        self.assertIn("checkout:", text)
        self.assertIn("repository: ${{ github.repository }}", text)
        self.assertIn("ref: ${{ inputs.base-sha }}", text)
        self.assertIn("fetch-depth: 0", text)

    def test_agent_permissions_are_read_only_except_copilot_request(self):
        text = self.source()
        self.assertRegex(text, r"(?m)^permissions:\s*$")
        self.assertRegex(text, r"(?m)^\s{2}contents:\s*read\s*$")
        self.assertRegex(text, r"(?m)^\s{2}copilot-requests:\s*write\s*$")
        for forbidden in ("contents: write", "issues: write", "pull-requests: write", "actions: write"):
            self.assertNotIn(forbidden, text)

    def test_safe_output_is_one_draft_pr_with_no_fallback_or_auto_merge(self):
        text = self.source()
        self.assertIn("safe-outputs:", text)
        self.assertIn("create-pull-request:", text)
        self.assertIn("draft: true", text)
        self.assertIn("max: 1", text)
        self.assertIn("fallback-as-issue: false", text)
        self.assertIn("auto-close-issue: false", text)
        self.assertIn("base-branch: main", text)
        self.assertNotIn("merge-pull-request:", text)
        self.assertNotIn("github-token-for-extra-empty-commit", text)
        self.assertNotIn("GH_AW_CI_TRIGGER_TOKEN", text)

    def test_allowed_files_are_exact_exclusive_initial_profile(self):
        text = self.source()
        marker = "allowed-files:"
        self.assertIn(marker, text)
        section = text.split(marker, 1)[1].split("max-patch-files:", 1)[0]
        patterns = re.findall(r"(?m)^\s*-\s+([^#\n]+?)\s*$", section)
        self.assertEqual(patterns, ["scripts/**", "tests/**", "docs/**", "config/**"])
        self.assertNotIn(".github/**", section)
        self.assertNotIn("Taskfile.yml", section)

    def test_task_spec_is_materialized_from_env_not_interpolated_into_shell(self):
        text = self.source()
        self.assertIn("ZB_R03_TASK_SPEC_B64: ${{ inputs.task-spec-b64 }}", text)
        self.assertIn('printf \'%s\' "$ZB_R03_TASK_SPEC_B64" | base64 -d > .zb-r03/task-spec.md', text)
        run_sections = re.findall(r"(?ms)^\s+run:\s*\|\n(.*?)(?=^\s{2,}\w|^---$)", text)
        self.assertTrue(run_sections)
        self.assertTrue(all("${{ inputs.task-spec-b64 }}" not in block for block in run_sections))

    def test_prompt_requires_exact_candidate_binding_marker(self):
        text = self.source()
        for token in (
            "ZB_R03_CANDIDATE_V1",
            "MESSAGE_ID = ${{ inputs.message-id }}",
            "CORRELATION_ID = ${{ inputs.correlation-id }}",
            "TASK_ID = ${{ inputs.task-id }}",
            "TASK_REVISION = ${{ inputs.task-revision }}",
            "BASE_SHA = ${{ inputs.base-sha }}",
            "AUTHORITY_REF = ${{ inputs.authority-ref }}",
        ):
            self.assertIn(token, text)

    def test_compile_workflow_is_sha_pinned_and_read_only(self):
        if not COMPILE_WORKFLOW.is_file():
            self.skipTest("compile workflow is added after source GREEN")
        text = COMPILE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("v0.86.2/linux-amd64", text)
        self.assertIn("b8fd100d1d56a77b842ad28375ff361215a5aa1277db6b9a05d70054cde7260e", text)
        self.assertIn("compile zb-r03-lester-agent --strict", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("git push", text)
        self.assertNotIn("sync-generated-lock:", text)
        self.assertNotIn("/latest/", text)
        self.assertNotIn("curl |", text)
        self.assertNotIn("curl -sL", text)
        self.assertNotIn("pull_request_target:", text)
        self.assertNotIn("secrets: inherit", text)

    def test_compiled_lock_is_installed_and_has_exact_compiler_metadata(self):
        if not LOCK.is_file():
            self.fail("R03_GH_AW_LOCK_MISSING")
        first = LOCK.read_text(encoding="utf-8").splitlines()[0]
        self.assertIn('"compiler_version":"v0.86.2"', first)
        self.assertIn('"strict":true', first)
        self.assertIn('"agent_id":"copilot"', first)
        self.assertIn('"agent_model":"auto"', first)


if __name__ == "__main__":
    unittest.main()
