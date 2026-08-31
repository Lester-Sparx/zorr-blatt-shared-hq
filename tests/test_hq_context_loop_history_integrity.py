from __future__ import annotations

import unittest

from scripts import hq_pre_action


class ContextLoopHistoryIntegrityTests(unittest.TestCase):
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
            "newPhysicalBlocker": False,
            "provenExternalBoundary": False,
            "freshVerificationEvidence": False,
            "explicitOwnerImageMutationCommand": False,
        }

    @staticmethod
    def packet_with_untrusted_count() -> dict[str, object]:
        fact = {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": "process-mutation-count-downgraded",
            "class": "E1",
            "key": "PROCESS_MUTATION_COUNT",
            "value": 1,
            "exclusive": True,
            "verified": False,
            "authority": "CHAT",
            "created_at": "2026-08-31T20:05:00Z",
            "scope_tags": ["LESTER", "SECURITY_R02"],
            "source_refs": ["chat:caller-reset"],
            "supersedes": [],
        }
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": [{"key": "CURRENT_TASK", "value": "#235"}],
            "current_state": {
                "schema": "ZB_CONTEXT_CURRENT_STATE_V1",
                "facts": [fact],
            },
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["chat:caller-reset"],
        }

    @staticmethod
    def packet_with_trusted_count() -> dict[str, object]:
        fact = {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": "process-mutation-count-proven",
            "class": "E2",
            "key": "PROCESS_MUTATION_COUNT",
            "value": 1,
            "exclusive": True,
            "verified": True,
            "authority": "GITHUB",
            "created_at": "2026-08-31T20:25:00Z",
            "scope_tags": ["LESTER", "SECURITY_R02"],
            "source_refs": ["github:test:process-mutation-count-proven"],
            "supersedes": [],
        }
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": [{"key": "CURRENT_TASK", "value": "#235"}],
            "current_state": {
                "schema": "ZB_CONTEXT_CURRENT_STATE_V1",
                "facts": [fact],
            },
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["github:test:process-mutation-count-proven"],
        }

    def test_untrusted_process_mutation_count_cannot_be_ignored_to_reopen_loop(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.packet_with_untrusted_count(),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_NOT_PROVEN"),
        )

    def test_caller_new_blocker_claim_cannot_override_durable_repeat_history(self) -> None:
        context = self.context()
        context["newPhysicalBlocker"] = True
        result = hq_pre_action.evaluate_pre_action(
            context,
            context_packet=self.packet_with_trusted_count(),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_NEW_BLOCKER_NOT_PROVEN"),
        )


if __name__ == "__main__":
    unittest.main()
