from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class UnifiedArchivePreActionTests(unittest.TestCase):
    @staticmethod
    def _gate_module():
        try:
            from scripts import hq_pre_action
        except ImportError as exc:
            raise AssertionError("scripts.hq_pre_action must exist before pre-action enforcement can pass") from exc
        return hq_pre_action

    @staticmethod
    def _context(**overrides: object) -> dict[str, object]:
        context: dict[str, object] = {
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
        context.update(overrides)
        return context

    @staticmethod
    def _terminal_pass_fact() -> dict[str, object]:
        return {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": "legacy-regression-pass",
            "class": "E2",
            "key": "RESULT",
            "value": "PASS",
            "exclusive": True,
            "verified": True,
            "authority": "GITHUB",
            "created_at": "2026-08-31T19:10:00Z",
            "scope_tags": ["ZORR"],
            "source_refs": ["github:test:legacy-regression-pass"],
            "supersedes": [],
        }

    @classmethod
    def _packet(cls, context: dict[str, object]) -> dict[str, object]:
        facts: list[dict[str, object]] = []
        if context.get("action") == "CLAIM_PASS" and context.get("freshVerificationEvidence") is True:
            facts.append(cls._terminal_pass_fact())
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": [{"key": "CURRENT_TASK", "value": "legacy-pre-action-regression"}],
            "current_state": {
                "schema": "ZB_CONTEXT_CURRENT_STATE_V1",
                "facts": facts,
            },
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["github:test:legacy-pre-action-regression"],
        }

    def _decide(
        self,
        context: dict[str, object],
        learning_policy: dict[str, object] | None = None,
    ) -> dict[str, object]:
        gate = self._gate_module()
        return gate.evaluate_pre_action(
            context,
            learning_policy=learning_policy,
            context_packet=self._packet(context),
        )

    def test_incident_replay_exact_owner_asset_blocks_search(self) -> None:
        result = self._decide(self._context(action="SEARCH_ASSET", directlyAdvancesPhysicalResult=False, exactOwnerInputProvided=True))
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "EXACT_OWNER_INPUT_SUPERSEDES_SEARCH"))

    def test_incident_replay_proven_prerequisite_blocks_reverification(self) -> None:
        result = self._decide(self._context(action="VERIFY_PREREQUISITE", directlyAdvancesPhysicalResult=False, prerequisiteAlreadyProven=True))
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "PREREQUISITE_ALREADY_PROVEN"))

    def test_incident_replay_process_mutation_requires_proven_process_blocker(self) -> None:
        result = self._decide(self._context(action="PROCESS_MUTATION", directlyAdvancesPhysicalResult=False, provenProcessBlocker=False))
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "PROCESS_MUTATION_REQUIRES_PROVEN_PROCESS_BLOCKER"))

    def test_incident_replay_active_attempt_owns_path(self) -> None:
        result = self._decide(self._context(action="PROCESS_MUTATION", directlyAdvancesPhysicalResult=False, activeAttempt=True, provenProcessBlocker=True))
        self.assertEqual((result["decision"], result["reason"]), ("WAIT", "ACTIVE_ATTEMPT_OWNS_PATH"))

    def test_incident_replay_owner_is_not_a_courier(self) -> None:
        result = self._decide(self._context(action="REQUEST_OWNER_ACTION", directlyAdvancesPhysicalResult=False, provenExternalBoundary=False))
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "OWNER_IS_NOT_A_COURIER"))

    def test_normal_product_step_is_allowed(self) -> None:
        result = self._decide(self._context())
        self.assertEqual(result["schema"], "ZB_PRE_ACTION_DECISION_V1")
        self.assertEqual((result["decision"], result["reason"]), ("ALLOW", "PRE_ACTION_GATE_PASS"))

    def test_read_active_result_is_allowed_while_attempt_is_running(self) -> None:
        result = self._decide(self._context(action="READ_ACTIVE_RESULT", directlyAdvancesPhysicalResult=False, activeAttempt=True))
        self.assertEqual(result["decision"], "ALLOW")

    def test_first_minimal_process_repair_after_proven_blocker_is_allowed(self) -> None:
        result = self._decide(self._context(action="PROCESS_MUTATION", provenProcessBlocker=True, processMutationCountForBlocker=0))
        self.assertEqual(result["decision"], "ALLOW")

    def test_repeat_process_mutation_requires_new_physical_blocker(self) -> None:
        gate = self._gate_module()
        blocked = self._decide(self._context(action="PROCESS_MUTATION", provenProcessBlocker=True, processMutationCountForBlocker=1, newPhysicalBlocker=False))
        self.assertEqual((blocked["decision"], blocked["reason"]), ("BLOCK", "REPEAT_PROCESS_MUTATION_REQUIRES_NEW_BLOCKER"))

        caller_only = self._decide(self._context(action="PROCESS_MUTATION", provenProcessBlocker=True, processMutationCountForBlocker=1, newPhysicalBlocker=True))
        self.assertEqual(
            (caller_only["decision"], caller_only["reason"]),
            ("BLOCK", "DURABLE_NEW_BLOCKER_NOT_PROVEN"),
        )

        context = self._context(action="PROCESS_MUTATION", provenProcessBlocker=True, processMutationCountForBlocker=1, newPhysicalBlocker=True)
        packet = self._packet(context)
        packet["current_state"]["facts"].extend(
            [
                {
                    "schema": "ZB_CONTEXT_FACT_V1",
                    "fact_id": "new-physical-blocker-proven",
                    "class": "E2",
                    "key": "NEW_PHYSICAL_BLOCKER",
                    "value": True,
                    "exclusive": True,
                    "verified": True,
                    "authority": "GITHUB",
                    "created_at": "2026-08-31T20:31:00Z",
                    "scope_tags": ["LESTER", "SECURITY_R02"],
                    "source_refs": ["github:test:new-physical-blocker-proven"],
                    "supersedes": [],
                },
                {
                    "schema": "ZB_CONTEXT_FACT_V1",
                    "fact_id": "current-error-signature-distinct",
                    "class": "E2",
                    "key": "ERROR_SIGNATURE",
                    "value": "physical:disk-full",
                    "exclusive": True,
                    "verified": True,
                    "authority": "GITHUB",
                    "created_at": "2026-08-31T20:31:01Z",
                    "scope_tags": ["LESTER", "SECURITY_R02"],
                    "source_refs": ["github:test:current-error-signature-distinct"],
                    "supersedes": [],
                },
                {
                    "schema": "ZB_CONTEXT_FACT_V1",
                    "fact_id": "prior-process-error-signature",
                    "class": "E2",
                    "key": "PROCESS_MUTATION_ERROR_SIGNATURE",
                    "value": "hq-schema:assertion-error",
                    "exclusive": True,
                    "verified": True,
                    "authority": "GITHUB",
                    "created_at": "2026-08-31T20:31:02Z",
                    "scope_tags": ["LESTER", "SECURITY_R02"],
                    "source_refs": ["github:test:prior-process-error-signature"],
                    "supersedes": [],
                },
            ]
        )
        packet["current_state"] = gate.project_current_state(packet["current_state"]["facts"])
        allowed = gate.evaluate_pre_action(context, context_packet=packet)
        self.assertEqual(allowed["decision"], "ALLOW")

    def test_repeat_process_mutation_cannot_bypass_gate_by_relabeling_action(self) -> None:
        disguised = self._decide(
            self._context(
                action="EXECUTE_PRODUCT_STEP",
                provenProcessBlocker=True,
                processMutationCountForBlocker=1,
                newPhysicalBlocker=False,
            )
        )
        self.assertEqual(
            (disguised["decision"], disguised["reason"]),
            ("BLOCK", "REPEAT_PROCESS_MUTATION_REQUIRES_NEW_BLOCKER"),
        )

    def test_repeat_process_mutation_cannot_bypass_gate_by_resetting_caller_count(self) -> None:
        gate = self._gate_module()
        context = self._context(
            action="EXECUTE_PRODUCT_STEP",
            provenProcessBlocker=True,
            processMutationCountForBlocker=0,
            newPhysicalBlocker=False,
        )
        packet = self._packet(context)
        packet["current_state"]["facts"].append(
            {
                "schema": "ZB_CONTEXT_FACT_V1",
                "fact_id": "process-mutation-count-1",
                "class": "E2",
                "key": "PROCESS_MUTATION_COUNT",
                "value": 1,
                "exclusive": True,
                "verified": True,
                "authority": "GITHUB",
                "created_at": "2026-08-31T20:00:00Z",
                "scope_tags": ["LESTER", "SECURITY_R02"],
                "source_refs": ["github:test:process-mutation-count-1"],
                "supersedes": [],
            }
        )
        result = gate.evaluate_pre_action(context, context_packet=packet)
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "REPEAT_PROCESS_MUTATION_REQUIRES_NEW_BLOCKER"),
        )

    def test_owner_action_requires_proven_external_boundary(self) -> None:
        result = self._decide(self._context(action="REQUEST_OWNER_ACTION", directlyAdvancesPhysicalResult=False, provenExternalBoundary=True))
        self.assertEqual((result["decision"], result["reason"]), ("OWNER_REQUIRED", "PROVEN_EXTERNAL_BOUNDARY"))

    def test_pass_claim_requires_fresh_verification(self) -> None:
        blocked = self._decide(self._context(action="CLAIM_PASS", freshVerificationEvidence=False))
        self.assertEqual((blocked["decision"], blocked["reason"]), ("BLOCK", "FRESH_VERIFICATION_REQUIRED"))
        allowed = self._decide(self._context(action="CLAIM_PASS", freshVerificationEvidence=True))
        self.assertEqual(allowed["decision"], "ALLOW")

    def test_image_mutation_requires_explicit_owner_command(self) -> None:
        blocked = self._decide(self._context(action="IMAGE_MUTATION", explicitOwnerImageMutationCommand=False))
        self.assertEqual((blocked["decision"], blocked["reason"]), ("BLOCK", "OWNER_IMAGE_MUTATION_COMMAND_REQUIRED"))
        allowed = self._decide(self._context(action="IMAGE_MUTATION", explicitOwnerImageMutationCommand=True))
        self.assertEqual(allowed["decision"], "ALLOW")

    def test_non_product_busywork_is_blocked(self) -> None:
        result = self._decide(self._context(directlyAdvancesPhysicalResult=False))
        self.assertEqual((result["decision"], result["reason"]), ("BLOCK", "NO_DIRECT_PRODUCT_PROGRESS"))

    def test_invalid_context_fails_closed(self) -> None:
        gate = self._gate_module()
        context = self._context()
        del context["activeAttempt"]
        with self.assertRaisesRegex(gate.PreActionError, "PRE_ACTION_CONTEXT_MISSING"):
            gate.evaluate_pre_action(context)
        with self.assertRaisesRegex(gate.PreActionError, "PRE_ACTION_CONTEXT_INVALID"):
            gate.evaluate_pre_action(self._context(processMutationCountForBlocker=-1))

    def test_verified_learning_policy_is_surfaced_at_decision_point(self) -> None:
        policy = {
            "status": "PROVEN",
            "lesson_count": 1,
            "policy_prefix": "RULE = do not repeat a known process loop",
            "lessons": [{"verdict_id": "SV1-LOOP-001"}],
        }
        result = self._decide(self._context(), learning_policy=policy)
        self.assertEqual(result["learning"]["status"], "PROVEN")
        self.assertEqual(result["learning"]["lesson_count"], 1)
        self.assertEqual(result["learning"]["verdict_ids"], ["SV1-LOOP-001"])
        self.assertIn("do not repeat", result["learning"]["policy_prefix"])

    def test_cli_is_real_fail_closed_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self._context(action="SEARCH_ASSET", directlyAdvancesPhysicalResult=False, exactOwnerInputProvided=True)
            context_path = root / "context.json"
            packet_path = root / "packet.json"
            context_path.write_text(json.dumps(context), encoding="utf-8")
            packet_path.write_text(json.dumps(self._packet(context)), encoding="utf-8")
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
        self.assertEqual((payload["decision"], payload["reason"]), ("BLOCK", "EXACT_OWNER_INPUT_SUPERSEDES_SEARCH"))


if __name__ == "__main__":
    unittest.main()
