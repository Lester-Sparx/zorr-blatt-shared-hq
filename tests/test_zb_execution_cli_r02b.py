from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

import scripts.zb_execution_cli as execution_cli
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


if __name__ == "__main__":
    unittest.main()
