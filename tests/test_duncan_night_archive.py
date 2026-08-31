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
        skill_before: str = "UNTESTED",
        skill_state: str = "PARTIAL",
        prime_core_changed: str = "NO",
        production_mutation: str = "NO",
        regression_results: str | None = "Prior lesson replay PASS on bounded changed fixture.",
        transfer_test: str | None = "Changed/unseen fixture PASS; not used to tune the original exercise.",
        omit_fields: set[str] | None = None,
    ) -> str:
        omitted = set(omit_fields or set())
        scalar_fields: list[tuple[str, str | None]] = [
            ("CYCLE_ID", cycle),
            ("SOURCE_WINDOW", "2026-08-31 bounded learning cycle"),
            ("MAIN_HEAD_OBSERVED", "deadbeef"),
            ("DAY_EVENTS_REVIEWED", "issue:206 learning law and current durable evidence"),
            ("ANIME_TOPICS_STUDIED", "silhouette and negative-space readability"),
            (
                "OPEN_SOURCE_CODE_INSPECTED",
                "opencv/opencv; ref=4.x; license=Apache-2.0; modules=imgproc; APIs=connectedComponentsWithStats",
            ),
            ("REFERENCE_PRINCIPLES", "preserve identity-bearing structure under simplification"),
            ("EXERCISES", "bounded original synthetic exercise plus changed fixture"),
            ("VERIFICATION", "objective structure metric checked against expected result"),
            ("FAILURES", "aggressive variant intentionally failed identity preservation"),
            ("ROOT_CAUSES", "over-cleaning destroyed identity-bearing structure"),
            ("REGRESSION_RESULTS", regression_results),
            ("TRANSFER_TEST", transfer_test),
            ("OWNER_TASTE_SIGNALS", "no new preference inferred; existing durable law only"),
            ("ZORR_APPLICATION", "candidate QC method only; no production mutation"),
            ("PRIME_CORE_CHANGED", prime_core_changed),
            ("PRODUCTION_MUTATION", production_mutation),
            ("NEXT_TARGETS", "one further changed/unseen bounded case"),
        ]
        lines = ["DUNCAN_NIGHT_REPORT_R01"]
        for key, value in scalar_fields:
            if key in omitted or value is None:
                continue
            lines.append(f"{key} = {value}")
        lines.extend(
            [
                "SKILL_DELTA =",
                f"- silhouette_qc: {skill_before} -> {skill_state}",
                "",
                "SELF_MODEL_DELTA =",
                "- DUNCAN_METHOD_TEST = prefer measurable OSS verification",
                "",
                "OWNER_TASTE_MODEL_DELTA =",
                "- SILHOUETTE_FIRST = CONFIRMED_HIGH",
            ]
        )
        return "\n".join(lines) + "\n"

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

    def test_missing_authoritative_report_contract_field_cannot_train(self) -> None:
        required_fields = (
            "SOURCE_WINDOW",
            "DAY_EVENTS_REVIEWED",
            "ANIME_TOPICS_STUDIED",
            "OPEN_SOURCE_CODE_INSPECTED",
            "REFERENCE_PRINCIPLES",
            "EXERCISES",
            "VERIFICATION",
            "FAILURES",
            "ROOT_CAUSES",
            "OWNER_TASTE_SIGNALS",
            "ZORR_APPLICATION",
            "NEXT_TARGETS",
        )
        for index, field in enumerate(required_fields, start=1):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                result = archive_duncan_night_event(
                    self.event(
                        self.report(
                            cycle=f"DNR01-CONTRACT-{index:03d}",
                            omit_fields={field},
                        ),
                        comment_id=7200 + index,
                    ),
                    root,
                    self.metadata(str(99200 + index)),
                )
                self.assertIsNotNone(result)
                self.assertFalse(result["training_eligible"])
                self.assertIn(f"{field}_MISSING", result["validation_errors"])
                self.assertEqual(rebuild_duncan_context(root)["skills"], {})

    def test_missing_regression_or_unseen_transfer_cannot_train(self) -> None:
        cases = (
            ("missing-regression", None, "Changed/unseen fixture PASS.", "REGRESSION_RESULTS_MISSING"),
            ("missing-transfer", "Prior regression PASS.", None, "TRANSFER_TEST_MISSING"),
            ("empty-regression", "", "Changed/unseen fixture PASS.", "REGRESSION_RESULTS_MISSING"),
            ("empty-transfer", "Prior regression PASS.", "", "TRANSFER_TEST_MISSING"),
        )
        for index, (name, regression, transfer, expected_error) in enumerate(cases, start=1):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                result = archive_duncan_night_event(
                    self.event(
                        self.report(
                            cycle=f"DNR01-TRANSFER-{index:03d}",
                            regression_results=regression,
                            transfer_test=transfer,
                        ),
                        comment_id=7100 + index,
                    ),
                    root,
                    self.metadata(str(99100 + index)),
                )
                self.assertIsNotNone(result)
                self.assertFalse(result["training_eligible"])
                self.assertIn(expected_error, result["validation_errors"])
                self.assertEqual(rebuild_duncan_context(root)["skills"], {})

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
                    self.report(
                        cycle="DNR01-TEST-002",
                        skill_before="PARTIAL",
                        skill_state="PARTIAL",
                    ),
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
            self.assertEqual(second["skills"]["silhouette_qc"], "PARTIAL")
            self.assertEqual(second["latest_cycle_id"], "DNR01-TEST-002")


if __name__ == "__main__":
    unittest.main()
