from zb_local_controller.task_contract import TaskContractError, parse_task

VALID = """ZB_AGENT_TASK_V0
TASK_ID = ZB-SALVADOR-20260826T160000Z-001
AGENT = SALVADOR
TASK_KIND = PRODUCTION_IMAGE_EDIT
STATE = ASSIGNED
REFERENCE = LOCAL_INBOX

Simplify the supplied face reference without redesign.
"""


def assert_code(text, code):
    try:
        parse_task(text)
    except TaskContractError as exc:
        assert exc.code == code
    else:
        raise AssertionError("expected TaskContractError")


def test_parse_valid_task():
    task = parse_task(VALID)
    assert task.task_id == "ZB-SALVADOR-20260826T160000Z-001"
    assert task.agent == "SALVADOR"
    assert task.task_kind == "PRODUCTION_IMAGE_EDIT"
    assert task.state == "ASSIGNED"
    assert task.reference == "LOCAL_INBOX"
    assert "Simplify the supplied face reference" in task.direction


def test_rejects_unknown_agent():
    assert_code(VALID.replace("AGENT = SALVADOR", "AGENT = LESTER"), "INVALID_AGENT")


def test_rejects_missing_marker():
    assert_code(VALID.replace("ZB_AGENT_TASK_V0\n", ""), "MISSING_MARKER")


def test_rejects_duplicate_field():
    assert_code(VALID.replace("AGENT = SALVADOR\n", "AGENT = SALVADOR\nAGENT = SALVADOR\n"), "DUPLICATE_FIELD")


def test_rejects_missing_field():
    assert_code(VALID.replace("REFERENCE = LOCAL_INBOX\n", ""), "MISSING_FIELD")


def test_rejects_invalid_task_kind():
    assert_code(VALID.replace("PRODUCTION_IMAGE_EDIT", "OTHER"), "INVALID_TASK_KIND")


def test_rejects_invalid_state():
    assert_code(VALID.replace("STATE = ASSIGNED", "STATE = RUNNING"), "INVALID_STATE")


def test_rejects_invalid_reference_mode():
    assert_code(VALID.replace("REFERENCE = LOCAL_INBOX", "REFERENCE = URL"), "INVALID_REFERENCE_MODE")


def test_rejects_unknown_machine_key():
    assert_code(VALID.replace("REFERENCE = LOCAL_INBOX\n", "REFERENCE = LOCAL_INBOX\nPATH = C:\\\\evil\n"), "UNKNOWN_FIELD")


def test_rejects_empty_direction():
    head = VALID.split("\n\n", 1)[0]
    assert_code(head + "\n", "EMPTY_DIRECTION")
