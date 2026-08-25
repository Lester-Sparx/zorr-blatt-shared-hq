from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

ROLES = {"OWNER": "owner", "LESTER": "lester", "DUNCAN": "duncan", "DJANGO": "django"}
COMMIT = "a" * 40
SHA = "B" * 64


def base_state():
    # Unit tests must never inherit the mutable live repository state.  A real
    # artifact/review transition intentionally advances that state, while the
    # tests below exercise deterministic revision-zero fixtures.
    state = {
        "schemaVersion": 1,
        "project": "ZORR BLATT",
        "revision": 0,
        "mainCommit": "0" * 40,
        "currentTask": "GITHUB_SHARED_HQ",
        "currentGate": "GITHUB_SHARED_HQ",
        "blockedGates": ["G2", "VOICE_TO_SHOT"],
        "lastTransition": None,
    }
    task = {
        "taskId": "GITHUB_SHARED_HQ",
        "revision": 0,
        "parentRevision": None,
        "expectedMainCommit": "0" * 40,
        "candidateCommit": None,
        "status": "IMPLEMENTATION_PENDING",
        "builderGitHubLogin": None,
        "artifactSha256": None,
        "artifactReleaseTag": None,
        "qcReview": None,
        "architectureReview": None,
        "lockRecord": None,
    }
    return copy.deepcopy(state), copy.deepcopy(task)


def reset_control_fixture(root: Path):
    """Replace copied live control data with a deterministic revision-zero fixture."""
    state, task = base_state()
    (root / "hq/state/HQ_STATE.json").write_text(
        json.dumps(state, indent=2) + "\n", encoding="utf-8"
    )
    (root / "hq/tasks/GITHUB_SHARED_HQ.json").write_text(
        json.dumps(task, indent=2) + "\n", encoding="utf-8"
    )
    for namespace in ("artifacts", "reviews", "locks"):
        for record in (root / "hq" / namespace).rglob("*.json"):
            record.unlink()


def registered_task():
    state, task = base_state()
    state["revision"] = 1
    task.update({
        "revision": 1, "parentRevision": 0, "candidateCommit": COMMIT,
        "status": "ARTIFACT_REGISTERED", "builderGitHubLogin": "lester",
        "artifactSha256": SHA, "artifactReleaseTag": "shared-hq-r01",
    })
    return state, task
