from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "deploy" / "windows" / "ZbReferenceBridge.ps1"


def source():
    return SCRIPT.read_text(encoding="utf-8").lower()


def test_reference_bridge_task_scheduler_contract_is_current_user_non_elevated():
    s = source()
    assert 'zb reference bridge v1' in s
    assert 'new-scheduledtasktrigger -atlogon' in s
    assert '-logontype interactive' in s
    assert '-runlevel limited' in s
    assert '-multipleinstances ignorenew' in s
    assert '-startwhenavailable' in s
    assert '-restartcount 5' in s
    assert 'new-timespan -minutes 1' in s
    assert '-executiontimelimit ([timespan]::zero)' in s


def test_install_runs_preflight_before_register_and_starts_exact_bridge_daemon():
    s = source()
    preflight = s.index('-m zb_reference_bridge --preflight --config')
    register = s.index('register-scheduledtask')
    start = s.index('start-scheduledtask')
    assert preflight < register < start
    assert '-m zb_reference_bridge --daemon --config' in s


def test_deployment_is_separate_from_controller_daemon_and_has_all_actions():
    s = source()
    for action in ('install','uninstall','status','start','stop','restart','enable','disable'):
        assert f'"{action}"' in s
    assert 'zb controller daemon v1' not in s
    assert 'new-service' not in s and 'nssm' not in s


def test_status_validates_schema_state_and_heartbeat_fail_closed():
    s = source()
    assert 'zb-reference-bridge-v1' in s
    for state in ('starting','healthy','degraded','fatal','stopping','missing','stale'):
        assert state in s
    assert 'health.schema' in s
    assert 'health.heartbeatutc' in s
    assert '$healthstate = "missing"' in s
    for key in ('task_registered','task_enabled','task_state','health_state','pid','pid_alive','instance_id','heartbeat_age_sec','config_sha256','drive_root_reachable'):
        assert key in s
