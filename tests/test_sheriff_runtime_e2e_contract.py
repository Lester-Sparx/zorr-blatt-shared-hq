import unittest
from pathlib import Path

from _support import ROOT


WORKFLOW = ROOT / ".github" / "workflows" / "sheriff-runtime-e2e.yml"
PROBE = ROOT / "scripts" / "sheriff_runtime_e2e.py"


class SheriffRuntimeE2EContractTest(unittest.TestCase):
    def test_runtime_e2e_workflow_exists(self):
        self.assertTrue(WORKFLOW.is_file())
        self.assertTrue(PROBE.is_file())

        workflow = WORKFLOW.read_text(encoding="utf-8")
        probe = PROBE.read_text(encoding="utf-8")

        for marker in (
            "docker compose -f config/sheriff/docker-compose.yml up -d --build",
            "stop sheriff-worker",
            "start sheriff-worker",
            "restart sheriff-worker",
            "assert-absent correctness",
            "assert replay",
            "SHERIFF_V1_RUNTIME_E2E = PASS",
        ):
            self.assertIn(marker, workflow)

        for marker in (
            "E2E-HONEST-FAIL-1",
            "E2E-CORRECTNESS-1",
            "E2E-FALSE-PASS-1",
            "HONEST_FAIL_ZERO_PENALTY = PASS",
            "CORRECTNESS_INCIDENT_REMEDIATION = PASS",
            "RESTART_REPLAY_IDEMPOTENT = PASS",
            "FALSE_PASS_CRITICAL_HOLD = PASS",
            "js.publish",
            "sheriff_agent_scores",
            "sheriff_remediations",
            "sheriff_outbox",
        ):
            self.assertIn(marker, probe)


if __name__ == "__main__":
    unittest.main()
