from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts import hq_pre_action


class ContextDisciplinePreActionTests(unittest.TestCase):
    @staticmethod
    def context() -> dict[str, object]:
        return {
            "action": "EXECUTE_PRODUCT_STEP",
            "directlyAdvancesPhysicalResult": True,
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
    def packet(status: str) -> dict[str, object]:
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": status,
            "missing_facets": [] if status == "PROVEN" else ["CURRENT_HEAD"],
            "source_refs": ["github:issue:235"],
        }

    def test_not_proven_context_packet_blocks_substantive_action(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.packet("NOT_PROVEN"),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_NOT_PROVEN"),
        )
        self.assertEqual(result["context"]["missing_facets"], ["CURRENT_HEAD"])

    def test_proven_context_packet_preserves_existing_decision(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=self.packet("PROVEN"),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("ALLOW", "PRE_ACTION_GATE_PASS"),
        )
        self.assertEqual(result["context"]["status"], "PROVEN")

    def test_context_packet_does_not_replace_verified_learning_view(self) -> None:
        policy = {
            "status": "PROVEN",
            "lesson_count": 1,
            "policy_prefix": "RULE = restore durable evidence before asserting state",
            "lessons": [{"verdict_id": "SV1-CONTEXT-001"}],
        }
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            learning_policy=policy,
            context_packet=self.packet("PROVEN"),
        )
        self.assertEqual(result["learning"]["status"], "PROVEN")
        self.assertEqual(result["learning"]["verdict_ids"], ["SV1-CONTEXT-001"])
        self.assertIn("restore durable evidence", result["learning"]["policy_prefix"])

    def test_invalid_context_packet_fails_closed(self) -> None:
        with self.assertRaisesRegex(hq_pre_action.PreActionError, "CONTEXT_PACKET_INVALID"):
            hq_pre_action.evaluate_pre_action(
                self.context(),
                context_packet={"schema": "WRONG", "status": "PROVEN"},
            )

    def test_cli_consumes_context_packet_without_archive_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context_path = root / "context.json"
            packet_path = root / "packet.json"
            context_path.write_text(json.dumps(self.context()), encoding="utf-8")
            packet_path.write_text(json.dumps(self.packet("NOT_PROVEN")), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/hq_pre_action.py",
                    "--context-path",
                    str(context_path),
                    "--context-packet-path",
                    str(packet_path),
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["reason"], "DURABLE_CONTEXT_NOT_PROVEN")


if __name__ == "__main__":
    unittest.main()
