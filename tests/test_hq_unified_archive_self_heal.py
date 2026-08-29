from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.hq_unified_archive import (
    build_restore_packet,
    derive_record,
    guard_assertion,
    resolve_assertion,
    write_record,
)


class UnifiedArchiveSelfHealTests(unittest.TestCase):
    @staticmethod
    def _write_event(
        root: Path,
        *,
        created_at: str,
        body: str,
        comment_id: int,
    ) -> dict[str, object]:
        payload = {
            "action": "created",
            "issue": {
                "number": 111,
                "title": "ZB bus",
                "pull_request": {},
                "html_url": "https://github.com/Lester-Sparx/zorr-blatt-shared-hq/pull/111",
            },
            "comment": {
                "id": comment_id,
                "created_at": created_at,
                "html_url": (
                    "https://github.com/Lester-Sparx/zorr-blatt-shared-hq/pull/111#issuecomment-"
                    f"{comment_id}"
                ),
                "body": body,
            },
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        record = derive_record(
            raw,
            raw_sha256=digest,
            event_name="issue_comment",
            repository="Lester-Sparx/zorr-blatt-shared-hq",
            actor="Lester-Sparx",
        )
        write_record(record, root)
        return record

    def test_latest_structured_assertion_supersedes_stale_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = self._write_event(
                root,
                created_at="2026-08-29T10:00:00Z",
                body="VISUAL_REFERENCE = OLD_REF\nSTATE = ACTIVE",
                comment_id=1,
            )
            new = self._write_event(
                root,
                created_at="2026-08-29T11:00:00Z",
                body="VISUAL_REFERENCE = NEW_REF\nSTATE = ACTIVE",
                comment_id=2,
            )

            resolved = resolve_assertion(root, "pull_request", 111, "VISUAL_REFERENCE")
            self.assertEqual(resolved["status"], "PROVEN")
            self.assertEqual(resolved["value"], "NEW_REF")
            self.assertEqual(resolved["raw_sha256"], new["raw_sha256"])
            self.assertNotEqual(resolved["raw_sha256"], old["raw_sha256"])

            guarded = guard_assertion(root, "pull_request", 111, "VISUAL_REFERENCE", "OLD_REF")
            self.assertEqual(guarded["status"], "CONFLICT")
            self.assertEqual(guarded["corrected_value"], "NEW_REF")
            self.assertEqual(guarded["raw_sha256"], new["raw_sha256"])

    def test_missing_assertion_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_event(
                root,
                created_at="2026-08-29T10:00:00Z",
                body="STATE = ACTIVE",
                comment_id=3,
            )
            resolved = resolve_assertion(root, "pull_request", 111, "UNKNOWN_KEY")
            self.assertEqual(resolved, {"status": "NOT_PROVEN", "key": "UNKNOWN_KEY"})

    def test_restore_packet_is_evidence_bound_and_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            record = self._write_event(
                root,
                created_at="2026-08-29T10:00:00Z",
                body="character visual reference https://example.invalid/ref.png",
                comment_id=4,
            )
            packet = build_restore_packet(root, "character visual reference", limit=5)
            self.assertEqual(packet["status"], "PROVEN")
            self.assertEqual(packet["results"][0]["raw_sha256"], record["raw_sha256"])
            self.assertEqual(packet["results"][0]["attachment_urls"], ["https://example.invalid/ref.png"])
            self.assertTrue(packet["results"][0]["source_url"].endswith("issuecomment-4"))

            missing = build_restore_packet(root, "totally absent evidence", limit=5)
            self.assertEqual(missing["status"], "NOT_PROVEN")
            self.assertEqual(missing["results"], [])


if __name__ == "__main__":
    unittest.main()
