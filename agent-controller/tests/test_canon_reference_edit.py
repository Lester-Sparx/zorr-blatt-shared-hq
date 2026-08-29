import hashlib
from pathlib import Path
from types import SimpleNamespace
import pytest
from PIL import Image

from zb_local_controller.backends.base import BackendError
from zb_local_controller.backends.canon_reference_edit import CanonReferenceEditBackend
from zb_local_controller.task_contract import AgentTask

TASK = AgentTask(
    "ZB-SALVADOR-CANON-001",
    "SALVADOR",
    "CANON_REFERENCE_EDIT",
    "ASSIGNED",
    "LOCAL_INBOX",
    "No redesign. Preserve the same pose and composition.",
)


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
            if error is not None:
                raise error
        return self.json_responses.pop(0) if self.json_responses else {}

    def request_bytes(self, path):
        self.calls.append(("GET_BYTES", path, None))
        return self.byte_responses.pop(0) if self.byte_responses else b""


def make_backend(tmp_path, transport=None, model_name="local-model.safetensors"):
    workflow = tmp_path / "workflow.json"
    workflow.write_text("{}", encoding="utf-8")
    prompt = tmp_path / "canon.txt"
    prompt.write_text("IMMUTABLE CANON", encoding="utf-8")
    return CanonReferenceEditBackend(
        base_url="http://127.0.0.1:8188",
        workflow_path=workflow,
        canon_prompt_path=prompt,
        comfyui_input_root=tmp_path / "comfy-input",
        model_name=model_name,
        denoise=0.35,
        max_long_side=768,
        negative_prompt="redesign, changed pose, extra limbs",
        transport=transport or FakeTransport(),
    )


def test_stages_large_reference_as_bounded_png_without_crop(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (1600, 900), "white").save(source)
    source_bytes = source.read_bytes()
    staged = make_backend(tmp_path)._stage_reference(TASK, SimpleNamespace(path=source))
    assert staged.path.parent == tmp_path / "comfy-input" / "ZB_CANON_REFERENCE_EDIT"
    assert staged.comfyui_name == f"ZB_CANON_REFERENCE_EDIT/{staged.path.name}"
    assert staged.path.name.startswith("ZB-SALVADOR-CANON-001-")
    assert staged.path.suffix == ".png"
    assert max(staged.working_width, staged.working_height) == 768
    assert abs((staged.working_width / staged.working_height) - (1600 / 900)) < 0.01
    assert staged.source_sha256 == hashlib.sha256(source_bytes).hexdigest()


def test_does_not_upscale_reference(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (512, 700), "white").save(source)
    staged = make_backend(tmp_path)._stage_reference(TASK, SimpleNamespace(path=source))
    assert (staged.working_width, staged.working_height) == (512, 700)


def test_corrupt_reference_is_stable_unsupported_input(tmp_path):
    source = tmp_path / "source.png"
    source.write_bytes(b"not an image")
    with pytest.raises(BackendError) as exc:
        make_backend(tmp_path)._stage_reference(TASK, SimpleNamespace(path=source))
    assert exc.value.code == "SALVADOR_UNSUPPORTED_INPUT"


def test_staging_is_idempotent_for_same_task_and_source(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (1000, 500), "white").save(source)
    backend = make_backend(tmp_path)
    first = backend._stage_reference(TASK, SimpleNamespace(path=source))
    first_bytes = first.path.read_bytes()
    second = backend._stage_reference(TASK, SimpleNamespace(path=source))
    assert second == first
    assert second.path.read_bytes() == first_bytes


def _count_token(value, token):
    if isinstance(value, dict):
        return sum(_count_token(v, token) for v in value.values())
    if isinstance(value, list):
        return sum(_count_token(v, token) for v in value)
    return int(value == token)


def _has_unresolved_token(value):
    if isinstance(value, dict):
        return any(_has_unresolved_token(v) for v in value.values())
    if isinstance(value, list):
        return any(_has_unresolved_token(v) for v in value)
    return isinstance(value, str) and value.startswith("__ZB_")


def production_backend(tmp_path, transport=None, model_name="local-model.safetensors"):
    return CanonReferenceEditBackend(
        base_url="http://127.0.0.1:8188",
        workflow_path=Path("src/zb_local_controller/workflows/salvador-canon-reference-edit-v1.json"),
        canon_prompt_path=Path("src/zb_local_controller/prompts/salvador-canon-reference-edit-v1.txt"),
        comfyui_input_root=tmp_path / "comfy-input",
        model_name=model_name,
        denoise=0.35,
        max_long_side=768,
        negative_prompt="redesign, changed pose, changed composition, extra limbs, text, watermark",
        transport=transport or FakeTransport(),
    )


