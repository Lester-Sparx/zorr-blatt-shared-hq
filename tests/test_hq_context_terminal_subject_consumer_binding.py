from __future__ import annotations

import unittest

from scripts import hq_pre_action


class FakeGitHubApi:
    def __init__(self, comment: dict[str, object]) -> None:
        self.comment = comment

    def read_comment(self, comment_id: int) -> dict[str, object]:
        assert comment_id == 9901
        return dict(self.comment)


class TerminalSubjectConsumerBindingTests(unittest.TestCase):
    @staticmethod
    def context() -> dict[str, object]:
        return {
            "action": "CLAIM_PASS",
            "directlyAdvancesPhysicalResult": True,
            "activeAttempt": False,
            "exactOwnerInputProvided": False,
            "prerequisiteAlreadyProven": False,
            "provenProcessBlocker": False,
            "processMutationCountForBlocker": 0,
            "newPhysicalBlocker": False,
            "provenExternalBoundary": False,
            "freshVerificationEvidence": True,
            "explicitOwnerImageMutationCommand": False,
        }

    @staticmethod
    def packet() -> dict[str, object]:
        fact = {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": "terminal-pass-bound-subject",
            "class": "E2",
            "key": "RESULT",
            "value": "PASS",
            "exclusive": True,
            "verified": True,
            "authority": "GITHUB",
            "created_at": "2026-09-01T00:01:00Z",
            "scope_tags": ["LESTER", "SECURITY_R02"],
            "source_refs": ["github:issue-comment:9901"],
            "supersedes": [],
        }
        anchors = [
            {"key": "CURRENT_TASK", "value": "#235"},
            {"key": "MESSAGE_ID", "value": "msg-17"},
            {"key": "CORRELATION_ID", "value": "corr-42"},
            {"key": "TASK_ID", "value": "ZB_EXECUTION_PROOF_R01"},
            {"key": "TASK_REVISION", "value": 2},
            {"key": "BASE_SHA", "value": "a" * 40},
            {"key": "LESTER_EXECUTION_ID", "value": "exec-lester-9"},
            {"key": "DUNCAN_EXECUTION_ID", "value": "exec-duncan-10"},
        ]
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": anchors,
            "current_state": hq_pre_action.project_current_state([fact]),
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["github:issue:235"],
        }

    @staticmethod
    def comment(*, message_id: str = "msg-17", duncan_execution_id: str = "exec-duncan-10") -> dict[str, object]:
        return {
            "id": 9901,
            "issue_url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/235",
            "user": {"login": "github-actions[bot]"},
            "body": "\n".join(
                [
                    "ZB_CONTEXT_E2_EVIDENCE_V1",
                    "KEY = RESULT",
                    'VALUE_JSON = "PASS"',
                    "AUTHORITY = GITHUB",
                    f"MESSAGE_ID = {message_id}",
                    "CORRELATION_ID = corr-42",
                    "TASK_ID = ZB_EXECUTION_PROOF_R01",
                    "TASK_REVISION = 2",
                    f"BASE_SHA = {'a' * 40}",
                    "LESTER_EXECUTION_ID = exec-lester-9",
                    f"DUNCAN_EXECUTION_ID = {duncan_execution_id}",
                ]
            ),
        }

    def test_exact_subject_terminal_pass_is_accepted(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(), context_packet=self.packet(), github_api=FakeGitHubApi(self.comment())
        )
        self.assertEqual((result["decision"], result["reason"]), ("ALLOW", "PRE_ACTION_GATE_PASS"))

    def test_other_message_terminal_pass_is_rejected(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(), context_packet=self.packet(), github_api=FakeGitHubApi(self.comment(message_id="msg-OTHER"))
        )
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "DURABLE_CONTEXT_EVIDENCE_SUBJECT_MISMATCH"))

    def test_other_execution_terminal_pass_is_rejected(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(), context_packet=self.packet(), github_api=FakeGitHubApi(self.comment(duncan_execution_id="exec-duncan-OTHER"))
        )
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "DURABLE_CONTEXT_EVIDENCE_SUBJECT_MISMATCH"))


if __name__ == "__main__":
    unittest.main()
