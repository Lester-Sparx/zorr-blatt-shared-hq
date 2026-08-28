from zb_communication_orchestrator.work_execution import WorkRunContext, start_current_work_run


def test_work_run_is_not_execution_before_role_phase():
    result = start_current_work_run(WorkRunContext('abc-123', False))
    assert result.started is False
    assert result.execution_id is None


def test_missing_physical_delivery_id_fails_closed():
    result = start_current_work_run(WorkRunContext(None, True))
    assert result.started is False
    assert result.execution_id is None


def test_current_work_event_run_becomes_real_role_execution_after_received_gate():
    result = start_current_work_run(WorkRunContext('b8cc54f0-a2c2-11f1-908c-33803cbeadec', True))
    assert result.started is True
    assert result.execution_id == 'work-event:b8cc54f0-a2c2-11f1-908c-33803cbeadec'
    assert result.evidence_ref is None
    assert result.evidence_sha256 is None


def test_delivery_id_must_be_stable_safe_token():
    for value in ('', 'bad id', 'x\ny', 'x'*129):
        result = start_current_work_run(WorkRunContext(value, True))
        assert result.started is False
        assert result.execution_id is None
