from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts import zb_communication_r02b as r02b


class RecordingPort:
    def __init__(self) -> None:
        self.comments: list[dict[str, object]] = []

    def create_tracker_comment(self, body: str) -> int:
        comment_id = 501
        self.comments.append(
            {
                "id": comment_id,
                "body": body,
                "issue_url": r02b.TRACKER_ISSUE_URL,
                "user": {"login": r02b.STATE_WRITER},
            }
        )
        return comment_id

    def read_comment(self, comment_id: int) -> dict[str, object]:
        for comment in self.comments:
            if comment["id"] == comment_id:
                return dict(comment)
        raise AssertionError(comment_id)


class ContextE2MachineWriterPathTests(unittest.TestCase):
    def test_verified_terminal_finalizer_outcome_mints_exact_pass_evidence(self) -> None:
        port = RecordingPort()
        with patch.object(r02b, "_original_finalize_substantive_execution", return_value="OWNER_GATE_REQUIRED"):
            result = r02b.finalize_substantive_execution("request", "lester", "duncan", port)
        self.assertEqual(result, "OWNER_GATE_REQUIRED")
        self.assertEqual(
            [comment["body"] for comment in port.comments],
            [
                "ZB_CONTEXT_E2_EVIDENCE_V1\n"
                "KEY = RESULT\n"
                'VALUE_JSON = "PASS"\n'
                "AUTHORITY = GITHUB"
            ],
        )

    def test_non_pass_finalizer_outcome_cannot_mint_pass_evidence(self) -> None:
        port = RecordingPort()
        with patch.object(r02b, "_original_finalize_substantive_execution", return_value="DUNCAN_QC_FAIL"):
            result = r02b.finalize_substantive_execution("request", "lester", "duncan", port)
        self.assertEqual(result, "DUNCAN_QC_FAIL")
        self.assertEqual(port.comments, [])

    def test_terminal_pass_evidence_is_bound_to_exact_execution_subject(self) -> None:
        body = r02b._verified_terminal_pass_evidence_body(
            message_id="msg-17",
            correlation_id="corr-42",
            task_id=r02b.R02B_TASK_ID,
            task_revision=r02b.R02B_TASK_REVISION,
            base_sha="a" * 40,
            lester_execution_id="exec-lester-9",
            duncan_execution_id="exec-duncan-10",
        )
        self.assertEqual(
            body,
            "ZB_CONTEXT_E2_EVIDENCE_V1\n"
            "KEY = RESULT\n"
            'VALUE_JSON = "PASS"\n'
            "AUTHORITY = GITHUB\n"
            "MESSAGE_ID = msg-17\n"
            "CORRELATION_ID = corr-42\n"
            f"TASK_ID = {r02b.R02B_TASK_ID}\n"
            f"TASK_REVISION = {r02b.R02B_TASK_REVISION}\n"
            f"BASE_SHA = {'a' * 40}\n"
            "LESTER_EXECUTION_ID = exec-lester-9\n"
            "DUNCAN_EXECUTION_ID = exec-duncan-10",
        )


if __name__ == "__main__":
    unittest.main()
