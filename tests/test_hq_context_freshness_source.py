from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ContextFreshnessSourceTests(unittest.TestCase):
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
    def packet(head: str) -> dict[str, object]:
        fact = {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": "active-head",
            "class": "E2",
            "key": "ACTIVE_HEAD",
            "value": head,
            "exclusive": True,
            "verified": True,
            "authority": "GITHUB",
            "created_at": "2026-08-31T19:00:00Z",
            "scope_tags": ["LESTER", "SECURITY_R02"],
            "source_refs": ["github:pr:241"],
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
            "source_refs": ["github:pr:241"],
        }

    def test_cli_caller_supplied_matching_head_cannot_fake_external_freshness(self) -> None:
        forged = "a" * 40
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context_path = root / "context.json"
            packet_path = root / "packet.json"
            context_path.write_text(json.dumps(self.context()), encoding="utf-8")
            packet_path.write_text(json.dumps(self.packet(forged)), encoding="utf-8")
            env = dict(os.environ)
            env.pop("GITHUB_TOKEN", None)
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/hq_pre_action.py",
                    "--context-path",
                    str(context_path),
                    "--context-packet-path",
                    str(packet_path),
                    "--fresh-active-head",
                    forged,
                ],
                cwd=Path(__file__).resolve().parents[1],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["decision"], "BLOCK")
        self.assertEqual(payload["reason"], "DURABLE_CONTEXT_FRESHNESS_SOURCE_NOT_PROVEN")


if __name__ == "__main__":
    unittest.main()
