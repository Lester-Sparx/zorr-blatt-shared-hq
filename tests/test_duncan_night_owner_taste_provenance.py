from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.duncan_night_archive import archive_duncan_night_event, rebuild_duncan_context


class DuncanNightOwnerTasteProvenanceTests(unittest.TestCase):
    @staticmethod
    def event(comment_id: int = 8301) -> bytes:
        body = "\n".join(
            [
                "DUNCAN_NIGHT_REPORT_R01",
                "CYCLE_ID = DNR01-OWNER-TASTE-UNPROVEN",
                "SOURCE_WINDOW = bounded learning cycle",
                "MAIN_HEAD_OBSERVED = deadbeef",
                "DAY_EVENTS_REVIEWED = issue:206 owner taste law",
                "ANIME_TOPICS_STUDIED = silhouette readability",
                "OPEN_SOURCE_CODE_INSPECTED = opencv/opencv; ref=4.x; license=Apache-2.0; modules=imgproc; APIs=connectedComponentsWithStats",
                "REFERENCE_PRINCIPLES = preserve identity-bearing structure",
                "EXERCISES = bounded synthetic exercise",
                "VERIFICATION = objective metric checked",
                "FAILURES = one aggressive variant failed",
                "ROOT_CAUSES = over-cleaning removed identity signal",
                "REGRESSION_RESULTS = prior bounded lesson replay PASS",
                "TRANSFER_TEST = changed unseen fixture PASS",
                "OWNER_TASTE_SIGNALS = no new preference inferred; no external OWNER signal",
                "ZORR_APPLICATION = candidate learning method only",
                "PRIME_CORE_CHANGED = NO",
                "PRODUCTION_MUTATION = NO",
                "NEXT_TARGETS = another bounded transfer case",
                "SKILL_DELTA =",
                "- silhouette_qc: UNTESTED -> PARTIAL",
                "",
                "SELF_MODEL_DELTA =",
                "- confidence_calibration = prefer measured evidence",
                "",
                "OWNER_TASTE_MODEL_DELTA =",
                "- INVENTED_OWNER_TASTE = CONFIRMED_HIGH",
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
        return {
            "event_name": "issue_comment",
            "actor": "Lester-Sparx",
            "trusted_main_head": "deadbeef",
        }

    def test_self_report_without_owner_provenance_cannot_mutate_owner_taste_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = archive_duncan_night_event(self.event(), root, self.metadata())
            self.assertIsNotNone(result)
            self.assertTrue(result["training_eligible"])

            context = rebuild_duncan_context(root)
            self.assertEqual(context["skills"].get("silhouette_qc"), "PARTIAL")
            self.assertEqual(
                context["self_model"].get("confidence_calibration"),
                "prefer measured evidence",
            )
            self.assertNotIn("INVENTED_OWNER_TASTE", context["owner_taste_model"])


if __name__ == "__main__":
    unittest.main()
