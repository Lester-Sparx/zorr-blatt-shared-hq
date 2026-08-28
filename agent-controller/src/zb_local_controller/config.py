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
    daemon_runtime_root: Path = Path(r"D:\BLATT2\ZB_AGENT_RUNTIME\controller-daemon")


def load_config(path: Path) -> ControllerConfig:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ConfigurationError("CONFIG_INVALID") from exc
    allowed = {"repository", "inboxRoot", "resultRoot", "comfyuiUrl", "workflowPath", "pollIntervalSeconds", "maxExecutionSeconds", "daemonRuntimeRoot"}
    if set(raw) - allowed:
        raise ConfigurationError("CONFIG_UNKNOWN_KEY")
    try:
        return ControllerConfig(
            repository=str(raw.get("repository", ControllerConfig.repository)),
            inbox_root=Path(raw.get("inboxRoot", str(ControllerConfig.inbox_root))),
            result_root=Path(raw.get("resultRoot", str(ControllerConfig.result_root))),
            comfyui_url=str(raw.get("comfyuiUrl", ControllerConfig.comfyui_url)),
            workflow_path=Path(raw.get("workflowPath", str(ControllerConfig.workflow_path))),
            poll_interval_seconds=float(raw.get("pollIntervalSeconds", ControllerConfig.poll_interval_seconds)),
            max_execution_seconds=float(raw.get("maxExecutionSeconds", ControllerConfig.max_execution_seconds)),
            daemon_runtime_root=Path(raw.get("daemonRuntimeRoot", str(ControllerConfig.daemon_runtime_root))),
        )
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("CONFIG_INVALID") from exc
