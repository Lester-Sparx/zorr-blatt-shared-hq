from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.duncan_night_archive import archive_duncan_night_event, rebuild_duncan_context


class DuncanNightStaleHeadGateTests(unittest.TestCase):
    def test_stale_main_head_cannot_train_future_context(self) -> None:
        body = """DUNCAN_NIGHT_REPORT_R01
CYCLE_ID = DNR01-STALE-001
SOURCE_WINDOW = bounded changed case
MAIN_HEAD_OBSERVED = stale-head
DAY_EVENTS_REVIEWED = issue:206 plus fresh task evidence
ANIME_TOPICS_STUDIED = silhouette readability
OPEN_SOURCE_CODE_INSPECTED = opencv/opencv; ref=4.x; license=Apache-2.0; modules=imgproc; APIs=connectedComponentsWithStats
REFERENCE_PRINCIPLES = preserve identity-bearing structure
EXERCISES = bounded synthetic exercise and changed fixture
VERIFICATION = objective metric checked against expected result
FAILURES = aggressive variant failed as expected
ROOT_CAUSES = over-cleaning destroyed identity-bearing structure
REGRESSION_RESULTS = prior bounded lesson replay PASS
TRANSFER_TEST = changed/unseen fixture PASS
OWNER_TASTE_SIGNALS = no new preference inferred
ZORR_APPLICATION = candidate QC method only
PRIME_CORE_CHANGED = NO
PRODUCTION_MUTATION = NO
NEXT_TARGETS = further changed case
SKILL_DELTA =
- silhouette_qc: UNTESTED -> PARTIAL

SELF_MODEL_DELTA =
- DUNCAN_METHOD_TEST = prefer measurable verification

OWNER_TASTE_MODEL_DELTA =
- SILHOUETTE_FIRST = CONFIRMED_HIGH
"""
        event = json.dumps(
            {
                "action": "created",
                "issue": {"number": 111},
                "comment": {
                    "id": 7301,
                    "body": body,
                    "user": {"login": "Lester-Sparx"},
                },
            },
            sort_keys=True,
        ).encode("utf-8")
        metadata = {
            "event_name": "issue_comment",
            "actor": "Lester-Sparx",
            "trusted_main_head": "fresh-head",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = archive_duncan_night_event(event, root, metadata)
            self.assertIsNotNone(result)
            self.assertFalse(result["training_eligible"])
            self.assertIn("MAIN_HEAD_STALE", result["validation_errors"])
            self.assertEqual(rebuild_duncan_context(root)["skills"], {})


if __name__ == "__main__":
    unittest.main()
