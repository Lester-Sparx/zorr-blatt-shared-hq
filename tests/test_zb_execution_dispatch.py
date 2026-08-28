from __future__ import annotations

import hashlib
import unittest

from scripts.zb_communication_base import (
    CONSOLE_ISSUE_URL,
    STATE_WRITER,
    SUBSTANTIVE_DESIGN_HEAD,
    TRACKER_ISSUE_URL,
    admit_event,
    finalize_substantive_execution,
    prepare_substantive_dispatch,
)
from scripts.zb_execution_contract import ExecutionResult, parse_execution_request, render_execution_result


BASE_SHA = "b" * 40


def substantive_body() -> str:
    return f"""ZB_AGENT_MESSAGE_V1
MESSAGE_ID = zb-exec-proof-r01-msg-001
EVENT_ID = zb-exec-proof-r01-evt-001
CORRELATION_ID = zb-exec-proof-r01
CAUSATION_MESSAGE_ID = NONE
TASK_ID = ZB_EXECUTION_PROOF_R01
FROM_ROLE = JINGO
TO_ROLE = LESTER
MESSAGE_KIND = ASSIGN
BASE_SHA = {BASE_SHA}
TASK_REVISION = 1
DESIGN_HEAD = {SUBSTANTIVE_DESIGN_HEAD}
NO_AUTO_MERGE = TRUE
"""


def event(*, private: bool) -> dict:
    return {
        "action": "created",
        "repository": {
            "full_name": "Lester-Sparx/zorr-blatt-shared-hq",
            "private": private,
        },
        "issue": {
            "number": 111,
            "pull_request": {"url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/pulls/111"},
        },
        "comment": {
            "id": 9101,
            "body": substantive_body(),
            "user": {"login": "Lester-Sparx"},
        },
    }


class RecordingPort:
    def __init__(self) -> None:
        self.comments: list[dict] = []
        self.console_comments: list[dict] = []
        self.next_id = 10001

    def create_tracker_comment(self, body: str) -> int:
        comment_id = self.next_id
        self.next_id += 1
        self.comments.append({"id": comment_id, "body": body, "issue_url": TRACKER_ISSUE_URL, "user": {"login": STATE_WRITER}})
        return comment_id

    def create_console_comment(self, body: str) -> int:
        comment_id = self.next_id
        self.next_id += 1
        self.console_comments.append({"id": comment_id, "body": body, "issue_url": CONSOLE_ISSUE_URL, "user": {"login": STATE_WRITER}})
        return comment_id

    def read_comment(self, comment_id: int) -> dict:
        for item in self.comments + self.console_comments:
            if item["id"] == comment_id:
                return dict(item)
        raise AssertionError(comment_id)

    def list_tracker_comments(self) -> list[dict]:
        return [dict(item) for item in self.comments]

    def list_console_comments(self) -> list[dict]:
        return [dict(item) for item in self.console_comments]


def admitted(private: bool):
    evt = event(private=private)
    message, context = admit_event(evt, expected_base_sha=BASE_SHA, run_id="500", run_attempt="1", github_sha=BASE_SHA)
    return evt, message, context


def result_body(request_body: str, *, role: str, profile: str, execution_id: str, state: str = "PASS") -> str:
    request = parse_execution_request(request_body)
    return render_execution_result(
        ExecutionResult(
            execution_request_id=(request.execution_request_id if role == "LESTER" else request.execution_request_id + "-qc"),
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
            terminal_state=state,
            result_code=("OK" if role == "LESTER" else "QC_PASS") if state == "PASS" else "QC_FAIL",
            process_exit_code=0 if state == "PASS" else 1,
            changed_files=("tests/fixtures/zb-execution-proof/result.txt",),
            test_evidence_refs=("tests.txt",),
            artifact_evidence_refs=("manifest.json", "patch.diff"),
            workflow_run_id="500",
            workflow_run_attempt=1,
            runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
            started_at="2026-08-28T14:00:00Z",
            finished_at="2026-08-28T14:01:00Z",
            production_active=False,
        )
    )


