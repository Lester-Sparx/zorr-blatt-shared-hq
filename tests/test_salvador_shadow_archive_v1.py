from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.salvador_shadow_archive import archive_salvador_shadow_event


class SalvadorShadowArchiveV1Tests(unittest.TestCase):
    @staticmethod
    def metadata() -> dict[str, str]:
        return {
            "event_name": "issue_comment",
            "run_id": "99001",
            "run_attempt": "1",
            "repository": "Lester-Sparx/zorr-blatt-shared-hq",
            "actor": "Lester-Sparx",
        }

    def test_result_ready_is_archived_without_skill_promotion(self) -> None:
        payload = {
            "action": "created",
            "issue": {
                "number": 72,
                "body": "ZB_AGENT_TASK_V0\nTASK_ID = ZB-SALVADOR-PROD-001\nAGENT = SALVADOR\nTASK_KIND = CANON_REFERENCE_EDIT\nSTATE = ASSIGNED\nREFERENCE = LOCAL_INBOX",
            },
            "comment": {
                "id": 5434385533,
                "user": {"login": "Lester-Sparx"},
                "body": "ZB_AGENT_EVENT_V0\nTASK_ID = ZB-SALVADOR-PROD-001\nAGENT = SALVADOR\nSTATE = RESULT_READY\nBACKEND = COMFYUI_LOCAL\nEXECUTION_ID = 619cbaba-03f2-43e6-a1df-7c7291f557b4\nRESULT_SHA256 = 69f20660a52750eeafbc97877f0c064d008e8e3fa1ed25dcd005924bed5ec6bf\nERROR_CODE = NONE\n\nSALVADOR_RESULT_READY",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            result = archive_salvador_shadow_event(
                json.dumps(payload).encode("utf-8"), Path(tmp), self.metadata()
            )
            self.assertIsNotNone(result)
            record = json.loads((Path(tmp) / result["shadow_relpath"]).read_text(encoding="utf-8"))
            self.assertEqual(record["kind"], "RUNTIME_OBSERVATION")
            self.assertEqual(record["state_before"], "UNTESTED")
            self.assertEqual(record["state_after"], "UNTESTED")
            self.assertFalse(record["training_eligible"])
            self.assertFalse(record["promotion_allowed"])


if __name__ == "__main__":
    unittest.main()
