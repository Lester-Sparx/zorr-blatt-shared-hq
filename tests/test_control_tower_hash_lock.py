import os
import tempfile
import unittest
from pathlib import Path

from hq_adapter import CT_LOCK, HQError, load_json, verify_control_tower_artifact


class ControlTowerHashTest(unittest.TestCase):
    def test_lock_manifest_is_pinned_and_wrong_artifact_rejected(self):
        expected = "AAADF06A0B64AF27F8E205596D09369705F36974CEED27DA05890DEA465A59EE"
        self.assertEqual(load_json(CT_LOCK)["sha256"], expected)
        with tempfile.TemporaryDirectory() as directory:
            wrong = Path(directory) / "wrong.zip"
            wrong.write_bytes(b"wrong")
            with self.assertRaisesRegex(HQError, "CONTROL TOWER HASH FAIL"):
                verify_control_tower_artifact(wrong)

    def test_exact_external_locked_artifact_when_supplied(self):
        supplied = os.environ.get("CONTROL_TOWER_ARTIFACT_PATH")
        if supplied:
            self.assertEqual(verify_control_tower_artifact(Path(supplied)), load_json(CT_LOCK)["sha256"])


if __name__ == "__main__": unittest.main()
