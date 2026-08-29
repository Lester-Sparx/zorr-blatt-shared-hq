from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.salvador_shadow_archive import archive_salvador_shadow_event


class SalvadorShadowArchiveV1Tests(unittest.TestCase):
    @staticmethod
    def metadata(run_id: str = "99001") -> dict[str, str]:
        return {
            "event_name": "issue_comment",
            "run_id": run_id,
            "run_attempt": "1",
            "repository": "Lester-Sparx/zorr-blatt-shared-hq",
            "actor": "Lester-Sparx",
        }

    @staticmethod
    def evaluator_event(body: str, comment_id: int = 5436515963) -> bytes:
        return json.dumps(
            {
                "action": "created",
                "issue": {"number": 98},
                "comment": {
                    "id": comment_id,
                    "user": {"login": "Lester-Sparx"},
                    "body": body,
                },
            }
        ).encode("utf-8")

    @staticmethod
    def runtime_event(comment_id: int = 5434385533) -> bytes:
        return json.dumps(
            {
                "action": "created",
                "issue": {
                    "number": 72,
                    "body": "ZB_AGENT_TASK_V0\nTASK_ID = ZB-SALVADOR-PROD-001\nAGENT = SALVADOR\nTASK_KIND = CANON_REFERENCE_EDIT\nSTATE = ASSIGNED\nREFERENCE = LOCAL_INBOX",
                },
                "comment": {
                    "id": comment_id,
                    "user": {"login": "Lester-Sparx"},
                    "body": "ZB_AGENT_EVENT_V0\nTASK_ID = ZB-SALVADOR-PROD-001\nAGENT = SALVADOR\nSTATE = RESULT_READY\nBACKEND = COMFYUI_LOCAL\nEXECUTION_ID = 619cbaba-03f2-43e6-a1df-7c7291f557b4\nRESULT_SHA256 = 69f20660a52750eeafbc97877f0c064d008e8e3fa1ed25dcd005924bed5ec6bf\nERROR_CODE = NONE\n\nSALVADOR_RESULT_READY",
                },
            }
        ).encode("utf-8")

    @staticmethod
    def passing_evaluation() -> str:
        return """JINGO_TARGETED_STRESS_R02_EVALUATION

LOGICAL_EVALUATOR = JINGO
AUTHENTICATED_CONNECTOR_ACTOR = Lester-Sparx
CLASS = TRAINING DIAGNOSIS / SAME-RUNTIME
PROMOTION = NO
CERTIFICATION = NO
HOLDOUT = NO
GENERALIZATION_CLAIM = NO

=== SALVADOR ===
S-T01 = PASS
S-T02 = PASS
S-T03 = PASS
S-T04 = PASS
S-T05 = PASS

SALVADOR RESULT
PASS = 5/5
MAJOR = 0
CRITICAL = 0
UNSUPPORTED GUESS = 0
ROOT-CAUSE DISCRIMINATION = PASS

NO PROMOTION
NO CERTIFICATION
NO HOLDOUT CLAIM
"""

    def test_result_ready_is_archived_without_skill_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = archive_salvador_shadow_event(
                self.runtime_event(), Path(tmp), self.metadata()
            )
            self.assertIsNotNone(result)
            record = json.loads((Path(tmp) / result["shadow_relpath"]).read_text(encoding="utf-8"))
            self.assertEqual(record["kind"], "RUNTIME_OBSERVATION")
            self.assertEqual(record["state_before"], "UNTESTED")
            self.assertEqual(record["state_after"], "UNTESTED")
            self.assertFalse(record["training_eligible"])
            self.assertFalse(record["promotion_allowed"])

    def test_same_runtime_jingo_evaluation_is_partial_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = archive_salvador_shadow_event(
                self.evaluator_event(self.passing_evaluation()), Path(tmp), self.metadata()
            )
            self.assertIsNotNone(result)
            record = json.loads((Path(tmp) / result["shadow_relpath"]).read_text(encoding="utf-8"))
            self.assertEqual(record["kind"], "TRAINING_EVALUATION")
            self.assertTrue(record["training_eligible"])
            self.assertEqual(record["measurements"]["pass"], 5)
            self.assertEqual(record["measurements"]["total"], 5)
            self.assertEqual(record["measurements"]["critical"], 0)
            self.assertEqual(record["state_before"], "UNTESTED")
            self.assertEqual(record["state_after"], "PARTIAL")
            self.assertFalse(record["certification"])
            self.assertFalse(record["holdout"])
            self.assertFalse(record["promotion_allowed"])

    def test_critical_failure_overrides_high_pass_count(self) -> None:
        body = self.passing_evaluation().replace("PASS = 5/5", "PASS = 4/5").replace("CRITICAL = 0", "CRITICAL = 1")
        with tempfile.TemporaryDirectory() as tmp:
            result = archive_salvador_shadow_event(
                self.evaluator_event(body, 5436515964), Path(tmp), self.metadata()
            )
            self.assertIsNotNone(result)
            record = json.loads((Path(tmp) / result["shadow_relpath"]).read_text(encoding="utf-8"))
            self.assertEqual(record["measurements"]["pass"], 4)
            self.assertEqual(record["measurements"]["critical"], 1)
            self.assertEqual(record["state_after"], "FAILED")
            self.assertFalse(record["promotion_allowed"])

    def test_later_runtime_event_restores_prior_partial_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_salvador_shadow_event(
                self.evaluator_event(self.passing_evaluation()), root, self.metadata("99001")
            )
            result = archive_salvador_shadow_event(
                self.runtime_event(5434385534), root, self.metadata("99002")
            )
            self.assertIsNotNone(result)
            record = json.loads((root / result["shadow_relpath"]).read_text(encoding="utf-8"))
            self.assertEqual(record["state_before"], "PARTIAL")
            self.assertEqual(record["state_after"], "PARTIAL")

    def test_replay_of_older_event_remains_idempotent_after_newer_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            event = self.evaluator_event(self.passing_evaluation())
            first = archive_salvador_shadow_event(event, root, self.metadata("99001"))
            archive_salvador_shadow_event(
                self.runtime_event(5434385534), root, self.metadata("99002")
            )
            replay = archive_salvador_shadow_event(event, root, self.metadata("99001"))
            self.assertIsNotNone(first)
            self.assertIsNotNone(replay)
            self.assertEqual(replay["shadow_relpath"], first["shadow_relpath"])


if __name__ == "__main__":
    unittest.main()
