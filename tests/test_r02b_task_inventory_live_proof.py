from pathlib import Path


def test_r02b_hosted_preflight_uses_complete_task_inventory():
    workflow = Path('.github/workflows/zb-communication-r02b.yml').read_text(encoding='utf-8')
    assert 'task --list-all --json' in workflow
    assert 'task --list --json' not in workflow
