from __future__ import annotations

import importlib
import inspect
from pathlib import Path
import tempfile
import unittest

from scripts.zb_execution_contract import parse_execution_request
from scripts.zb_execution_copilot import CopilotWorker


ROOT = Path(__file__).resolve().parents[1]
TARGET = "tests/fixtures/zb-execution-proof/result.txt"
BASE_SHA = "d" * 40
DESIGN_HEAD = "2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8"


def request_body() -> str:
    return f"""ZB_EXECUTION_REQUEST_V1
EXECUTION_REQUEST_ID = req-r02b-proof
MESSAGE_ID = msg-r02b-proof
EVENT_ID = evt-r02b-proof
CORRELATION_ID = corr-r02b-proof
CAUSATION_MESSAGE_ID = msg-r02b-proof
TASK_ID = ZB_EXECUTION_PROOF_R01
TASK_REVISION = 2
LOGICAL_ROLE = LESTER
EXECUTION_PROFILE = LESTER_IMPLEMENT_R02A
EXECUTION_PROFILE_VERSION = 1
BASE_SHA = {BASE_SHA}
AUTHORITY_REF = pr:111:comment:1
DESIGN_HEAD = {DESIGN_HEAD}
SOURCE_REFS = pr:111;pr:123;pr:124;pr:125
EVIDENCE_INPUT_REFS = spec:123;plan:124;implementation:125
ALLOWED_WRITE_SCOPE = tests/fixtures/zb-execution-proof/
TIMEOUT_SECONDS = 600
NO_AUTO_MERGE = TRUE
PRODUCTION_ACTIVE = NO
"""


class R02BProofTests(unittest.TestCase):
    def test_copilot_prompt_contains_exact_deterministic_proof_edit(self) -> None:
        prompt = CopilotWorker._prompt(parse_execution_request(request_body()))
        self.assertIn(f"TARGET_FILE={TARGET}", prompt)
        self.assertIn("STATE = BEFORE", prompt)
        self.assertIn("STATE = AFTER", prompt)
        self.assertIn("Change exactly one existing file", prompt)

    def test_trusted_verifier_accepts_only_exact_after_state(self) -> None:
        module = importlib.import_module("scripts.zb_execution_proof_verify")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / TARGET
            target.parent.mkdir(parents=True)
            target.write_text("ZB_R02A_PROOF_TARGET_V1\nSTATE = BEFORE\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "PROOF_TARGET_NOT_AFTER"):
                module.verify_proof_target(root)
            target.write_text("ZB_R02A_PROOF_TARGET_V1\nSTATE = AFTER\n", encoding="utf-8")
            self.assertEqual(module.verify_proof_target(root), target)
            target.write_text("ZB_R02A_PROOF_TARGET_V1\nSTATE = AFTER\nEXTRA = BAD\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "PROOF_TARGET_NOT_AFTER"):
                module.verify_proof_target(root)

    def test_r02b_wrapper_passes_static_verifier_into_existing_execution_pipeline(self) -> None:
        module = importlib.import_module("scripts.zb_execution_r02b_cli")
        source = inspect.getsource(module)
        self.assertIn("run_lester_execution", source)
        self.assertIn("verification_commands", source)
        self.assertIn("scripts.zb_execution_proof_verify", source)
        self.assertNotIn("subprocess.run", source)
        taskfile = (ROOT / "Taskfile.yml").read_text(encoding="utf-8")
        self.assertIn("python -m scripts.zb_execution_r02b_cli execute --from-env", taskfile)


if __name__ == "__main__":
    unittest.main()
