from __future__ import annotations

import unittest

from scripts.zb_execution_evidence import EvidenceError, verify_artifact_metadata
from scripts.zb_execution_preflight import (
    OPENCODE_VERSION,
    OPENCODE_WINDOWS_X64_SHA256,
    RUNNER_VERSION,
    RUNNER_WINDOWS_X64_SHA256,
)


class CurrentRuntimePinTests(unittest.TestCase):
    def test_activation_pins_current_verified_windows_runtimes(self) -> None:
        self.assertEqual(RUNNER_VERSION, "2.337.0")
        self.assertEqual(
            RUNNER_WINDOWS_X64_SHA256,
            "1150692afa94e71f872017e254ea55b6eece1eece3fe7e3a6d4c93d0a1b85cfc",
        )
        self.assertEqual(OPENCODE_VERSION, "1.18.25")
        self.assertEqual(
            OPENCODE_WINDOWS_X64_SHA256,
            "831e213e5f454d6e8b26f0fb24c7b3d42b40e47d73d154672a9192702eb08416",
        )


class ArtifactMetadataGateTests(unittest.TestCase):
    def test_exact_id_digest_and_workflow_run_are_required(self) -> None:
        digest = "a" * 64
        good = {
            "id": 42,
            "expired": False,
            "digest": f"sha256:{digest}",
            "workflow_run": {"id": 9001},
        }
        verify_artifact_metadata(good, expected_id=42, expected_digest=digest, expected_run_id=9001)

        bad_cases = (
            {**good, "id": 43},
            {**good, "expired": True},
            {**good, "digest": "sha256:" + "b" * 64},
            {**good, "workflow_run": {"id": 9002}},
        )
        for metadata in bad_cases:
            with self.subTest(metadata=metadata), self.assertRaises(EvidenceError):
                verify_artifact_metadata(metadata, expected_id=42, expected_digest=digest, expected_run_id=9001)

    def test_invalid_expected_digest_is_rejected(self) -> None:
        metadata = {
            "id": 42,
            "expired": False,
            "digest": "sha256:" + "a" * 64,
            "workflow_run": {"id": 9001},
        }
        for digest in ("", "A" * 64, "a" * 63, "g" * 64):
            with self.subTest(digest=digest), self.assertRaises(EvidenceError):
                verify_artifact_metadata(metadata, expected_id=42, expected_digest=digest, expected_run_id=9001)


if __name__ == "__main__":
    unittest.main()
