from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.hq_unified_archive import (
    UnifiedArchiveError,
    build_learning_policy,
    sync_sheriff_lessons,
)


class UnifiedArchiveLearningTests(unittest.TestCase):
    @staticmethod
    def _write_verdict(
        root: Path,
        *,
        verdict_id: str,
        status: str,
        lesson_ref: str,
        error_signature: str = "STALE_VISUAL_REFERENCE_ASSERTION",
        root_cause: str = "Agent answered from stale chat memory before restoring durable evidence.",
        regression_test: str | None = "tests/test_hq_unified_archive_learning.py::test_closed_verdict_becomes_relevant_policy",
    ) -> Path:
        verdict_root = root / "hq" / "sheriff" / "verdicts"
        verdict_root.mkdir(parents=True, exist_ok=True)
        payload = {
            "schemaVersion": "SHERIFF_VERDICT_V1",
            "verdictId": verdict_id,
            "agentId": "DUNCAN",
            "logicalRole": "DUNCAN",
            "taskRef": "PR#205",
            "incidentClass": "I1_CORRECTNESS",
            "evidence": ["github:pr:205", "github:run:33268102845"],
            "errorSignature": error_signature,
            "rootCause": root_cause,
            "selfCaught": False,
            "repeatOf": None,
            "decision": {
                "disciplineDelta": -1,
                "meritDelta": 0,
                "executionGate": "NONE",
                "ownerActionRequired": False,
                "reason": "Regression fixture",
            },
            "remediation": ["RESTORE_DURABLE_EVIDENCE_BEFORE_ASSERTION"],
            "regressionTest": regression_test,
            "lessonRef": lesson_ref,
            "status": status,
            "sheriffId": "LESTER",
            "issuedAt": "2026-08-29T18:30:00Z",
        }
        path = verdict_root / f"{verdict_id}.json"
        path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def test_closed_verdict_becomes_relevant_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            archive_root = Path(tmp) / "archive"
            lesson_ref = "hq/sheriff/lessons/SV1-LEARN-001.md"
            lesson_path = repo_root / lesson_ref
            lesson_path.parent.mkdir(parents=True, exist_ok=True)
            lesson_path.write_text(
                "Before claiming a visual reference, restore exact durable evidence. "
                "If no authority is found, answer NOT_PROVEN instead of guessing.\n",
                encoding="utf-8",
            )
            self._write_verdict(
                repo_root,
                verdict_id="SV1-LEARN-001",
                status="CLOSED",
                lesson_ref=lesson_ref,
            )

            result = sync_sheriff_lessons(
                repo_root / "hq" / "sheriff" / "verdicts",
                repo_root,
                archive_root,
            )
            self.assertEqual(result["learned"], 1)
            self.assertEqual(result["skipped_open"], 0)
            self.assertEqual(result["corpus_count"], 1)

            policy = build_learning_policy(archive_root, "visual reference durable evidence", limit=5)
            self.assertEqual(policy["status"], "PROVEN")
            self.assertEqual(policy["lesson_count"], 1)
            self.assertIn("NOT_PROVEN", policy["policy_prefix"])
            self.assertEqual(policy["lessons"][0]["verdict_id"], "SV1-LEARN-001")
            self.assertEqual(policy["lessons"][0]["error_signature"], "STALE_VISUAL_REFERENCE_ASSERTION")
            self.assertEqual(
                policy["lessons"][0]["evidence"],
                ["github:pr:205", "github:run:33268102845"],
            )

            learning_root = archive_root / "derived" / "unified-v1" / "learning"
            corpus_path = learning_root / "TRAINING_CORPUS.jsonl"
            corpus = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines() if line]
            self.assertEqual(len(corpus), 1)
            self.assertEqual(corpus[0]["verdict_id"], "SV1-LEARN-001")
            self.assertIn("NOT_PROVEN", corpus[0]["lesson"])
            self.assertEqual(corpus[0]["regression_test"], "tests/test_hq_unified_archive_learning.py::test_closed_verdict_becomes_relevant_policy")

            current = json.loads((learning_root / "CURRENT_LESSONS.json").read_text(encoding="utf-8"))
            self.assertEqual(current["schema"], "ZB_CURRENT_LESSONS_V1")
            self.assertEqual(current["lesson_count"], 1)
            self.assertEqual(current["lessons"][0]["verdict_id"], "SV1-LEARN-001")
            self.assertIn("NOT_PROVEN", current["lessons"][0]["lesson_excerpt"])
            self.assertEqual(current["lessons"][0]["evidence"], ["github:pr:205", "github:run:33268102845"])

    def test_open_verdict_never_trains_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            archive_root = Path(tmp) / "archive"
            lesson_ref = "hq/sheriff/lessons/SV1-OPEN-001.md"
            lesson_path = repo_root / lesson_ref
            lesson_path.parent.mkdir(parents=True, exist_ok=True)
            lesson_path.write_text("Unverified lesson must not become policy.\n", encoding="utf-8")
            self._write_verdict(
                repo_root,
                verdict_id="SV1-OPEN-001",
                status="OPEN",
                lesson_ref=lesson_ref,
            )

            result = sync_sheriff_lessons(
                repo_root / "hq" / "sheriff" / "verdicts",
                repo_root,
                archive_root,
            )
            self.assertEqual(result["learned"], 0)
            self.assertEqual(result["skipped_open"], 1)
            self.assertEqual(result["corpus_count"], 0)
            policy = build_learning_policy(archive_root, "unverified lesson", limit=5)
            self.assertEqual(policy["status"], "NOT_PROVEN")
            self.assertEqual(policy["lesson_count"], 0)
            self.assertEqual(policy["policy_prefix"], "")

            current = json.loads(
                (archive_root / "derived" / "unified-v1" / "learning" / "CURRENT_LESSONS.json").read_text(encoding="utf-8")
            )
            self.assertEqual(current["lesson_count"], 0)
            self.assertEqual(current["lessons"], [])

    def test_closed_verdict_missing_lesson_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            archive_root = Path(tmp) / "archive"
            self._write_verdict(
                repo_root,
                verdict_id="SV1-MISSING-001",
                status="CLOSED",
                lesson_ref="hq/sheriff/lessons/DOES_NOT_EXIST.md",
            )
            with self.assertRaisesRegex(UnifiedArchiveError, "LESSON_REF_MISSING"):
                sync_sheriff_lessons(
                    repo_root / "hq" / "sheriff" / "verdicts",
                    repo_root,
                    archive_root,
                )


if __name__ == "__main__":
    unittest.main()
