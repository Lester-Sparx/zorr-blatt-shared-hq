from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.hq_unified_archive import (
    derive_record,
    rebuild_current_context,
    search_records,
    write_record,
)


class UnifiedArchiveV1Tests(unittest.TestCase):
    def fixture(self) -> tuple[bytes, str]:
        event = {
            "action": "created",
            "repository": {"full_name": "Lester-Sparx/zorr-blatt-shared-hq"},
            "sender": {"login": "Lester-Sparx"},
            "issue": {
                "number": 999,
                "title": "ZORR visual canon restore",
                "html_url": "https://github.com/Lester-Sparx/zorr-blatt-shared-hq/issues/999",
                "pull_request": {"url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/pulls/999"},
            },
            "comment": {
                "body": "OWNER LOCK: current character drawing reference. ![ref](https://private-user-images.githubusercontent.com/example/ref.png)",
                "html_url": "https://github.com/Lester-Sparx/zorr-blatt-shared-hq/pull/999#issuecomment-1",
            },
        }
        raw = (json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        return raw, hashlib.sha256(raw).hexdigest()

    def test_derives_searchable_record_and_attachment_url(self) -> None:
        raw, digest = self.fixture()
        record = derive_record(
            raw,
            raw_sha256=digest,
            event_name="issue_comment",
            repository="Lester-Sparx/zorr-blatt-shared-hq",
            actor="Lester-Sparx",
        )
        self.assertEqual(record["schema"], "ZB_UNIFIED_ARCHIVE_RECORD_V1")
        self.assertEqual(record["raw_sha256"], digest)
        self.assertEqual(record["subject_kind"], "pull_request")
        self.assertEqual(record["subject_number"], 999)
        self.assertEqual(record["subject_title"], "ZORR visual canon restore")
        self.assertIn("OWNER LOCK", record["search_text"])
        self.assertEqual(
            record["attachment_urls"],
            ["https://private-user-images.githubusercontent.com/example/ref.png"],
        )

    def test_record_write_is_idempotent_and_context_is_deterministic(self) -> None:
        raw, digest = self.fixture()
        record = derive_record(
            raw,
            raw_sha256=digest,
            event_name="issue_comment",
            repository="Lester-Sparx/zorr-blatt-shared-hq",
            actor="Lester-Sparx",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = write_record(record, root)
            second = write_record(record, root)
            self.assertEqual(first, second)
            first_context = rebuild_current_context(root, limit=50)
            first_bytes = (root / "derived/unified-v1/CURRENT_CONTEXT.json").read_bytes()
            second_context = rebuild_current_context(root, limit=50)
            second_bytes = (root / "derived/unified-v1/CURRENT_CONTEXT.json").read_bytes()
            self.assertEqual(first_context, second_context)
            self.assertEqual(first_bytes, second_bytes)
            self.assertEqual(first_context["schema"], "ZB_UNIFIED_CURRENT_CONTEXT_V1")
            self.assertEqual(first_context["record_count"], 1)
            self.assertEqual(first_context["latest_records"][0]["raw_sha256"], digest)

    def test_fts5_search_returns_raw_bound_evidence(self) -> None:
        raw, digest = self.fixture()
        record = derive_record(
            raw,
            raw_sha256=digest,
            event_name="issue_comment",
            repository="Lester-Sparx/zorr-blatt-shared-hq",
            actor="Lester-Sparx",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_record(record, root)
            matches = search_records(root, "character drawing reference", limit=10)
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["raw_sha256"], digest)
            self.assertEqual(matches[0]["subject_number"], 999)


if __name__ == "__main__":
    unittest.main()
