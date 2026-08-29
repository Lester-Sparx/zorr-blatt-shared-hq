from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "config" / "sheriff" / "deploy" / "windows" / "BootstrapSheriffV1Host.ps1"
DEPLOYER = ROOT / "config" / "sheriff" / "deploy" / "windows" / "ZbSheriffV1.ps1"


class SheriffWindowsRuntimeSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        cls.deployer = DEPLOYER.read_text(encoding="utf-8")

    def test_windows_10_uses_supported_podman_5_8_5(self):
        self.assertIn('v5.8.5', self.bootstrap)
        self.assertIn('podman-installer-windows-amd64.msi', self.bootstrap)
        self.assertIn('a2d78a2460dc4745684ee443ced8878fbf3a2fe4d8c620a290500e85367d2a33', self.bootstrap)
        self.assertIn('releases/download/v5.8.5/podman-installer-windows-amd64.msi', self.bootstrap)
        self.assertIn('$MinWindows10Build = 19043', self.bootstrap)

    def test_windows_11_preserves_proven_podman_6_deployer(self):
        self.assertIn('v6.1.0', self.deployer)
        self.assertIn('1958aac22abb3a9cf7b52626c71ba1a26015c323f0b5fa74671e303b22b043d3', self.deployer)
        self.assertIn('PODMAN_V6_WINDOWS_VERSION_UNSUPPORTED', self.deployer)
        self.assertIn('$Windows11Build = 22000', self.bootstrap)

    def test_bootstrap_patches_only_windows_10_host_runtime_layer(self):
        self.assertIn('PODMAN_V6_WINDOWS_VERSION_UNSUPPORTED', self.bootstrap)
        self.assertIn('HOST_RUNTIME = PODMAN_5_8_5_WIN10', self.bootstrap)
        self.assertIn('HOST_RUNTIME = PODMAN_6_1_0_WIN11', self.bootstrap)
        self.assertIn('DEPLOYER_PATCH_CONTRACT_MISMATCH', self.bootstrap)

    def test_bootstrap_keeps_exact_proven_runtime_commit(self):
        self.assertIn('47a92fc4a0d685e1a892285c568a59dfc5ccac82', self.bootstrap)
        self.assertIn('ab816ff383c74d1c72ee36df31bc381cf062f52b', self.bootstrap)

    def test_powershell_variable_before_colon_is_braced(self):
        self.assertNotIn('$build:MIN', self.bootstrap)
        self.assertIn('${build}:MIN', self.bootstrap)

    def test_win10_preflights_wsl_before_podman_machine(self):
        self.assertIn('function Assert-WslReady', self.bootstrap)
        self.assertIn('WSL_NOT_READY', self.bootstrap)
        self.assertIn('WSL_STATUS = PASS', self.bootstrap)
        self.assertLess(self.bootstrap.find('Assert-WslReady'), self.bootstrap.find('& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Deployer -Action Install'))

    def test_github_cli_is_not_a_physical_runtime_gate(self):
        self.assertIn('function Patch-EvidenceTransport', self.bootstrap)
        self.assertIn('GITHUB_EVIDENCE_POST = DEFERRED_TO_CONNECTED_CHAT', self.bootstrap)
        self.assertIn('PHYSICAL_RUNTIME_DOES_NOT_REQUIRE_GH_CLI', self.bootstrap)


if __name__ == '__main__':
    unittest.main()
