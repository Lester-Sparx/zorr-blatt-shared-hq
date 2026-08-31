from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.duncan_night_archive import archive_duncan_night_event, rebuild_duncan_context


class DuncanNightModelScopeGuardTests(unittest.TestCase):
    @staticmethod
    def event(self_model_key: str, *, comment_id: int) -> bytes:
        body = "\n".join(
            [
                "DUNCAN_NIGHT_REPORT_R01",
                f"CYCLE_ID = DNR01-MODEL-SCOPE-{comment_id}",
                "SOURCE_WINDOW = bounded learning cycle",
                "MAIN_HEAD_OBSERVED = deadbeef",
                "DAY_EVENTS_REVIEWED = issue:206 personality law",
                "ANIME_TOPICS_STUDIED = silhouette readability",
                "OPEN_SOURCE_CODE_INSPECTED = opencv/opencv; ref=4.x; license=Apache-2.0; modules=imgproc; APIs=connectedComponentsWithStats",
                "REFERENCE_PRINCIPLES = preserve identity-bearing structure",
                "EXERCISES = bounded synthetic exercise",
                "VERIFICATION = objective metric checked",
                "FAILURES = one aggressive variant failed",
                "ROOT_CAUSES = over-cleaning removed identity signal",
                "REGRESSION_RESULTS = prior bounded lesson replay PASS",
                "TRANSFER_TEST = changed unseen fixture PASS",
                "OWNER_TASTE_SIGNALS = no new preference inferred",
                "ZORR_APPLICATION = candidate learning method only",
                "PRIME_CORE_CHANGED = NO",
                "PRODUCTION_MUTATION = NO",
                "NEXT_TARGETS = another bounded transfer case",
                "SKILL_DELTA =",
                "- silhouette_qc: UNTESTED -> PARTIAL",
                "",
                "SELF_MODEL_DELTA =",
                f"- {self_model_key} = OWNER",
                "",
                "OWNER_TASTE_MODEL_DELTA =",
                "- SILHOUETTE_FIRST = CONFIRMED_HIGH",
            ]
        ) + "\n"
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
    def metadata() -> dict[str, str]:
        return {"event_name": "issue_comment", "actor": "Lester-Sparx"}

    def test_self_model_cannot_persist_protected_authority_or_canon_namespaces(self) -> None:
        protected_keys = (
            "owner_relationship",
            "constitution",
            "authority",
            "authority_boundary",
            "canon",
            "production_lock",
            "prime_core",
        )
        for offset, key in enumerate(protected_keys, start=1):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                result = archive_duncan_night_event(
                    self.event(key, comment_id=8100 + offset),
                    root,
                    self.metadata(),
                )
                self.assertIsNotNone(result)
                self.assertFalse(result["training_eligible"])
                self.assertIn(
                    f"SELF_MODEL_PROTECTED_KEY:{key}",
                    result["validation_errors"],
                )
                context = rebuild_duncan_context(root)
                self.assertEqual(context["self_model"], {})
                self.assertEqual(context["skills"], {})
                self.assertEqual(context["source_events"], [])

    def test_legitimate_self_model_method_key_remains_trainable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = archive_duncan_night_event(
                self.event("confidence_calibration", comment_id=8199),
                root,
                self.metadata(),
            )
            self.assertIsNotNone(result)
            self.assertTrue(result["training_eligible"])
            context = rebuild_duncan_context(root)
            self.assertEqual(context["self_model"]["confidence_calibration"], "OWNER")
            self.assertEqual(context["skills"]["silhouette_qc"], "PARTIAL")


if __name__ == "__main__":
    unittest.main()
