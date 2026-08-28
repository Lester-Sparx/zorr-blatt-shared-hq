import json
import pytest
import zb_local_controller.__main__ as cli_module
from zb_local_controller.__main__ import main
from zb_local_controller.controller import RunSummary
from zb_local_controller.instance_lock import ControllerInstanceLock
from zb_local_controller.github_cli import GitHubConfigurationError


class NoIssuesGitHub:
    def __init__(self, repository): self.repository=repository; self.auth_calls=0; self.list_calls=0
    def ensure_authenticated(self): self.auth_calls += 1
    def list_candidate_issues(self): self.list_calls += 1; return []
    def post_comment(self, n, body): pass


class NeverUsedBackend:
    def ensure_ready(self): raise AssertionError("backend must not run with no tasks")


class FakeController:
    def __init__(self, *args, **kwargs): self.run_forever_calls=0
    def run_once(self): return RunSummary(0,0,0,0)
    def run_forever(self): self.run_forever_calls += 1


def daemon_config(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"daemonRuntimeRoot": str(tmp_path / "runtime")}), encoding="utf-8")
    return path


def test_existing_once_default_behavior_is_unchanged(monkeypatch):
    monkeypatch.setattr(cli_module, "Controller", FakeController)
    assert main(["--once"], github_factory=NoIssuesGitHub, backend_factory=lambda cfg: NeverUsedBackend()) == 0


def test_daemon_and_once_are_mutually_exclusive():
    with pytest.raises(SystemExit): main(["--daemon", "--once"])


def test_daemon_requires_explicit_config(monkeypatch):
    monkeypatch.setattr(cli_module, "Controller", FakeController)
    assert main(["--daemon"], github_factory=NoIssuesGitHub, backend_factory=lambda cfg: NeverUsedBackend()) == 2


def test_preflight_mode_authenticates_without_task_discovery(tmp_path):
    path = daemon_config(tmp_path)
    holder = {}
    def factory(repo): holder["gh"] = NoIssuesGitHub(repo); return holder["gh"]
    assert main(["--daemon-preflight", "--config", str(path)], github_factory=factory, backend_factory=lambda cfg: NeverUsedBackend()) == 0
    assert holder["gh"].auth_calls == 1
    assert holder["gh"].list_calls == 0


def test_once_fails_closed_before_controller_when_lock_owned(tmp_path, monkeypatch):
    path = daemon_config(tmp_path)
    def must_not_construct(*args, **kwargs): raise AssertionError("controller must not construct")
    monkeypatch.setattr(cli_module, "Controller", must_not_construct)
    from zb_local_controller.config import load_config
    with ControllerInstanceLock(load_config(path).daemon_runtime_root):
        assert main(["--once", "--config", str(path)], github_factory=NoIssuesGitHub, backend_factory=lambda cfg: NeverUsedBackend()) == 3


def test_daemon_fails_closed_before_controller_when_lock_owned(tmp_path, monkeypatch):
    path = daemon_config(tmp_path)
    def must_not_construct(*args, **kwargs): raise AssertionError("controller must not construct")
    monkeypatch.setattr(cli_module, "Controller", must_not_construct)
    from zb_local_controller.config import load_config
    with ControllerInstanceLock(load_config(path).daemon_runtime_root):
        assert main(["--daemon", "--config", str(path)], github_factory=NoIssuesGitHub, backend_factory=lambda cfg: NeverUsedBackend()) == 3


class BrokenGitHub(NoIssuesGitHub):
    def list_candidate_issues(self):
        raise GitHubConfigurationError("GH_NOT_AUTHENTICATED")


def test_baseline_once_no_eligible_tasks_exits_zero_and_never_dispatches():
    exit_code = main(["--once"], github_factory=NoIssuesGitHub, backend_factory=lambda cfg: NeverUsedBackend())
    assert exit_code == 0


def test_baseline_configuration_failure_exits_nonzero():
    exit_code = main(["--once"], github_factory=BrokenGitHub, backend_factory=lambda cfg: NeverUsedBackend())
    assert exit_code != 0
