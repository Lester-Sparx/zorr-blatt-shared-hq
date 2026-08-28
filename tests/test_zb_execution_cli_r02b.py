from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import scripts.zb_execution_cli as execution_cli
import scripts.zb_execution_r02b_cli as r02b_cli
from scripts.zb_execution_profiles import PROFILES
from scripts.zb_execution_worker import AUTH_ENV_KEYS, WorkerError
from scripts.zb_execution_workspace import Completed


class FakeCommand:
    def __init__(self):
        self.calls: list[dict[str, object]] = []

    def run(self, argv, *, cwd=None, timeout=None, env=None):
        self.calls.append({"argv": tuple(argv), "cwd": cwd, "timeout": timeout, "env": None if env is None else dict(env)})
        return Completed(tuple(argv), 0, "ok\n", "")


class R02BCliBoundaryTests(unittest.TestCase):
    def test_worker_factory_selects_backend_only_from_static_profile(self) -> None:
        factory = getattr(execution_cli, "build_execution_worker", None)
        self.assertIsNotNone(factory, "build_execution_worker must exist")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            command = FakeCommand()
            r02b = factory(
                PROFILES["LESTER_IMPLEMENT_R02A"],
                command=command,
                workspace_root=root,
                job_root=root / "job-r02b",
                copilot_token="personal-token",
            )
            self.assertEqual(type(r02b).__name__, "CopilotWorker")

            r01 = factory(
                PROFILES["LESTER_IMPLEMENT_R01"],
                command=command,
                workspace_root=root,
                job_root=root / "job-r01",
                copilot_token="",
            )
            self.assertEqual(type(r01).__name__, "OpenCodeWorker")

            with self.assertRaisesRegex(WorkerError, "WORKER_BACKEND_REJECTED"):
                factory(
                    PROFILES["DUNCAN_QC_R01"],
                    command=command,
                    workspace_root=root,
                    job_root=root / "job-duncan",
                    copilot_token="personal-token",
                )

    def test_copilot_token_is_captured_once_then_all_auth_is_removed_from_parent_env(self) -> None:
        capture = getattr(execution_cli, "capture_copilot_token_and_scrub", None)
        self.assertIsNotNone(capture, "capture_copilot_token_and_scrub must exist")
        env = {key: "ambient-secret" for key in AUTH_ENV_KEYS}
        env["COPILOT_GITHUB_TOKEN"] = "personal-token"
        env["KEEP_ME"] = "safe"
        token = capture(env)
        self.assertEqual(token, "personal-token")
        for key in AUTH_ENV_KEYS:
            self.assertNotIn(key, env)
        self.assertEqual(env["KEEP_ME"], "safe")

    def test_trusted_verification_receives_explicit_sanitized_environment(self) -> None:
        command = FakeCommand()
        old = {key: os.environ.get(key) for key in AUTH_ENV_KEYS}
        try:
            for key in AUTH_ENV_KEYS:
                os.environ[key] = "ambient-secret"
            ok, _ = execution_cli._run_verification_commands(
                Path.cwd(),
                (("python", "-c", "print('ok')"),),
                command,
            )
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        self.assertTrue(ok)
        self.assertEqual(len(command.calls), 1)
        child_env = command.calls[0]["env"]
        self.assertIsNotNone(child_env)
        for key in AUTH_ENV_KEYS:
            self.assertNotIn(key, child_env)

    def test_r02b_main_keeps_evidence_in_workspace_but_places_worktree_under_runner_temp(self) -> None:
        request_body = """ZB_EXECUTION_REQUEST_V1
EXECUTION_REQUEST_ID = zb-r02b-live-test-lester
MESSAGE_ID = zb-r02b-live-test
EVENT_ID = zb-event-test
CORRELATION_ID = zb-corr-test
CAUSATION_MESSAGE_ID = zb-r02b-live-test
TASK_ID = ZB_EXECUTION_PROOF_R01
TASK_REVISION = 2
LOGICAL_ROLE = LESTER
EXECUTION_PROFILE = LESTER_IMPLEMENT_R02A
EXECUTION_PROFILE_VERSION = 1
BASE_SHA = 50a38c73bbff042ea29039d3cbf8fe35b25f7f52
AUTHORITY_REF = pr:111:comment:1
DESIGN_HEAD = 2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8
SOURCE_REFS = pr:111;source-comment:1;pr:123;pr:124;pr:125
EVIDENCE_INPUT_REFS = spec:123;plan:124;implementation:125
ALLOWED_WRITE_SCOPE = tests/fixtures/zb-execution-proof/
TIMEOUT_SECONDS = 600
NO_AUTO_MERGE = TRUE
PRODUCTION_ACTIVE = NO
"""
        with tempfile.TemporaryDirectory() as workspace_tmp, tempfile.TemporaryDirectory() as runner_tmp:
            workspace = Path(workspace_tmp).resolve()
            runner_temp = Path(runner_tmp).resolve()
            request_path = workspace / ".zb-exec" / "request" / "request.txt"
            result_path = workspace / ".zb-exec" / "lester" / "evidence" / "result.txt"
            evidence_dir = result_path.parent
            request_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_dir.mkdir(parents=True, exist_ok=True)
            request_path.write_text(request_body, encoding="utf-8")
            captured: dict[str, object] = {}

            def fake_run_lester(*args, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(terminal_state="PASS")

            env = {
                "GITHUB_WORKSPACE": str(workspace),
                "RUNNER_TEMP": str(runner_temp),
                "ZB_EXECUTION_REQUEST_PATH": str(request_path),
                "ZB_EXECUTION_RESULT_PATH": str(result_path),
                "ZB_EVIDENCE_DIR": str(evidence_dir),
                "ZB_EXECUTION_ID": "github-actions:123:1:lester_execute",
                "ZB_WORKFLOW_RUN_ID": "123",
                "ZB_WORKFLOW_RUN_ATTEMPT": "1",
                "ZB_RUNNER_PROVENANCE": "github-actions:github-hosted:windows-2025",
                "COPILOT_GITHUB_TOKEN": "personal-token",
            }
            with patch.dict(os.environ, env, clear=True), patch.object(
                r02b_cli,
                "build_execution_worker",
                return_value=object(),
            ), patch.object(
                r02b_cli,
                "run_lester_execution",
                side_effect=fake_run_lester,
            ), patch.object(
                r02b_cli,
                "render_execution_result",
                return_value="PASS\n",
            ):
                self.assertEqual(r02b_cli.main(["execute", "--from-env"]), 0)

            self.assertEqual(captured["job_root"], evidence_dir.parent)
            self.assertIn("worktree_root", captured, "R02B must pass an external worktree root")
            expected_worktree_root = runner_temp / "zb-r02b-123-1"
            self.assertEqual(captured["worktree_root"], expected_worktree_root)
            self.assertNotEqual(captured["worktree_root"], captured["job_root"])
            self.assertNotIn(workspace, expected_worktree_root.parents)


if __name__ == "__main__":
    unittest.main()
