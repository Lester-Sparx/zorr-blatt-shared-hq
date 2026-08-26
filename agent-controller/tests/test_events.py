import pytest
from zb_local_controller.events import EventFormatError, format_event


def test_result_event_contains_metadata_not_local_path():
    body = format_event(
        task_id="ZB-SALVADOR-X-001",
        state="RESULT_READY",
        execution_id="prompt-123",
        result_sha256="abc123",
        error_code=None,
    )
    assert "ZB_AGENT_EVENT_V0" in body
    assert "STATE = RESULT_READY" in body
    assert "EXECUTION_ID = prompt-123" in body
    assert "RESULT_SHA256 = abc123" in body
    assert "D:\\" not in body
    assert "SALVADOR_RESULT_READY" in body
    assert "SALVADOR_RUNNING" not in body


def test_running_compatibility_line_only_for_running():
    body = format_event("ZB-X", "RUNNING", "prompt-1", None, None)
    assert "SALVADOR_RUNNING" in body
    assert "SALVADOR_RESULT_READY" not in body


def test_reference_compatibility_line_only_for_waiting():
    body = format_event("ZB-X", "WAITING_REFERENCE", None, None, None)
    assert "SALVADOR_REFERENCE_REQUIRED" in body
    assert "EXECUTION_ID = NONE" in body


def test_rejects_multiline_metadata():
    with pytest.raises(EventFormatError):
        format_event("ZB-X\nINJECT", "RUNNING", "p", None, None)
