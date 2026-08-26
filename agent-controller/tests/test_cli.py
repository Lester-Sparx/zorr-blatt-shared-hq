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


def test_once_no_eligible_tasks_exits_zero_and_never_dispatches():
    exit_code = main(["--once"], github_factory=NoIssuesGitHub, backend_factory=lambda cfg: NeverUsedBackend())
    assert exit_code == 0


def test_configuration_failure_exits_nonzero():
    exit_code = main(["--once"], github_factory=BrokenGitHub, backend_factory=lambda cfg: NeverUsedBackend())
    assert exit_code != 0
