from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "config" / "sheriff" / "deploy" / "windows"
PS1 = DEPLOY / "ZbSheriffV1.ps1"
CMD = DEPLOY / "RUN_TO_PRODUCTION_PASS.cmd"
AGENTS = ROOT / "AGENTS.md"


class SheriffWindowsProductionContractTests(unittest.TestCase):
    def test_base_first_law_is_durable(self):
        text = AGENTS.read_text(encoding="utf-8")
        self.assertIn("## Base-first law", text)
        self.assertIn("Only after the base is PASS/LOCKED", text)

    def test_one_click_runner_exists(self):
        self.assertTrue(CMD.is_file())
        text = CMD.read_text(encoding="utf-8")
        self.assertIn("ZbSheriffV1.ps1", text)
        self.assertIn("-Action Install", text)
        self.assertIn("-Action Verify", text)

    def test_windows_deployer_reuses_existing_lifecycle_pattern(self):
        self.assertTrue(PS1.is_file())
        text = PS1.read_text(encoding="utf-8")
        for marker in (
            'ValidateSet("Install","Uninstall","Status","Start","Stop","Restart","Verify")',
            '$TaskName = "ZB Sheriff V1"',
            'New-ScheduledTaskTrigger -AtLogOn',
            'New-ScheduledTaskSettingsSet',
            'RestartCount 5',
            'podman machine',
            'podman compose',
        ):
            self.assertIn(marker, text)

    def test_open_code_runtime_is_pinned_and_verified(self):
        text = PS1.read_text(encoding="utf-8")
        self.assertIn('Podman', text)
        self.assertIn('docker-compose-windows-x86_64.exe', text)
        self.assertIn('v5.5.0', text)
        self.assertIn('51e1e61195f3616896265487ed64551095f3bd27ac7fbd5758d3538c3bfa1b19', text)
        self.assertNotIn('Docker Desktop', text)

    def test_runtime_semantics_are_pinned_to_proven_e2e(self):
        text = PS1.read_text(encoding="utf-8")
        self.assertIn('47a92fc4a0d685e1a892285c568a59dfc5ccac82', text)
        self.assertIn('sheriff_runtime_e2e.py', text)
        self.assertIn('SHERIFF_V1_24_7_PRODUCTION_ACTIVE = YES', text)
        self.assertIn('SHERIFF_V1_24_7_PRODUCTION_ACTIVE = NO', text)

    def test_verify_is_fail_closed(self):
        text = PS1.read_text(encoding="utf-8")
        for marker in (
            'TASK_REGISTERED =',
            'TASK_ENABLED =',
            'STACK_SERVICES_RUNNING =',
            'SHERIFF_LIVE_PATH =',
            'BLOCKER =',
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
