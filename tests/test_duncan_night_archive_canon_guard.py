from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.duncan_night_archive import archive_duncan_night_event, rebuild_duncan_context


class DuncanNightArchiveCanonGuardTests(unittest.TestCase):
    @staticmethod
    def event(body: str) -> bytes:
        return json.dumps(
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

    @staticmethod
    def metadata() -> dict[str, str]:
        return {"event_name": "issue_comment", "actor": "Lester-Sparx"}

    def test_explicit_canon_mutation_attempt_cannot_train(self) -> None:
        body = """DUNCAN_NIGHT_REPORT_R01
CYCLE_ID = DNR01-CANON-GUARD-001
SOURCE_WINDOW = bounded test
MAIN_HEAD_OBSERVED = deadbeef
DAY_EVENTS_REVIEWED = issue:206
ANIME_TOPICS_STUDIED = silhouette
OPEN_SOURCE_CODE_INSPECTED = opencv/opencv; ref=4.x; license=Apache-2.0
REFERENCE_PRINCIPLES = preserve structure
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
CANON_MUTATION = YES
NEXT_TARGETS = another bounded case
SKILL_DELTA =
- silhouette_qc: UNTESTED -> PARTIAL

SELF_MODEL_DELTA =
- DUNCAN_METHOD_TEST = measurable verification

OWNER_TASTE_MODEL_DELTA =
- SILHOUETTE_FIRST = CONFIRMED_HIGH
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = archive_duncan_night_event(self.event(body), root, self.metadata())
            self.assertIsNotNone(result)
            self.assertFalse(result["training_eligible"])
            self.assertIn("CANON_MUTATION_FORBIDDEN", result["validation_errors"])
            self.assertEqual(rebuild_duncan_context(root)["skills"], {})


if __name__ == "__main__":
    unittest.main()
