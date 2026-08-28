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


if __name__ == '__main__':
    unittest.main()
