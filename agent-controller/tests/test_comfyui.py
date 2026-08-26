import json
from pathlib import Path
from types import SimpleNamespace
import pytest

from zb_local_controller.backends.base import BackendError
from zb_local_controller.backends.comfyui import ComfyUIBackend
from zb_local_controller.task_contract import AgentTask

PNG = b"\x89PNG\r\n\x1a\n" + b"data"
TASK = AgentTask("ZB-X", "SALVADOR", "PRODUCTION_IMAGE_EDIT", "ASSIGNED", "LOCAL_INBOX", "clean graphite")
REF = SimpleNamespace(path=Path("ref.png"))


class FakeTransport:
    def __init__(self, json_responses=None, byte_responses=None, errors=None):
        self.json_responses = list(json_responses or [])
        self.byte_responses = list(byte_responses or [])
        self.errors = list(errors or [])
        self.calls = []

    def request_json(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if self.errors:
            error = self.errors.pop(0)
            if error:
                raise error
        return self.json_responses.pop(0) if self.json_responses else {}

    def request_bytes(self, path):
        self.calls.append(("GET_BYTES", path, None))
        return self.byte_responses.pop(0) if self.byte_responses else b""


def workflow(tmp_path: Path) -> Path:
    p = tmp_path / "workflow.json"
    p.write_text(json.dumps({
        "1": {"inputs": {"text": "__ZB_PROMPT__", "image": "__ZB_REFERENCE__", "ckpt_name": "LOCAL_MODEL.safetensors"}}
    }), encoding="utf-8")
    return p


def backend(tmp_path, transport):
    return ComfyUIBackend("http://127.0.0.1:8188", workflow(tmp_path), transport=transport)


def test_system_stats_success_is_ready(tmp_path):
    t = FakeTransport(json_responses=[{"system": {}}])
    backend(tmp_path, t).ensure_ready()
    assert t.calls[0][:2] == ("GET", "/system_stats")


def test_unreachable_backend_is_stable_error(tmp_path):
    t = FakeTransport(errors=[OSError("down")])
    with pytest.raises(BackendError) as exc:
        backend(tmp_path, t).ensure_ready()
    assert exc.value.code == "BACKEND_UNAVAILABLE"


def test_submit_without_prompt_id_is_not_execution_evidence(tmp_path):
    t = FakeTransport(json_responses=[{}])
    with pytest.raises(BackendError) as exc:
        backend(tmp_path, t).submit(TASK, REF)
    assert exc.value.code == "SUBMIT_EVIDENCE_MISSING"


def test_submit_returns_exact_prompt_id_and_only_replaces_allowlisted_tokens(tmp_path):
    t = FakeTransport(json_responses=[{"prompt_id": "prompt-123"}])
    result = backend(tmp_path, t).submit(TASK, REF)
    assert result == "prompt-123"
    payload = t.calls[0][2]
    inputs = payload["prompt"]["1"]["inputs"]
    assert inputs["text"] == "clean graphite"
    assert inputs["image"] == "ref.png"
    assert inputs["ckpt_name"] == "LOCAL_MODEL.safetensors"


def test_history_without_completion_is_running(tmp_path):
    t = FakeTransport(json_responses=[{"prompt-123": {"status": {"status_str": "running"}, "outputs": {}}}])
    result = backend(tmp_path, t).poll("prompt-123")
    assert result.state == "RUNNING"


def test_history_completed_with_output_is_complete(tmp_path):
    history = {"prompt-123": {"status": {"completed": True, "status_str": "success"}, "outputs": {"9": {"images": [{"filename": "out.png", "subfolder": "", "type": "output"}]}}}}
    t = FakeTransport(json_responses=[history])
    result = backend(tmp_path, t).poll("prompt-123")
    assert result.state == "COMPLETE"


def test_history_execution_error_is_failed(tmp_path):
    history = {"prompt-123": {"status": {"status_str": "error", "messages": [["execution_error", {"exception_message": "boom"}]]}, "outputs": {}}}
    t = FakeTransport(json_responses=[history])
    result = backend(tmp_path, t).poll("prompt-123")
    assert result.state == "FAILED"
    assert result.error_code == "BACKEND_EXECUTION_FAILED"


def test_collect_returns_nonempty_png_bytes(tmp_path):
    history = {"prompt-123": {"status": {"completed": True, "status_str": "success"}, "outputs": {"9": {"images": [{"filename": "out.png", "subfolder": "sub", "type": "output"}]}}}}
    t = FakeTransport(json_responses=[history], byte_responses=[PNG])
    b = backend(tmp_path, t)
    assert b.poll("prompt-123").state == "COMPLETE"
    assert b.collect("prompt-123") == PNG
    assert "/view?" in t.calls[-1][1]
