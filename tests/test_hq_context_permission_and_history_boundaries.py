from __future__ import annotations

import unittest

from scripts import hq_pre_action


ISSUE_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/235"


class FakeGitHubApi:
    def __init__(self, comments: list[dict[str, object]]) -> None:
        self.comments = comments

    def _list_issue_comments(self, issue_url: str, label: str) -> list[dict[str, object]]:
        if issue_url != ISSUE_URL:
            raise AssertionError("unexpected issue")
        return list(self.comments)


class PermissionAndHistoryBoundaryTests(unittest.TestCase):
    @staticmethod
    def context(**overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "action": "EXECUTE_PRODUCT_STEP",
            "directlyAdvancesPhysicalResult": True,
            "activeAttempt": False,
            "exactOwnerInputProvided": False,
            "prerequisiteAlreadyProven": False,
            "provenProcessBlocker": False,
            "processMutationCountForBlocker": 0,
            "newPhysicalBlocker": False,
            "provenExternalBoundary": False,
            "freshVerificationEvidence": False,
            "explicitOwnerImageMutationCommand": False,
        }
        value.update(overrides)
        return value

    @staticmethod
    def packet() -> dict[str, object]:
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": [{"key": "CURRENT_TASK", "value": "#235"}],
            "current_state": hq_pre_action.project_current_state([]),
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["github:issue:235"],
        }

    @staticmethod
    def evidence_comment(key: str, value_json: str) -> dict[str, object]:
        return {
            "body": "\n".join(
                [
                    "ZB_CONTEXT_E2_EVIDENCE_V1",
                    f"KEY = {key}",
                    f"VALUE_JSON = {value_json}",
                    "AUTHORITY = GITHUB",
                ]
            ),
            "issue_url": ISSUE_URL,
            "user": {"login": "Lester-Sparx"},
        }

    def test_caller_boolean_cannot_self_prove_first_process_blocker(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(action="PROCESS_MUTATION", provenProcessBlocker=True),
            context_packet=self.packet(),
            github_api=FakeGitHubApi([]),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_PROCESS_BLOCKER_NOT_PROVEN"),
        )

    def test_caller_boolean_cannot_self_prove_external_owner_boundary(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(
                action="REQUEST_OWNER_ACTION",
                directlyAdvancesPhysicalResult=False,
                provenExternalBoundary=True,
            ),
            context_packet=self.packet(),
            github_api=FakeGitHubApi([]),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_EXTERNAL_BOUNDARY_NOT_PROVEN"),
        )

    def test_omitted_packet_count_cannot_erase_durable_repeat_history(self) -> None:
        api = FakeGitHubApi([self.evidence_comment("PROCESS_MUTATION_COUNT", "1")])
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(action="EXECUTE_PRODUCT_STEP", processMutationCountForBlocker=0),
            context_packet=self.packet(),
            github_api=api,
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "REPEAT_PROCESS_MUTATION_REQUIRES_NEW_BLOCKER"),
        )


if __name__ == "__main__":
    unittest.main()
