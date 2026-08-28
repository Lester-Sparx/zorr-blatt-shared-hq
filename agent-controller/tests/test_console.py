from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tomllib

import pytest

from zb_local_controller.console import main
from zb_local_controller.github_cli import GitHubCLIError, GitHubConfigurationError


SNAPSHOT = """ZB_OWNER_VIEW_V0
UPDATED_AT = 2026-08-27T01:00:00Z
OVERALL_STATUS = WAITING
SPARX_ACTION = NONE
WHY = Duncan verdict required before Task 9.
SCOUT_LAST_CHECK = 2026-08-27T00:50:00Z
SCOUT_SUMMARY = NONE
AGENT = JINGO | WORKING | coordinates | NONE | NONE | wait for Duncan
AGENT = LESTER | WAITING | repair ready | repair complete | Duncan QC | wait
AGENT = DUNCAN | WORKING | independent QC | NONE | NONE | PASS or CHANGES_REQUIRED
AGENT = SALVADOR | WAITING | production visual | NONE | gate | model smoke
AGENT = LYNCH | WORKING | research | NONE | NONE | continue
AGENT = MAO | WORKING | performance research | NONE | NONE | report
AGENT = CHARLIE | WAITING | model board | NONE | NONE | start
AGENT = MEMORO | WAITING | truth audit | NONE | NONE | start
GATE = DUNCAN_QC | WAITING | exact candidate under review
GATE = REAL_MODEL_SMOKE | WAITING | locked until Duncan PASS
"""
PNG = b"\x89PNG\r\n\x1a\nconsole"
NOW = lambda: datetime(2026, 8, 27, 1, 30, tzinfo=timezone.utc)


class FakeGitHub:
    def __init__(self, comments=(SNAPSHOT,), error=None):
        self.comments = comments
        self.error = error
        self.reads = 0

    def get_issue_comments(self, issue_number):
        assert issue_number == 39
        self.reads += 1
        if self.error:
            raise self.error
        return self.comments


def setup_config(tmp_path, *, with_output=True):
    root = tmp_path / "results"
    root.mkdir()
    if with_output:
        task = root / "TASK_7"
        task.mkdir()
        (task / "result.png").write_bytes(PNG)
        (task / "result.json").write_text(json.dumps({
            "taskId": "TASK_7",
            "agent": "SALVADOR",
            "state": "RESULT_READY",
            "executionId": "exec-7",
            "sha256": hashlib.sha256(PNG).hexdigest(),
            "createdAt": "2026-08-27T01:10:00Z",
        }), encoding="utf-8")
    config = tmp_path / "config.json"
    config.write_text(json.dumps({
        "repository": "Lester-Sparx/zorr-blatt-shared-hq",
        "resultRoot": str(root),
    }), encoding="utf-8")
    return config, root


def run_console(tmp_path, capsys, command=None, *, github=None, opener=lambda path: None, sleeper=lambda seconds: None, with_output=True):
    config, root = setup_config(tmp_path, with_output=with_output)
    github = github or FakeGitHub()
    argv = ([command] if command else []) + ["--config", str(config)]
    result = main(
        argv,
        github_factory=lambda repository: github,
        now_factory=NOW,
        sleeper=sleeper,
        opener=opener,
    )
    return result, capsys.readouterr(), github, root


def test_default_renders_complete_human_view_in_required_order(tmp_path, capsys):
    result, captured, _, _ = run_console(tmp_path, capsys)
    assert result == 0
    headings = ["SPARX CONTROL", "AGENTS", "GATES", "LAST REAL OUTPUT", "SCOUT", "WHY WAITING"]
    assert [captured.out.index(item) for item in headings] == sorted(captured.out.index(item) for item in headings)
    assert "SPARX ACTION: NOTHING NEEDED" in captured.out
    assert "LESTER" in captured.out
    assert "DUNCAN_QC" in captured.out
    assert "TASK_7" in captured.out
    assert "result.png" in captured.out
    assert "PRODUCTION APPROVAL: NOT ESTABLISHED" in captured.out


@pytest.mark.parametrize(
    ("command", "present", "absent"),
    [
        ("why", "Duncan verdict required", "AGENTS"),
        ("agents", "LESTER", "GATES"),
        ("gates", "DUNCAN_QC", "AGENTS"),
        ("scout", "SCOUT", "AGENTS"),
    ],
)
def test_read_only_subcommands_render_only_requested_section(tmp_path, capsys, command, present, absent):
    result, captured, _, _ = run_console(tmp_path, capsys, command)
    assert result == 0
    assert present in captured.out
    assert absent not in captured.out


def test_output_opens_exactly_one_validated_path(tmp_path, capsys):
    opened = []
    result, captured, _, root = run_console(tmp_path, capsys, "output", opener=opened.append)
    expected = root / "TASK_7" / "result.png"
    assert result == 0
    assert opened == [expected]
    assert str(expected) in captured.out
    assert hashlib.sha256(PNG).hexdigest() in captured.out


def test_output_without_valid_result_does_not_open(tmp_path, capsys):
    opened = []
    result, captured, _, _ = run_console(tmp_path, capsys, "output", opener=opened.append, with_output=False)
    assert result != 0
    assert "NO VALID OUTPUT FOUND" in captured.out
    assert opened == []


@pytest.mark.parametrize(
    "error",
    [
        GitHubConfigurationError("GH_CLI_UNAVAILABLE"),
        GitHubConfigurationError("GH_NOT_AUTHENTICATED"),
        GitHubCLIError("GH_READ_FAILED"),
    ],
)
def test_github_failure_keeps_local_output_and_marks_remote_unknown(tmp_path, capsys, error):
    result, captured, _, _ = run_console(tmp_path, capsys, github=FakeGitHub(error=error))
    assert result == 0
    assert "STATUS: UNKNOWN" in captured.out
    assert "TASK_7" in captured.out
    assert str(error) in captured.out
    assert "DONE" not in captured.out


def test_stale_snapshot_is_visibly_stale(tmp_path, capsys):
    stale_now = lambda: datetime(2026, 8, 27, 3, 0, 1, tzinfo=timezone.utc)
    config, _ = setup_config(tmp_path)
    result = main(
        ["--config", str(config)],
        github_factory=lambda repository: FakeGitHub(),
        now_factory=stale_now,
    )
    captured = capsys.readouterr()
    assert result == 0
    assert "STATUS: STALE" in captured.out


def test_watch_refreshes_read_only_until_keyboard_interrupt(tmp_path, capsys):
    calls = []
    def stop(seconds):
        calls.append(seconds)
        raise KeyboardInterrupt
    config, root = setup_config(tmp_path)
    github = FakeGitHub()
    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*") if path.is_file()
    }
    result = main(
        ["watch", "--config", str(config)],
        github_factory=lambda repository: github,
        now_factory=NOW,
        sleeper=stop,
    )
    capsys.readouterr()
    after = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*") if path.is_file()
    }
    assert result == 0
    assert github.reads == 1
    assert calls == [10.0]
    assert before == after
    assert not hasattr(github, "post_comment")


def test_project_exposes_zb_console_entry_point():
    project = Path(__file__).resolve().parents[1]
    data = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["scripts"]["zb"] == "zb_local_controller.console:main"
