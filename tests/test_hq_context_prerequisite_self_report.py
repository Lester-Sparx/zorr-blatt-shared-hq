from __future__ import annotations

import unittest

from scripts import hq_pre_action


class ContextPrerequisiteSelfReportTests(unittest.TestCase):
    @staticmethod
    def context(
        *,
        prerequisite_already_proven: bool,
        directly_advances_physical_result: bool = True,
    ) -> dict[str, object]:
        return {
            "action": "VERIFY_PREREQUISITE",
            "directlyAdvancesPhysicalResult": directly_advances_physical_result,
            "activeAttempt": False,
            "exactOwnerInputProvided": False,
            "prerequisiteAlreadyProven": prerequisite_already_proven,
            "provenProcessBlocker": False,
            "processMutationCountForBlocker": 0,
            "newPhysicalBlocker": False,
            "provenExternalBoundary": False,
            "freshVerificationEvidence": False,
            "explicitOwnerImageMutationCommand": False,
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

    def test_caller_claim_cannot_suppress_prerequisite_verification(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(prerequisite_already_proven=True),
            context_packet=self.packet(),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("ALLOW", "PRE_ACTION_GATE_PASS"),
        )

    def test_progress_hint_cannot_suppress_prerequisite_verification(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(
                prerequisite_already_proven=True,
                directly_advances_physical_result=False,
            ),
            context_packet=self.packet(),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("ALLOW", "PRE_ACTION_GATE_PASS"),
        )

    def test_normal_prerequisite_verification_remains_allowed(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(prerequisite_already_proven=False),
            context_packet=self.packet(),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("ALLOW", "PRE_ACTION_GATE_PASS"),
        )


if __name__ == "__main__":
    unittest.main()
