from __future__ import annotations

import subprocess
from pathlib import Path
import tempfile
import unittest

from scripts.zb_communication_r02b import _parse_r02b_root
from scripts.zb_communication_r02b_dispatch import prepare_r02b_dispatch_once
from scripts.zb_execution_copilot import CopilotWorker
from scripts.zb_execution_contract import parse_execution_request
from scripts.zb_execution_workspace import Completed, WorkspaceError


ROOT = Path(__file__).resolve().parents[1]
TARGET = "tests/fixtures/zb-execution-proof/result.txt"
DESIGN_HEAD = "2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8"
BASE_SHA = "d" * 40


def request_body() -> str:
    return f"""ZB_EXECUTION_REQUEST_V1
EXECUTION_REQUEST_ID = req-r02b-review
MESSAGE_ID = msg-r02b-review
EVENT_ID = evt-r02b-review
CORRELATION_ID = corr-r02b-review
CAUSATION_MESSAGE_ID = msg-r02b-review
TASK_ID = ZB_EXECUTION_PROOF_R01
TASK_REVISION = 2
LOGICAL_ROLE = LESTER
EXECUTION_PROFILE = LESTER_IMPLEMENT_R02A
EXECUTION_PROFILE_VERSION = 1
BASE_SHA = {BASE_SHA}
AUTHORITY_REF = pr:111:comment:1
DESIGN_HEAD = {DESIGN_HEAD}
SOURCE_REFS = pr:111;pr:123;pr:124;pr:125
EVIDENCE_INPUT_REFS = spec:123;plan:124;implementation:125
ALLOWED_WRITE_SCOPE = tests/fixtures/zb-execution-proof/
TIMEOUT_SECONDS = 600
NO_AUTO_MERGE = TRUE
PRODUCTION_ACTIVE = NO
"""


def root_body() -> str:
    return """ZB_AGENT_MESSAGE_R02B_V1
MESSAGE_ID = msg-r02b-review
EVENT_ID = evt-r02b-review
CORRELATION_ID = corr-r02b-review
CAUSATION_MESSAGE_ID = NONE
TASK_ID = ZB_EXECUTION_PROOF_R01
FROM_ROLE = JINGO
TO_ROLE = LESTER
MESSAGE_KIND = ASSIGN
BASE_SHA = dddddddddddddddddddddddddddddddddddddddddddd
TASK_REVISION = 2
DESIGN_HEAD = 2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8
NO_AUTO_MERGE = TRUE
"""


class _ReplayPort:
    def __init__(self, body: str) -> None:
        self.body = body

    def list_tracker_comments(self):
        return [{"issue_url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106", "user": {"login": "github-actions[bot]"}, "body": self.body}]

    def create_tracker_comment(self, body: str) -> int:
        raise AssertionError("replay must not write a new request")

    def read_comment(self, comment_id: int):
        raise AssertionError("replay must not read a new comment")

    def create_console_comment(self, body: str) -> int:
        raise AssertionError("replay must not project a new console state")

    def list_console_comments(self):
        return []


class _TimeoutCommand:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, argv, *, cwd=None, timeout=None, env=None):
        self.calls += 1
        if list(argv) == ["copilot", "--version"]:
            return Completed(tuple(argv), 0, "copilot 1.0.80\n", "")
        try:
            raise subprocess.TimeoutExpired(list(argv), timeout)
        except subprocess.TimeoutExpired as exc:
            raise WorkspaceError("COMMAND_EXECUTION_ERROR") from exc


class R02BReviewFixTests(unittest.TestCase):
    def test_copilot_wrapped_timeout_is_terminal_worker_timeout(self) -> None:
        command = _TimeoutCommand()
        worker = CopilotWorker(command=command, auth_token="secret", home_path=Path(tempfile.mkdtemp()) / "copilot-home")
        with tempfile.TemporaryDirectory() as tmp:
            outcome = worker.execute(
                parse_execution_request(request_body()),
                worktree=Path(tmp),
                timeout_seconds=60,
            )
        self.assertTrue(outcome.timed_out)
        self.assertEqual(outcome.exit_code, 124)
        self.assertEqual(command.calls, 2)

    def test_replayed_r02b_request_never_unlocks_execution(self) -> None:
        root = _parse_r02b_root(root_body())
        event = {"comment": {"id": 1}}
        body = request_body()
        decision = prepare_r02b_dispatch_once(root, event, _ReplayPort(body))
        self.assertEqual(decision.state, "REQUEST_REPLAY_BLOCKED")
        self.assertIsNone(decision.request_body)

    def test_workflow_contains_replay_lock_and_independent_proof_qc(self) -> None:
        workflow = (ROOT / ".github/workflows/zb-communication-r02b.yml").read_text(encoding="utf-8")
        self.assertIn("prepare_r02b_dispatch_once", workflow)
        self.assertIn("REQUEST_REPLAY_BLOCKED", workflow)
        self.assertIn("request_ready={'true' if decision.state == 'REQUEST_NEW' else 'false'}", workflow)
        self.assertIn("Independently verify exact R02B proof edit", workflow)
        self.assertIn("verify_proof_target", workflow)
        self.assertIn("R02B_PROOF_PATCH_MISMATCH", workflow)
        self.assertIn("+STATE = AFTER", workflow)


if __name__ == "__main__":
    unittest.main()
