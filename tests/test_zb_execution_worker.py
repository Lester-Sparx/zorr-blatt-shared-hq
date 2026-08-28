from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from scripts.zb_execution_contract import parse_execution_request
from scripts.zb_execution_worker import OpenCodeWorker, WorkerError
from scripts.zb_execution_workspace import Completed


BASE_SHA = "0123456789abcdef0123456789abcdef01234567"
DESIGN_HEAD = "89abcdef0123456789abcdef0123456789abcdef"


def request_body() -> str:
    fields = {
        "EXECUTION_REQUEST_ID": "exec-request-worker-001",
        "MESSAGE_ID": "message-worker-001",
        "EVENT_ID": "event-worker-001",
        "CORRELATION_ID": "corr-worker-001",
        "CAUSATION_MESSAGE_ID": "cause-worker-001",
        "TASK_ID": "ZB_EXECUTION_PROOF_R01",
        "TASK_REVISION": "1",
        "LOGICAL_ROLE": "LESTER",
        "EXECUTION_PROFILE": "LESTER_IMPLEMENT_R01",
        "EXECUTION_PROFILE_VERSION": "1",
        "BASE_SHA": BASE_SHA,
        "AUTHORITY_REF": "issue:106:comment:5453724500",
        "DESIGN_HEAD": DESIGN_HEAD,
        "SOURCE_REFS": "issue:106;pr:122",
        "EVIDENCE_INPUT_REFS": "spec:120;plan:121",
        "ALLOWED_WRITE_SCOPE": "scripts/;tests/",
        "TIMEOUT_SECONDS": "900",
        "NO_AUTO_MERGE": "TRUE",
        "PRODUCTION_ACTIVE": "NO",
    }
    return "ZB_EXECUTION_REQUEST_V1\n" + "\n".join(f"{key} = {value}" for key, value in fields.items()) + "\n"


class FakeCommand:
    def __init__(self, results: list[Completed]):
        self.results = list(results)
        self.calls: list[dict[str, object]] = []

    def run(self, argv, *, cwd=None, timeout=None, env=None):
        self.calls.append({"argv": tuple(argv), "cwd": cwd, "timeout": timeout, "env": dict(env or {})})
        if not self.results:
            raise AssertionError("unexpected command")
        return self.results.pop(0)


def completed(argv: tuple[str, ...], *, code: int = 0, stdout: str = "", stderr: str = "") -> Completed:
    return Completed(argv=argv, returncode=code, stdout=stdout, stderr=stderr)


