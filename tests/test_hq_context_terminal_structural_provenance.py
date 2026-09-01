from __future__ import annotations

import unittest

from scripts import hq_pre_action


BUS_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/111"
TRACKER_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106"
WRONG_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/235"


class FakeGitHubApi:
    def __init__(
        self,
        *,
        marker: str = "ZB_CONTEXT_E2_EVIDENCE_V1",
        result_url: str = TRACKER_URL,
        result_actor: str = "github-actions[bot]",
    ) -> None:
        self.marker = marker
        self.result_url = result_url
        self.result_actor = result_actor

    def read_comment(self, comment_id: int) -> dict[str, object]:
        if comment_id == 8801:
            return {
                "id": 8801,
                "issue_url": BUS_URL,
                "created_at": "2026-09-01T05:00:00Z",
                "updated_at": "2026-09-01T05:00:00Z",
                "author_association": "OWNER",
                "user": {"login": "Lester-Sparx"},
                "body": "\n".join(
                    [
                        "ZB_AGENT_TASK_R03_V1",
                        "MESSAGE_ID = msg-structural-17",
                        "EVENT_ID = evt-structural-17",
                        "CORRELATION_ID = corr-structural-42",
                        "TASK_ID = ZB_EXECUTION_PROOF_R01",
                        "TASK_REVISION = 2",
                        f"BASE_SHA = {'a' * 40}",
                        "TASK_SPEC_COMMENT_ID = 7701",
                    ]
                ),
            }
        if comment_id == 9901:
            return {
                "id": 9901,
                "issue_url": self.result_url,
                "created_at": "2026-09-01T05:01:00Z",
                "updated_at": "2026-09-01T05:01:00Z",
                "user": {"login": self.result_actor},
                "body": "\n".join(
                    [
                        self.marker,
                        "KEY = RESULT",
                        'VALUE_JSON = "PASS"',
                        "AUTHORITY = GITHUB",
                        "MESSAGE_ID = msg-structural-17",
                        "CORRELATION_ID = corr-structural-42",
                        "TASK_ID = ZB_EXECUTION_PROOF_R01",
                        "TASK_REVISION = 2",
                        f"BASE_SHA = {'a' * 40}",
                        "LESTER_EXECUTION_ID = exec-lester-structural-9",
                        "DUNCAN_EXECUTION_ID = exec-duncan-structural-10",
                    ]
                ),
            }
        raise AssertionError(comment_id)

    def list_tracker_comments(self) -> list[dict[str, object]]:
        return [
            {
                "id": 9001,
                "issue_url": TRACKER_URL,
                "created_at": "2026-09-01T05:00:30Z",
                "updated_at": "2026-09-01T05:00:30Z",
                "user": {"login": "github-actions[bot]"},
                "body": "\n".join(
                    [
                        "ZB_R03_DISPATCH_V1",
                        "ROOT_COMMENT_ID = 8801",
                        "MESSAGE_ID = msg-structural-17",
                        "CORRELATION_ID = corr-structural-42",
                        "TASK_ID = ZB_EXECUTION_PROOF_R01",
                        "TASK_REVISION = 2",
                        f"BASE_SHA = {'a' * 40}",
                    ]
                ),
            }
        ]


class TerminalStructuralProvenanceTests(unittest.TestCase):
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
            "fact_id": "terminal-structural-pass",
            "class": "E2",
            "key": "RESULT",
            "value": "PASS",
            "exclusive": True,
            "verified": True,
            "authority": "GITHUB",
            "created_at": "2026-09-01T05:01:00Z",
            "scope_tags": ["LESTER", "SECURITY_R02"],
            "source_refs": ["github:issue-comment:9901"],
            "supersedes": [],
        }
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": [
                {"key": "CURRENT_TASK", "value": "#106"},
                {"key": "MESSAGE_ID", "value": "msg-structural-17"},
                {"key": "CORRELATION_ID", "value": "corr-structural-42"},
                {"key": "TASK_ID", "value": "ZB_EXECUTION_PROOF_R01"},
                {"key": "TASK_REVISION", "value": 2},
                {"key": "BASE_SHA", "value": "a" * 40},
                {"key": "LESTER_EXECUTION_ID", "value": "exec-lester-structural-9"},
                {"key": "DUNCAN_EXECUTION_ID", "value": "exec-duncan-structural-10"},
                {"key": "AUTHORITY_REF", "value": "github:issue-comment:8801"},
            ],
            "current_state": hq_pre_action.project_current_state([fact]),
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["github:issue:106", "github:issue-comment:8801"],
        }

    def evaluate(self, api: FakeGitHubApi) -> dict[str, object]:
        return hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(),
            context_packet=self.packet(),
            github_api=api,
        )

    def test_exact_structural_provenance_preserves_bound_pass(self) -> None:
        result = self.evaluate(FakeGitHubApi())
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("ALLOW", "PRE_ACTION_GATE_PASS"),
        )

    def test_wrong_protocol_marker_with_exact_subject_is_rejected(self) -> None:
        result = self.evaluate(FakeGitHubApi(marker="ZB_OWNER_VIEW_V0"))
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_EVIDENCE_SOURCE_NOT_PROVEN"),
        )

    def test_wrong_container_with_exact_subject_is_rejected(self) -> None:
        result = self.evaluate(FakeGitHubApi(result_url=WRONG_URL))
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_EVIDENCE_SOURCE_NOT_PROVEN"),
        )

    def test_wrong_writer_with_exact_subject_is_rejected(self) -> None:
        result = self.evaluate(FakeGitHubApi(result_actor="Lester-Sparx"))
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_EVIDENCE_SOURCE_NOT_PROVEN"),
        )


if __name__ == "__main__":
    unittest.main()
