from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

from scripts.zb_execution_contract import parse_execution_request
from scripts.zb_execution_workspace import Completed


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "zb_execution_copilot.py"
BASE_SHA = "0123456789abcdef0123456789abcdef01234567"
DESIGN_HEAD = "2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8"


def request_body() -> str:
    fields = {
        "EXECUTION_REQUEST_ID": "exec-request-copilot-001",
        "MESSAGE_ID": "message-copilot-001",
        "EVENT_ID": "event-copilot-001",
        "CORRELATION_ID": "corr-copilot-001",
        "CAUSATION_MESSAGE_ID": "cause-copilot-001",
        "TASK_ID": "ZB_EXECUTION_PROOF_R01",
        "TASK_REVISION": "2",
        "LOGICAL_ROLE": "LESTER",
        "EXECUTION_PROFILE": "LESTER_IMPLEMENT_R02A",
        "EXECUTION_PROFILE_VERSION": "1",
        "BASE_SHA": BASE_SHA,
        "AUTHORITY_REF": "issue:106:r02a",
        "DESIGN_HEAD": DESIGN_HEAD,
        "SOURCE_REFS": "issue:106;pr:123",
        "EVIDENCE_INPUT_REFS": "spec:123;plan:124",
        "ALLOWED_WRITE_SCOPE": "tests/fixtures/zb-execution-proof/",
        "TIMEOUT_SECONDS": "900",
        "NO_AUTO_MERGE": "TRUE",
        "PRODUCTION_ACTIVE": "NO",
    }
    return "ZB_EXECUTION_REQUEST_V1\n" + "\n".join(f"{key} = {value}" for key, value in fields.items()) + "\n"


class FakeCommand:
    def __init__(self, results: list[Completed] | None = None, *, timeout_on_run: bool = False):
        self.results = list(results or [])
        self.timeout_on_run = timeout_on_run
        self.calls: list[dict[str, object]] = []

    def run(self, argv, *, cwd=None, timeout=None, env=None):
        self.calls.append({"argv": tuple(argv), "cwd": cwd, "timeout": timeout, "env": dict(env or {})})
        if self.timeout_on_run and len(self.calls) > 1:
            raise TimeoutError("timeout")
        if not self.results:
            raise AssertionError("unexpected command")
        return self.results.pop(0)


def completed(argv: tuple[str, ...], *, code: int = 0, stdout: str = "", stderr: str = "") -> Completed:
    return Completed(argv=argv, returncode=code, stdout=stdout, stderr=stderr)


def load_copilot_worker():
    if not MODULE.is_file():
        raise AssertionError("scripts/zb_execution_copilot.py must exist")
    spec = importlib.util.spec_from_file_location("zb_execution_copilot_under_test", MODULE)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load Copilot worker module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CopilotWorker


class CopilotWorkerTests(unittest.TestCase):
    def test_execute_uses_exact_confined_static_argv_and_process_only_token(self) -> None:
        CopilotWorker = load_copilot_worker()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktree = root / "worktree"; worktree.mkdir()
            home = root / "copilot-home"
            fake = FakeCommand([
                completed(("copilot", "--version"), stdout="GitHub Copilot CLI 1.0.80\n"),
                completed(("copilot", "-p"), stdout='{"type":"result"}\n'),
            ])
            old = {key: os.environ.get(key) for key in (
                "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "ACTIONS_ID_TOKEN_REQUEST_URL",
                "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_RESULTS_URL",
                "COPILOT_GITHUB_TOKEN", "COPILOT_PROVIDER_API_KEY", "COPILOT_PROVIDER_BASE_URL",
                "COPILOT_ALLOW_ALL", "COPILOT_MODEL",
            )}
            try:
                for key in old:
                    os.environ[key] = "ambient-secret"
                worker = CopilotWorker(command=fake, auth_token="job-scoped-token", home_path=home)
                outcome = worker.execute(parse_execution_request(request_body()), worktree=worktree, timeout_seconds=123)
            finally:
                for key, value in old.items():
                    if value is None: os.environ.pop(key, None)
                    else: os.environ[key] = value

            self.assertEqual(outcome.exit_code, 0)
            self.assertFalse(outcome.timed_out)
            self.assertEqual(fake.calls[0]["argv"], ("copilot", "--version"))
            self.assertNotIn("COPILOT_GITHUB_TOKEN", fake.calls[0]["env"])
            argv = fake.calls[1]["argv"]
            for token in (
                "--model=auto", "--no-ask-user", "--available-tools=edit,view,grep,glob",
                "--allow-tool=write", "--disable-builtin-mcps", "--no-auto-update",
                "--no-custom-instructions", "--no-experimental", "--no-remote",
                "--no-remote-export", "--disallow-temp-dir", "--output-format=json",
                "--no-color",
            ):
                self.assertIn(token, argv)
            self.assertNotIn("--no-banner", argv)
            joined = " ".join(argv).lower()
            for forbidden in ("--yolo", "--allow-all", "--allow-all-tools", "apply_patch", "bash", "powershell", "web_fetch", "task"):
                self.assertNotIn(forbidden, joined)
            env = fake.calls[1]["env"]
            self.assertEqual(env["COPILOT_GITHUB_TOKEN"], "job-scoped-token")
            self.assertEqual(env["COPILOT_HOME"], str(home.resolve()))
            for key in old:
                if key != "COPILOT_GITHUB_TOKEN":
                    self.assertNotIn(key, env)

    def test_empty_token_version_mismatch_and_home_inside_worktree_fail_closed(self) -> None:
        CopilotWorker = load_copilot_worker()
        request = parse_execution_request(request_body())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); worktree = root / "worktree"; worktree.mkdir()
            with self.assertRaisesRegex(RuntimeError, "COPILOT_TOKEN_MISSING"):
                CopilotWorker(command=FakeCommand(), auth_token="", home_path=root / "home")
            with self.assertRaisesRegex(RuntimeError, "COPILOT_HOME_INSIDE_WORKTREE"):
                CopilotWorker(command=FakeCommand(), auth_token="x", home_path=worktree / "home").execute(request, worktree=worktree, timeout_seconds=30)
            fake = FakeCommand([completed(("copilot", "--version"), stdout="1.0.79\n")])
            with self.assertRaisesRegex(RuntimeError, "COPILOT_VERSION_MISMATCH"):
                CopilotWorker(command=fake, auth_token="x", home_path=root / "home").execute(request, worktree=worktree, timeout_seconds=30)

    def test_nonzero_exit_and_timeout_preserve_terminal_worker_outcome(self) -> None:
        CopilotWorker = load_copilot_worker()
        request = parse_execution_request(request_body())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); worktree = root / "worktree"; worktree.mkdir()
            fake = FakeCommand([
                completed(("copilot", "--version"), stdout="1.0.80\n"),
                completed(("copilot", "-p"), code=7, stderr="failed\n"),
            ])
            outcome = CopilotWorker(command=fake, auth_token="x", home_path=root / "home").execute(request, worktree=worktree, timeout_seconds=30)
            self.assertEqual(outcome.exit_code, 7)
            self.assertFalse(outcome.timed_out)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); worktree = root / "worktree"; worktree.mkdir()
            fake = FakeCommand([completed(("copilot", "--version"), stdout="1.0.80\n")], timeout_on_run=True)
            outcome = CopilotWorker(command=fake, auth_token="x", home_path=root / "home").execute(request, worktree=worktree, timeout_seconds=1)
            self.assertTrue(outcome.timed_out)
            self.assertNotEqual(outcome.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
