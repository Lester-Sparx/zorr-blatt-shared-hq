from zb_local_controller.state_machine import can_transition


def test_allowed_transitions():
    assert can_transition("ASSIGNED", "WAITING_REFERENCE")
    assert can_transition("ASSIGNED", "STARTING_BACKEND")
    assert can_transition("WAITING_REFERENCE", "STARTING_BACKEND")
    assert can_transition("STARTING_BACKEND", "RUNNING")
    assert can_transition("STARTING_BACKEND", "FAILED")
    assert can_transition("RUNNING", "RESULT_READY")
    assert can_transition("RUNNING", "FAILED")


def test_terminal_states_do_not_restart():
    assert not can_transition("RESULT_READY", "RUNNING")
    assert not can_transition("FAILED", "RUNNING")
    assert not can_transition("ASSIGNED", "RESULT_READY")
