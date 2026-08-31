from __future__ import annotations

import unittest

from scripts.zb_communication_base import finalize_substantive_execution
from scripts.zb_execution_contract import (
    ExecutionRequest,
    ExecutionResult,
    render_execution_request,
    render_execution_result,
)


BASE_SHA = "a" * 40
DESIGN_HEAD = "b" * 40
TRACKER_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106"
CONSOLE_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/39"
BOT = "github-actions[bot]"


class RecordingPort:
    def __init__(self) -> None:
        self.comments: list[dict] = []
        self.console_comments: list[dict] = []
        self.next_id = 10000

    def create_tracker_comment(self, body: str) -> int:
        comment_id = self.next_id
        self.next_id += 1
        self.comments.append(
            {"id": comment_id, "body": body, "issue_url": TRACKER_URL, "user": {"login": BOT}}
        )
        return comment_id

    def create_console_comment(self, body: str) -> int:
        comment_id = self.next_id
        self.next_id += 1
        self.console_comments.append(
            {"id": comment_id, "body": body, "issue_url": CONSOLE_URL, "user": {"login": BOT}}
        )
        return comment_id

    def read_comment(self, comment_id: int) -> dict:
        for comment in self.comments + self.console_comments:
            if comment["id"] == comment_id:
                return dict(comment)
        raise AssertionError(f"missing comment {comment_id}")

    def list_tracker_comments(self) -> list[dict]:
        return [dict(comment) for comment in self.comments]

    def list_console_comments(self) -> list[dict]:
        return [dict(comment) for comment in self.console_comments]


def request_body() -> str:
    return render_execution_request(
        ExecutionRequest(
            execution_request_id="claim-gate-request-1",
            message_id="claim-gate-message-1",
            event_id="claim-gate-event-1",
            correlation_id="claim-gate-correlation-1",
            causation_message_id="claim-gate-message-1",
            task_id="ZB_EXECUTION_PROOF_R01",
            task_revision=1,
            logical_role="LESTER",
            execution_profile="LESTER_IMPLEMENT_R01",
            execution_profile_version=1,
            base_sha=BASE_SHA,
            authority_ref="pr:111:comment:9001",
            design_head=DESIGN_HEAD,
            source_refs=("pr:111", "source-comment:9001"),
            evidence_input_refs=("spec:120", "plan:121"),
            allowed_write_scope=("tests/fixtures/zb-execution-proof/",),
            timeout_seconds=600,
            no_auto_merge=True,
            production_active=False,
        )
    )


def result_body(
    role: str,
    profile: str,
    execution_id: str,
    *,
    execution_request_id: str | None = None,
    process_exit_code: int = 0,
    test_evidence_refs: tuple[str, ...] = ("run:123:test:unit",),
) -> str:
    expected_request_id = "claim-gate-request-1" if role == "LESTER" else "claim-gate-request-1-qc"
    return render_execution_result(
        ExecutionResult(
            execution_request_id=expected_request_id if execution_request_id is None else execution_request_id,
            execution_id=execution_id,
            attempt=1,
            message_id="claim-gate-message-1",
            correlation_id="claim-gate-correlation-1",
            task_id="ZB_EXECUTION_PROOF_R01",
            task_revision=1,
            logical_role=role,
            execution_profile=profile,
            execution_profile_version=1,
            base_sha=BASE_SHA,
            start_head=BASE_SHA,
            end_head=BASE_SHA,
            terminal_state="PASS",
            result_code="PASS",
            process_exit_code=process_exit_code,
            changed_files=(),
            test_evidence_refs=test_evidence_refs,
            artifact_evidence_refs=(),
            workflow_run_id="123",
            workflow_run_attempt=1,
            runner_provenance=f"runner:{role.lower()}",
            started_at="2026-08-31T13:00:00Z",
            finished_at="2026-08-31T13:01:00Z",
            production_active=False,
        )
    )


class TerminalClaimEvidenceGateTest(unittest.TestCase):
    def test_lester_pass_without_test_evidence_is_rejected_before_owner_gate(self) -> None:
        port = RecordingPort()
        result = finalize_substantive_execution(
            request_body(),
            result_body("LESTER", "LESTER_IMPLEMENT_R01", "exec:lester", test_evidence_refs=()),
            result_body("DUNCAN", "DUNCAN_QC_R01", "exec:duncan"),
            port,
        )

        self.assertEqual(result, "LESTER_RESULT_REJECTED")
        self.assertFalse(any("OWNER_GATE_REQUIRED = TRUE" in comment["body"] for comment in port.comments))

    def test_lester_pass_with_nonzero_process_exit_is_rejected_before_owner_gate(self) -> None:
        port = RecordingPort()
        result = finalize_substantive_execution(
            request_body(),
            result_body("LESTER", "LESTER_IMPLEMENT_R01", "exec:lester", process_exit_code=17),
            result_body("DUNCAN", "DUNCAN_QC_R01", "exec:duncan"),
            port,
        )

        self.assertEqual(result, "LESTER_RESULT_REJECTED")
        self.assertFalse(any("OWNER_GATE_REQUIRED = TRUE" in comment["body"] for comment in port.comments))

    def test_duncan_pass_without_test_evidence_is_rejected_before_owner_gate(self) -> None:
        port = RecordingPort()
        result = finalize_substantive_execution(
            request_body(),
            result_body("LESTER", "LESTER_IMPLEMENT_R01", "exec:lester"),
            result_body("DUNCAN", "DUNCAN_QC_R01", "exec:duncan", test_evidence_refs=()),
            port,
        )

        self.assertEqual(result, "DUNCAN_QC_FAIL")
        self.assertFalse(any("OWNER_GATE_REQUIRED = TRUE" in comment["body"] for comment in port.comments))

    def test_lester_pass_from_different_execution_request_is_rejected_before_owner_gate(self) -> None:
        port = RecordingPort()
        result = finalize_substantive_execution(
            request_body(),
            result_body(
                "LESTER",
                "LESTER_IMPLEMENT_R01",
                "exec:lester",
                execution_request_id="claim-gate-request-foreign",
            ),
            result_body("DUNCAN", "DUNCAN_QC_R01", "exec:duncan"),
            port,
        )

        self.assertEqual(result, "LESTER_RESULT_REJECTED")
        self.assertFalse(any("OWNER_GATE_REQUIRED = TRUE" in comment["body"] for comment in port.comments))

    def test_duncan_pass_from_different_execution_request_is_rejected_before_owner_gate(self) -> None:
        port = RecordingPort()
        result = finalize_substantive_execution(
            request_body(),
            result_body("LESTER", "LESTER_IMPLEMENT_R01", "exec:lester"),
            result_body(
                "DUNCAN",
                "DUNCAN_QC_R01",
                "exec:duncan",
                execution_request_id="claim-gate-request-foreign",
            ),
            port,
        )

        self.assertEqual(result, "DUNCAN_QC_FAIL")
        self.assertFalse(any("OWNER_GATE_REQUIRED = TRUE" in comment["body"] for comment in port.comments))


if __name__ == "__main__":
    unittest.main()
