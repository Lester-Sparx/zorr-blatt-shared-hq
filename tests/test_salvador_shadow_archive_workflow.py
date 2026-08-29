from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class SalvadorShadowArchiveWorkflowTests(unittest.TestCase):
    def test_permanent_archive_reuses_same_event_trigger_and_permissions(self) -> None:
        text = Path(".github/workflows/zb-permanent-archive-v1.yml").read_text(encoding="utf-8")
        self.assertNotIn("schedule:", text)
        self.assertEqual(text.count("contents: write"), 1)
        self.assertIn("python3 -m scripts.salvador_shadow_archive", text)
        self.assertIn('--event-path "$GITHUB_EVENT_PATH"', text)
        self.assertIn('--archive-root "$GITHUB_WORKSPACE/archive/hq/archive-v1"', text)

    def test_cli_derives_shadow_record_inside_existing_archive_root(self) -> None:
        payload = {
            "action": "created",
            "issue": {"number": 72},
            "comment": {
                "id": 5434385533,
                "user": {"login": "Lester-Sparx"},
                "body": "ZB_AGENT_EVENT_V0\nTASK_ID = ZB-SALVADOR-PROD-001\nAGENT = SALVADOR\nSTATE = RESULT_READY\nBACKEND = COMFYUI_LOCAL\nEXECUTION_ID = 619cbaba-03f2-43e6-a1df-7c7291f557b4\nRESULT_SHA256 = 69f20660a52750eeafbc97877f0c064d008e8e3fa1ed25dcd005924bed5ec6bf\nERROR_CODE = NONE\n\nSALVADOR_RESULT_READY",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            event_path = root / "event.json"
            archive_root = root / "archive"
            event_path.write_text(json.dumps(payload), encoding="utf-8")
            env = os.environ.copy()
            env.update(
                {
                    "GITHUB_EVENT_NAME": "issue_comment",
                    "GITHUB_RUN_ID": "99001",
                    "GITHUB_RUN_ATTEMPT": "1",
                    "GITHUB_REPOSITORY": "Lester-Sparx/zorr-blatt-shared-hq",
                    "GITHUB_ACTOR": "Lester-Sparx",
                }
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.salvador_shadow_archive",
                    "--event-path",
                    str(event_path),
                    "--archive-root",
                    str(archive_root),
                ],
                cwd=Path.cwd(),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            records = list((archive_root / "derived" / "salvador-shadow-v1" / "events").glob("*.json"))
            self.assertEqual(len(records), 1)


if __name__ == "__main__":
    unittest.main()
