from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

from scripts.zb_communication_r02b import (
    CONSOLE_ISSUE_URL,
    STATE_WRITER,
    TRACKER_ISSUE_URL,
    ProtocolError,
    admit_event,
    finalize_substantive_execution,
    prepare_substantive_dispatch,
)
from scripts.zb_execution_contract import ExecutionResult, parse_execution_request, render_execution_result


BASE_SHA = "c" * 40
R02B_DESIGN_HEAD = "2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8"
R01_DESIGN_HEAD = "7bac0b6c10dda0448a8792dd3c97f8cec76bbb03"
ROOT = Path(__file__).resolve().parents[1]


def body(*, revision: int, design_head: str) -> str:
    return f"""ZB_AGENT_MESSAGE_V1
MESSAGE_ID = zb-exec-r02b-msg-001
EVENT_ID = zb-exec-r02b-evt-001
CORRELATION_ID = zb-exec-r02b
CAUSATION_MESSAGE_ID = NONE
TASK_ID = ZB_EXECUTION_PROOF_R01
FROM_ROLE = JINGO
TO_ROLE = LESTER
MESSAGE_KIND = ASSIGN
BASE_SHA = {BASE_SHA}
TASK_REVISION = {revision}
DESIGN_HEAD = {design_head}
NO_AUTO_MERGE = TRUE
"""


def event(*, revision: int, design_head: str, private: bool = False, actor: str = "Lester-Sparx") -> dict:
    return {
        "action": "created",
        "repository": {"full_name": "Lester-Sparx/zorr-blatt-shared-hq", "private": private},
        "issue": {"number": 111, "pull_request": {"url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/pulls/111"}},
        "comment": {"id": 9202, "body": body(revision=revision, design_head=design_head), "user": {"login": actor}},
    }


class RecordingPort:
    def __init__(self):
        self.comments: list[dict] = []
        self.console_comments: list[dict] = []
        self.next_id = 12000

    def create_tracker_comment(self, body: str) -> int:
        cid = self.next_id; self.next_id += 1
        self.comments.append({"id": cid, "body": body, "issue_url": TRACKER_ISSUE_URL, "user": {"login": STATE_WRITER}})
        return cid

    def create_console_comment(self, body: str) -> int:
        cid = self.next_id; self.next_id += 1
        self.console_comments.append({"id": cid, "body": body, "issue_url": CONSOLE_ISSUE_URL, "user": {"login": STATE_WRITER}})
        return cid

    def read_comment(self, comment_id: int) -> dict:
        for item in self.comments + self.console_comments:
            if item["id"] == comment_id:
                return dict(item)
        raise AssertionError(comment_id)

    def list_tracker_comments(self):
        return [dict(item) for item in self.comments]

    def list_console_comments(self):
        return [dict(item) for item in self.console_comments]


def admitted(evt: dict):
    return admit_event(evt, expected_base_sha=BASE_SHA, run_id="602", run_attempt="1", github_sha=BASE_SHA)[0]


def result_body(request_body: str, *, role: str, profile: str, execution_id: str) -> str:
    request = parse_execution_request(request_body)
    return render_execution_result(
        ExecutionResult(
            execution_request_id=request.execution_request_id if role == "LESTER" else request.execution_request_id + "-qc",
            execution_id=execution_id,
            attempt=1,
            message_id=request.message_id,
            correlation_id=request.correlation_id,
            task_id=request.task_id,
            task_revision=request.task_revision,
            logical_role=role,
            execution_profile=profile,
            execution_profile_version=1,
            base_sha=request.base_sha,
            start_head=request.base_sha,
            end_head=request.base_sha,
            terminal_state="PASS",
            result_code="OK" if role == "LESTER" else "QC_PASS",
            process_exit_code=0,
            changed_files=("tests/fixtures/zb-execution-proof/result.txt",),
            test_evidence_refs=("tests.txt",),
            artifact_evidence_refs=("manifest.json", "patch.diff"),
            workflow_run_id="602",
            workflow_run_attempt=1,
            runner_provenance="github-actions:github-hosted:windows-2025",
            started_at="2026-08-28T16:00:00Z",
            finished_at="2026-08-28T16:01:00Z",
            production_active=False,
        )
    )


class R02BDispatchTests(unittest.TestCase):
    def test_public_r02b_records_exact_hosted_request_and_replays_without_duplicate(self) -> None:
        evt = event(revision=2, design_head=R02B_DESIGN_HEAD, private=False)
        message = admitted(evt)
        port = RecordingPort()
        first = prepare_substantive_dispatch(message, evt, port)
        self.assertEqual(first.state, "REQUEST_RECORDED")
        self.assertEqual(first.request_sha256, hashlib.sha256(first.request_body.encode("utf-8")).hexdigest())
        request = parse_execution_request(first.request_body)
        self.assertEqual(request.task_revision, 2)
        self.assertEqual(request.design_head, R02B_DESIGN_HEAD)
        self.assertEqual(request.execution_profile, "LESTER_IMPLEMENT_R02A")
        self.assertEqual(request.allowed_write_scope, ("tests/fixtures/zb-execution-proof/",))
        self.assertIn("pr:123", request.evidence_input_refs + request.source_refs)
        count = len(port.comments)
        second = prepare_substantive_dispatch(message, evt, port)
        self.assertEqual(second, first)
        self.assertEqual(len(port.comments), count)

    def test_historical_r01_stays_blocked_on_public_repository(self) -> None:
        evt = event(revision=1, design_head=R01_DESIGN_HEAD, private=False)
        message = admitted(evt)
        port = RecordingPort()
        decision = prepare_substantive_dispatch(message, evt, port)
        self.assertEqual(decision.state, "BLOCKED")
        self.assertIn("RUNNER_SECURITY_GATE_BLOCKED", port.comments[-1]["body"])

    def test_r02b_wrong_revision_design_or_actor_fail_before_request(self) -> None:
        for evt in (
            event(revision=2, design_head=R01_DESIGN_HEAD),
            event(revision=3, design_head=R02B_DESIGN_HEAD),
            event(revision=2, design_head=R02B_DESIGN_HEAD, actor="foreign-user"),
        ):
            with self.subTest(evt=evt), self.assertRaises(ProtocolError):
                admitted(evt)

    def test_r02b_finalize_accepts_copilot_lester_and_distinct_duncan(self) -> None:
        evt = event(revision=2, design_head=R02B_DESIGN_HEAD, private=False)
        message = admitted(evt)
        port = RecordingPort()
        decision = prepare_substantive_dispatch(message, evt, port)
        lester = result_body(decision.request_body, role="LESTER", profile="LESTER_IMPLEMENT_R02A", execution_id="github-actions:602:1:lester_execute")
        duncan = result_body(decision.request_body, role="DUNCAN", profile="DUNCAN_QC_R01", execution_id="github-actions:602:1:duncan_qc")
        self.assertEqual(finalize_substantive_execution(decision.request_body, lester, duncan, port), "OWNER_GATE_REQUIRED")

    def test_proof_fixture_is_precommitted_for_no_create_worker(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "zb-execution-proof" / "result.txt"
        self.assertTrue(fixture.is_file())
        self.assertEqual(fixture.read_text(encoding="utf-8"), "ZB_R02A_PROOF_TARGET_V1\nSTATE = BEFORE\n")


if __name__ == "__main__":
    unittest.main()