class SubstantiveDispatchTests(unittest.TestCase):
    def test_public_repository_blocks_before_self_hosted_dispatch(self) -> None:
        evt, message, _ = admitted(False)
        port = RecordingPort()
        decision = prepare_substantive_dispatch(message, evt, port)
        self.assertEqual(decision.state, "BLOCKED")
        self.assertIsNone(decision.request_body)
        self.assertIsNone(decision.request_sha256)
        self.assertEqual(len(port.comments), 1)
        self.assertIn("RESULT_CODE = RUNNER_SECURITY_GATE_BLOCKED", port.comments[0]["body"])
        self.assertEqual(len(port.console_comments), 1)
        self.assertIn("GATE = SUBSTANTIVE_EXECUTION | BLOCKED |", port.console_comments[0]["body"])
        self.assertNotIn("LESTER | DONE", port.console_comments[0]["body"])
        self.assertNotIn("DUNCAN | DONE", port.console_comments[0]["body"])

    def test_private_repository_records_exact_immutable_request_and_reuses_it_on_replay(self) -> None:
        evt, message, _ = admitted(True)
        port = RecordingPort()
        first = prepare_substantive_dispatch(message, evt, port)
        self.assertEqual(first.state, "REQUEST_RECORDED")
        self.assertIsNotNone(first.request_body)
        self.assertEqual(first.request_sha256, hashlib.sha256(first.request_body.encode("utf-8")).hexdigest())
        parsed = parse_execution_request(first.request_body)
        self.assertEqual(parsed.logical_role, "LESTER")
        self.assertEqual(parsed.execution_profile, "LESTER_IMPLEMENT_R01")
        self.assertEqual(parsed.allowed_write_scope, ("tests/fixtures/zb-execution-proof/",))
        self.assertEqual(port.comments[-1]["body"], first.request_body)
        created_count = len(port.comments)
        second = prepare_substantive_dispatch(message, evt, port)
        self.assertEqual(second, first)
        self.assertEqual(len(port.comments), created_count)

    def test_finalize_requires_verified_lester_and_distinct_duncan_pass(self) -> None:
        evt, message, _ = admitted(True)
        port = RecordingPort()
        decision = prepare_substantive_dispatch(message, evt, port)
        lester = result_body(decision.request_body, role="LESTER", profile="LESTER_IMPLEMENT_R01", execution_id="github-actions:500:1:lester_execute")
        duncan = result_body(decision.request_body, role="DUNCAN", profile="DUNCAN_QC_R01", execution_id="github-actions:500:1:duncan_qc")
        state = finalize_substantive_execution(decision.request_body, lester, duncan, port)
        self.assertEqual(state, "OWNER_GATE_REQUIRED")
        self.assertTrue(any(body["body"].startswith("ZB_OWNER_VIEW_V0\n") for body in port.comments))
        self.assertTrue(any("GATE = SUBSTANTIVE_EXECUTION | DONE |" in body["body"] for body in port.console_comments))

    def test_duncan_fail_or_same_execution_id_never_advances_to_owner_gate(self) -> None:
        for same_id, state in ((False, "FAIL"), (True, "PASS")):
            with self.subTest(same_id=same_id, state=state):
                evt, message, _ = admitted(True)
                port = RecordingPort()
                decision = prepare_substantive_dispatch(message, evt, port)
                lester_id = "github-actions:500:1:lester_execute"
                lester = result_body(decision.request_body, role="LESTER", profile="LESTER_IMPLEMENT_R01", execution_id=lester_id)
                duncan = result_body(
                    decision.request_body,
                    role="DUNCAN",
                    profile="DUNCAN_QC_R01",
                    execution_id=lester_id if same_id else "github-actions:500:1:duncan_qc",
                    state=state,
                )
                outcome = finalize_substantive_execution(decision.request_body, lester, duncan, port)
                self.assertNotEqual(outcome, "OWNER_GATE_REQUIRED")
                tracker_text = "\n".join(item["body"] for item in port.comments)
                self.assertNotIn("OWNER_GATE_REQUIRED = TRUE", tracker_text)


if __name__ == "__main__":
    unittest.main()
