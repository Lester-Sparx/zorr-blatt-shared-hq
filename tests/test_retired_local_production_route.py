from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_local_controller_execution_entrypoint_is_fail_closed():
    text = (ROOT / "agent-controller/src/zb_local_controller/__main__.py").read_text(encoding="utf-8")
    assert "RETIRED_PRODUCTION_ROUTE" in text
    assert "ComfyUIBackend" not in text
    assert "PRODUCTION_IMAGE_EDIT" not in text


def test_windows_controller_launcher_is_fail_closed():
    text = (ROOT / "agent-controller/scripts/run-controller.cmd").read_text(encoding="utf-8")
    assert "RETIRED_PRODUCTION_ROUTE" in text
    assert "python -m zb_local_controller" not in text


def test_active_example_config_does_not_bind_comfyui():
    text = (ROOT / "agent-controller/config.example.json").read_text(encoding="utf-8")
    assert "comfyui" not in text.lower()
    assert "salvador-production-image-edit" not in text.lower()


def test_read_only_owner_console_entrypoint_remains_available():
    text = (ROOT / "agent-controller/pyproject.toml").read_text(encoding="utf-8")
    assert 'zb = "zb_local_controller.console:main"' in text
