from __future__ import annotations

import unittest

from scripts import hq_pre_action


AUTHORITY_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/111"
TRACKER_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106"
RESULT_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/235"


class FakeGitHubApi:
    def read_comment(self, comment_id: int) -> dict[str, object]:
        if comment_id == 8801:
            return {
                "id": 8801,
                "issue_url": AUTHORITY_URL,
                "created_at": "2026-09-01T00:00:00Z",
                "updated_at": "2026-09-01T00:00:00Z",
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
        if comment_id == 9901:
            return {
                "id": 9901,
                "issue_url": RESULT_URL,
                "created_at": "2026-09-01T00:01:00Z",
                "updated_at": "2026-09-01T00:02:00Z",
                "user": {"login": "github-actions[bot]"},
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
        raise AssertionError(comment_id)

    def list_tracker_comments(self) -> list[dict[str, object]]:
        return [
            {
                "id": 9001,
                "issue_url": TRACKER_URL,
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


class TerminalEvidenceImmutabilityTests(unittest.TestCase):
    def test_edited_terminal_pass_comment_is_rejected(self) -> None:
        context = {
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
            {"key": "AUTHORITY_REF", "value": "github:issue-comment:8801"},
        ]
        packet = {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": anchors,
            "current_state": hq_pre_action.project_current_state([fact]),
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["github:issue:235", "github:issue-comment:8801"],
        }

        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            context,
            context_packet=packet,
            github_api=FakeGitHubApi(),
        )

        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_EVIDENCE_IMMUTABILITY_NOT_PROVEN"),
        )


if __name__ == "__main__":
    unittest.main()
