from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from typing import Callable, Any


class GitHubConfigurationError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class GitHubCLIError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitHubIssue:
    number: int
    title: str
    body: str
    comments: tuple[str, ...] = ()


def _default_runner(args: list[str], **kwargs: Any):
    return subprocess.run(args, **kwargs)


class GitHubCLI:
    def __init__(self, repository: str, runner: Callable[..., Any] | None = None):
        self.repository = repository
        self._runner = runner or _default_runner

    def ensure_authenticated(self) -> None:
        try:
            result = self._runner(["gh", "auth", "status"], capture_output=True, text=True, shell=False)
        except FileNotFoundError as exc:
            raise GitHubConfigurationError("GH_CLI_UNAVAILABLE") from exc
        if result.returncode != 0:
            raise GitHubConfigurationError("GH_NOT_AUTHENTICATED")

    def list_candidate_issues(self) -> list[GitHubIssue]:
        self.ensure_authenticated()
        args = [
            "gh", "issue", "list",
            "--repo", self.repository,
            "--state", "open",
            "--search", "ZB_AGENT_TASK_V0",
            "--json", "number,title,body,comments",
        ]
        result = self._runner(args, capture_output=True, text=True, shell=False)
        if result.returncode != 0:
            raise GitHubCLIError("GH_ISSUE_LIST_FAILED")
        try:
            raw = json.loads(result.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise GitHubCLIError("GH_OUTPUT_INVALID") from exc
        issues: list[GitHubIssue] = []
        for item in raw:
            body = str(item.get("body") or "")
            if "ZB_AGENT_TASK_V0" not in body:
                continue
            comments = tuple(str(c.get("body") or "") for c in (item.get("comments") or []))
            issues.append(GitHubIssue(int(item["number"]), str(item.get("title") or ""), body, comments))
        return issues

    def post_comment(self, issue_number: int, body: str) -> None:
        args = [
            "gh", "issue", "comment", str(int(issue_number)),
            "--repo", self.repository,
            "--body", body,
        ]
        result = self._runner(args, capture_output=True, text=True, shell=False)
        if result.returncode != 0:
            raise GitHubCLIError("GH_COMMENT_FAILED")
