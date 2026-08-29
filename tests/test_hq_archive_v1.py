from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.hq_archive_ingest import ArchiveError, archive_event
from scripts.hq_archive_verify import verify_archive


class PermanentArchiveV1Tests(unittest.TestCase):
    @staticmethod
    def metadata(run_id: str = "9001", run_attempt: str = "1") -> dict[str, str]:
        return {
            "event_name": "issue_comment",
            "run_id": run_id,
            "run_attempt": run_attempt,
            "repository": "Lester-Sparx/zorr-blatt-shared-hq",
            "actor": "Lester-Sparx",
            "workflow": "ZB Permanent Archive V1",
            "source_sha": "abc123",
            "source_ref": "refs/heads/main",
        }

    def test_preserves_raw_event_bytes_and_verifies(self) -> None:
        raw = b'{\n  "action": "created",\n  "comment": {"body": "DUNCAN \\u2192 LESTER"}\n}\n'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = archive_event(raw, root, self.metadata())
            raw_path = root / result["raw_relpath"]
            self.assertEqual(raw_path.read_bytes(), raw)
            self.assertEqual(result["raw_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(verify_archive(root), {"events": 1, "raw_objects": 1})

    def test_same_run_is_idempotent(self) -> None:
        raw = json.dumps({"action": "created", "n": 1}).encode()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = archive_event(raw, root, self.metadata())
            second = archive_event(raw, root, self.metadata())
            self.assertEqual(first, second)
            self.assertEqual(verify_archive(root), {"events": 1, "raw_objects": 1})

    def test_same_event_identity_cannot_be_rewritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_event(b'{"action":"created","value":1}', root, self.metadata())
            with self.assertRaisesRegex(ArchiveError, "EVENT_ID_COLLISION"):
                archive_event(b'{"action":"created","value":2}', root, self.metadata())

    def test_tampered_raw_bytes_fail_closed(self) -> None:
        raw = b'{"action":"created","value":1}'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = archive_event(raw, root, self.metadata())
            (root / result["raw_relpath"]).write_bytes(b"tampered")
            with self.assertRaisesRegex(ArchiveError, "RAW_FILENAME_HASH_MISMATCH|EVENT_RAW_HASH_MISMATCH"):
                verify_archive(root)


if __name__ == "__main__":
    unittest.main()
