import zb_local_controller.__main__ as cli_module
from zb_local_controller.github_cli import GitHubConfigurationError
from zb_local_controller.__main__ import main


class NoIssuesGitHub:
    def __init__(self, repository):
        self.repository = repository
        self.posts = []
    def list_candidate_issues(self):
        return []
    def post_comment(self, n, body):
        self.posts.append((n, body))


class BrokenGitHub(NoIssuesGitHub):
    def list_candidate_issues(self):
        raise GitHubConfigurationError("GH_NOT_AUTHENTICATED")


class NeverUsedBackend:
    def ensure_ready(self): raise AssertionError("backend must not run with no tasks")


def registry(_cfg):
    return {
        ("SALVADOR", "PRODUCTION_IMAGE_EDIT"): NeverUsedBackend(),
        ("SALVADOR", "CANON_REFERENCE_EDIT"): NeverUsedBackend(),
    }


def test_once_no_eligible_tasks_exits_zero_and_never_dispatches():
    exit_code = main(["--once"], github_factory=NoIssuesGitHub, backend_registry_factory=registry)
    assert exit_code == 0


def test_configuration_failure_exits_nonzero():
    exit_code = main(["--once"], github_factory=BrokenGitHub, backend_registry_factory=registry)
    assert exit_code != 0


def test_cli_passes_smoke_and_canon_backends_side_by_side(monkeypatch):
    smoke = object()
    canon = object()
    captured = {}

    class CaptureController:
        def __init__(self, github, inbox_root, result_root, backend_registry, **kwargs):
            captured["registry"] = backend_registry
        def run_once(self):
            return type("Summary", (), {"discovered": 0, "processed": 0, "submitted": 0, "skipped": 0})()

    monkeypatch.setattr(cli_module, "Controller", CaptureController)
    exit_code = main(
        ["--once"],
        github_factory=NoIssuesGitHub,
        backend_registry_factory=lambda cfg: {
            ("SALVADOR", "PRODUCTION_IMAGE_EDIT"): smoke,
            ("SALVADOR", "CANON_REFERENCE_EDIT"): canon,
        },
    )
    assert exit_code == 0
    assert captured["registry"] == {
        ("SALVADOR", "PRODUCTION_IMAGE_EDIT"): smoke,
        ("SALVADOR", "CANON_REFERENCE_EDIT"): canon,
    }


def test_default_registry_keeps_disposable_smoke_independent_of_empty_canon_model():
    from zb_local_controller.__main__ import _default_backend_registry
    from zb_local_controller.backends.canon_reference_edit import CanonReferenceEditBackend
    from zb_local_controller.backends.comfyui import ComfyUIBackend
    from zb_local_controller.config import ControllerConfig

    registry = _default_backend_registry(ControllerConfig(canon_model_name=""))
    smoke = registry[("SALVADOR", "PRODUCTION_IMAGE_EDIT")]
    canon = registry[("SALVADOR", "CANON_REFERENCE_EDIT")]
    assert type(smoke) is ComfyUIBackend
    assert smoke.workflow_path.name == "salvador-production-image-edit.json"
    assert isinstance(canon, CanonReferenceEditBackend)
    assert canon.model_name == ""

import json
import pytest
from zb_local_controller.config import load_config
from zb_local_controller.instance_lock import ControllerInstanceLock


def daemon_config(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"daemonRuntimeRoot": str(tmp_path / "runtime")}), encoding="utf-8")
    return path


def test_daemon_and_once_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        main(["--daemon", "--once"])


def test_daemon_requires_explicit_config():
    assert main(["--daemon"], github_factory=NoIssuesGitHub, backend_registry_factory=registry) == 2


def test_preflight_mode_does_not_discover_tasks(tmp_path):
    path = daemon_config(tmp_path)

    class PreflightGitHub(NoIssuesGitHub):
        def ensure_authenticated(self):
            pass
        def list_candidate_issues(self):
            raise AssertionError("must not list tasks")

    assert main(["--daemon-preflight", "--config", str(path)], github_factory=PreflightGitHub, backend_registry_factory=registry) == 0


def test_once_is_rejected_before_github_discovery_when_lock_owned(tmp_path):
    path = daemon_config(tmp_path)
    cfg = load_config(path)
    calls = {"list": 0}

    class CountingGitHub(NoIssuesGitHub):
        def list_candidate_issues(self):
            calls["list"] += 1
            return []

    with ControllerInstanceLock(cfg.daemon_runtime_root):
        code = main(["--once", "--config", str(path)], github_factory=CountingGitHub, backend_registry_factory=registry)
    assert code == 3
    assert calls["list"] == 0


def test_legacy_mode_is_rejected_before_run_forever_when_lock_owned(tmp_path, monkeypatch):
    path = daemon_config(tmp_path)
    cfg = load_config(path)

    class MustNotRunController:
        def __init__(self, *args, **kwargs):
            pass
        def run_forever(self):
            raise AssertionError("run_forever must not run while lock is owned")

    monkeypatch.setattr(cli_module, "Controller", MustNotRunController)
    with ControllerInstanceLock(cfg.daemon_runtime_root):
        code = main(["--config", str(path)], github_factory=NoIssuesGitHub, backend_registry_factory=registry)
    assert code == 3


def test_invalid_daemon_runtime_root_fails_closed_with_stable_code(tmp_path, capsys):
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("x", encoding="utf-8")
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"daemonRuntimeRoot": str(blocker / "runtime")}), encoding="utf-8")

    code = main(["--once", "--config", str(path)], github_factory=NoIssuesGitHub, backend_registry_factory=registry)

    assert code == 2
    assert "DAEMON_RUNTIME_UNWRITABLE" in capsys.readouterr().err
