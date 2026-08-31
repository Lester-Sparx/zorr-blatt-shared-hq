from __future__ import annotations

import unittest

from scripts import hq_pre_action


class ContextExternalFreshnessRequiredGateTests(unittest.TestCase):
    @staticmethod
    def context(action: str = "EXECUTE_PRODUCT_STEP") -> dict[str, object]:
        return {
            "action": action,
            "directlyAdvancesPhysicalResult": action == "EXECUTE_PRODUCT_STEP",
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

    @staticmethod
    def active_head_fact(value: str) -> dict[str, object]:
        return {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": "active-head-requires-freshness",
            "class": "E2",
            "key": "ACTIVE_HEAD",
            "value": value,
            "exclusive": True,
            "verified": True,
            "authority": "GITHUB",
            "created_at": "2026-08-31T19:15:00Z",
            "scope_tags": ["LESTER", "SECURITY_R02"],
            "source_refs": [f"github:commit:{value}"],
            "supersedes": [],
        }

    @classmethod
    def packet(cls, *, with_head: bool) -> dict[str, object]:
        facts = [cls.active_head_fact("packet-head")] if with_head else []
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": [{"key": "CURRENT_TASK", "value": "#235"}],
            "current_state": {
                "schema": "ZB_CONTEXT_CURRENT_STATE_V1",
                "facts": facts,
            },
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["github:issue:235"],
        }

    def test_substantive_packet_with_active_head_requires_external_freshness_input(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.packet(with_head=True),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_NOT_PROVEN"),
        )

    def test_substantive_task_without_active_head_can_use_proven_packet_without_head_binding(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.packet(with_head=False),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("ALLOW", "PRE_ACTION_GATE_PASS"),
        )

    def test_read_required_evidence_does_not_require_external_head_binding(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context("READ_REQUIRED_EVIDENCE"),
            context_packet=self.packet(with_head=True),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("ALLOW", "PRE_ACTION_GATE_PASS"),
        )


if __name__ == "__main__":
    unittest.main()
