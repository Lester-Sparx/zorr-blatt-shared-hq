#!/usr/bin/env python3
"""Render a read-only Markdown dashboard from protected-main state."""

from pathlib import Path

from hq_adapter import load_json
from hq_validate import ROOT, validate_repository


def render(root: Path = ROOT) -> str:
    validate_repository(root)
    state = load_json(root / "hq/state/HQ_STATE.json")
    task = load_json(root / "hq/tasks/GITHUB_SHARED_HQ.json")
    return f"""# ZORR BLATT — GITHUB SHARED HQ

| Field | Value |
|---|---|
| Gate | `{state['currentGate']}` |
| HQ revision | `r{state['revision']:02d}` |
| Status | `{task['status']}` |
| Builder | `{task['builderGitHubLogin'] or 'PENDING'}` |
| Artifact | `{task['artifactSha256'] or 'PENDING'}` |
| Duncan QC | `{'RECORDED' if task['qcReview'] else 'PENDING'}` |
| Django architecture | `{'RECORDED' if task['architectureReview'] else 'PENDING'}` |
| Owner lock | `{'RECORDED' if task['lockRecord'] else 'PENDING'}` |
| G2 | `BLOCKED` |

This page is read-only. Protected `main` is the authoritative control/workflow state.
"""


if __name__ == "__main__":
    output = ROOT / "hq/dashboard/HQ_STATUS.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(), encoding="utf-8")
    print(output)
