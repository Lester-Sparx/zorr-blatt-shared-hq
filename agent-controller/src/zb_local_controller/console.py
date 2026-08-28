from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
import time
from typing import Any, Callable

from .config import ConfigurationError, ControllerConfig, load_config
from .github_cli import GitHubCLI, GitHubCLIError, GitHubConfigurationError
from .owner_output import OutputView, find_latest_valid_output, open_output
from .owner_snapshot import OwnerSnapshot, parse_owner_view_comments


ISSUE_NUMBER = 39


def _timestamp(value: datetime | None) -> str:
    return "UNKNOWN" if value is None else value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _status(snapshot: OwnerSnapshot | None) -> str:
    if snapshot is None:
        return "UNKNOWN"
    return "STALE" if snapshot.is_stale else snapshot.overall_status


def _control(snapshot: OwnerSnapshot | None) -> str:
    action = "UNKNOWN"
    if snapshot is not None:
        action = "NOTHING NEEDED" if snapshot.sparx_action is None else snapshot.sparx_action
    return "\n".join([
        "SPARX CONTROL",
        f"STATUS: {_status(snapshot)}",
        f"SPARX ACTION: {action}",
    ])


def _agents(snapshot: OwnerSnapshot | None) -> str:
    lines = ["AGENTS"]
    if snapshot is None:
        return "\n".join(lines + ["UNKNOWN"])
    for agent in snapshot.agents.values():
        lines.extend([
            f"{agent.name} | {agent.status}",
            f"  DOING: {agent.doing}",
            f"  BLOCKER: {agent.blocker or 'NONE'}",
            f"  NEXT: {agent.next}",
        ])
    return "\n".join(lines)


def _gates(snapshot: OwnerSnapshot | None) -> str:
    lines = ["GATES"]
    if snapshot is None:
        return "\n".join(lines + ["UNKNOWN"])
    lines.extend(f"{gate.name} | {gate.status} | {gate.reason}" for gate in snapshot.gates.values())
    return "\n".join(lines)


def _output(output: OutputView | None) -> str:
    lines = ["LAST REAL OUTPUT"]
    if output is None:
        return "\n".join(lines + ["NO VALID OUTPUT FOUND"])
    lines.extend([
        f"TASK: {output.task_id}",
        f"AGENT: {output.agent}",
        f"STATE: {output.state}",
        f"CREATED: {_timestamp(output.created_at)}",
        f"SHA256: {output.sha256}",
        f"PATH: {output.path}",
        "PRODUCTION APPROVAL: NOT ESTABLISHED",
    ])
    return "\n".join(lines)


def _scout(snapshot: OwnerSnapshot | None) -> str:
    if snapshot is None:
        return "SCOUT\nLAST CHECK: UNKNOWN\nSUMMARY: UNKNOWN"
    return "\n".join([
        "SCOUT",
        f"LAST CHECK: {_timestamp(snapshot.scout_last_check)}",
        f"SUMMARY: {snapshot.scout_summary or 'NONE'}",
    ])


def _why(snapshot: OwnerSnapshot | None) -> str:
    return f"WHY WAITING\n{snapshot.why if snapshot is not None else 'UNKNOWN'}"


def _collect(
    config: ControllerConfig,
    github_factory: Callable[[str], Any],
    now_factory: Callable[[], datetime],
) -> tuple[OwnerSnapshot | None, OutputView | None, str | None]:
    snapshot = None
    detail = None
    try:
        comments = github_factory(config.repository).get_issue_comments(ISSUE_NUMBER)
        snapshot = parse_owner_view_comments(comments, now_factory())
        if snapshot is None:
            detail = "NO_VALID_OWNER_SNAPSHOT"
    except (GitHubConfigurationError, GitHubCLIError) as exc:
        detail = getattr(exc, "code", str(exc))
    output = find_latest_valid_output(config.result_root)
    return snapshot, output, detail


def render_once(
    command: str | None,
    config: ControllerConfig,
    *,
    github_factory: Callable[[str], Any],
    now_factory: Callable[[], datetime],
) -> OutputView | None:
    snapshot, output, detail = _collect(config, github_factory, now_factory)
    sections = {
        "why": _why(snapshot),
        "agents": _agents(snapshot),
        "gates": _gates(snapshot),
        "scout": _scout(snapshot),
        "output": _output(output),
    }
    if command in sections:
        print(sections[command])
    else:
        print("\n\n".join([
            _control(snapshot),
            _agents(snapshot),
            _gates(snapshot),
            _output(output),
            _scout(snapshot),
            _why(snapshot),
        ]))
    if detail:
        print(f"\nDETAILS: {detail}")
    return output


def main(
    argv: list[str] | None = None,
    *,
    github_factory: Callable[[str], Any] = GitHubCLI,
    now_factory: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    sleeper: Callable[[float], None] = time.sleep,
    opener: Callable[[Path], None] = open_output,
) -> int:
    parser = argparse.ArgumentParser(prog="zb")
    parser.add_argument("command", nargs="?", choices=("watch", "why", "agents", "gates", "scout", "output"))
    parser.add_argument("--config", type=Path, help="optional controller JSON config")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config) if args.config else ControllerConfig()
    except ConfigurationError as exc:
        print(f"CONFIGURATION_ERROR {exc.code}", file=sys.stderr)
        return 2

    if args.command == "watch":
        try:
            while True:
                render_once(None, config, github_factory=github_factory, now_factory=now_factory)
                sleeper(10.0)
        except KeyboardInterrupt:
            return 0

    output = render_once(args.command, config, github_factory=github_factory, now_factory=now_factory)
    if args.command == "output":
        if output is None:
            return 1
        try:
            opener(output.path)
        except RuntimeError as exc:
            print(str(exc))
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
