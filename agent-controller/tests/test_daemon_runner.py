import logging
from pathlib import Path

import pytest

from zb_local_controller.config import ControllerConfig
from zb_local_controller.controller import RunSummary
from zb_local_controller.github_cli import GitHubCLIError
from zb_local_controller.daemon_runner import DaemonPreflightError, DaemonRunner, run_daemon_preflight


class AuthOnlyGitHub:
    def __init__(self):
        self.auth_calls = 0
        self.list_calls = 0

    def ensure_authenticated(self):
        self.auth_calls += 1

    def list_candidate_issues(self):
        self.list_calls += 1
        raise AssertionError("preflight must not discover tasks")


def test_preflight_authenticates_without_task_discovery(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    github = AuthOnlyGitHub()
    run_daemon_preflight(ControllerConfig(daemon_runtime_root=tmp_path / "runtime"), config_path, github)
    assert github.auth_calls == 1
    assert github.list_calls == 0


def test_preflight_probe_write_failure_is_runtime_unwritable(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    runtime = tmp_path / "runtime"
    original_open = Path.open

    def fail_probe(self, *args, **kwargs):
        if self.parent == runtime and self.name.startswith(".daemon-preflight-"):
            raise OSError("blocked")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_probe)
    with pytest.raises(DaemonPreflightError) as exc:
        run_daemon_preflight(ControllerConfig(daemon_runtime_root=runtime), config_path, AuthOnlyGitHub())
    assert exc.value.code == "DAEMON_RUNTIME_UNWRITABLE"


class FakeHealth:
    def __init__(self):
        self.writes = []

    def write(self, state, last_cycle=None, last_error_code=None):
        self.writes.append((state, last_cycle, last_error_code))


def logger():
    result = logging.Logger("daemon-test")
    result.addHandler(logging.NullHandler())
    return result


class SequenceController:
    def __init__(self, values):
        self.values = iter(values)

    def run_once(self):
        value = next(self.values)
        if isinstance(value, BaseException):
            raise value
        return value


def test_healthy_cycle_then_graceful_stop():
    health = FakeHealth()
    sleeps = []
    controller = SequenceController([RunSummary(4, 1, 0, 3), KeyboardInterrupt()])
    code = DaemonRunner(controller, health, logger(), 15.0, sleeps.append).run()
    assert code == 0
    assert health.writes[0][0] == "HEALTHY"
    assert health.writes[-1][0] == "STOPPING"
    assert sleeps == [15.0]


def test_keyboard_interrupt_during_poll_sleep_writes_stopping_and_returns_zero():
    health = FakeHealth()

    def interrupted_sleep(_seconds):
        raise KeyboardInterrupt()

    controller = SequenceController([RunSummary(1, 0, 0, 1)])
    code = DaemonRunner(controller, health, logger(), 15.0, interrupted_sleep).run()

    assert code == 0
    assert health.writes[0][0] == "HEALTHY"
    assert health.writes[-1][0] == "STOPPING"


def test_transient_github_error_degrades_and_retries():
    health = FakeHealth()
    sleeps = []
    controller = SequenceController([GitHubCLIError("GH_ISSUE_LIST_FAILED"), KeyboardInterrupt()])
    assert DaemonRunner(controller, health, logger(), 15.0, sleeps.append).run() == 0
    assert ("DEGRADED", None, "GH_ISSUE_LIST_FAILED") in health.writes
    assert sleeps == [15.0]


def test_unexpected_exception_is_fatal_and_nonzero():
    health = FakeHealth()
    controller = SequenceController([RuntimeError("boom")])
    assert DaemonRunner(controller, health, logger(), 15.0, lambda _: None).run() != 0
    assert health.writes[-1][0] == "FATAL"
