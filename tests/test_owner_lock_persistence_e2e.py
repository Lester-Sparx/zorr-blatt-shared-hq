import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from _support import ROOT
from hq_adapter import create_owner_lock, record_sha256, submit_review
from hq_transition_validate import render_dashboard, validate_transition
from hq_validate import validate_repository


ARTIFACT_SHA = "B" * 64
ROLES = {"OWNER": "Sparx-Owner-ZB", "LESTER": "Lester-Sparx", "DUNCAN": "Duncan-Sparx-ZB", "DJANGO": "Django-Sparx-ZB"}


class OwnerLockPersistenceE2ETest(unittest.TestCase):
    def write(self, root: Path, relative: str, value: dict):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def read(self, root: Path, relative: str):
        return json.loads((root / relative).read_text(encoding="utf-8"))

    def dashboard(self, root: Path, state: dict, task: dict):
        (root / "hq/dashboard/HQ_STATUS.md").write_bytes(render_dashboard(state, task))

    def next_copy(self, source: Path, destination: Path):
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    def test_qc_arch_owner_lock_record_passes_persistence_validator(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            base = work / "base"
            head = work / "head"
            self.next_copy(ROOT, base)
            self.next_copy(base, head)

            # LESTER artifact transition.
            state = self.read(head, "hq/state/HQ_STATE.json")
            task = self.read(head, "hq/tasks/GITHUB_SHARED_HQ.json")
            artifact_commit = "1" * 40
            artifact = {
                "taskId": task["taskId"], "revision": 1, "sha256": ARTIFACT_SHA,
                "releaseTag": "shared-hq-r01", "sourceCommit": artifact_commit,
                "builderGitHubLogin": "Lester-Sparx", "immutable": True,
            }
            task.update({
                "revision": 1, "parentRevision": 0, "expectedMainCommit": "1" * 40,
                "candidateCommit": artifact_commit, "status": "ARTIFACT_REGISTERED",
                "builderGitHubLogin": "Lester-Sparx", "artifactSha256": ARTIFACT_SHA,
                "artifactReleaseTag": "shared-hq-r01",
            })
            state.update({
                "revision": 1, "mainCommit": "1" * 40,
                "lastTransition": {
                    "kind": "ARTIFACT_REGISTERED", "actorGitHubLogin": "Lester-Sparx",
                    "taskRevision": 1, "candidateCommit": artifact_commit,
                    "artifactSha256": ARTIFACT_SHA, "previousRevision": 0,
                },
            })
            self.write(head, f"hq/artifacts/{ARTIFACT_SHA}.json", artifact)
            self.write(head, "hq/state/HQ_STATE.json", state)
            self.write(head, "hq/tasks/GITHUB_SHARED_HQ.json", task)
            self.dashboard(head, state, task)
            self.assertEqual(validate_transition(base, head, actor="Lester-Sparx", base_sha="1" * 40, head_sha=artifact_commit), "ARTIFACT_REGISTERED")

            # DUNCAN QC PASS transition.
            self.next_copy(head, base)
            self.next_copy(base, head)
            state = self.read(head, "hq/state/HQ_STATE.json")
            task = self.read(head, "hq/tasks/GITHUB_SHARED_HQ.json")
            task, qc = submit_review(task, actor="Duncan-Sparx-ZB", kind="QC", result="PASS", report_sha256="C" * 64, roles=ROLES)
            task["expectedMainCommit"] = "3" * 40
            state.update({
                "mainCommit": "3" * 40,
                "lastTransition": {
                    "kind": "QC_RECORDED", "actorGitHubLogin": "Duncan-Sparx-ZB",
                    "taskRevision": 1, "candidateCommit": artifact_commit,
                    "artifactSha256": ARTIFACT_SHA, "previousRevision": 1,
                },
            })
            self.write(head, "hq/reviews/qc/GITHUB_SHARED_HQ/r01/Duncan-Sparx-ZB.json", qc)
            self.write(head, "hq/state/HQ_STATE.json", state)
            self.write(head, "hq/tasks/GITHUB_SHARED_HQ.json", task)
            self.dashboard(head, state, task)
            self.assertEqual(validate_transition(base, head, actor="Duncan-Sparx-ZB", base_sha="3" * 40, head_sha="4" * 40), "QC_RECORDED")

            # DJANGO architecture acceptance transition.
            self.next_copy(head, base)
            self.next_copy(base, head)
            state = self.read(head, "hq/state/HQ_STATE.json")
            task = self.read(head, "hq/tasks/GITHUB_SHARED_HQ.json")
            task, architecture = submit_review(task, actor="Django-Sparx-ZB", kind="ARCHITECTURE", result="ACCEPTED", report_sha256="D" * 64, roles=ROLES)
            task["expectedMainCommit"] = "5" * 40
            state.update({
                "mainCommit": "5" * 40,
                "lastTransition": {
                    "kind": "ARCHITECTURE_RECORDED", "actorGitHubLogin": "Django-Sparx-ZB",
                    "taskRevision": 1, "candidateCommit": artifact_commit,
                    "artifactSha256": ARTIFACT_SHA, "previousRevision": 1,
                },
            })
            self.write(head, "hq/reviews/architecture/GITHUB_SHARED_HQ/r01/Django-Sparx-ZB.json", architecture)
            self.write(head, "hq/state/HQ_STATE.json", state)
            self.write(head, "hq/tasks/GITHUB_SHARED_HQ.json", task)
            self.dashboard(head, state, task)
            self.assertEqual(validate_transition(base, head, actor="Django-Sparx-ZB", base_sha="5" * 40, head_sha="6" * 40), "ARCHITECTURE_RECORDED")

            # Authenticated OWNER lock transition and repository validation.
            self.next_copy(head, base)
            self.next_copy(base, head)
            state = self.read(head, "hq/state/HQ_STATE.json")
            task = self.read(head, "hq/tasks/GITHUB_SHARED_HQ.json")
            lock_base_state = copy.deepcopy(state)
            lock_base_state["mainCommit"] = "7" * 40
            task, lock = create_owner_lock(
                lock_base_state, task, qc, architecture, actor="Sparx-Owner-ZB",
                timestamp="2026-08-25T00:00:00Z", roles=ROLES,
            )
            task["expectedMainCommit"] = "7" * 40
            state.update({
                "mainCommit": "7" * 40,
                "lastTransition": {
                    "kind": "OWNER_LOCKED", "actorGitHubLogin": "Sparx-Owner-ZB",
                    "taskRevision": 1, "candidateCommit": artifact_commit,
                    "artifactSha256": ARTIFACT_SHA, "previousRevision": 1,
                },
            })
            self.write(head, "hq/locks/GITHUB_SHARED_HQ/r01.json", lock)
            self.write(head, "hq/state/HQ_STATE.json", state)
            self.write(head, "hq/tasks/GITHUB_SHARED_HQ.json", task)
            self.dashboard(head, state, task)
            self.assertEqual(task["lockRecord"], record_sha256(lock))
            self.assertEqual(validate_transition(base, head, actor="Sparx-Owner-ZB", base_sha="7" * 40, head_sha="8" * 40), "OWNER_LOCKED")
            validate_repository(head)


if __name__ == "__main__": unittest.main()
