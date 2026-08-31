from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.duncan_night_archive import archive_duncan_night_event, rebuild_duncan_context
from scripts.hq_archive_ingest import archive_event
from scripts.hq_archive_verify import verify_archive


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "zb-permanent-archive-v1.yml"


class DuncanNightArchiveWorkflowTests(unittest.TestCase):
    @staticmethod
    def event() -> bytes:
        body = """DUNCAN_NIGHT_REPORT_R01
CYCLE_ID = DNR01-WORKFLOW-001
MAIN_HEAD_OBSERVED = deadbeef
REGRESSION_RESULTS = Prior composition lesson replay PASS on bounded fixture.
TRANSFER_TEST = Changed/unseen composition fixture PASS; not used to tune original exercise.
PRIME_CORE_CHANGED = NO
PRODUCTION_MUTATION = NO

SKILL_DELTA =
- composition_qc: UNTESTED -> PARTIAL

SELF_MODEL_DELTA =
- DUNCAN_METHOD_WORKFLOW = verify derived state

OWNER_TASTE_MODEL_DELTA =
- SILHOUETTE_FIRST = CONFIRMED_HIGH
"""
        return json.dumps(
            {
                "action": "created",
                "issue": {"number": 111},
                "comment": {
                    "id": 81001,
                    "body": body,
                    "user": {"login": "Lester-Sparx"},
                },
            },
            sort_keys=True,
        ).encode("utf-8")

    @staticmethod
    def archive_metadata() -> dict[str, str]:
        return {
            "event_name": "issue_comment",
            "run_id": "99101",
            "run_attempt": "1",
            "repository": "Lester-Sparx/zorr-blatt-shared-hq",
            "actor": "Lester-Sparx",
            "workflow": "ZB Permanent Archive V1",
            "source_sha": "deadbeef",
            "source_ref": "refs/heads/main",
        }

    def test_permanent_archive_runs_duncan_reducer_inside_same_archive(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Derive DUNCAN Night School learning", text)
        self.assertIn("python3 -m scripts.duncan_night_archive", text)
        self.assertNotIn("duncan-night-v1.yml", text)

    def test_permanent_archive_bootstrap_guard_skips_duncan_until_trusted_main_contains_reducer(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if [[ -f scripts/duncan_night_archive.py ]]; then", text)
        self.assertIn("DUNCAN_NIGHT_ARCHIVE_NOT_ACTIVE_ON_TRUSTED_MAIN", text)

    def test_archive_verifier_rejects_tampered_duncan_context(self) -> None:
        raw = self.event()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_event(raw, root, self.archive_metadata())
            archive_duncan_night_event(
                raw,
                root,
                {"event_name": "issue_comment", "actor": "Lester-Sparx"},
            )
            rebuild_duncan_context(root)
            self.assertEqual(verify_archive(root)["events"], 1)

            context = root / "derived" / "duncan-night-v1" / "DUNCAN_CONTEXT_NEXT.json"
            payload = json.loads(context.read_text(encoding="utf-8"))
            payload["skills"]["composition_qc"] = "PROVEN"
            context.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(Exception, "DUNCAN_CONTEXT"):
                verify_archive(root)


if __name__ == "__main__":
    unittest.main()