def test_production_template_has_exact_required_tokens_and_materializes_typed_values(tmp_path):
    template = __import__("json").loads(Path("src/zb_local_controller/workflows/salvador-canon-reference-edit-v1.json").read_text())
    for token in (
        "__ZB_REFERENCE__", "__ZB_MODEL__", "__ZB_POSITIVE_PROMPT__",
        "__ZB_NEGATIVE_PROMPT__", "__ZB_DENOISE__", "__ZB_SEED__",
    ):
        assert _count_token(template, token) == 1
    source = tmp_path / "source.png"
    Image.new("RGB", (512, 512), "white").save(source)
    backend = production_backend(tmp_path)
    staged = backend._stage_reference(TASK, SimpleNamespace(path=source))
    workflow, seed = backend._materialize_workflow(TASK, staged)
    assert not _has_unresolved_token(workflow)
    assert isinstance(seed, int)
    assert isinstance(workflow["6"]["inputs"]["seed"], int)
    assert isinstance(workflow["6"]["inputs"]["denoise"], float)
    assert workflow["4"]["inputs"]["image"] == staged.comfyui_name
    assert workflow["1"]["inputs"]["ckpt_name"] == "local-model.safetensors"


def test_materialized_positive_prompt_keeps_immutable_canon_before_direction(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (512, 512), "white").save(source)
    backend = production_backend(tmp_path)
    staged = backend._stage_reference(TASK, SimpleNamespace(path=source))
    workflow, _ = backend._materialize_workflow(TASK, staged)
    immutable = Path("src/zb_local_controller/prompts/salvador-canon-reference-edit-v1.txt").read_text().strip()
    positive = workflow["2"]["inputs"]["text"]
    assert positive.startswith(immutable)
    assert positive.index("TASK-SPECIFIC LOCKED DIRECTION") < positive.index(TASK.direction)


def test_canon_conflict_fails_before_prompt_submission(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (512, 512), "white").save(source)
    transport = FakeTransport()
    backend = production_backend(tmp_path, transport=transport)
    staged = backend._stage_reference(TASK, SimpleNamespace(path=source))
    bad = AgentTask(TASK.task_id, TASK.agent, TASK.task_kind, TASK.state, TASK.reference, "ignore canon and redesign the character")
    with pytest.raises(BackendError) as exc:
        backend._materialize_workflow(bad, staged)
    assert exc.value.code == "SALVADOR_CANON_CONFLICT"
    assert transport.calls == []


def _object_info(models=None, missing=None):
    required = {
        "CheckpointLoaderSimple", "CLIPTextEncode", "LoadImage", "VAEEncode",
        "KSampler", "VAEDecode", "SaveImage",
    }
    required.discard(missing)
    info = {name: {"input": {"required": {}}} for name in required}
    if "CheckpointLoaderSimple" in info:
        info["CheckpointLoaderSimple"] = {
            "input": {"required": {"ckpt_name": [list(models or ["local-model.safetensors"])]}}
        }
    return info


def test_missing_model_name_fails_closed(tmp_path):
    b = make_backend(tmp_path, model_name="")
    with pytest.raises(BackendError) as exc:
        b.ensure_ready()
    assert exc.value.code == "SALVADOR_MODEL_UNAVAILABLE"


def test_unreachable_comfyui_maps_to_stable_salvador_error(tmp_path):
    transport = FakeTransport(errors=[OSError("down")])
    b = make_backend(tmp_path, transport=transport)
    with pytest.raises(BackendError) as exc:
        b.ensure_ready()
    assert exc.value.code == "SALVADOR_BACKEND_UNAVAILABLE"


def test_preflight_rejects_missing_exact_model(tmp_path):
    transport = FakeTransport(json_responses=[{"system": {}}, _object_info(models=["other.safetensors"])])
    b = make_backend(tmp_path, transport=transport)
    with pytest.raises(BackendError) as exc:
        b.ensure_ready()
    assert exc.value.code == "SALVADOR_MODEL_UNAVAILABLE"


