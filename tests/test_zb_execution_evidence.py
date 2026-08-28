from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.zb_execution_evidence import EvidenceError, build_evidence_bundle, verify_evidence_manifest


class EvidenceTests(unittest.TestCase):
    def test_build_bundle_writes_required_files_and_stable_manifest_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence_dir = Path(tmp) / "evidence"
            manifest = build_evidence_bundle(
                request_body="ZB_EXECUTION_REQUEST_V1\nEXECUTION_REQUEST_ID = req-1\n",
                result_body="ZB_EXECUTION_RESULT_V1\nEXECUTION_REQUEST_ID = req-1\n",
                patch_bytes=b"diff --git a/a b/a\n",
                changed_files=("scripts/a.py",),
                tests_text="tests passed\n",
                worker_events="{\"type\":\"step\"}\n",
                evidence_dir=evidence_dir,
            )

            expected_names = {
                "request.txt",
                "result.txt",
                "patch.diff",
                "changed-files.txt",
                "tests.txt",
                "worker-events.jsonl",
                "manifest.json",
            }
            self.assertEqual({p.name for p in evidence_dir.iterdir()}, expected_names)
            self.assertEqual(set(manifest), expected_names - {"manifest.json"})
            for name, digest in manifest.items():
                raw = (evidence_dir / name).read_bytes()
                self.assertEqual(digest, hashlib.sha256(raw).hexdigest())

            verify_evidence_manifest(evidence_dir)
            first_manifest = (evidence_dir / "manifest.json").read_bytes()
            second = build_evidence_bundle(
                request_body="ZB_EXECUTION_REQUEST_V1\nEXECUTION_REQUEST_ID = req-1\n",
                result_body="ZB_EXECUTION_RESULT_V1\nEXECUTION_REQUEST_ID = req-1\n",
                patch_bytes=b"diff --git a/a b/a\n",
                changed_files=("scripts/a.py",),
                tests_text="tests passed\n",
                worker_events="{\"type\":\"step\"}\n",
                evidence_dir=evidence_dir,
            )
            self.assertEqual(second, manifest)
            self.assertEqual((evidence_dir / "manifest.json").read_bytes(), first_manifest)

    def test_result_file_is_optional_before_terminal_result_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence_dir = Path(tmp) / "evidence"
            manifest = build_evidence_bundle(
                request_body="request\n",
                result_body=None,
                patch_bytes=b"",
                changed_files=(),
                tests_text="",
                worker_events="",
                evidence_dir=evidence_dir,
            )
            self.assertNotIn("result.txt", manifest)
            self.assertFalse((evidence_dir / "result.txt").exists())
            verify_evidence_manifest(evidence_dir)

    def test_manifest_is_canonical_sorted_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence_dir = Path(tmp) / "evidence"
            build_evidence_bundle(
                request_body="request\n",
                result_body="result\n",
                patch_bytes=b"patch\n",
                changed_files=("z.py", "a.py"),
                tests_text="ok\n",
                worker_events="events\n",
                evidence_dir=evidence_dir,
            )
            raw = (evidence_dir / "manifest.json").read_text(encoding="utf-8")
            parsed = json.loads(raw)
            self.assertEqual(list(parsed), sorted(parsed))
            self.assertTrue(raw.endswith("\n"))

    def test_verify_manifest_rejects_tamper_missing_file_and_unknown_extra_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence_dir = Path(tmp) / "evidence"
            build_evidence_bundle(
                request_body="request\n",
                result_body="result\n",
                patch_bytes=b"patch\n",
                changed_files=("a.py",),
                tests_text="ok\n",
                worker_events="events\n",
                evidence_dir=evidence_dir,
            )
            (evidence_dir / "tests.txt").write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(EvidenceError, "EVIDENCE_HASH_MISMATCH"):
                verify_evidence_manifest(evidence_dir)

            build_evidence_bundle(
                request_body="request\n",
                result_body="result\n",
                patch_bytes=b"patch\n",
                changed_files=("a.py",),
                tests_text="ok\n",
                worker_events="events\n",
                evidence_dir=evidence_dir,
            )
            (evidence_dir / "tests.txt").unlink()
            with self.assertRaisesRegex(EvidenceError, "EVIDENCE_FILE_MISSING"):
                verify_evidence_manifest(evidence_dir)

            build_evidence_bundle(
                request_body="request\n",
                result_body="result\n",
                patch_bytes=b"patch\n",
                changed_files=("a.py",),
                tests_text="ok\n",
                worker_events="events\n",
                evidence_dir=evidence_dir,
            )
            (evidence_dir / "unexpected.txt").write_text("no\n", encoding="utf-8")
            with self.assertRaisesRegex(EvidenceError, "EVIDENCE_EXTRA_FILE"):
                verify_evidence_manifest(evidence_dir)

    def test_changed_file_paths_must_be_repository_relative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(EvidenceError, "INVALID_CHANGED_FILE"):
                build_evidence_bundle(
                    request_body="request\n",
                    result_body=None,
                    patch_bytes=b"",
                    changed_files=("../escape",),
                    tests_text="",
                    worker_events="",
                    evidence_dir=Path(tmp) / "evidence",
                )


if __name__ == "__main__":
    unittest.main()
