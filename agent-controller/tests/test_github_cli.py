import json
import pytest
from zb_local_controller.github_cli import GitHubCLI, GitHubConfigurationError


class Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FakeRunner:
    def __init__(self, results=None):
        self.calls = []
        self.results = list(results or [])

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        return self.results.pop(0) if self.results else Result()


def test_post_comment_uses_fixed_argument_list():
    runner = FakeRunner([Result()])
    gh = GitHubCLI("Lester-Sparx/zorr-blatt-shared-hq", runner=runner)
    gh.post_comment(45, "event body")
    args, kwargs = runner.calls[0]
    assert args == ["gh", "issue", "comment", "45", "--repo", "Lester-Sparx/zorr-blatt-shared-hq", "--body", "event body"]
    assert kwargs.get("shell") is not True


def test_auth_failure_is_configuration_error():
    runner = FakeRunner([Result(returncode=1, stderr="not logged in")])
    gh = GitHubCLI("Lester-Sparx/zorr-blatt-shared-hq", runner=runner)
    with pytest.raises(GitHubConfigurationError) as exc:
        gh.ensure_authenticated()
    assert exc.value.code == "GH_NOT_AUTHENTICATED"


def test_candidate_discovery_auths_and_queries_only_marked_open_issues():
    payload = [{"number": 47, "title": "Task", "body": "ZB_AGENT_TASK_V0\n...", "comments": [{"body": "x"}]}]
    runner = FakeRunner([Result(), Result(stdout=json.dumps(payload))])
    gh = GitHubCLI("Lester-Sparx/zorr-blatt-shared-hq", runner=runner)
    issues = gh.list_candidate_issues()
    assert issues[0].number == 47
    assert issues[0].comments == ("x",)
    query_args = runner.calls[1][0]
    assert query_args[:4] == ["gh", "issue", "list", "--repo"]
    assert "--state" in query_args and query_args[query_args.index("--state") + 1] == "open"
    assert "--search" in query_args and query_args[query_args.index("--search") + 1] == "ZB_AGENT_TASK_V0"
    assert isinstance(query_args, list)


def test_default_runner_forwards_kwargs_once(monkeypatch):
    import zb_local_controller.github_cli as module
    seen = {}
    def fake_run(args, **kwargs):
        seen["args"] = args; seen["kwargs"] = kwargs
        return Result()
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module._default_runner(["gh", "auth", "status"], capture_output=True, text=True, shell=False)
    assert seen["kwargs"] == {"capture_output": True, "text": True, "shell": False}


def test_missing_gh_executable_is_configuration_error():
    def missing(*args, **kwargs):
        raise FileNotFoundError("gh")
    gh = GitHubCLI("Lester-Sparx/zorr-blatt-shared-hq", runner=missing)
    with pytest.raises(GitHubConfigurationError) as exc:
        gh.ensure_authenticated()
    assert exc.value.code == "GH_CLI_UNAVAILABLE"
