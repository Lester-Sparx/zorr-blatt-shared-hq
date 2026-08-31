from __future__ import annotations

import unittest

from scripts import hq_pre_action


class ContextDisciplineExternalFreshnessTests(unittest.TestCase):
    @staticmethod
    def context(action: str = "EXECUTE_PRODUCT_STEP") -> dict[str, object]:
        return {
            "action": action,
            "directlyAdvancesPhysicalResult": True,
            "activeAttempt": False,
            "exactOwnerInputProvided": False,
            "prerequisiteAlreadyProven": False,
            "provenProcessBlocker": False,
            "processMutationCountForBlocker": 0,
            "newPhysicalBlocker": False,
            "provenExternalBoundary": False,
            "freshVerificationEvidence": action == "CLAIM_PASS",
            "explicitOwnerImageMutationCommand": False,
        }

    @staticmethod
    def head_fact(value: str) -> dict[str, object]:
        return {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": "active-head",
            "class": "E2",
            "key": "ACTIVE_HEAD",
            "value": value,
            "exclusive": True,
            "verified": True,
            "authority": "GITHUB",
            "created_at": "2026-08-31T18:00:00Z",
            "scope_tags": ["LESTER", "SECURITY_R02"],
            "source_refs": [f"github:commit:{value}"],
            "supersedes": [],
        }

    @classmethod
    def packet(cls, head: str) -> dict[str, object]:
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": [{"key": "CURRENT_TASK", "value": "#235"}],
            "current_state": {
                "schema": "ZB_CONTEXT_CURRENT_STATE_V1",
                "facts": [cls.head_fact(head)],
            },
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": [f"github:commit:{head}"],
        }

    def test_internally_proven_packet_with_superseded_external_head_blocks_execution(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.packet("old-head"),
            fresh_active_head="new-head",
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_STALE"),
        )


if __name__ == "__main__":
    unittest.main()
