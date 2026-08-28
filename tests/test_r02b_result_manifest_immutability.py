from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import scripts.zb_execution_r02b_cli as r02b_cli
from scripts.zb_execution_evidence import build_evidence_bundle, verify_evidence_manifest


REQUEST_BODY = """ZB_EXECUTION_REQUEST_V1
EXECUTION_REQUEST_ID = zb-r02b-manifest-test-lester
MESSAGE_ID = zb-r02b-manifest-test
EVENT_ID = zb-event-manifest-test
CORRELATION_ID = zb-corr-manifest-test
CAUSATION_MESSAGE_ID = zb-r02b-manifest-test
TASK_ID = ZB_EXECUTION_PROOF_R01
TASK_REVISION = 2
LOGICAL_ROLE = LESTER
EXECUTION_PROFILE = LESTER_IMPLEMENT_R02A
EXECUTION_PROFILE_VERSION = 1
BASE_SHA = 6656d2954304ee5e90b17d4553f6ffa477d1d103
AUTHORITY_REF = pr:111:comment:1
DESIGN_HEAD = 2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8
SOURCE_REFS = pr:111;source-comment:1;pr:123;pr:124;pr:125
EVIDENCE_INPUT_REFS = spec:123;plan:124;implementation:125
ALLOWED_WRITE_SCOPE = tests/fixtures/zb-execution-proof/
TIMEOUT_SECONDS = 600
NO_AUTO_MERGE = TRUE
PRODUCTION_ACTIVE = NO
"""


class R02BResultManifestImmutabilityTests(unittest.TestCase):
    def test_wrapper_must_not_rewrite_core_hashed_result_file(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_tmp, tempfile.TemporaryDirectory() as runner_tmp:
            workspace = Path(workspace_tmp).resolve()
            runner_temp = Path(runner_tmp).resolve()
            request_path = workspace / ".zb-exec" / "request" / "request.txt"
            evidence_dir = workspace / ".zb-exec" / "lester" / "evidence"
            result_path = evidence_dir / "result.txt"
            request_path.parent.mkdir(parents=True, exist_ok=True)
            request_path.write_text(REQUEST_BODY, encoding="utf-8")

            def fake_run_lester(request_body: str, **kwargs):
                build_evidence_bundle(
                    request_body=request_body,
                    result_body="RESULT\n",
                    patch_bytes=b"",
                    changed_files=(),
                    tests_text="PASS\n",
                    worker_events="{}\n",
                    evidence_dir=evidence_dir,
                )
                return SimpleNamespace(terminal_state="PASS")

            env = {
                "GITHUB_WORKSPACE": str(workspace),
                "RUNNER_TEMP": str(runner_temp),
                "ZB_EXECUTION_REQUEST_PATH": str(request_path),
                "ZB_EXECUTION_RESULT_PATH": str(result_path),
                "ZB_EVIDENCE_DIR": str(evidence_dir),
                "ZB_EXECUTION_ID": "github-actions:123:1:lester_execute",
                "ZB_WORKFLOW_RUN_ID": "123",
                "ZB_WORKFLOW_RUN_ATTEMPT": "1",
                "ZB_RUNNER_PROVENANCE": "github-actions:github-hosted:windows-2025",
                "COPILOT_GITHUB_TOKEN": "personal-token",
            }

            original_write_text = Path.write_text

            def windows_result_write_text(path: Path, data: str, *args, **kwargs):
                if path.resolve() == result_path.resolve():
                    data = data.replace("\n", "\r\n")
                return original_write_text(path, data, *args, **kwargs)

            with patch.dict(os.environ, env, clear=True), patch.object(
                r02b_cli,
                "build_execution_worker",
                return_value=object(),
            ), patch.object(
                r02b_cli,
                "run_lester_execution",
                side_effect=fake_run_lester,
            ), patch.object(
                r02b_cli,
                "render_execution_result",
                return_value="RESULT\n",
            ), patch.object(
                Path,
                "write_text",
                new=windows_result_write_text,
            ):
                self.assertEqual(r02b_cli.main(["execute", "--from-env"]), 0)

            verify_evidence_manifest(evidence_dir)


if __name__ == "__main__":
    unittest.main()
