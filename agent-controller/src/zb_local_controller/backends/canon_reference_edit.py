from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from io import BytesIO
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from PIL import Image

from .base import BackendError, BackendPollResult
from .comfyui import ComfyUIBackend
from ..production_policy import CanonPolicyError, compose_canon_prompt


@dataclass(frozen=True)
class StagedReference:
    path: Path
    comfyui_name: str
    source_sha256: str
    working_width: int
    working_height: int


class CanonReferenceEditBackend(ComfyUIBackend):
    _REQUIRED_NODES = {
        "CheckpointLoaderSimple", "CLIPTextEncode", "LoadImage", "VAEEncode",
        "KSampler", "VAEDecode", "SaveImage",
    }
    WORKFLOW_VERSION = "salvador-canon-reference-edit-v1"
    CANON_PROMPT_VERSION = "salvador-canon-v1"

    def __init__(
        self,
        base_url: str,
        workflow_path: Path,
        canon_prompt_path: Path,
        comfyui_input_root: Path,
        model_name: str,
        denoise: float,
        max_long_side: int,
        negative_prompt: str,
        transport: Any | None = None,
    ):
        super().__init__(base_url, workflow_path, transport=transport)
        self.canon_prompt_path = Path(canon_prompt_path)
        self.comfyui_input_root = Path(comfyui_input_root)
        self.model_name = str(model_name)
        self.denoise = float(denoise)
        self.max_long_side = int(max_long_side)
        self.negative_prompt = str(negative_prompt)
        self._execution_metadata: dict[str, dict[str, Any]] = {}

    def ensure_ready(self) -> None:
        if not self.model_name.strip():
            raise BackendError("SALVADOR_MODEL_UNAVAILABLE")
        try:
            self.transport.request_json("GET", "/system_stats")
            object_info = self.transport.request_json("GET", "/object_info")
        except Exception as exc:
            raise BackendError("SALVADOR_BACKEND_UNAVAILABLE") from exc
        if not isinstance(object_info, dict) or not self._REQUIRED_NODES.issubset(object_info):
            raise BackendError("SALVADOR_BACKEND_UNAVAILABLE")
        try:
            choices = object_info["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
        except Exception as exc:
            raise BackendError("SALVADOR_BACKEND_UNAVAILABLE") from exc
        if self.model_name not in choices:
            raise BackendError("SALVADOR_MODEL_UNAVAILABLE")

    def _stage_reference(self, task: Any, reference: Any) -> StagedReference:
        source_path = Path(reference.path)
        try:
            source_bytes = source_path.read_bytes()
            source_sha256 = sha256(source_bytes).hexdigest()
            with Image.open(source_path) as decoded:
                decoded.load()
                image = decoded.convert("RGB")
        except Exception as exc:
            raise BackendError("SALVADOR_UNSUPPORTED_INPUT") from exc

        if max(image.size) > self.max_long_side:
            image.thumbnail((self.max_long_side, self.max_long_side), Image.Resampling.LANCZOS)

        stage_dir = self.comfyui_input_root / "ZB_CANON_REFERENCE_EDIT"
        stage_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{task.task_id}-{source_sha256[:12]}.png"
        path = stage_dir / filename
        tmp = path.with_suffix(path.suffix + ".tmp")
        try:
            image.save(tmp, format="PNG")
            os.replace(tmp, path)
        except Exception as exc:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise BackendError("SALVADOR_UNSUPPORTED_INPUT") from exc

        return StagedReference(
            path=path,
            comfyui_name="ZB_CANON_REFERENCE_EDIT/" + filename,
            source_sha256=source_sha256,
            working_width=image.width,
            working_height=image.height,
        )
    def _materialize_workflow(self, task: Any, staged: StagedReference) -> tuple[dict[str, Any], int]:
        try:
            template = json.loads(self.workflow_path.read_text(encoding="utf-8"))
            canon_prompt = self.canon_prompt_path.read_text(encoding="utf-8").strip()
        except Exception as exc:
            raise BackendError("SALVADOR_RESULT_INVALID") from exc
        try:
            positive_prompt = compose_canon_prompt(canon_prompt, task.direction)
        except CanonPolicyError as exc:
            raise BackendError(exc.code) from exc

        seed_bytes = sha256(f"{task.task_id}:{staged.source_sha256}".encode("utf-8")).digest()[:8]
        seed = int.from_bytes(seed_bytes, "big") & ((1 << 63) - 1)
        replacements = {
            "__ZB_REFERENCE__": staged.comfyui_name,
            "__ZB_MODEL__": self.model_name,
            "__ZB_POSITIVE_PROMPT__": positive_prompt,
            "__ZB_NEGATIVE_PROMPT__": self.negative_prompt,
            "__ZB_DENOISE__": float(self.denoise),
            "__ZB_SEED__": seed,
        }
        counts = {token: 0 for token in replacements}

        def replace(value: Any) -> Any:
            if isinstance(value, dict):
                return {key: replace(item) for key, item in value.items()}
            if isinstance(value, list):
                return [replace(item) for item in value]
            if isinstance(value, str) and value in replacements:
                counts[value] += 1
                return replacements[value]
            return value

        materialized = replace(template)
        if any(count != 1 for count in counts.values()):
            raise BackendError("SALVADOR_RESULT_INVALID")

        def unresolved(value: Any) -> bool:
            if isinstance(value, dict):
                return any(unresolved(item) for item in value.values())
            if isinstance(value, list):
                return any(unresolved(item) for item in value)
            return isinstance(value, str) and value.startswith("__ZB_")

        if unresolved(materialized):
            raise BackendError("SALVADOR_RESULT_INVALID")
        if not isinstance(materialized, dict):
            raise BackendError("SALVADOR_RESULT_INVALID")
        return materialized, seed
    def submit(self, task: Any, reference: Any) -> str:
        staged = self._stage_reference(task, reference)
        workflow, seed = self._materialize_workflow(task, staged)
        try:
            response = self.transport.request_json("POST", "/prompt", {"prompt": workflow})
        except Exception as exc:
            raise BackendError("SALVADOR_BACKEND_UNAVAILABLE") from exc
        prompt_id = response.get("prompt_id") if isinstance(response, dict) else None
        if not isinstance(prompt_id, str) or not prompt_id.strip():
            raise BackendError("SALVADOR_BACKEND_UNAVAILABLE")
        prompt_id = prompt_id.strip()
        self._execution_metadata[prompt_id] = {
            "taskKind": "CANON_REFERENCE_EDIT",
            "workflowVersion": self.WORKFLOW_VERSION,
            "canonPromptVersion": self.CANON_PROMPT_VERSION,
            "modelId": self.model_name,
            "workingWidth": staged.working_width,
            "workingHeight": staged.working_height,
            "sourceSha256": staged.source_sha256,
            "seed": seed,
            "denoise": float(self.denoise),
        }
        return prompt_id

    def execution_metadata(self, execution_id: str) -> dict[str, Any]:
        return dict(self._execution_metadata.get(execution_id, {}))

    def poll(self, execution_id: str) -> BackendPollResult:
        try:
            history = self.transport.request_json("GET", f"/history/{execution_id}")
        except Exception as exc:
            raise BackendError("SALVADOR_BACKEND_UNAVAILABLE") from exc
        entry = history.get(execution_id, {}) if isinstance(history, dict) else {}
        status = entry.get("status", {}) if isinstance(entry, dict) else {}
        status_str = str(status.get("status_str", "")).lower()
        messages = status.get("messages") or []
        if status_str == "error" or any(isinstance(m, list) and m and m[0] == "execution_error" for m in messages):
            return BackendPollResult("FAILED", "BACKEND_EXECUTION_FAILED")

        completed = bool(status.get("completed")) or status_str in {"success", "completed"}
        if not completed:
            return BackendPollResult("RUNNING")

        outputs = entry.get("outputs", {}) if isinstance(entry, dict) else {}
        images: list[dict[str, Any]] = []
        if isinstance(outputs, dict):
            for node in outputs.values():
                node_images = node.get("images") if isinstance(node, dict) else None
                if isinstance(node_images, list):
                    images.extend(item for item in node_images if isinstance(item, dict))
        if len(images) != 1 or not str(images[0].get("filename", "")):
            raise BackendError("SALVADOR_RESULT_INVALID")
        image = images[0]
        self._outputs[execution_id] = {
            "filename": str(image.get("filename", "")),
            "subfolder": str(image.get("subfolder", "")),
            "type": str(image.get("type", "output")),
        }
        return BackendPollResult("COMPLETE")

    def collect(self, execution_id: str) -> bytes:
        output = self._outputs.get(execution_id)
        if not output or not output.get("filename"):
            raise BackendError("SALVADOR_RESULT_INVALID")
        try:
            content = self.transport.request_bytes(f"/view?{urlencode(output)}")
        except Exception as exc:
            raise BackendError("SALVADOR_BACKEND_UNAVAILABLE") from exc
        try:
            with Image.open(BytesIO(content)) as image:
                image.load()
                if image.format != "PNG" or image.width <= 0 or image.height <= 0:
                    raise ValueError("invalid image")
        except Exception as exc:
            raise BackendError("SALVADOR_RESULT_INVALID") from exc
        return content

