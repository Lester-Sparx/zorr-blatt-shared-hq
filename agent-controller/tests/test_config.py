import json
from zb_local_controller.config import load_config


def test_loads_deployment_owned_execution_deadline(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"maxExecutionSeconds": 42}), encoding="utf-8")
    config = load_config(path)
    assert config.max_execution_seconds == 42.0
