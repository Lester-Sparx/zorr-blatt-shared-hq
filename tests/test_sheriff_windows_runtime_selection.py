from pathlib import Path
import re
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

    def test_win10_automatically_repairs_wsl_instead_of_fail_only(self):
        self.assertIn('function Ensure-WslReady', self.bootstrap)
        self.assertIn('Microsoft-Windows-Subsystem-Linux', self.bootstrap)
        self.assertIn('VirtualMachinePlatform', self.bootstrap)
        self.assertIn('Enable-WindowsOptionalFeature', self.bootstrap)
        self.assertIn('--install', self.bootstrap)
        self.assertIn('--no-distribution', self.bootstrap)
        self.assertIn('WSL_STATUS = PASS', self.bootstrap)
        invocation = re.search(
            r'if \(\$build -lt \$Windows11Build\) \{\s*Ensure-WslReady\s*\}',
            self.bootstrap,
        )
        self.assertIsNotNone(invocation, 'Win10 execution path must invoke Ensure-WslReady')
        install = self.bootstrap.find('& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Deployer -Action Install')
        self.assertGreater(install, invocation.start())

    def test_wsl_repair_self_elevates_without_manual_admin_commands(self):
        self.assertIn('function Test-IsAdministrator', self.bootstrap)
        self.assertIn('function Invoke-ElevatedSelf', self.bootstrap)
        self.assertIn('-Verb RunAs', self.bootstrap)
        self.assertIn('ELEVATION_REQUIRED_FOR_WSL', self.bootstrap)

    def test_wsl_repair_can_resume_after_required_reboot(self):
        self.assertIn('[ValidateSet("Auto", "Resume")]', self.bootstrap)
        self.assertIn('function Register-WslResume', self.bootstrap)
        self.assertIn('ZORR SHERIFF V1 WSL Resume', self.bootstrap)
        self.assertIn('New-ScheduledTaskTrigger -AtLogOn', self.bootstrap)
        self.assertIn('-Stage Resume', self.bootstrap)
        self.assertIn('shutdown.exe', self.bootstrap)
        self.assertIn('/r', self.bootstrap)
        self.assertIn('/t', self.bootstrap)
        self.assertIn('WSL_REBOOT_SCHEDULED = YES', self.bootstrap)
        cleanup = re.search(
            r'if \(\$Stage -eq "Resume"\) \{\s*Unregister-WslResume\s*\}',
            self.bootstrap,
        )
        self.assertIsNotNone(cleanup, 'Resume task must remove itself before continuing')
        ensure_call = self.bootstrap.find('    Ensure-WslReady', cleanup.end())
        self.assertGreater(ensure_call, cleanup.end())

    def test_virtualization_is_checked_before_wsl2_machine_use(self):
        self.assertIn('VirtualizationFirmwareEnabled', self.bootstrap)
        self.assertIn('CPU_VIRTUALIZATION_DISABLED_IN_FIRMWARE', self.bootstrap)
        ensure_body = self.bootstrap.find('function Ensure-WslReady')
        firmware_call = self.bootstrap.find('    Assert-VirtualizationFirmware', ensure_body)
        install = self.bootstrap.find('& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Deployer -Action Install')
        self.assertGreater(firmware_call, ensure_body)
        self.assertGreater(install, firmware_call)

    def test_first_podman_machine_creation_uses_non_erroring_list_probe(self):
        self.assertIn('function Patch-PodmanMachineFirstInit', self.bootstrap)
        self.assertIn('@("machine", "list", "--format", "json")', self.bootstrap)
        self.assertIn('Start-Process -FilePath $PodmanExe', self.bootstrap)
        self.assertIn('PODMAN_MACHINE_LIST_FAILED', self.bootstrap)
        self.assertIn('PODMAN_MACHINE_FIRST_INIT_SAFE', self.bootstrap)
        self.assertIn('PODMAN_MACHINE_PATCH_VERIFY_FAILED', self.bootstrap)
        invocation = self.bootstrap.find('Patch-PodmanMachineFirstInit $Deployer')
        install = self.bootstrap.find('& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Deployer -Action Install')
        self.assertGreater(invocation, 0)
        self.assertGreater(install, invocation)

    def test_openssh_client_is_repaired_before_first_podman_machine_init(self):
        self.assertIn('function Ensure-OpenSshClient', self.bootstrap)
        self.assertIn('OpenSSH.Client~~~~0.0.1.0', self.bootstrap)
        self.assertIn('Get-WindowsCapability -Online -Name', self.bootstrap)
        self.assertIn('Add-WindowsCapability -Online -Name', self.bootstrap)
        self.assertIn('System32\\OpenSSH', self.bootstrap)
        self.assertIn('ssh-keygen.exe', self.bootstrap)
        self.assertIn('OPENSSH_CLIENT = PASS', self.bootstrap)
        self.assertIn('[Environment]::SetEnvironmentVariable("PATH"', self.bootstrap)
        call = re.search(r'\nEnsure-OpenSshClient\s*\n', self.bootstrap)
        self.assertIsNotNone(call, 'execution path must invoke Ensure-OpenSshClient')
        machine_patch = self.bootstrap.find('Patch-PodmanMachineFirstInit $Deployer')
        install = self.bootstrap.find('& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Deployer -Action Install')
        self.assertGreater(machine_patch, call.start())
        self.assertGreater(install, machine_patch)

    def test_github_cli_is_not_a_physical_runtime_gate(self):
        self.assertIn('function Patch-EvidenceTransport', self.bootstrap)
        self.assertIn('GITHUB_EVIDENCE_POST = DEFERRED_TO_CONNECTED_CHAT', self.bootstrap)
        self.assertIn('PHYSICAL_RUNTIME_DOES_NOT_REQUIRE_GH_CLI', self.bootstrap)


if __name__ == '__main__':
    unittest.main()