class OpenCodeWorkerTests(unittest.TestCase):
    def test_execute_uses_documented_static_argv_cwd_and_deterministic_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            worktree = Path(tmp) / "worktree"
            worktree.mkdir()
            config = Path(tmp) / "opencode-r01.json"
            config.write_text("{}\n", encoding="utf-8")
            fake = FakeCommand([
                completed(("opencode", "--version"), stdout="1.18.17\n"),
                completed(("opencode", "run"), stdout='{"type":"step"}\n'),
            ])
            worker = OpenCodeWorker(command=fake, config_path=config)
            outcome = worker.execute(parse_execution_request(request_body()), worktree=worktree, timeout_seconds=123)

            self.assertEqual(outcome.exit_code, 0)
            self.assertFalse(outcome.timed_out)
            self.assertEqual(outcome.stdout, '{"type":"step"}\n')
            self.assertEqual(len(fake.calls), 2)
            self.assertEqual(fake.calls[0]["argv"], ("opencode", "--version"))
            argv = fake.calls[1]["argv"]
            self.assertEqual(argv[:6], ("opencode", "run", "--format", "json", "--agent", "build"))
            self.assertEqual(len(argv), 7)
            self.assertNotIn("--auto", argv)
            self.assertNotIn("--pure", argv)
            self.assertNotIn("--dir", argv)
            prompt = argv[-1]
            self.assertIn("TASK_ID=ZB_EXECUTION_PROOF_R01", prompt)
            self.assertIn(f"BASE_SHA={BASE_SHA}", prompt)
            self.assertIn("ALLOWED_WRITE_SCOPE=scripts/;tests/", prompt)
            self.assertIn("DO NOT commit", prompt)
            self.assertIn("DO NOT push", prompt)
            self.assertIn("DO NOT merge", prompt)
            self.assertEqual(fake.calls[1]["cwd"], worktree)
            self.assertEqual(fake.calls[1]["timeout"], 123)

    def test_worker_strips_github_credentials_and_sets_static_policy_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            worktree = Path(tmp) / "worktree"
            worktree.mkdir()
            config = Path(tmp) / "policy.json"
            config.write_text("{}\n", encoding="utf-8")
            fake = FakeCommand([
                completed(("opencode", "--version"), stdout="1.18.17\n"),
                completed(("opencode", "run")),
            ])
            old = {key: os.environ.get(key) for key in (
                "GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_URL", "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "GITHUB_PAT"
            )}
            try:
                for key in old:
                    os.environ[key] = "secret"
                OpenCodeWorker(command=fake, config_path=config).execute(
                    parse_execution_request(request_body()), worktree=worktree, timeout_seconds=30
                )
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

            env = fake.calls[1]["env"]
            for key in old:
                self.assertNotIn(key, env)
            self.assertEqual(env["OPENCODE_CONFIG"], str(config.resolve()))
            self.assertEqual(env["OPENCODE_DISABLE_AUTOUPDATE"], "true")
            self.assertEqual(env["OPENCODE_AUTO_SHARE"], "false")

    def test_version_mismatch_is_rejected_before_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            worktree = Path(tmp) / "worktree"
            worktree.mkdir()
            config = Path(tmp) / "policy.json"
            config.write_text("{}\n", encoding="utf-8")
            fake = FakeCommand([completed(("opencode", "--version"), stdout="1.18.16\n")])
            with self.assertRaisesRegex(WorkerError, "OPENCODE_VERSION_MISMATCH"):
                OpenCodeWorker(command=fake, config_path=config).execute(
                    parse_execution_request(request_body()), worktree=worktree, timeout_seconds=30
                )
            self.assertEqual(len(fake.calls), 1)

    def test_project_opencode_config_sources_are_blocked(self) -> None:
        for relative in ("opencode.json", "opencode.jsonc", ".opencode"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as tmp:
                worktree = Path(tmp) / "worktree"
                worktree.mkdir()
                target = worktree / relative
                if relative == ".opencode":
                    target.mkdir()
                else:
                    target.write_text("{}\n", encoding="utf-8")
                config = Path(tmp) / "policy.json"
                config.write_text("{}\n", encoding="utf-8")
                fake = FakeCommand([])
                with self.assertRaisesRegex(WorkerError, "PROJECT_OPENCODE_CONFIG_PRESENT"):
                    OpenCodeWorker(command=fake, config_path=config).execute(
                        parse_execution_request(request_body()), worktree=worktree, timeout_seconds=30
                    )
                self.assertEqual(fake.calls, [])

    def test_nonzero_exit_is_preserved_and_json_stream_is_only_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            worktree = Path(tmp) / "worktree"
            worktree.mkdir()
            config = Path(tmp) / "policy.json"
            config.write_text("{}\n", encoding="utf-8")
            fake = FakeCommand([
                completed(("opencode", "--version"), stdout="1.18.17\n"),
                completed(("opencode", "run"), code=7, stdout="{incomplete-json\n", stderr="worker failed\n"),
            ])
            outcome = OpenCodeWorker(command=fake, config_path=config).execute(
                parse_execution_request(request_body()), worktree=worktree, timeout_seconds=55
            )
            self.assertEqual(outcome.exit_code, 7)
            self.assertEqual(outcome.stdout, "{incomplete-json\n")
            self.assertEqual(outcome.stderr, "worker failed\n")
            self.assertFalse(outcome.timed_out)

    def test_timeout_from_command_runner_maps_to_timed_out_outcome(self) -> None:
        class TimeoutCommand:
            def __init__(self):
                self.calls = 0
            def run(self, argv, *, cwd=None, timeout=None, env=None):
                self.calls += 1
                if self.calls == 1:
                    return completed(tuple(argv), stdout="1.18.17\n")
                raise TimeoutError("timeout")

        with tempfile.TemporaryDirectory() as tmp:
            worktree = Path(tmp) / "worktree"
            worktree.mkdir()
            config = Path(tmp) / "policy.json"
            config.write_text("{}\n", encoding="utf-8")
            outcome = OpenCodeWorker(command=TimeoutCommand(), config_path=config).execute(
                parse_execution_request(request_body()), worktree=worktree, timeout_seconds=1
            )
            self.assertTrue(outcome.timed_out)
            self.assertNotEqual(outcome.exit_code, 0)

    def test_repository_policy_file_is_deny_by_default_and_has_no_network_or_subagent_permission(self) -> None:
        root = Path(__file__).resolve().parents[1]
        policy = json.loads((root / "config/zb-execution/opencode-r01.json").read_text(encoding="utf-8"))
        permission = policy["permission"]
        self.assertEqual(permission["*"], "deny")
        self.assertEqual(permission["external_directory"], "deny")
        self.assertEqual(permission["webfetch"], "deny")
        self.assertEqual(permission["websearch"], "deny")
        self.assertEqual(permission["task"], "deny")
        self.assertEqual(permission["question"], "deny")
        self.assertEqual(permission["edit"]["*"], "allow")
        self.assertEqual(permission["bash"]["*"], "deny")
        self.assertEqual(permission["bash"]["git push *"], "deny")
        self.assertEqual(permission["bash"]["git commit *"], "deny")


if __name__ == "__main__":
    unittest.main()
