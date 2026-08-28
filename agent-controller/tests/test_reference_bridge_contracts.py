import pytest

from zb_reference_bridge.contracts import (
    ReferenceContractError,
    format_reference_failed,
    format_reference_ready,
    latest_agent_terminal_state,
    parse_delivery_event,
)


def canonical_delivery(**overrides):
    fields = {
        "TASK_ID": "ZB-REF-001",
        "DELIVERY_ID": "DELIV-001",
        "DRIVE_FOLDER_ID": "folder123",
        "DRIVE_FILE_ID": "file123",
        "SOURCE_FILE_NAME": "source.png",
        "SIZE_BYTES": "8",
        "SOURCE_SHA256": "a" * 64,
        "MIME_TYPE": "image/png",
        "SOURCE_STATUS": "OWNER_PROVIDED_REFERENCE",
        "TRANSPORT": "GOOGLE_DRIVE",
    }
    fields.update(overrides)
    return "ZB_REFERENCE_DELIVERY_V1\n" + "\n".join(f"{k} = {v}" for k, v in fields.items())


def test_parse_delivery_event_accepts_canonical_schema():
    d = parse_delivery_event(canonical_delivery())
    assert d and d.task_id == "ZB-REF-001" and d.delivery_id == "DELIV-001"
    assert d.size_bytes == 8


def test_non_delivery_comment_is_ignored():
    assert parse_delivery_event("hello") is None


@pytest.mark.parametrize("body", [
    canonical_delivery(EXTRA="x"),
    canonical_delivery().replace("TASK_ID = ZB-REF-001", "TASK_ID = ZB-REF-001\nTASK_ID = AGAIN"),
    canonical_delivery(SOURCE_SHA256="A" * 64),
    canonical_delivery(SOURCE_STATUS="OTHER"),
    canonical_delivery(TRANSPORT="OTHER"),
])
def test_malformed_delivery_event_fails_closed(body):
    with pytest.raises(ReferenceContractError) as exc:
        parse_delivery_event(body)
    assert exc.value.code == "REFERENCE_DELIVERY_EVENT_INVALID"


def test_reference_ready_formatter_is_transport_only():
    text = format_reference_ready("ZB-REF-001", "DELIV-001", "a" * 64)
    assert text.splitlines()[0] == "ZB_REFERENCE_EVENT_V1"
    assert "STATE = REFERENCE_READY" in text
    assert "SOURCE_SHA256 = " + "a" * 64 in text
    assert "ZB_AGENT_EVENT_V0" not in text


def test_reference_failed_formatter_is_transport_only():
    text = format_reference_failed("ZB-REF-001", "DELIV-001", "REFERENCE_HASH_MISMATCH")
    assert "STATE = REFERENCE_FAILED" in text
    assert "ERROR_CODE = REFERENCE_HASH_MISMATCH" in text
    assert "ZB_AGENT_EVENT_V0" not in text


def test_latest_agent_terminal_state_observes_matching_terminal_only():
    comments = (
        "ZB_AGENT_EVENT_V0\nTASK_ID = OTHER\nSTATE = RESULT_READY\nEXECUTION_ID = x",
        "ZB_AGENT_EVENT_V0\nTASK_ID = ZB-REF-001\nSTATE = RUNNING\nEXECUTION_ID = y",
        "ZB_AGENT_EVENT_V0\nTASK_ID = ZB-REF-001\nSTATE = FAILED\nEXECUTION_ID = z",
    )
    assert latest_agent_terminal_state(comments, "ZB-REF-001") == "FAILED"


def test_bridge_integration_does_not_broaden_current_agent_task_legality():
    from zb_local_controller.task_contract import ALLOWED_TASK_KINDS
    assert ALLOWED_TASK_KINDS == {"PRODUCTION_IMAGE_EDIT"}
