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


if __name__ == "__main__":
    unittest.main()
