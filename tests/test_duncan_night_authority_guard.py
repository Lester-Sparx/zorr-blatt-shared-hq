from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.duncan_night_archive import archive_duncan_night_event, rebuild_duncan_context


class DuncanNightAuthorityGuardTests(unittest.TestCase):
    @staticmethod
    def report(extra_line: str, cycle: str) -> str:
        return f"""DUNCAN_NIGHT_REPORT_R01
CYCLE_ID = {cycle}
SOURCE_WINDOW = bounded authority guard test
MAIN_HEAD_OBSERVED = deadbeef
DAY_EVENTS_REVIEWED = issue:206
ANIME_TOPICS_STUDIED = silhouette readability
OPEN_SOURCE_CODE_INSPECTED = opencv/opencv; ref=4.x; license=Apache-2.0
REFERENCE_PRINCIPLES = preserve identity-bearing structure
EXERCISES = bounded synthetic exercise
VERIFICATION = objective metric checked
FAILURES = aggressive variant failed
ROOT_CAUSES = over-cleaning
REGRESSION_RESULTS = prior lesson replay PASS
TRANSFER_TEST = changed/unseen fixture PASS
OWNER_TASTE_SIGNALS = no new preference inferred
ZORR_APPLICATION = candidate QC only
PRIME_CORE_CHANGED = NO
PRODUCTION_MUTATION = NO
{extra_line}
NEXT_TARGETS = another bounded case
SKILL_DELTA =
- silhouette_qc: UNTESTED -> PARTIAL

SELF_MODEL_DELTA =
- DUNCAN_METHOD_TEST = measurable verification

OWNER_TASTE_MODEL_DELTA =
- SILHOUETTE_FIRST = CONFIRMED_HIGH
"""

    @staticmethod
    def event(body: str, comment_id: int) -> bytes:
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

    def test_explicit_authority_escalation_flags_cannot_train(self) -> None:
        cases = (
            ("AUTHORITY_EXPANSION = YES", "AUTHORITY_EXPANSION_FORBIDDEN"),
            ("AUTO_MERGE = YES", "AUTO_MERGE_FORBIDDEN"),
            ("SELF_AWARDED_QC_PASS = YES", "SELF_AWARDED_QC_PASS_FORBIDDEN"),
        )
        metadata = {"event_name": "issue_comment", "actor": "Lester-Sparx"}
        for index, (line, expected_error) in enumerate(cases, start=1):
            with self.subTest(line=line), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                result = archive_duncan_night_event(
                    self.event(self.report(line, f"DNR01-AUTH-{index:03d}"), 7400 + index),
                    root,
                    metadata,
                )
                self.assertIsNotNone(result)
                self.assertFalse(result["training_eligible"])
                self.assertIn(expected_error, result["validation_errors"])
                self.assertEqual(rebuild_duncan_context(root)["skills"], {})


if __name__ == "__main__":
    unittest.main()
