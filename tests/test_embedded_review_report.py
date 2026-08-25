import unittest

from _support import ROOT, ROLES, registered_task
from hq_adapter import HQError, load_json, record_sha256, submit_review
from hq_validate import validate_review_evidence, validate_schema


QC_REPORT = {
    "format": "ZB_QC_REPORT_V1",
    "overallResult": "PASS",
    "checks": [
        {"id": "repository_validation", "result": "PASS"},
        {"id": "full_suite", "result": "PASS", "observed": "27/27"},
    ],
}


class EmbeddedReviewReportTest(unittest.TestCase):
    def test_submit_review_embeds_report_and_separates_all_three_hashes(self):
        _, task = registered_task()

        updated, review = submit_review(
            task, actor="duncan", kind="QC", result="PASS",
            report=QC_REPORT, roles=ROLES,
        )

        self.assertEqual(review["report"], QC_REPORT)
        self.assertEqual(review["reportSha256"], record_sha256(QC_REPORT))
        self.assertEqual(updated["qcReview"], record_sha256(review))
        self.assertEqual(len({task["artifactSha256"], review["reportSha256"], updated["qcReview"]}), 3)

    def test_submit_review_rejects_result_different_from_embedded_report(self):
        _, task = registered_task()
        with self.assertRaisesRegex(HQError, "RESULT"):
            submit_review(
                task, actor="duncan", kind="QC", result="FAIL",
                report=QC_REPORT, roles=ROLES,
            )

    def test_validator_rejects_report_digest_mismatch(self):
        _, task = registered_task()
        _, review = submit_review(
            task, actor="duncan", kind="QC", result="PASS",
            report=QC_REPORT, roles=ROLES,
        )
        review["reportSha256"] = "C" * 64

        with self.assertRaisesRegex(HQError, "REPORT SHA256"):
            validate_review_evidence(review)

    def test_validator_rejects_result_mismatch_even_with_valid_report_digest(self):
        _, task = registered_task()
        _, review = submit_review(
            task, actor="duncan", kind="QC", result="PASS",
            report=QC_REPORT, roles=ROLES,
        )
        review["result"] = "FAIL"

        with self.assertRaisesRegex(HQError, "RESULT"):
            validate_review_evidence(review)

    def test_validator_rejects_report_format_mismatched_with_review_kind(self):
        _, task = registered_task()
        architecture_report = {
            **QC_REPORT,
            "format": "ZB_ARCHITECTURE_REPORT_V1",
        }
        _, review = submit_review(
            task, actor="duncan", kind="QC", result="PASS",
            report=architecture_report, roles=ROLES,
        )

        with self.assertRaisesRegex(HQError, "FORMAT"):
            validate_review_evidence(review)

    def test_schema_requires_and_accepts_structured_embedded_report(self):
        _, task = registered_task()
        _, review = submit_review(
            task, actor="duncan", kind="QC", result="PASS",
            report=QC_REPORT, roles=ROLES,
        )
        schema = load_json(ROOT / "schemas/review.schema.json")

        validate_schema(review, schema)
        review.pop("report")
        with self.assertRaisesRegex(HQError, "missing"):
            validate_schema(review, schema)


if __name__ == "__main__":
    unittest.main()
