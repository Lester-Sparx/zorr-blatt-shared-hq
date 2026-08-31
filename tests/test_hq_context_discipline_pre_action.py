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
            "mandatory_anchors": [{"key": "CURRENT_TASK", "value": "#235"}],
            "current_state": {
                "schema": "ZB_CONTEXT_CURRENT_STATE_V1",
                "facts": [],
            },
            "jit_facets": {},
            "missing_facets": [] if status == "PROVEN" else ["CURRENT_HEAD"],
            "source_refs": ["github:issue:235"],
        }

    @staticmethod
    def head_fact(fact_id: str, value: str, source_ref: str) -> dict[str, object]:
        return {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": fact_id,
            "class": "E2",
            "key": "ACTIVE_HEAD",
            "value": value,
            "exclusive": True,
            "verified": True,
            "authority": "GITHUB",
            "created_at": "2026-08-31T18:00:00Z",
            "scope_tags": ["LESTER", "SECURITY_R02"],
            "source_refs": [source_ref],
            "supersedes": [],
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

    def test_forged_minimal_proven_packet_fails_closed(self) -> None:
        forged = {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "missing_facets": [],
            "source_refs": [],
        }
        with self.assertRaisesRegex(hq_pre_action.PreActionError, "CONTEXT_PACKET_INVALID"):
            hq_pre_action.evaluate_pre_action(self.context(), context_packet=forged)

    def test_unseen_conflicting_proven_heads_fail_closed_before_claim_pass(self) -> None:
        stale = self.packet("PROVEN")
        stale["current_state"] = {
            "schema": "ZB_CONTEXT_CURRENT_STATE_V1",
            "facts": [
                self.head_fact("head-a", "stale-head", "github:commit:stale-head"),
                self.head_fact("head-b", "fresh-head", "github:commit:fresh-head"),
            ],
        }
        claim = self.context()
        claim["action"] = "CLAIM_PASS"
        claim["freshVerificationEvidence"] = True
        with self.assertRaisesRegex(
            hq_pre_action.PreActionError,
            "DURABLE_CONTEXT_NOT_PROVEN|CONTEXT_PACKET_INVALID",
        ):
            hq_pre_action.evaluate_pre_action(claim, context_packet=stale)

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
