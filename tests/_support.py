from __future__ import annotations

import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from hq_adapter import load_json  # noqa: E402


ROLES = {"OWNER": "owner", "LESTER": "lester", "DUNCAN": "duncan", "DJANGO": "django"}
COMMIT = "a" * 40
SHA = "B" * 64


def base_state():
    state = load_json(ROOT / "hq/state/HQ_STATE.json")
    task = load_json(ROOT / "hq/tasks/GITHUB_SHARED_HQ.json")
    return copy.deepcopy(state), copy.deepcopy(task)


def registered_task():
    state, task = base_state()
    state["revision"] = 1
    task.update({
        "revision": 1, "parentRevision": 0, "candidateCommit": COMMIT,
        "status": "ARTIFACT_REGISTERED", "builderGitHubLogin": "lester",
        "artifactSha256": SHA, "artifactReleaseTag": "shared-hq-r01",
    })
    return state, task
