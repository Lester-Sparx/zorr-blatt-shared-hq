from __future__ import annotations

import unittest

from scripts import hq_pre_action


BUS_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/111"
TRACKER_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106"


class FakeGitHubApi:
    def __init__(self, *, newer_dispatch: bool, edited_dispatch: bool = False) -> None:
        self.newer_dispatch = newer_dispatch
        self.edited_dispatch = edited_dispatch

    def read_comment(self, comment_id: int) -> dict[str, object]:
        if comment_id == 8801:
            return {
                "id": 8801,
                "issue_url": BUS_URL,
                "created_at": "2026-09-01T00:00:00Z",
                "updated_at": "2026-09-01T00:00:00Z",
                "author_association": "OWNER",
                "user": {"login": "Lester-Sparx"},
                "body": "\n".join(
                    [
                        "ZB_AGENT_TASK_R03_V1",
                        "MESSAGE_ID = msg-old",
                        "EVENT_ID = evt-old",
                        "CORRELATION_ID = corr-old",
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
                "issue_url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/235",
                "created_at": "2026-09-01T00:01:00Z",
                "updated_at": "2026-09-01T00:01:00Z",
                "user": {"login": "github-actions[bot]"},
                "body": "\n".join(
                    [
                        "ZB_CONTEXT_E2_EVIDENCE_V1",
                        "KEY = RESULT",
                        'VALUE_JSON = "PASS"',
                        "AUTHORITY = GITHUB",
                        "MESSAGE_ID = msg-old",
                        "CORRELATION_ID = corr-old",
                        "TASK_ID = ZB_EXECUTION_PROOF_R01",
                        "TASK_REVISION = 2",
                        f"BASE_SHA = {'a' * 40}",
                        "LESTER_EXECUTION_ID = exec-lester-old",
                        "DUNCAN_EXECUTION_ID = exec-duncan-old",
                    ]
                ),
            }
        raise AssertionError(comment_id)

    def list_tracker_comments(self) -> list[dict[str, object]]:
        current = {
            "id": 9001,
            "issue_url": TRACKER_URL,
            "created_at": "2026-09-01T00:00:30Z",
            "updated_at": "2026-09-01T00:02:30Z" if self.edited_dispatch else "2026-09-01T00:00:30Z",
            "user": {"login": "github-actions[bot]"},
            "body": "\n".join(
                [
                    "ZB_R03_DISPATCH_V1",
                    "ROOT_COMMENT_ID = 8801",
                    "MESSAGE_ID = msg-old",
                    "CORRELATION_ID = corr-old",
                    "TASK_ID = ZB_EXECUTION_PROOF_R01",
                    "TASK_REVISION = 2",
                    f"BASE_SHA = {'a' * 40}",
                ]
            ),
        }
        if not self.newer_dispatch:
            return [current]
        newer = {
            "id": 9002,
            "issue_url": TRACKER_URL,
            "created_at": "2026-09-01T00:01:30Z",
            "updated_at": "2026-09-01T00:01:30Z",
            "user": {"login": "github-actions[bot]"},
            "body": "\n".join(
                [
                    "ZB_R03_DISPATCH_V1",
                    "ROOT_COMMENT_ID = 8802",
                    "MESSAGE_ID = msg-new",
                    "CORRELATION_ID = corr-new",
                    "TASK_ID = ZB_EXECUTION_PROOF_R01",
                    "TASK_REVISION = 2",
                    f"BASE_SHA = {'b' * 40}",
                ]
            ),
        }
        return [current, newer]


class TerminalAuthorityStalenessTests(unittest.TestCase):
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
            "fact_id": "old-terminal-pass",
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
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": [
                {"key": "CURRENT_TASK", "value": "#235"},
                {"key": "MESSAGE_ID", "value": "msg-old"},
                {"key": "CORRELATION_ID", "value": "corr-old"},
                {"key": "TASK_ID", "value": "ZB_EXECUTION_PROOF_R01"},
                {"key": "TASK_REVISION", "value": 2},
                {"key": "BASE_SHA", "value": "a" * 40},
                {"key": "LESTER_EXECUTION_ID", "value": "exec-lester-old"},
                {"key": "DUNCAN_EXECUTION_ID", "value": "exec-duncan-old"},
                {"key": "AUTHORITY_REF", "value": "github:issue-comment:8801"},
            ],
            "current_state": hq_pre_action.project_current_state([fact]),
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["github:issue:235", "github:issue-comment:8801"],
        }

    def test_current_dispatched_authority_still_allows_bound_pass(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(), context_packet=self.packet(), github_api=FakeGitHubApi(newer_dispatch=False)
        )
        self.assertEqual((result["decision"], result["reason"]), ("ALLOW", "PRE_ACTION_GATE_PASS"))

    def test_old_bound_pass_is_rejected_after_newer_trusted_dispatch(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(), context_packet=self.packet(), github_api=FakeGitHubApi(newer_dispatch=True)
        )
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "DURABLE_CONTEXT_AUTHORITY_STALE"))

    def test_edited_trusted_dispatch_cannot_define_current_authority(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(),
            context_packet=self.packet(),
            github_api=FakeGitHubApi(newer_dispatch=False, edited_dispatch=True),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_AUTHORITY_FRESHNESS_NOT_PROVEN"),
        )


if __name__ == "__main__":
    unittest.main()