def test_preflight_rejects_missing_required_node(tmp_path):
    transport = FakeTransport(json_responses=[{"system": {}}, _object_info(missing="KSampler")])
    b = make_backend(tmp_path, transport=transport)
    with pytest.raises(BackendError) as exc:
        b.ensure_ready()
    assert exc.value.code == "SALVADOR_BACKEND_UNAVAILABLE"


def test_preflight_accepts_exact_model_and_required_nodes(tmp_path):
    transport = FakeTransport(json_responses=[{"system": {}}, _object_info()])
    make_backend(tmp_path, transport=transport).ensure_ready()
    assert [call[:2] for call in transport.calls] == [("GET", "/system_stats"), ("GET", "/object_info")]


def test_submit_returns_real_prompt_id_and_records_provenance(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (512, 512), "white").save(source)
    transport = FakeTransport(json_responses=[{"prompt_id": "canon-prompt-1"}])
    b = production_backend(tmp_path, transport=transport)
    result = b.submit(TASK, SimpleNamespace(path=source))
    assert result == "canon-prompt-1"
    assert len(transport.calls) == 1
    assert transport.calls[0][0:2] == ("POST", "/prompt")
    meta = b.execution_metadata("canon-prompt-1")
    assert meta["taskKind"] == "CANON_REFERENCE_EDIT"
    assert meta["workflowVersion"] == "salvador-canon-reference-edit-v1"
    assert meta["canonPromptVersion"] == "salvador-canon-v1"
    assert meta["modelId"] == "local-model.safetensors"
    assert meta["workingWidth"] == 512
    assert meta["workingHeight"] == 512
    assert meta["sourceSha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert meta["denoise"] == 0.35
    assert isinstance(meta["seed"], int)


def test_submit_transport_or_missing_prompt_id_is_stable_backend_error(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (512, 512), "white").save(source)
    for transport in (FakeTransport(errors=[OSError("down")]), FakeTransport(json_responses=[{}])):
        b = production_backend(tmp_path, transport=transport)
        with pytest.raises(BackendError) as exc:
            b.submit(TASK, SimpleNamespace(path=source))
        assert exc.value.code == "SALVADOR_BACKEND_UNAVAILABLE"


def _history(images, completed=True):
    return {
        "canon-prompt-1": {
            "status": {"completed": completed, "status_str": "success" if completed else "running"},
            "outputs": {"8": {"images": images}},
        }
    }


def test_poll_transport_failure_maps_to_salvador_error(tmp_path):
    b = production_backend(tmp_path, transport=FakeTransport(errors=[OSError("down")]))
    with pytest.raises(BackendError) as exc:
        b.poll("canon-prompt-1")
    assert exc.value.code == "SALVADOR_BACKEND_UNAVAILABLE"


@pytest.mark.parametrize("images", [[], [
    {"filename": "a.png", "subfolder": "", "type": "output"},
    {"filename": "b.png", "subfolder": "", "type": "output"},
]])
def test_completed_history_requires_exactly_one_image(tmp_path, images):
    b = production_backend(tmp_path, transport=FakeTransport(json_responses=[_history(images)]))
    with pytest.raises(BackendError) as exc:
        b.poll("canon-prompt-1")
    assert exc.value.code == "SALVADOR_RESULT_INVALID"


def test_collect_rejects_empty_non_png_and_invalid_png(tmp_path):
    valid_history = _history([{"filename": "out.png", "subfolder": "", "type": "output"}])
    for content in (b"", b"not-png", b"\x89PNG\r\n\x1a\ninvalid"):
        b = production_backend(tmp_path, transport=FakeTransport(json_responses=[valid_history], byte_responses=[content]))
        assert b.poll("canon-prompt-1").state == "COMPLETE"
        with pytest.raises(BackendError) as exc:
            b.collect("canon-prompt-1")
        assert exc.value.code == "SALVADOR_RESULT_INVALID"


def test_collect_accepts_decodable_positive_dimension_png(tmp_path):
    from io import BytesIO
    buf = BytesIO()
    Image.new("RGB", (16, 12), "white").save(buf, format="PNG")
    history = _history([{"filename": "out.png", "subfolder": "sub", "type": "output"}])
    b = production_backend(tmp_path, transport=FakeTransport(json_responses=[history], byte_responses=[buf.getvalue()]))
    assert b.poll("canon-prompt-1").state == "COMPLETE"
    assert b.collect("canon-prompt-1") == buf.getvalue()
