from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts import hq_pre_action


class FakeGitHubApi:
    def __init__(self, payload: object):
        self.payload = payload
        self.urls: list[str] = []

    def _request_json(self, url: str) -> object:
        self.urls.append(url)
        return self.payload


class ContextFreshnessSourceTests(unittest.TestCase):
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

    def test_matching_remote_pr_head_allows_substantive_action(self) -> None:
        head = "1" * 40
        api = FakeGitHubApi({"head": {"sha": head}})
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(),
            context_packet=self.packet(head),
            github_api=api,
        )
        self.assertEqual((result["decision"], result["reason"]), ("ALLOW", "PRE_ACTION_GATE_PASS"))
        self.assertEqual(len(api.urls), 1)
        self.assertTrue(api.urls[0].endswith("/pulls/241"))

    def test_remote_pr_head_mismatch_blocks_as_stale(self) -> None:
        api = FakeGitHubApi({"head": {"sha": "2" * 40}})
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(),
            context_packet=self.packet("1" * 40),
            github_api=api,
        )
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "DURABLE_CONTEXT_STALE"))

    def test_malformed_remote_head_fails_closed(self) -> None:
        api = FakeGitHubApi({"head": {"sha": "not-a-sha"}})
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(),
            context_packet=self.packet("1" * 40),
            github_api=api,
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_FRESHNESS_SOURCE_NOT_PROVEN"),
        )

    def test_ambiguous_pr_provenance_fails_closed(self) -> None:
        packet = self.packet("1" * 40)
        packet["current_state"]["facts"][0]["source_refs"] = ["github:pr:241", "github:pr:242"]
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(),
            context_packet=packet,
            github_api=FakeGitHubApi({"head": {"sha": "1" * 40}}),
        )
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_FRESHNESS_SOURCE_NOT_PROVEN"),
        )

    def test_read_only_recovery_does_not_need_github_freshness(self) -> None:
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context("READ_REQUIRED_EVIDENCE"),
            context_packet=self.packet("1" * 40),
            github_api=None,
        )
        self.assertEqual((result["decision"], result["reason"]), ("ALLOW", "PRE_ACTION_GATE_PASS"))

    def test_matching_remote_head_preserves_verified_learning(self) -> None:
        head = "3" * 40
        policy = {
            "status": "PROVEN",
            "lesson_count": 1,
            "policy_prefix": "RULE = bind mutable authority to independent remote read",
            "lessons": [{"verdict_id": "SV1-FRESHNESS-PROVENANCE-001"}],
        }
        result = hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(),
            learning_policy=policy,
            context_packet=self.packet(head),
            github_api=FakeGitHubApi({"head": {"sha": head}}),
        )
        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(result["learning"]["status"], "PROVEN")
        self.assertEqual(result["learning"]["verdict_ids"], ["SV1-FRESHNESS-PROVENANCE-001"])


if __name__ == "__main__":
    unittest.main()
