from __future__ import annotations

import unittest

from scripts import hq_pre_action


class FakeGitHubApi:
    def __init__(self, comments: dict[int, dict[str, object]]) -> None:
        self.comments = comments

    def read_comment(self, comment_id: int) -> dict[str, object]:
        return self.comments[comment_id]

    def list_tracker_comments(self) -> list[dict[str, object]]:
        return [
            {
                "id": 9001,
                "issue_url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106",
                "user": {"login": "github-actions[bot]"},
                "body": "\n".join(
                    [
                        "ZB_R03_DISPATCH_V1",
                        "ROOT_COMMENT_ID = 202",
                        "MESSAGE_ID = msg-17",
                        "CORRELATION_ID = corr-42",
                        "TASK_ID = ZB_EXECUTION_PROOF_R01",
                        "TASK_REVISION = 2",
                        f"BASE_SHA = {'a' * 40}",
                    ]
                ),
            }
        ]


class ContextTerminalEvidenceGateTests(unittest.TestCase):
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
    def subject_anchors() -> list[dict[str, object]]:
        return [
            {"key": "MESSAGE_ID", "value": "msg-17"},
            {"key": "CORRELATION_ID", "value": "corr-42"},
            {"key": "TASK_ID", "value": "ZB_EXECUTION_PROOF_R01"},
            {"key": "TASK_REVISION", "value": 2},
            {"key": "BASE_SHA", "value": "a" * 40},
            {"key": "LESTER_EXECUTION_ID", "value": "exec-lester-9"},
            {"key": "DUNCAN_EXECUTION_ID", "value": "exec-duncan-10"},
            {"key": "AUTHORITY_REF", "value": "github:issue-comment:202"},
        ]

    @staticmethod
    def result_fact(value: str) -> dict[str, object]:
        source_ref = "github:issue-comment:201" if value == "PASS" else f"github:verified-result:{value.lower()}"
        return {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": f"terminal-{value.lower()}",
            "class": "E2",
            "key": "RESULT",
            "value": value,
            "exclusive": True,
            "verified": True,
            "authority": "GITHUB",
            "created_at": "2026-08-31T19:01:00Z",
            "scope_tags": ["LESTER", "SECURITY_R02"],
            "source_refs": [source_ref],
            "supersedes": [],
        }

    @classmethod
    def packet(cls, result: str | None) -> dict[str, object]:
        facts = [] if result is None else [cls.result_fact(result)]
        anchors: list[dict[str, object]] = [{"key": "CURRENT_TASK", "value": "#235"}]
        if result == "PASS":
            anchors.extend(cls.subject_anchors())
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": anchors,
            "current_state": {
                "schema": "ZB_CONTEXT_CURRENT_STATE_V1",
                "facts": facts,
            },
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["github:issue:235", "github:issue-comment:202"],
        }

    @staticmethod
    def pass_comment() -> dict[str, object]:
        return {
            "id": 201,
            "issue_url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/235",
            "user": {"login": hq_pre_action.STATE_WRITER},
            "body": "\n".join(
                [
                    "ZB_CONTEXT_E2_EVIDENCE_V1",
                    "KEY = RESULT",
                    'VALUE_JSON = "PASS"',
                    "AUTHORITY = GITHUB",
                    "MESSAGE_ID = msg-17",
                    "CORRELATION_ID = corr-42",
                    "TASK_ID = ZB_EXECUTION_PROOF_R01",
                    "TASK_REVISION = 2",
                    f"BASE_SHA = {'a' * 40}",
                    "LESTER_EXECUTION_ID = exec-lester-9",
                    "DUNCAN_EXECUTION_ID = exec-duncan-10",
                ]
            ),
        }

    @staticmethod
    def authority_comment() -> dict[str, object]:
        return {
            "id": 202,
            "issue_url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/111",
            "created_at": "2026-08-31T19:00:00Z",
            "updated_at": "2026-08-31T19:00:00Z",
            "author_association": "OWNER",
            "user": {"login": "Lester-Sparx"},
            "body": "\n".join(
                [
                    "ZB_AGENT_TASK_R03_V1",
                    "MESSAGE_ID = msg-17",
                    "EVENT_ID = evt-17",
                    "CORRELATION_ID = corr-42",
                    "TASK_ID = ZB_EXECUTION_PROOF_R01",
                    "TASK_REVISION = 2",
                    f"BASE_SHA = {'a' * 40}",
                    "TASK_SPEC_COMMENT_ID = 7701",
                ]
            ),
        }

    def _proven_pass(self, *, learning_policy: dict[str, object] | None = None) -> dict[str, object]:
        return hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(),
            learning_policy=learning_policy,
            context_packet=self.packet("PASS"),
            github_api=FakeGitHubApi({201: self.pass_comment(), 202: self.authority_comment()}),
        )

    def test_boolean_fresh_verification_without_durable_pass_cannot_claim_pass(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.packet(None),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_TERMINAL_EVIDENCE_NOT_PROVEN"),
        )

    def test_running_durable_result_cannot_be_upgraded_by_boolean_to_pass(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.packet("RUNNING"),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_TERMINAL_EVIDENCE_NOT_PROVEN"),
        )

    def test_verified_durable_pass_preserves_claim_pass_path(self) -> None:
        result = self._proven_pass()
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("ALLOW", "PRE_ACTION_GATE_PASS"),
        )

    def test_unseen_durable_fail_cannot_be_upgraded_by_boolean_to_pass(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.packet("FAIL"),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_TERMINAL_EVIDENCE_NOT_PROVEN"),
        )

    def test_verified_pass_preserves_verified_learning_path(self) -> None:
        policy = {
            "status": "PROVEN",
            "lesson_count": 1,
            "policy_prefix": "RULE = terminal claims require bound durable evidence",
            "lessons": [{"verdict_id": "SV1-TERMINAL-EVIDENCE-001"}],
        }
        result = self._proven_pass(learning_policy=policy)
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("ALLOW", "PRE_ACTION_GATE_PASS"),
        )
        self.assertEqual(result["learning"]["status"], "PROVEN")
        self.assertEqual(
            result["learning"]["verdict_ids"],
            ["SV1-TERMINAL-EVIDENCE-001"],
        )
        self.assertIn("bound durable evidence", result["learning"]["policy_prefix"])


if __name__ == "__main__":
    unittest.main()
