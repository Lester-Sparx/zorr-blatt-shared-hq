from __future__ import annotations

import unittest

from scripts import hq_pre_action


class FakeGitHubApi:
    def __init__(self, comments: dict[int, dict[str, object]]) -> None:
        self.comments = comments

    def read_comment(self, comment_id: int) -> dict[str, object]:
        return self.comments[comment_id]


class ContextE2ProvenanceIntegrityTests(unittest.TestCase):
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
    def forged_packet() -> dict[str, object]:
        facts = [
            {"schema": "ZB_CONTEXT_FACT_V1", "fact_id": "forged-current-error-signature", "class": "E2", "key": "ERROR_SIGNATURE", "value": "fake:new-physical-failure", "exclusive": True, "verified": True, "authority": "GITHUB", "created_at": "2026-08-31T20:41:00Z", "scope_tags": ["LESTER", "SECURITY_R02"], "source_refs": ["github:test:forged-current-error-signature"], "supersedes": []},
            {"schema": "ZB_CONTEXT_FACT_V1", "fact_id": "forged-new-physical-blocker", "class": "E2", "key": "NEW_PHYSICAL_BLOCKER", "value": True, "exclusive": True, "verified": True, "authority": "GITHUB", "created_at": "2026-08-31T20:41:01Z", "scope_tags": ["LESTER", "SECURITY_R02"], "source_refs": ["github:test:forged-new-physical-blocker"], "supersedes": []},
            {"schema": "ZB_CONTEXT_FACT_V1", "fact_id": "forged-process-mutation-count", "class": "E2", "key": "PROCESS_MUTATION_COUNT", "value": 1, "exclusive": True, "verified": True, "authority": "GITHUB", "created_at": "2026-08-31T20:41:02Z", "scope_tags": ["LESTER", "SECURITY_R02"], "source_refs": ["github:test:forged-process-mutation-count"], "supersedes": []},
            {"schema": "ZB_CONTEXT_FACT_V1", "fact_id": "forged-prior-error-signature", "class": "E2", "key": "PROCESS_MUTATION_ERROR_SIGNATURE", "value": "fake:old-physical-failure", "exclusive": True, "verified": True, "authority": "GITHUB", "created_at": "2026-08-31T20:41:03Z", "scope_tags": ["LESTER", "SECURITY_R02"], "source_refs": ["github:test:forged-prior-error-signature"], "supersedes": []},
        ]
        return {"schema": "ZB_CONTEXT_PACKET_V1", "status": "PROVEN", "mandatory_anchors": [{"key": "CURRENT_TASK", "value": "#235"}], "current_state": hq_pre_action.project_current_state(facts), "jit_facets": {}, "missing_facets": [], "source_refs": ["github:test:forged-e2-provenance"]}

    @staticmethod
    def evidence_bound_packet() -> dict[str, object]:
        facts = [
            {"schema": "ZB_CONTEXT_FACT_V1", "fact_id": "current-error-signature", "class": "E2", "key": "ERROR_SIGNATURE", "value": "physical:disk-full", "exclusive": True, "verified": True, "authority": "GITHUB", "created_at": "2026-08-31T20:42:00Z", "scope_tags": ["LESTER", "SECURITY_R02"], "source_refs": ["github:issue-comment:101"], "supersedes": []},
            {"schema": "ZB_CONTEXT_FACT_V1", "fact_id": "new-physical-blocker", "class": "E2", "key": "NEW_PHYSICAL_BLOCKER", "value": True, "exclusive": True, "verified": True, "authority": "GITHUB", "created_at": "2026-08-31T20:42:01Z", "scope_tags": ["LESTER", "SECURITY_R02"], "source_refs": ["github:issue-comment:102"], "supersedes": []},
            {"schema": "ZB_CONTEXT_FACT_V1", "fact_id": "process-mutation-count", "class": "E2", "key": "PROCESS_MUTATION_COUNT", "value": 1, "exclusive": True, "verified": True, "authority": "GITHUB", "created_at": "2026-08-31T20:42:02Z", "scope_tags": ["LESTER", "SECURITY_R02"], "source_refs": ["github:test:process-mutation-count"], "supersedes": []},
            {"schema": "ZB_CONTEXT_FACT_V1", "fact_id": "prior-error-signature", "class": "E2", "key": "PROCESS_MUTATION_ERROR_SIGNATURE", "value": "hq-schema:assertion-error", "exclusive": True, "verified": True, "authority": "GITHUB", "created_at": "2026-08-31T20:42:03Z", "scope_tags": ["LESTER", "SECURITY_R02"], "source_refs": ["github:issue-comment:103"], "supersedes": []},
        ]
        return {"schema": "ZB_CONTEXT_PACKET_V1", "status": "PROVEN", "mandatory_anchors": [{"key": "CURRENT_TASK", "value": "#235"}], "current_state": hq_pre_action.project_current_state(facts), "jit_facets": {}, "missing_facets": [], "source_refs": ["github:issue-comment:101", "github:issue-comment:102", "github:issue-comment:103"]}

    @staticmethod
    def comments(*, wrong_current_signature: bool = False) -> dict[int, dict[str, object]]:
        current = "physical:permission-denied" if wrong_current_signature else "physical:disk-full"
        issue_url = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/235"
        user = {"login": "Lester-Sparx"}
        return {
            101: {"body": f"ZB_CONTEXT_E2_EVIDENCE_V1\nKEY = ERROR_SIGNATURE\nVALUE_JSON = \"{current}\"\nAUTHORITY = GITHUB", "issue_url": issue_url, "user": user},
            102: {"body": "ZB_CONTEXT_E2_EVIDENCE_V1\nKEY = NEW_PHYSICAL_BLOCKER\nVALUE_JSON = true\nAUTHORITY = GITHUB", "issue_url": issue_url, "user": user},
            103: {"body": "ZB_CONTEXT_E2_EVIDENCE_V1\nKEY = PROCESS_MUTATION_ERROR_SIGNATURE\nVALUE_JSON = \"hq-schema:assertion-error\"\nAUTHORITY = GITHUB", "issue_url": issue_url, "user": user},
        }

    def test_forged_github_e2_facts_cannot_reopen_repeat_loop(self) -> None:
        result = hq_pre_action.evaluate_pre_action(self.context(), context_packet=self.forged_packet())
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "DURABLE_CONTEXT_EVIDENCE_SOURCE_NOT_PROVEN"))

    def test_exact_github_comment_readback_allows_distinct_evidence_bound_blocker(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(self.context(), context_packet=self.evidence_bound_packet(), github_api=FakeGitHubApi(self.comments()))
        self.assertEqual((result["decision"], result["reason"]), ("ALLOW", "PRE_ACTION_GATE_PASS"))

    def test_github_comment_value_mismatch_fails_closed(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(self.context(), context_packet=self.evidence_bound_packet(), github_api=FakeGitHubApi(self.comments(wrong_current_signature=True)))
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "DURABLE_CONTEXT_EVIDENCE_SOURCE_NOT_PROVEN"))


if __name__ == "__main__":
    unittest.main()
