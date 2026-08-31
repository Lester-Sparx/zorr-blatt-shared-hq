from __future__ import annotations

import unittest

from scripts import hq_pre_action


class ContextTerminalEvidenceGateTests(unittest.TestCase):
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
    def result_fact(value: str) -> dict[str, object]:
        return {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": f"terminal-{value.lower()}",
            "class": "E2",
            "key": "RESULT",
            "value": value,
            "exclusive": True,
            "verified": True,
            "authority": "GITHUB",
            "created_at": "2026-08-31T19:01:00Z",
            "scope_tags": ["LESTER", "SECURITY_R02"],
            "source_refs": [f"github:verified-result:{value.lower()}"],
            "supersedes": [],
        }

    @classmethod
    def packet(cls, result: str | None) -> dict[str, object]:
        facts = [] if result is None else [cls.result_fact(result)]
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

    def test_boolean_fresh_verification_without_durable_pass_cannot_claim_pass(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.packet(None),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_TERMINAL_EVIDENCE_NOT_PROVEN"),
        )

    def test_running_durable_result_cannot_be_upgraded_by_boolean_to_pass(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.packet("RUNNING"),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_TERMINAL_EVIDENCE_NOT_PROVEN"),
        )

    def test_verified_durable_pass_preserves_claim_pass_path(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.packet("PASS"),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("ALLOW", "PRE_ACTION_GATE_PASS"),
        )

    def test_unseen_durable_fail_cannot_be_upgraded_by_boolean_to_pass(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.packet("FAIL"),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_TERMINAL_EVIDENCE_NOT_PROVEN"),
        )

    def test_verified_pass_preserves_verified_learning_path(self) -> None:
        policy = {
            "status": "PROVEN",
            "lesson_count": 1,
            "policy_prefix": "RULE = terminal claims require bound durable evidence",
            "lessons": [{"verdict_id": "SV1-TERMINAL-EVIDENCE-001"}],
        }
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            learning_policy=policy,
            context_packet=self.packet("PASS"),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("ALLOW", "PRE_ACTION_GATE_PASS"),
        )
        self.assertEqual(result["learning"]["status"], "PROVEN")
        self.assertEqual(
            result["learning"]["verdict_ids"],
            ["SV1-TERMINAL-EVIDENCE-001"],
        )
        self.assertIn("bound durable evidence", result["learning"]["policy_prefix"])


if __name__ == "__main__":
    unittest.main()
