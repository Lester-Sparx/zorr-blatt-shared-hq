from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.duncan_night_archive import (
    CONTEXT_REL,
    archive_duncan_night_event,
    rebuild_duncan_context,
)


class DuncanNightArchiveTests(unittest.TestCase):
    @staticmethod
    def metadata(run_id: str = "99001", run_attempt: str = "1") -> dict[str, str]:
        return {
            "event_name": "issue_comment",
            "run_id": run_id,
            "run_attempt": run_attempt,
            "repository": "Lester-Sparx/zorr-blatt-shared-hq",
            "actor": "Lester-Sparx",
        }

    @staticmethod
    def event(body: str, comment_id: int = 7001) -> bytes:
        return json.dumps(
            {
                "action": "created",
                "issue": {"number": 111},
                "comment": {
                    "id": comment_id,
                    "body": body,
                    "user": {"login": "Lester-Sparx"},
                },
            },
            sort_keys=True,
        ).encode("utf-8")

    @staticmethod
    def report(
        *,
        cycle: str = "DNR01-TEST-001",
        skill_state: str = "PARTIAL",
        prime_core_changed: str = "NO",
        production_mutation: str = "NO",
    ) -> str:
        return f"""DUNCAN_NIGHT_REPORT_R01
CYCLE_ID = {cycle}
MAIN_HEAD_OBSERVED = deadbeef
PRIME_CORE_CHANGED = {prime_core_changed}
PRODUCTION_MUTATION = {production_mutation}

SKILL_DELTA =
- silhouette_qc: UNTESTED -> {skill_state}

SELF_MODEL_DELTA =
- DUNCAN_METHOD_TEST = prefer measurable OSS verification

OWNER_TASTE_MODEL_DELTA =
- SILHOUETTE_FIRST = CONFIRMED_HIGH

NEXT_TARGETS =
- transfer test
"""

    def test_valid_partial_skill_delta_updates_rebuildable_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = archive_duncan_night_event(
                self.event(self.report()), root, self.metadata()
            )
            self.assertIsNotNone(result)
            self.assertTrue(result["training_eligible"])

            context = rebuild_duncan_context(root)
            self.assertEqual(context["schema"], "DUNCAN_CONTEXT_NEXT_V1")
            self.assertEqual(context["skills"]["silhouette_qc"], "PARTIAL")
            self.assertEqual(context["latest_cycle_id"], "DNR01-TEST-001")
            self.assertEqual(len(context["source_events"]), 1)
            self.assertTrue((root / CONTEXT_REL).is_file())

    def test_partial_plus_is_archived_as_invalid_derived_fact_but_cannot_train(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = archive_duncan_night_event(
                self.event(self.report(skill_state="PARTIAL+")), root, self.metadata()
            )
            self.assertIsNotNone(result)
            self.assertFalse(result["training_eligible"])
            self.assertIn("SKILL_STATE_INVALID:PARTIAL+", result["validation_errors"])

            context = rebuild_duncan_context(root)
            self.assertEqual(context["skills"], {})
            self.assertEqual(context["source_events"], [])

    def test_prime_core_mutation_attempt_cannot_train(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = archive_duncan_night_event(
                self.event(self.report(prime_core_changed="YES")), root, self.metadata()
            )
            self.assertIsNotNone(result)
            self.assertFalse(result["training_eligible"])
            self.assertIn("PRIME_CORE_MUTATION_FORBIDDEN", result["validation_errors"])
            self.assertEqual(rebuild_duncan_context(root)["skills"], {})

    def test_rebuild_is_byte_identical_for_same_validated_event_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_duncan_night_event(
                self.event(self.report(), comment_id=7001), root, self.metadata("99001")
            )
            archive_duncan_night_event(
                self.event(
                    self.report(cycle="DNR01-TEST-002", skill_state="PROVEN"),
                    comment_id=7002,
                ),
                root,
                self.metadata("99002"),
            )

            first = rebuild_duncan_context(root)
            first_bytes = (root / CONTEXT_REL).read_bytes()
            second = rebuild_duncan_context(root)
            second_bytes = (root / CONTEXT_REL).read_bytes()

            self.assertEqual(first, second)
            self.assertEqual(first_bytes, second_bytes)
            self.assertEqual(second["skills"]["silhouette_qc"], "PROVEN")
            self.assertEqual(second["latest_cycle_id"], "DNR01-TEST-002")


if __name__ == "__main__":
    unittest.main()
