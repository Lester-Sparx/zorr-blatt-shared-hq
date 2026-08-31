from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.duncan_night_archive import archive_duncan_night_event, rebuild_duncan_context


class DuncanNightSkillTransitionGateTests(unittest.TestCase):
    @staticmethod
    def report(*, cycle: str, before: str, after: str) -> str:
        return f"""DUNCAN_NIGHT_REPORT_R01
CYCLE_ID = {cycle}
SOURCE_WINDOW = bounded transition test
MAIN_HEAD_OBSERVED = deadbeef
DAY_EVENTS_REVIEWED = issue:206 plus prior durable Night School state
ANIME_TOPICS_STUDIED = silhouette readability
OPEN_SOURCE_CODE_INSPECTED = existing ZORR ordered-state reducers; no new framework
REFERENCE_PRINCIPLES = claimed before-state must match prior durable skill state
EXERCISES = bounded synthetic exercise
VERIFICATION = objective metric checked inside bounded exercise
FAILURES = deliberate changed-case failure recorded
ROOT_CAUSES = bounded method limit
REGRESSION_RESULTS = prior lesson replay PASS
TRANSFER_TEST = changed/unseen fixture PASS
OWNER_TASTE_SIGNALS = no new preference inferred
ZORR_APPLICATION = candidate QC only
PRIME_CORE_CHANGED = NO
PRODUCTION_MUTATION = NO
NEXT_TARGETS = another bounded case
SKILL_DELTA =
- silhouette_qc: {before} -> {after}

SELF_MODEL_DELTA =
- DUNCAN_METHOD_TRANSITION = use prior durable state rather than self-claimed history

OWNER_TASTE_MODEL_DELTA =
- SILHOUETTE_FIRST = CONFIRMED_HIGH
"""

    @classmethod
    def event(cls, *, cycle: str, before: str, after: str, comment_id: int) -> bytes:
        return json.dumps(
            {
                "action": "created",
                "issue": {"number": 111},
                "comment": {
                    "id": comment_id,
                    "body": cls.report(cycle=cycle, before=before, after=after),
                    "user": {"login": "Lester-Sparx"},
                },
            },
            sort_keys=True,
        ).encode("utf-8")

    @staticmethod
    def metadata() -> dict[str, str]:
        return {"event_name": "issue_comment", "actor": "Lester-Sparx"}

    def test_false_before_state_cannot_overwrite_prior_durable_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_duncan_night_event(
                self.event(
                    cycle="DNR01-TRANSITION-001",
                    before="UNTESTED",
                    after="PARTIAL",
                    comment_id=7601,
                ),
                root,
                self.metadata(),
            )
            archive_duncan_night_event(
                self.event(
                    cycle="DNR01-TRANSITION-002",
                    before="UNTESTED",
                    after="FAILED",
                    comment_id=7602,
                ),
                root,
                self.metadata(),
            )

            context = rebuild_duncan_context(root)
            self.assertEqual(context["skills"], {"silhouette_qc": "PARTIAL"})
            self.assertEqual(context["latest_cycle_id"], "DNR01-TRANSITION-001")
            self.assertEqual(len(context["source_events"]), 1)

    def test_out_of_order_ingest_still_reduces_by_durable_comment_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_duncan_night_event(
                self.event(
                    cycle="DNR01-TRANSITION-002",
                    before="PARTIAL",
                    after="FAILED",
                    comment_id=7602,
                ),
                root,
                self.metadata(),
            )
            archive_duncan_night_event(
                self.event(
                    cycle="DNR01-TRANSITION-001",
                    before="UNTESTED",
                    after="PARTIAL",
                    comment_id=7601,
                ),
                root,
                self.metadata(),
            )

            context = rebuild_duncan_context(root)
            self.assertEqual(context["skills"], {"silhouette_qc": "FAILED"})
            self.assertEqual(context["latest_cycle_id"], "DNR01-TRANSITION-002")
            self.assertEqual(len(context["source_events"]), 2)


if __name__ == "__main__":
    unittest.main()
