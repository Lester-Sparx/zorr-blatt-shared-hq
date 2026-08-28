from pathlib import Path


def test_r02b_v2_hosted_preflight_uses_complete_task_inventory():
    workflow = Path('.github/workflows/zb-communication-r02b-v2.yml').read_text(encoding='utf-8')
    assert "startsWith(github.event.comment.body, 'ZB_AGENT_MESSAGE_R02B_V2')" in workflow
    assert 'task --list-all --json' in workflow
    assert 'task --list --json' not in workflow


def test_r02b_v2_workflow_has_independent_duncan_and_finalize():
    workflow = Path('.github/workflows/zb-communication-r02b-v2.yml').read_text(encoding='utf-8')
    assert 'duncan_qc:' in workflow
    assert 'finalize:' in workflow
    assert 'finalize_substantive_execution' in workflow
    assert 'ZB_INDEPENDENT_PROOF_VERIFY' not in workflow
    assert 'R02B_INDEPENDENT_PROOF_VERIFY = PASS' in workflow
