from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DEPLOYER = ROOT / "config" / "sheriff" / "deploy" / "windows" / "ZbSheriffV1.ps1"


class SheriffWindowsRuntimeSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DEPLOYER.read_text(encoding="utf-8")

    def test_windows_10_uses_supported_podman_5_8_5(self):
        self.assertIn('v5.8.5', self.text)
        self.assertIn('podman-installer-windows-amd64.msi', self.text)
        self.assertIn('a2d78a2460dc4745684ee443ced8878fbf3a2fe4d8c620a290500e85367d2a33', self.text)
        self.assertIn('releases/download/v5.8.5/podman-installer-windows-amd64.msi', self.text)
        self.assertRegex(self.text, r'Build\s+-lt\s+19043')

    def test_windows_11_keeps_podman_6_path(self):
        self.assertIn('v6.1.0', self.text)
        self.assertIn('1958aac22abb3a9cf7b52626c71ba1a26015c323f0b5fa74671e303b22b043d3', self.text)

    def test_old_fail_fast_guard_is_removed(self):
        self.assertNotIn('PODMAN_V6_WINDOWS_VERSION_UNSUPPORTED', self.text)

    def test_runtime_selection_happens_before_installer_download(self):
        select = self.text.find('Select-PodmanRuntime')
        download = self.text.find('Download-Verified $PodmanInstallerUrl')
        self.assertGreaterEqual(select, 0)
        self.assertGreater(download, select)


if __name__ == '__main__':
    unittest.main()
