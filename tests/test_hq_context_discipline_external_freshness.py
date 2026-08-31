from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
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

    def test_unseen_stale_head_blocks_claim_pass_before_terminal_logic(self) -> None:
        result = hq_pre_action.evaluate_pre_action(
            self.context("CLAIM_PASS"),
            context_packet=self.packet("reviewed-head"),
            fresh_active_head="superseding-head",
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_STALE"),
        )

    def test_unseen_fresh_head_without_packet_head_fails_closed(self) -> None:
        packet = self.packet("unused-head")
        packet["current_state"] = {
            "schema": "ZB_CONTEXT_CURRENT_STATE_V1",
            "facts": [],
        }
        result = hq_pre_action.evaluate_pre_action(
            self.context(),
            context_packet=packet,
            fresh_active_head="fresh-head",
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_NOT_PROVEN"),
        )

    def test_matching_fresh_head_preserves_verified_learning_with_zero_payload_growth(self) -> None:
        policy = {
            "status": "PROVEN",
            "lesson_count": 1,
            "policy_prefix": "RULE = restore durable evidence before asserting state",
            "lessons": [{"verdict_id": "SV1-CONTEXT-UNSEEN-001"}],
        }
        packet = self.packet("fresh-head")
        baseline_packet = self.packet("fresh-head")
        baseline_packet["current_state"] = {
            "schema": "ZB_CONTEXT_CURRENT_STATE_V1",
            "facts": [],
        }
        baseline = hq_pre_action.evaluate_pre_action(
            self.context(),
            learning_policy=policy,
            context_packet=baseline_packet,
        )
        fresh_bound = hq_pre_action.evaluate_pre_action(
            self.context(),
            learning_policy=policy,
            context_packet=packet,
            fresh_active_head="fresh-head",
        )
        self.assertEqual(fresh_bound, baseline)
        self.assertEqual(fresh_bound["decision"], "ALLOW")
        self.assertEqual(fresh_bound["learning"]["status"], "PROVEN")
        self.assertEqual(
            fresh_bound["learning"]["verdict_ids"],
            ["SV1-CONTEXT-UNSEEN-001"],
        )
        self.assertEqual(
            len(json.dumps(fresh_bound, sort_keys=True)),
            len(json.dumps(baseline, sort_keys=True)),
        )

    def test_cli_external_head_binding_blocks_stale_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context_path = root / "context.json"
            packet_path = root / "packet.json"
            context_path.write_text(json.dumps(self.context()), encoding="utf-8")
            packet_path.write_text(json.dumps(self.packet("old-head")), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/hq_pre_action.py",
                    "--context-path",
                    str(context_path),
                    "--context-packet-path",
                    str(packet_path),
                    "--fresh-active-head",
                    "new-head",
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["reason"], "DURABLE_CONTEXT_STALE")


if __name__ == "__main__":
    unittest.main()
