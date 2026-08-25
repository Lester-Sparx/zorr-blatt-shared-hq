import tempfile
import unittest
from pathlib import Path

from _support import COMMIT, ROLES, base_state, review_report
from hq_adapter import HQError, register_artifact, submit_review


class ArtifactHashTest(unittest.TestCase):
    def test_review_before_registered_verified_artifact_is_rejected(self):
        _, task = base_state()
        with self.assertRaisesRegex(HQError, "VERIFIED ARTIFACT"):
            submit_review(task, actor="duncan", kind="QC", result="PASS", report=review_report("QC", "PASS"), roles=ROLES)

    def test_registered_manifest_uses_actual_file_hash(self):
        state, task = base_state()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "candidate.zip").write_bytes(b"candidate")
            _, new_task, manifest = register_artifact(
                state, task, actor="lester", expected_revision=0, expected_main="0" * 40,
                candidate_commit=COMMIT, artifact_path="candidate.zip", artifact_root=root,
                release_tag="r01", roles=ROLES,
            )
            self.assertEqual(new_task["artifactSha256"], manifest["sha256"])
            self.assertEqual(len(manifest["sha256"]), 64)


if __name__ == "__main__": unittest.main()
