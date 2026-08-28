import json
from pathlib import Path
import pytest
from zb_local_controller.config import ConfigurationError, ControllerConfig, load_config


def test_loads_deployment_owned_execution_deadline(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"maxExecutionSeconds": 42}), encoding="utf-8")
    assert load_config(path).max_execution_seconds == 42.0


def test_loads_only_new_daemon_runtime_root(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"daemonRuntimeRoot": str(tmp_path / "runtime")}), encoding="utf-8")
    assert load_config(path).daemon_runtime_root == tmp_path / "runtime"


def test_default_daemon_runtime_root_is_locked():
    assert ControllerConfig().daemon_runtime_root == Path(r"D:\BLATT2\ZB_AGENT_RUNTIME\controller-daemon")


@pytest.mark.parametrize("key", ["canonReferenceWorkflowPath", "canonPromptPath", "canonModelName", "canonDenoise", "executionProfile", "modelProfile"])
def test_rejects_historical_canon_model_profile_keys(tmp_path, key):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({key: "forbidden"}), encoding="utf-8")
    with pytest.raises(ConfigurationError) as exc:
        load_config(path)
    assert exc.value.code == "CONFIG_UNKNOWN_KEY"
