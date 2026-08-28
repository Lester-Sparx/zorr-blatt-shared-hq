import pytest
from zb_communication_orchestrator.execution import ExecutionError, StartResult, TerminalResult, require_started, require_terminal
def test_queued_is_not_running():
    with pytest.raises(ExecutionError) as e: require_started(StartResult(False,None,None,None))
    assert e.value.code=='EXECUTION_START_FAILED'
def test_started_requires_real_id():
    with pytest.raises(ExecutionError): require_started(StartResult(True,None,None,None))
    assert require_started(StartResult(True,'work-123','ref','a'*64)).execution_id=='work-123'
def test_timeout_never_upgrades_to_success():
    with pytest.raises(ExecutionError) as e: require_terminal(TerminalResult(False,'EXECUTION_TIMEOUT','ref','a'*64,timed_out=True))
    assert e.value.code=='EXECUTION_TIMEOUT'
