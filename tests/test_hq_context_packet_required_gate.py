from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts import hq_pre_action


class ContextPacketRequiredGateTests(unittest.TestCase):
    @staticmethod
    def context(action: str = "EXECUTE_PRODUCT_STEP", **overrides: object) -> dict[str, object]:
        context: dict[str, object] = {
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
        context.update(overrides)
        return context

    @staticmethod
    def packet() -> dict[str, object]:
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": [{"key": "CURRENT_TASK", "value": "#235"}],
            "current_state": {
                "schema": "ZB_CONTEXT_CURRENT_STATE_V1",
                "facts": [],
            },
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["github:issue:235"],
        }

    def test_substantive_action_without_context_packet_fails_closed(self) -> None:
        result = hq_pre_action.evaluate_pre_action(self.context())
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_NOT_PROVEN"),
        )

    def test_cli_cannot_bypass_context_discipline_by_omitting_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            context_path = Path(tmp) / "context.json"
            context_path.write_text(json.dumps(self.context()), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/hq_pre_action.py",
                    "--context-path",
                    str(context_path),
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["reason"], "DURABLE_CONTEXT_NOT_PROVEN")

    def test_read_required_evidence_remains_available_without_packet(self) -> None:
        result = hq_pre_action.evaluate_pre_action(self.context("READ_REQUIRED_EVIDENCE"))
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("ALLOW", "PRE_ACTION_GATE_PASS"),
        )

    def test_unseen_owner_action_cannot_bypass_required_context(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(
                "REQUEST_OWNER_ACTION",
                directlyAdvancesPhysicalResult=False,
                provenExternalBoundary=True,
            )
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_NOT_PROVEN"),
        )

    def test_proven_packet_preserves_verified_learning_on_substantive_path(self) -> None:
        policy = {
            "status": "PROVEN",
            "lesson_count": 1,
            "policy_prefix": "RULE = durable context precedes substantive action",
            "lessons": [{"verdict_id": "SV1-CONTEXT-REQUIRED-001"}],
        }
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            learning_policy=policy,
            context_packet=self.packet(),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("ALLOW", "PRE_ACTION_GATE_PASS"),
        )
        self.assertEqual(result["learning"]["status"], "PROVEN")
        self.assertEqual(
            result["learning"]["verdict_ids"],
            ["SV1-CONTEXT-REQUIRED-001"],
        )
        self.assertIn("durable context", result["learning"]["policy_prefix"])


if __name__ == "__main__":
    unittest.main()
