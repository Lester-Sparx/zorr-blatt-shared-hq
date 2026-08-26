import json
from pathlib import Path
from types import SimpleNamespace

from zb_local_controller.backends.comfyui import ComfyUIBackend
from zb_local_controller.task_contract import AgentTask

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "src/zb_local_controller/workflows/salvador-production-image-edit.json"
PROMPT = ROOT / "src/zb_local_controller/prompts/salvador-production-image-edit.txt"


def _count_token(value, token):
    if isinstance(value, dict):
        return sum(_count_token(v, token) for v in value.values())
    if isinstance(value, list):
        return sum(_count_token(v, token) for v in value)
    return int(value == token)


class CaptureTransport:
    def __init__(self):
        self.payload = None

    def request_json(self, method, path, payload=None):
        assert method == "POST"
        assert path == "/prompt"
        self.payload = payload
        return {"prompt_id": "smoke-prompt-id"}


def test_task7_disposable_core_only_workflow_is_ready_for_backend_submission():
    assert WORKFLOW.is_file(), "Task 7 workflow asset is missing"
    assert PROMPT.is_file(), "Task 7 prompt asset is missing"

    workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    assert _count_token(workflow, "__ZB_REFERENCE__") == 1
    assert _count_token(workflow, "__ZB_PROMPT__") == 1

    by_class = {node["class_type"]: (node_id, node) for node_id, node in workflow.items()}
    assert set(by_class) == {"LoadImage", "ImageInvert", "SaveImage"}
    assert len(workflow) == 3

    load_id, load = by_class["LoadImage"]
    invert_id, invert = by_class["ImageInvert"]
    _, save = by_class["SaveImage"]
    assert load["inputs"]["image"] == "__ZB_REFERENCE__"
    assert invert["inputs"]["image"] == [load_id, 0]
    assert save["inputs"]["images"] == [invert_id, 0]

    prompt_text = PROMPT.read_text(encoding="utf-8").strip().lower()
    assert "disposable" in prompt_text
    assert ".safetensors" not in prompt_text
    assert "checkpoint" not in prompt_text

    transport = CaptureTransport()
    backend = ComfyUIBackend("http://127.0.0.1:8188", WORKFLOW, transport=transport)
    task = AgentTask(
        "ZB-SALVADOR-SMOKE-001",
        "SALVADOR",
        "PRODUCTION_IMAGE_EDIT",
        "ASSIGNED",
        "LOCAL_INBOX",
        "Disposable smoke: invert the supplied non-production reference image.",
    )
    reference = SimpleNamespace(path=Path("reference.png"))

    assert backend.submit(task, reference) == "smoke-prompt-id"
    submitted = transport.payload["prompt"]
    assert submitted[load_id]["inputs"]["image"] == "reference.png"
    assert _count_token(submitted, "__ZB_REFERENCE__") == 0
    assert _count_token(submitted, "__ZB_PROMPT__") == 0
