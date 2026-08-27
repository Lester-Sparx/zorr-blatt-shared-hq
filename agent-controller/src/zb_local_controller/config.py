from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


class ConfigurationError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ControllerConfig:
    repository: str = "Lester-Sparx/zorr-blatt-shared-hq"
    inbox_root: Path = Path(r"D:\BLATT2\ZB_AGENT_INBOX")
    result_root: Path = Path(r"D:\BLATT2\ZB_AGENT_RESULTS")
    comfyui_url: str = "http://127.0.0.1:8188"
    workflow_path: Path = Path("src/zb_local_controller/workflows/salvador-production-image-edit.json")
    poll_interval_seconds: float = 15.0
    max_execution_seconds: float = 900.0
    comfyui_input_root: Path = Path(r"D:\BLATT2\ComfyUI_windows_portable\ComfyUI\input")
    canon_reference_workflow_path: Path = Path("src/zb_local_controller/workflows/salvador-canon-reference-edit-v1.json")
    canon_prompt_path: Path = Path("src/zb_local_controller/prompts/salvador-canon-reference-edit-v1.txt")
    canon_model_name: str = ""
    canon_denoise: float = 0.35
    canon_max_long_side: int = 768
    canon_negative_prompt: str = "redesign, changed pose, changed composition, extra limbs, text, watermark"
    daemon_runtime_root: Path = Path(r"D:\BLATT2\ZB_AGENT_RUNTIME\controller-daemon")


def load_config(path: Path) -> ControllerConfig:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ConfigurationError("CONFIG_INVALID") from exc
    allowed = {
        "repository", "inboxRoot", "resultRoot", "comfyuiUrl", "workflowPath",
        "pollIntervalSeconds", "maxExecutionSeconds", "comfyuiInputRoot",
        "canonReferenceWorkflowPath", "canonPromptPath", "canonModelName",
        "canonDenoise", "canonMaxLongSide", "canonNegativePrompt", "daemonRuntimeRoot",
    }
    if set(raw) - allowed:
        raise ConfigurationError("CONFIG_UNKNOWN_KEY")
    try:
        config = ControllerConfig(
            repository=str(raw.get("repository", ControllerConfig.repository)),
            inbox_root=Path(raw.get("inboxRoot", str(ControllerConfig.inbox_root))),
            result_root=Path(raw.get("resultRoot", str(ControllerConfig.result_root))),
            comfyui_url=str(raw.get("comfyuiUrl", ControllerConfig.comfyui_url)),
            workflow_path=Path(raw.get("workflowPath", str(ControllerConfig.workflow_path))),
            poll_interval_seconds=float(raw.get("pollIntervalSeconds", ControllerConfig.poll_interval_seconds)),
            max_execution_seconds=float(raw.get("maxExecutionSeconds", ControllerConfig.max_execution_seconds)),
            comfyui_input_root=Path(raw.get("comfyuiInputRoot", str(ControllerConfig.comfyui_input_root))),
            canon_reference_workflow_path=Path(raw.get("canonReferenceWorkflowPath", str(ControllerConfig.canon_reference_workflow_path))),
            canon_prompt_path=Path(raw.get("canonPromptPath", str(ControllerConfig.canon_prompt_path))),
            canon_model_name=str(raw.get("canonModelName", ControllerConfig.canon_model_name)),
            canon_denoise=float(raw.get("canonDenoise", ControllerConfig.canon_denoise)),
            canon_max_long_side=int(raw.get("canonMaxLongSide", ControllerConfig.canon_max_long_side)),
            canon_negative_prompt=str(raw.get("canonNegativePrompt", ControllerConfig.canon_negative_prompt)),
            daemon_runtime_root=Path(raw.get("daemonRuntimeRoot", str(ControllerConfig.daemon_runtime_root))),
        )
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("CONFIG_INVALID") from exc
    if not 0.25 <= config.canon_denoise <= 0.45:
        raise ConfigurationError("CONFIG_INVALID")
    if not 64 <= config.canon_max_long_side <= 768:
        raise ConfigurationError("CONFIG_INVALID")
    return config
