from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.hq_unified_archive import (
    optimize_learning_policy,
    sync_sheriff_lessons,
)


class UnifiedArchiveOptimizerTests(unittest.TestCase):
    @staticmethod
    def _write_verdict(
        repo_root: Path,
        *,
        verdict_id: str,
        error_signature: str,
        lesson_text: str,
        issued_at: str,
    ) -> None:
        lesson_ref = f"hq/sheriff/lessons/{verdict_id}.md"
        lesson_path = repo_root / lesson_ref
        lesson_path.parent.mkdir(parents=True, exist_ok=True)
        lesson_path.write_text(lesson_text + "\n", encoding="utf-8")

        verdict_root = repo_root / "hq" / "sheriff" / "verdicts"
        verdict_root.mkdir(parents=True, exist_ok=True)
        verdict = {
            "schemaVersion": "SHERIFF_VERDICT_V1",
            "verdictId": verdict_id,
            "agentId": "DUNCAN",
            "logicalRole": "DUNCAN",
            "taskRef": "PR#205",
            "incidentClass": "I1_CORRECTNESS",
            "evidence": [f"github:verdict:{verdict_id}"],
            "errorSignature": error_signature,
            "rootCause": "Regression fixture root cause.",
            "selfCaught": False,
            "repeatOf": None,
            "decision": {
                "disciplineDelta": -1,
                "meritDelta": 0,
                "executionGate": "NONE",
                "ownerActionRequired": False,
                "reason": "Optimizer regression fixture",
            },
            "remediation": ["APPLY_VERIFIED_LESSON"],
            "regressionTest": f"tests/test_hq_unified_archive_optimizer.py::{verdict_id}",
            "lessonRef": lesson_ref,
            "status": "CLOSED",
            "sheriffId": "LESTER",
            "issuedAt": issued_at,
        }
        (verdict_root / f"{verdict_id}.json").write_text(
            json.dumps(verdict, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def test_optimizer_deduplicates_verified_rules_without_losing_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            archive_root = Path(tmp) / "archive"
            rule = "Restore durable evidence before asserting state; otherwise return NOT_PROVEN."
            self._write_verdict(
                repo_root,
                verdict_id="OPT-001",
                error_signature="STALE_STATE_ASSERTION",
                lesson_text=rule,
                issued_at="2026-08-29T18:00:00Z",
            )
            self._write_verdict(
                repo_root,
                verdict_id="OPT-002",
                error_signature="STALE_STATE_ASSERTION_REPEAT",
                lesson_text=rule,
                issued_at="2026-08-29T18:10:00Z",
            )
            sync_sheriff_lessons(repo_root / "hq" / "sheriff" / "verdicts", repo_root, archive_root)

            result = optimize_learning_policy(archive_root)

            self.assertEqual(result["status"], "IMPROVED")
            self.assertTrue(result["accepted"])
            self.assertEqual(result["baseline_rule_count"], 2)
            self.assertEqual(result["optimized_rule_count"], 1)
            self.assertEqual(result["training_coverage"], 1.0)
            self.assertEqual(result["holdout_coverage"], 1.0)
            self.assertLess(result["optimized_bytes"], result["baseline_bytes"])
            self.assertIn("NOT_PROVEN", result["policy_prefix"])
            self.assertEqual(result["source_verdict_ids"], ["OPT-001", "OPT-002"])
            self.assertRegex(result["corpus_sha256"], r"^[0-9a-f]{64}$")

    def test_optimizer_fails_closed_on_conflicting_rules_for_same_error_signature(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            archive_root = Path(tmp) / "archive"
            self._write_verdict(
                repo_root,
                verdict_id="OPT-CONFLICT-001",
                error_signature="SAME_ERROR",
                lesson_text="Always require durable evidence before the claim.",
                issued_at="2026-08-29T18:00:00Z",
            )
            self._write_verdict(
                repo_root,
                verdict_id="OPT-CONFLICT-002",
                error_signature="SAME_ERROR",
                lesson_text="Chat memory may override durable evidence.",
                issued_at="2026-08-29T18:10:00Z",
            )
            sync_sheriff_lessons(repo_root / "hq" / "sheriff" / "verdicts", repo_root, archive_root)

            result = optimize_learning_policy(archive_root)

            self.assertEqual(result["status"], "CONFLICT")
            self.assertFalse(result["accepted"])
            self.assertEqual(result["policy_prefix"], "")
            self.assertEqual(result["conflicting_error_signatures"], ["SAME_ERROR"])

    def test_sync_persists_current_optimized_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            archive_root = Path(tmp) / "archive"
            self._write_verdict(
                repo_root,
                verdict_id="OPT-PERSIST-001",
                error_signature="UNPROVEN_SUCCESS_CLAIM",
                lesson_text="Never claim PASS without fresh exact-head verification evidence.",
                issued_at="2026-08-29T18:20:00Z",
            )

            result = sync_sheriff_lessons(repo_root / "hq" / "sheriff" / "verdicts", repo_root, archive_root)

            self.assertEqual(result["optimizer_status"], "BASELINE_KEPT")
            optimized_path = archive_root / "derived" / "unified-v1" / "learning" / "CURRENT_OPTIMIZED_POLICY.json"
            self.assertTrue(optimized_path.is_file())
            current = json.loads(optimized_path.read_text(encoding="utf-8"))
            self.assertEqual(current["schema"], "ZB_OPTIMIZED_LEARNING_POLICY_V1")
            self.assertTrue(current["accepted"])
            self.assertEqual(current["baseline_rule_count"], 1)
            self.assertEqual(current["optimized_rule_count"], 1)
            self.assertEqual(current["training_coverage"], 1.0)
            self.assertEqual(current["holdout_coverage"], 1.0)


if __name__ == "__main__":
    unittest.main()
