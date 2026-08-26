from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .base import BackendError, BackendPollResult


class UrllibTransport:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request_json(self, method: str, path: str, payload: Any = None) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"} if data is not None else {}
        request = Request(self.base_url + path, data=data, headers=headers, method=method)
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def request_bytes(self, path: str) -> bytes:
        request = Request(self.base_url + path, method="GET")
        with urlopen(request, timeout=self.timeout) as response:
            return response.read()


class ComfyUIBackend:
    PROMPT_TOKEN = "__ZB_PROMPT__"
    REFERENCE_TOKEN = "__ZB_REFERENCE__"

    def __init__(self, base_url: str, workflow_path: Path, transport: Any | None = None):
        self.base_url = base_url.rstrip("/")
        self.workflow_path = Path(workflow_path)
        self.transport = transport or UrllibTransport(self.base_url)
        self._outputs: dict[str, dict[str, str]] = {}

    def ensure_ready(self) -> None:
        try:
            self.transport.request_json("GET", "/system_stats")
        except Exception as exc:
            raise BackendError("BACKEND_UNAVAILABLE") from exc

    def _replace_tokens(self, value: Any, prompt: str, reference_name: str, counts: dict[str, int]) -> Any:
        if isinstance(value, dict):
            return {k: self._replace_tokens(v, prompt, reference_name, counts) for k, v in value.items()}
        if isinstance(value, list):
            return [self._replace_tokens(v, prompt, reference_name, counts) for v in value]
        if value == self.PROMPT_TOKEN:
            counts["prompt"] += 1
            return prompt
        if value == self.REFERENCE_TOKEN:
            counts["reference"] += 1
            return reference_name
        return value

    def _workflow_for(self, task: Any, reference: Any) -> dict[str, Any]:
        try:
            raw = json.loads(self.workflow_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise BackendError("WORKFLOW_TEMPLATE_INVALID") from exc
        counts = {"prompt": 0, "reference": 0}
        replaced = self._replace_tokens(raw, task.direction, reference.path.name, counts)
        if counts != {"prompt": 1, "reference": 1}:
            raise BackendError("WORKFLOW_TEMPLATE_INVALID")
        return replaced

    def submit(self, task: Any, reference: Any) -> str:
        workflow = self._workflow_for(task, reference)
        try:
            response = self.transport.request_json("POST", "/prompt", {"prompt": workflow})
        except Exception as exc:
            raise BackendError("BACKEND_UNAVAILABLE") from exc
        prompt_id = response.get("prompt_id") if isinstance(response, dict) else None
        if not isinstance(prompt_id, str) or not prompt_id.strip():
            raise BackendError("SUBMIT_EVIDENCE_MISSING")
        return prompt_id.strip()

    def poll(self, execution_id: str) -> BackendPollResult:
        try:
            history = self.transport.request_json("GET", f"/history/{execution_id}")
        except Exception as exc:
            raise BackendError("BACKEND_UNAVAILABLE") from exc
        entry = history.get(execution_id, {}) if isinstance(history, dict) else {}
        status = entry.get("status", {}) if isinstance(entry, dict) else {}
        status_str = str(status.get("status_str", "")).lower()
        messages = status.get("messages") or []
        if status_str == "error" or any(isinstance(m, list) and m and m[0] == "execution_error" for m in messages):
            return BackendPollResult("FAILED", "BACKEND_EXECUTION_FAILED")

        outputs = entry.get("outputs", {}) if isinstance(entry, dict) else {}
        image = None
        for node in outputs.values() if isinstance(outputs, dict) else ():
            images = node.get("images") if isinstance(node, dict) else None
            if images:
                image = images[0]
                break
        completed = bool(status.get("completed")) or status_str in {"success", "completed"}
        if completed and image:
            self._outputs[execution_id] = {
                "filename": str(image.get("filename", "")),
                "subfolder": str(image.get("subfolder", "")),
                "type": str(image.get("type", "output")),
            }
            return BackendPollResult("COMPLETE")
        if completed:
            return BackendPollResult("FAILED", "BACKEND_OUTPUT_MISSING")
        return BackendPollResult("RUNNING")

    def collect(self, execution_id: str) -> bytes:
        output = self._outputs.get(execution_id)
        if not output or not output["filename"]:
            raise BackendError("BACKEND_OUTPUT_MISSING")
        query = urlencode(output)
        try:
            content = self.transport.request_bytes(f"/view?{query}")
        except Exception as exc:
            raise BackendError("BACKEND_UNAVAILABLE") from exc
        if not content or not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise BackendError("BACKEND_OUTPUT_INVALID")
        return content
