from __future__ import annotations

import unittest

from scripts import hq_pre_action


class ContextOwnerCommandProvenanceTests(unittest.TestCase):
    @staticmethod
    def context() -> dict[str, object]:
        return {
            "action": "IMAGE_MUTATION",
            "directlyAdvancesPhysicalResult": True,
            "activeAttempt": False,
            "exactOwnerInputProvided": False,
            "prerequisiteAlreadyProven": False,
            "provenProcessBlocker": False,
            "processMutationCountForBlocker": 0,
            "newPhysicalBlocker": False,
            "provenExternalBoundary": False,
            "freshVerificationEvidence": False,
            "explicitOwnerImageMutationCommand": True,
        }

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

    def test_caller_boolean_cannot_self_authorize_owner_image_mutation(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.packet(),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_OWNER_COMMAND_NOT_PROVEN"),
        )


if __name__ == "__main__":
    unittest.main()
