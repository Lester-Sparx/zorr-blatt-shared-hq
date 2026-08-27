import json
import pytest
from zb_local_controller.config import ConfigurationError, load_config


def test_loads_deployment_owned_execution_deadline(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"maxExecutionSeconds": 42}), encoding="utf-8")
    config = load_config(path)
    assert config.max_execution_seconds == 42.0


def test_loads_canon_reference_edit_deployment_settings(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "comfyuiInputRoot": r"D:\BLATT2\ComfyUI_windows_portable\ComfyUI\input",
        "canonReferenceWorkflowPath": "src/zb_local_controller/workflows/salvador-canon-reference-edit-v1.json",
        "canonPromptPath": "src/zb_local_controller/prompts/salvador-canon-reference-edit-v1.txt",
        "canonModelName": "local-sd15-illustration.safetensors",
        "canonDenoise": 0.35,
        "canonMaxLongSide": 768,
        "canonNegativePrompt": "redesign, changed pose, changed composition, extra limbs, text, watermark",
    }), encoding="utf-8")
    config = load_config(path)
    assert config.canon_model_name == "local-sd15-illustration.safetensors"
    assert config.canon_denoise == 0.35
    assert config.canon_max_long_side == 768


@pytest.mark.parametrize("payload", [
    {"canonDenoise": 0.24},
    {"canonDenoise": 0.46},
    {"canonMaxLongSide": 769},
])
def test_rejects_out_of_policy_canon_settings(tmp_path, payload):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ConfigurationError) as exc:
        load_config(path)
    assert exc.value.code == "CONFIG_INVALID"

from pathlib import Path


def test_loads_daemon_runtime_root(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"daemonRuntimeRoot": r"D:\BLATT2\RUNTIME\daemon"}), encoding="utf-8")
    assert load_config(path).daemon_runtime_root == Path(r"D:\BLATT2\RUNTIME\daemon")


def test_default_daemon_runtime_root_is_locked():
    from zb_local_controller.config import ControllerConfig
    assert ControllerConfig().daemon_runtime_root == Path(r"D:\BLATT2\ZB_AGENT_RUNTIME\controller-daemon")
