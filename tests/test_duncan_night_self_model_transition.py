from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.duncan_night_archive import archive_duncan_night_event, rebuild_duncan_context


class DuncanNightSelfModelTransitionTests(unittest.TestCase):
    @staticmethod
    def event(*, comment_id: int, cycle: str, skill_before: str, self_value: str) -> bytes:
        body = "\n".join(
            [
                "DUNCAN_NIGHT_REPORT_R01",
                f"CYCLE_ID = {cycle}",
                "SOURCE_WINDOW = bounded learning cycle",
                "MAIN_HEAD_OBSERVED = deadbeef",
                "DAY_EVENTS_REVIEWED = issue:206 self model law",
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
                f"- silhouette_qc: {skill_before} -> PARTIAL",
                "",
                "SELF_MODEL_DELTA =",
                f"- confidence_calibration = {self_value}",
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
        return {
            "event_name": "issue_comment",
            "actor": "Lester-Sparx",
            "trusted_main_head": "deadbeef",
        }

    def test_later_self_report_cannot_silently_overwrite_stable_self_model_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = archive_duncan_night_event(
                self.event(
                    comment_id=8401,
                    cycle="DNR01-SELF-MODEL-001",
                    skill_before="UNTESTED",
                    self_value="prefer measured evidence",
                ),
                root,
                self.metadata(),
            )
            second = archive_duncan_night_event(
                self.event(
                    comment_id=8402,
                    cycle="DNR01-SELF-MODEL-002",
                    skill_before="PARTIAL",
                    self_value="trust first impression without measurement",
                ),
                root,
                self.metadata(),
            )
            self.assertTrue(first and first["training_eligible"])
            self.assertTrue(second and second["training_eligible"])

            context = rebuild_duncan_context(root)
            self.assertEqual(context["skills"].get("silhouette_qc"), "PARTIAL")
            self.assertEqual(
                context["self_model"].get("confidence_calibration"),
                "prefer measured evidence",
            )
            self.assertEqual(len(context["source_events"]), 2)

    def test_same_self_model_value_can_be_reaffirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for comment_id, cycle, before in (
                (8411, "DNR01-SELF-MODEL-SAME-001", "UNTESTED"),
                (8412, "DNR01-SELF-MODEL-SAME-002", "PARTIAL"),
            ):
                result = archive_duncan_night_event(
                    self.event(
                        comment_id=comment_id,
                        cycle=cycle,
                        skill_before=before,
                        self_value="prefer measured evidence",
                    ),
                    root,
                    self.metadata(),
                )
                self.assertTrue(result and result["training_eligible"])
            context = rebuild_duncan_context(root)
            self.assertEqual(
                context["self_model"].get("confidence_calibration"),
                "prefer measured evidence",
            )
            self.assertEqual(len(context["source_events"]), 2)


if __name__ == "__main__":
    unittest.main()
