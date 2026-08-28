from pathlib import Path
import unittest


WORKFLOW = Path('.github/workflows/zb-communication-r02b-v2.yml')


def test_r02b_v2_hosted_preflight_uses_complete_task_inventory():
    workflow = WORKFLOW.read_text(encoding='utf-8')
    assert "startsWith(github.event.comment.body, 'ZB_AGENT_MESSAGE_R02B_V2')" in workflow
    assert 'task --list-all --json' in workflow
    assert 'task --list --json' not in workflow


def test_r02b_v2_workflow_has_independent_duncan_and_finalize():
    workflow = WORKFLOW.read_text(encoding='utf-8')
    assert 'duncan_qc:' in workflow
    assert 'finalize:' in workflow
    assert 'finalize_substantive_execution' in workflow
    assert 'ZB_INDEPENDENT_PROOF_VERIFY' not in workflow
    assert 'R02B_INDEPENDENT_PROOF_VERIFY = PASS' in workflow


class R02BV2HostedSourceCleanlinessTests(unittest.TestCase):
    def test_python_bootstrap_cannot_dirty_source_checkout(self):
        workflow = WORKFLOW.read_text(encoding='utf-8')
        lester = workflow.split('  lester_execute:\n', 1)[1].split('  duncan_qc:\n', 1)[0]
        duncan = workflow.split('  duncan_qc:\n', 1)[1].split('  finalize:\n', 1)[0]
        for job in (lester, duncan):
            self.assertIn('PYTHONDONTWRITEBYTECODE: "1"', job)

    def test_windows_lester_uses_hash_pinned_native_copilot(self):
        workflow = WORKFLOW.read_text(encoding='utf-8')
        lester = workflow.split('  lester_execute:\n', 1)[1].split('  duncan_qc:\n', 1)[0]
        self.assertNotIn('npm install --global @github/copilot@1.0.80', lester)
        self.assertIn(
            'https://github.com/github/copilot-cli/releases/download/v1.0.80/copilot-win32-x64.zip',
            lester,
        )
        self.assertIn('e9ea2063913faa8a9f1cf374529c5fea075da0545a894d7469026166f854c541', lester.lower())
        self.assertIn('Get-FileHash -Algorithm SHA256', lester)
        self.assertIn("'copilot.exe'", lester)
        self.assertIn('$env:GITHUB_PATH', lester)


if __name__ == '__main__':
    unittest.main()
