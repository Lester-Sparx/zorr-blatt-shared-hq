from __future__ import annotations

import unittest

from scripts import hq_unified_archive as archive


class UnifiedArchivePreActionTests(unittest.TestCase):
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

    def _decide(
        self,
        context: dict[str, object],
        learning_policy: dict[str, object] | None = None,
    ) -> dict[str, object]:
        self.assertTrue(
            hasattr(archive, "evaluate_pre_action"),
            "evaluate_pre_action must exist before pre-action enforcement can pass",
        )
        return archive.evaluate_pre_action(context, learning_policy=learning_policy)  # type: ignore[attr-defined]

    def test_incident_replay_exact_owner_asset_blocks_search(self) -> None:
        result = self._decide(
            self._context(
                action="SEARCH_ASSET",
                directlyAdvancesPhysicalResult=False,
                exactOwnerInputProvided=True,
            )
        )
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["reason"], "EXACT_OWNER_INPUT_SUPERSEDES_SEARCH")

    def test_incident_replay_proven_prerequisite_blocks_reverification(self) -> None:
        result = self._decide(
            self._context(
                action="VERIFY_PREREQUISITE",
                directlyAdvancesPhysicalResult=False,
                prerequisiteAlreadyProven=True,
            )
        )
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["reason"], "PREREQUISITE_ALREADY_PROVEN")

    def test_incident_replay_process_mutation_requires_proven_process_blocker(self) -> None:
        result = self._decide(
            self._context(
                action="PROCESS_MUTATION",
                directlyAdvancesPhysicalResult=False,
                provenProcessBlocker=False,
            )
        )
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["reason"], "PROCESS_MUTATION_REQUIRES_PROVEN_PROCESS_BLOCKER")

    def test_incident_replay_active_attempt_owns_path(self) -> None:
        result = self._decide(
            self._context(
                action="PROCESS_MUTATION",
                directlyAdvancesPhysicalResult=False,
                activeAttempt=True,
                provenProcessBlocker=True,
            )
        )
        self.assertEqual(result["decision"], "WAIT")
        self.assertEqual(result["reason"], "ACTIVE_ATTEMPT_OWNS_PATH")

    def test_incident_replay_owner_is_not_a_courier(self) -> None:
        result = self._decide(
            self._context(
                action="REQUEST_OWNER_ACTION",
                directlyAdvancesPhysicalResult=False,
                provenExternalBoundary=False,
            )
        )
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["reason"], "OWNER_IS_NOT_A_COURIER")

    def test_normal_product_step_is_allowed(self) -> None:
        result = self._decide(self._context())
        self.assertEqual(result["schema"], "ZB_PRE_ACTION_DECISION_V1")
        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(result["reason"], "PRE_ACTION_GATE_PASS")

    def test_read_active_result_is_allowed_while_attempt_is_running(self) -> None:
        result = self._decide(
            self._context(
                action="READ_ACTIVE_RESULT",
                directlyAdvancesPhysicalResult=False,
                activeAttempt=True,
            )
        )
        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(result["reason"], "PRE_ACTION_GATE_PASS")

    def test_first_minimal_process_repair_after_proven_blocker_is_allowed(self) -> None:
        result = self._decide(
            self._context(
                action="PROCESS_MUTATION",
                directlyAdvancesPhysicalResult=True,
                provenProcessBlocker=True,
                processMutationCountForBlocker=0,
            )
        )
        self.assertEqual(result["decision"], "ALLOW")

    def test_repeat_process_mutation_requires_new_physical_blocker(self) -> None:
        blocked = self._decide(
            self._context(
                action="PROCESS_MUTATION",
                directlyAdvancesPhysicalResult=True,
                provenProcessBlocker=True,
                processMutationCountForBlocker=1,
                newPhysicalBlocker=False,
            )
        )
        self.assertEqual(blocked["decision"], "BLOCK")
        self.assertEqual(blocked["reason"], "REPEAT_PROCESS_MUTATION_REQUIRES_NEW_BLOCKER")

        allowed = self._decide(
            self._context(
                action="PROCESS_MUTATION",
                directlyAdvancesPhysicalResult=True,
                provenProcessBlocker=True,
                processMutationCountForBlocker=1,
                newPhysicalBlocker=True,
            )
        )
        self.assertEqual(allowed["decision"], "ALLOW")

    def test_owner_action_requires_proven_external_boundary(self) -> None:
        result = self._decide(
            self._context(
                action="REQUEST_OWNER_ACTION",
                directlyAdvancesPhysicalResult=False,
                provenExternalBoundary=True,
            )
        )
        self.assertEqual(result["decision"], "OWNER_REQUIRED")
        self.assertEqual(result["reason"], "PROVEN_EXTERNAL_BOUNDARY")

    def test_pass_claim_requires_fresh_verification(self) -> None:
        blocked = self._decide(
            self._context(
                action="CLAIM_PASS",
                directlyAdvancesPhysicalResult=True,
                freshVerificationEvidence=False,
            )
        )
        self.assertEqual(blocked["decision"], "BLOCK")
        self.assertEqual(blocked["reason"], "FRESH_VERIFICATION_REQUIRED")

        allowed = self._decide(
            self._context(
                action="CLAIM_PASS",
                directlyAdvancesPhysicalResult=True,
                freshVerificationEvidence=True,
            )
        )
        self.assertEqual(allowed["decision"], "ALLOW")

    def test_image_mutation_requires_explicit_owner_command(self) -> None:
        blocked = self._decide(
            self._context(
                action="IMAGE_MUTATION",
                directlyAdvancesPhysicalResult=True,
                explicitOwnerImageMutationCommand=False,
            )
        )
        self.assertEqual(blocked["decision"], "BLOCK")
        self.assertEqual(blocked["reason"], "OWNER_IMAGE_MUTATION_COMMAND_REQUIRED")

        allowed = self._decide(
            self._context(
                action="IMAGE_MUTATION",
                directlyAdvancesPhysicalResult=True,
                explicitOwnerImageMutationCommand=True,
            )
        )
        self.assertEqual(allowed["decision"], "ALLOW")

    def test_non_product_busywork_is_blocked(self) -> None:
        result = self._decide(
            self._context(
                action="EXECUTE_PRODUCT_STEP",
                directlyAdvancesPhysicalResult=False,
            )
        )
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["reason"], "NO_DIRECT_PRODUCT_PROGRESS")

    def test_invalid_context_fails_closed(self) -> None:
        self.assertTrue(hasattr(archive, "evaluate_pre_action"))
        context = self._context()
        del context["activeAttempt"]
        with self.assertRaisesRegex(archive.UnifiedArchiveError, "PRE_ACTION_CONTEXT_MISSING"):
            archive.evaluate_pre_action(context)  # type: ignore[attr-defined]

        with self.assertRaisesRegex(archive.UnifiedArchiveError, "PRE_ACTION_CONTEXT_INVALID"):
            archive.evaluate_pre_action(  # type: ignore[attr-defined]
                self._context(processMutationCountForBlocker=-1)
            )

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


if __name__ == "__main__":
    unittest.main()
