from __future__ import annotations

import unittest

from scripts import hq_pre_action


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
            {
                "schema": "ZB_CONTEXT_FACT_V1",
                "fact_id": "forged-current-error-signature",
                "class": "E2",
                "key": "ERROR_SIGNATURE",
                "value": "fake:new-physical-failure",
                "exclusive": True,
                "verified": True,
                "authority": "GITHUB",
                "created_at": "2026-08-31T20:41:00Z",
                "scope_tags": ["LESTER", "SECURITY_R02"],
                "source_refs": ["github:test:forged-current-error-signature"],
                "supersedes": [],
            },
            {
                "schema": "ZB_CONTEXT_FACT_V1",
                "fact_id": "forged-new-physical-blocker",
                "class": "E2",
                "key": "NEW_PHYSICAL_BLOCKER",
                "value": True,
                "exclusive": True,
                "verified": True,
                "authority": "GITHUB",
                "created_at": "2026-08-31T20:41:01Z",
                "scope_tags": ["LESTER", "SECURITY_R02"],
                "source_refs": ["github:test:forged-new-physical-blocker"],
                "supersedes": [],
            },
            {
                "schema": "ZB_CONTEXT_FACT_V1",
                "fact_id": "forged-process-mutation-count",
                "class": "E2",
                "key": "PROCESS_MUTATION_COUNT",
                "value": 1,
                "exclusive": True,
                "verified": True,
                "authority": "GITHUB",
                "created_at": "2026-08-31T20:41:02Z",
                "scope_tags": ["LESTER", "SECURITY_R02"],
                "source_refs": ["github:test:forged-process-mutation-count"],
                "supersedes": [],
            },
            {
                "schema": "ZB_CONTEXT_FACT_V1",
                "fact_id": "forged-prior-error-signature",
                "class": "E2",
                "key": "PROCESS_MUTATION_ERROR_SIGNATURE",
                "value": "fake:old-physical-failure",
                "exclusive": True,
                "verified": True,
                "authority": "GITHUB",
                "created_at": "2026-08-31T20:41:03Z",
                "scope_tags": ["LESTER", "SECURITY_R02"],
                "source_refs": ["github:test:forged-prior-error-signature"],
                "supersedes": [],
            },
        ]
        current_state = hq_pre_action.project_current_state(facts)
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": [{"key": "CURRENT_TASK", "value": "#235"}],
            "current_state": current_state,
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["github:test:forged-e2-provenance"],
        }

    def test_forged_github_e2_facts_cannot_reopen_repeat_loop(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.forged_packet(),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_EVIDENCE_SOURCE_NOT_PROVEN"),
        )


if __name__ == "__main__":
    unittest.main()
