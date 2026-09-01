from __future__ import annotations

import unittest

from scripts import hq_pre_action


class FakeGitHubApi:
    def __init__(self, *, result_comment: dict[str, object], authority_comment: dict[str, object] | None = None) -> None:
        self.result_comment = result_comment
        self.authority_comment = authority_comment

    def read_comment(self, comment_id: int) -> dict[str, object]:
        if comment_id == 9901:
            return dict(self.result_comment)
        if comment_id == 8801 and self.authority_comment is not None:
            return dict(self.authority_comment)
        raise AssertionError(comment_id)

    def list_tracker_comments(self) -> list[dict[str, object]]:
        return [
            {
                "id": 9001,
                "issue_url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106",
                "created_at": "2026-09-01T00:00:30Z",
                "updated_at": "2026-09-01T00:00:30Z",
                "user": {"login": "github-actions[bot]"},
                "body": "\n".join(
                    [
                        "ZB_R03_DISPATCH_V1",
                        "ROOT_COMMENT_ID = 8801",
                        "MESSAGE_ID = msg-17",
                        "CORRELATION_ID = corr-42",
                        "TASK_ID = ZB_EXECUTION_PROOF_R01",
                        "TASK_REVISION = 2",
                        f"BASE_SHA = {'a' * 40}",
                    ]
                ),
            }
        ]


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
    def packet(*, authority_ref: str = "github:issue-comment:8801") -> dict[str, object]:
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
            {"key": "AUTHORITY_REF", "value": authority_ref},
        ]
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": anchors,
            "current_state": hq_pre_action.project_current_state([fact]),
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["github:issue:235", authority_ref],
        }

    @staticmethod
    def result_comment(*, message_id: str = "msg-17", duncan_execution_id: str = "exec-duncan-10") -> dict[str, object]:
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

    @staticmethod
    def authority_comment(*, message_id: str = "msg-17") -> dict[str, object]:
        return {
            "id": 8801,
            "issue_url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/111",
            "created_at": "2026-09-01T00:00:00Z",
            "updated_at": "2026-09-01T00:00:00Z",
            "author_association": "OWNER",
            "user": {"login": "Lester-Sparx"},
            "body": "\n".join(
                [
                    "ZB_AGENT_TASK_R03_V1",
                    f"MESSAGE_ID = {message_id}",
                    "EVENT_ID = evt-17",
                    "CORRELATION_ID = corr-42",
                    "TASK_ID = ZB_EXECUTION_PROOF_R01",
                    "TASK_REVISION = 2",
                    f"BASE_SHA = {'a' * 40}",
                    "TASK_SPEC_COMMENT_ID = 7701",
                ]
            ),
        }

    def api(self, **result_overrides: str) -> FakeGitHubApi:
        return FakeGitHubApi(
            result_comment=self.result_comment(**result_overrides),
            authority_comment=self.authority_comment(),
        )

    def test_exact_subject_terminal_pass_is_accepted(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(), context_packet=self.packet(), github_api=self.api()
        )
        self.assertEqual((result["decision"], result["reason"]), ("ALLOW", "PRE_ACTION_GATE_PASS"))

    def test_other_message_terminal_pass_is_rejected(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(), context_packet=self.packet(), github_api=self.api(message_id="msg-OTHER")
        )
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "DURABLE_CONTEXT_EVIDENCE_SUBJECT_MISMATCH"))

    def test_other_execution_terminal_pass_is_rejected(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(), context_packet=self.packet(), github_api=self.api(duncan_execution_id="exec-duncan-OTHER")
        )
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "DURABLE_CONTEXT_EVIDENCE_SUBJECT_MISMATCH"))

    def test_caller_supplied_subject_without_fresh_authority_readback_is_rejected(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(),
            context_packet=self.packet(),
            github_api=FakeGitHubApi(result_comment=self.result_comment(), authority_comment=None),
        )
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "DURABLE_CONTEXT_AUTHORITY_SUBJECT_NOT_PROVEN"))

    def test_changed_unseen_authority_message_rejects_matching_caller_and_result_self_report(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(),
            context_packet=self.packet(),
            github_api=FakeGitHubApi(
                result_comment=self.result_comment(),
                authority_comment=self.authority_comment(message_id="msg-AUTHORITY-OTHER"),
            ),
        )
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "DURABLE_CONTEXT_AUTHORITY_SUBJECT_MISMATCH"))


if __name__ == "__main__":
    unittest.main()
