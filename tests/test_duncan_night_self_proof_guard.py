from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.duncan_night_archive import archive_duncan_night_event, rebuild_duncan_context


class DuncanNightSelfProofGuardTests(unittest.TestCase):
    @staticmethod
    def event() -> bytes:
        body = """DUNCAN_NIGHT_REPORT_R01
CYCLE_ID = DNR01-SELF-PROOF-001
SOURCE_WINDOW = bounded self-proof guard test
MAIN_HEAD_OBSERVED = deadbeef
DAY_EVENTS_REVIEWED = issue:206 plus Salvador Shadow promotion pattern
ANIME_TOPICS_STUDIED = silhouette readability
OPEN_SOURCE_CODE_INSPECTED = existing ZORR Salvador Shadow reducer; no new framework
REFERENCE_PRINCIPLES = same-runtime learning may improve partial skill without self-certification
EXERCISES = bounded synthetic exercise
VERIFICATION = objective metric checked inside the same learning cycle
FAILURES = aggressive variant failed
ROOT_CAUSES = over-cleaning
REGRESSION_RESULTS = prior lesson replay PASS
TRANSFER_TEST = changed/unseen fixture PASS
OWNER_TASTE_SIGNALS = no new preference inferred
ZORR_APPLICATION = candidate QC only
PRIME_CORE_CHANGED = NO
PRODUCTION_MUTATION = NO
NEXT_TARGETS = independent proof path for promotion
SKILL_DELTA =
- silhouette_qc: UNTESTED -> PROVEN

SELF_MODEL_DELTA =
- DUNCAN_METHOD_TEST = same-cycle evidence is useful but not independent certification

OWNER_TASTE_MODEL_DELTA =
- SILHOUETTE_FIRST = CONFIRMED_HIGH
"""
        return json.dumps(
            {
                "action": "created",
                "issue": {"number": 111},
                "comment": {
                    "id": 7501,
                    "body": body,
                    "user": {"login": "Lester-Sparx"},
                },
            },
            sort_keys=True,
        ).encode("utf-8")

    def test_night_school_self_report_cannot_self_promote_skill_to_proven(self) -> None:
        metadata = {"event_name": "issue_comment", "actor": "Lester-Sparx"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = archive_duncan_night_event(self.event(), root, metadata)
            self.assertIsNotNone(result)
            self.assertFalse(result["training_eligible"])
            self.assertIn("SELF_REPORTED_PROVEN_FORBIDDEN", result["validation_errors"])
            self.assertEqual(rebuild_duncan_context(root)["skills"], {})


if __name__ == "__main__":
    unittest.main()
