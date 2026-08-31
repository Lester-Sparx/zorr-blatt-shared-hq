from __future__ import annotations

import unittest

from scripts import hq_pre_action


class FakeEvidenceGitHubApi:
    def __init__(self, comments: dict[int, dict[str, object]]):
        self.comments = comments
        self.read_ids: list[int] = []

    def read_comment(self, comment_id: int) -> dict[str, object]:
        self.read_ids.append(comment_id)
        return self.comments[comment_id]


class ContextE2CommentAuthorityTests(unittest.TestCase):
    @staticmethod
    def context() -> dict[str, object]:
        return {
            "action": "EXECUTE_PRODUCT_STEP",
            "directlyAdvancesPhysicalResult": True,
            "activeAttempt": False,
            "exactOwnerInputProvided": False,
            "prerequisiteAlreadyProven": False,
            "provenProcessBlocker": True,
            "processMutationCountForBlocker": 0,
            "newPhysicalBlocker": True,
            "provenExternalBoundary": False,
            "freshVerificationEvidence": False,
            "explicitOwnerImageMutationCommand": False,
        }

    @staticmethod
    def fact(fact_id: str, key: str, value: object, comment_id: int, created_at: str) -> dict[str, object]:
        return {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": fact_id,
            "class": "E2",
            "key": key,
            "value": value,
            "exclusive": True,
            "verified": True,
            "authority": "GITHUB",
            "created_at": created_at,
            "scope_tags": ["LESTER", "SECURITY_R02"],
            "source_refs": [f"github:issue-comment:{comment_id}"],
            "supersedes": [],
        }

    @classmethod
    def packet(cls) -> dict[str, object]:
        facts = [
            cls.fact("current-error", "ERROR_SIGNATURE", "physical:disk-full", 101, "2026-08-31T20:50:00Z"),
            cls.fact("new-blocker", "NEW_PHYSICAL_BLOCKER", True, 102, "2026-08-31T20:50:01Z"),
            {
                "schema": "ZB_CONTEXT_FACT_V1",
                "fact_id": "mutation-count",
                "class": "E2",
                "key": "PROCESS_MUTATION_COUNT",
                "value": 1,
                "exclusive": True,
                "verified": True,
                "authority": "GITHUB",
                "created_at": "2026-08-31T20:50:02Z",
                "scope_tags": ["LESTER", "SECURITY_R02"],
                "source_refs": ["github:test:mutation-count"],
                "supersedes": [],
            },
            cls.fact(
                "prior-error",
                "PROCESS_MUTATION_ERROR_SIGNATURE",
                "hq-schema:assertion-error",
                103,
                "2026-08-31T20:50:03Z",
            ),
        ]
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": [{"key": "CURRENT_TASK", "value": "#235"}],
            "current_state": hq_pre_action.project_current_state(facts),
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["github:issue:235"],
        }

    @staticmethod
    def evidence_body(key: str, value_json: str) -> str:
        return "\n".join(
            [
                "ZB_CONTEXT_E2_EVIDENCE_V1",
                f"KEY = {key}",
                f"VALUE_JSON = {value_json}",
                "AUTHORITY = GITHUB",
            ]
        )

    def test_untrusted_actor_and_wrong_container_cannot_self_certify_e2_facts(self) -> None:
        wrong_issue = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/999"
        comments = {
            101: {
                "id": 101,
                "body": self.evidence_body("ERROR_SIGNATURE", '"physical:disk-full"'),
                "issue_url": wrong_issue,
                "user": {"login": "attacker"},
            },
            102: {
                "id": 102,
                "body": self.evidence_body("NEW_PHYSICAL_BLOCKER", "true"),
                "issue_url": wrong_issue,
                "user": {"login": "attacker"},
            },
            103: {
                "id": 103,
                "body": self.evidence_body("PROCESS_MUTATION_ERROR_SIGNATURE", '"hq-schema:assertion-error"'),
                "issue_url": wrong_issue,
                "user": {"login": "attacker"},
            },
        }
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(),
            context_packet=self.packet(),
            github_api=FakeEvidenceGitHubApi(comments),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_EVIDENCE_SOURCE_NOT_PROVEN"),
        )


if __name__ == "__main__":
    unittest.main()
