import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from _support import COMMIT, ROOT, SHA
from hq_adapter import HQError, record_sha256, submit_review
from hq_transition_validate import render_dashboard, validate_transition


BASE_SHA = "b" * 40
HEAD_SHA = "c" * 40


class PersistenceBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name) / "base"
        self.head = Path(self.temp.name) / "head"
        shutil.copytree(ROOT, self.base, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(ROOT, self.head, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    def tearDown(self):
        self.temp.cleanup()

    def read(self, root, relative):
        return json.loads((root / relative).read_text(encoding="utf-8"))

    def write(self, root, relative, value):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def dashboard(self, root, state, task):
        (root / "hq/dashboard/HQ_STATUS.md").write_bytes(render_dashboard(state, task))

    def make_registered(self, root):
        state = self.read(root, "hq/state/HQ_STATE.json")
        task = self.read(root, "hq/tasks/GITHUB_SHARED_HQ.json")
        state.update({
            "revision": 1, "mainCommit": BASE_SHA,
            "lastTransition": {
                "kind": "ARTIFACT_REGISTERED", "actorGitHubLogin": "Lester-Sparx",
                "taskRevision": 1, "candidateCommit": COMMIT,
                "artifactSha256": SHA, "previousRevision": 0,
            },
        })
        task.update({
            "revision": 1, "parentRevision": 0, "expectedMainCommit": BASE_SHA,
            "candidateCommit": COMMIT, "status": "ARTIFACT_REGISTERED",
            "builderGitHubLogin": "Lester-Sparx", "artifactSha256": SHA,
            "artifactReleaseTag": "shared-hq-r01",
        })
        artifact = {
            "taskId": "GITHUB_SHARED_HQ", "revision": 1, "sha256": SHA,
            "releaseTag": "shared-hq-r01", "sourceCommit": COMMIT,
            "builderGitHubLogin": "Lester-Sparx", "immutable": True,
        }
        self.write(root, "hq/state/HQ_STATE.json", state)
        self.write(root, "hq/tasks/GITHUB_SHARED_HQ.json", task)
        self.write(root, f"hq/artifacts/{SHA}.json", artifact)
        self.dashboard(root, state, task)
        return state, task

    def test_valid_authenticated_lester_artifact_transition(self):
        state = self.read(self.head, "hq/state/HQ_STATE.json")
        task = self.read(self.head, "hq/tasks/GITHUB_SHARED_HQ.json")
        artifact = {
            "taskId": "GITHUB_SHARED_HQ", "revision": 1, "sha256": SHA,
            "releaseTag": "shared-hq-r01", "sourceCommit": HEAD_SHA,
            "builderGitHubLogin": "Lester-Sparx", "immutable": True,
        }
        state.update({
            "revision": 1, "mainCommit": BASE_SHA,
            "lastTransition": {
                "kind": "ARTIFACT_REGISTERED", "actorGitHubLogin": "Lester-Sparx",
                "taskRevision": 1, "candidateCommit": HEAD_SHA,
                "artifactSha256": SHA, "previousRevision": 0,
            },
        })
        task.update({
            "revision": 1, "parentRevision": 0, "expectedMainCommit": BASE_SHA,
            "candidateCommit": HEAD_SHA, "status": "ARTIFACT_REGISTERED",
            "builderGitHubLogin": "Lester-Sparx", "artifactSha256": SHA,
            "artifactReleaseTag": "shared-hq-r01",
        })
        self.write(self.head, f"hq/artifacts/{SHA}.json", artifact)
        self.write(self.head, "hq/state/HQ_STATE.json", state)
        self.write(self.head, "hq/tasks/GITHUB_SHARED_HQ.json", task)
        self.dashboard(self.head, state, task)
        self.assertEqual(validate_transition(
            self.base, self.head, actor="Lester-Sparx", base_sha=BASE_SHA, head_sha=HEAD_SHA
        ), "ARTIFACT_REGISTERED")

    def test_direct_qc_architecture_and_lock_claims_are_rejected(self):
        for mutation in ("QC", "ARCH", "LOCK"):
            with self.subTest(mutation=mutation):
                shutil.rmtree(self.head)
                shutil.copytree(self.base, self.head)
                state, task = self.make_registered(self.head)
                if mutation == "QC":
                    task.update({"status": "QC_PASS", "qcReview": "C" * 64})
                elif mutation == "ARCH":
                    task["architectureReview"] = "D" * 64
                else:
                    task.update({"status": "LOCKED", "lockRecord": "E" * 64})
                self.write(self.head, "hq/tasks/GITHUB_SHARED_HQ.json", task)
                self.dashboard(self.head, state, task)
                with self.assertRaises(HQError):
                    validate_transition(self.base, self.head, actor="Lester-Sparx", base_sha=BASE_SHA, head_sha=HEAD_SHA)

    def test_wrong_role_and_stale_review_evidence_are_rejected(self):
        self.make_registered(self.base)
        shutil.rmtree(self.head)
        shutil.copytree(self.base, self.head)
        state = self.read(self.head, "hq/state/HQ_STATE.json")
        task = self.read(self.head, "hq/tasks/GITHUB_SHARED_HQ.json")
        review = {
            "kind": "ARCHITECTURE", "taskId": task["taskId"], "revision": task["revision"],
            "candidateCommit": task["candidateCommit"], "artifactSha256": task["artifactSha256"],
            "reviewerGitHubLogin": "Duncan-Sparx-ZB", "result": "ACCEPTED", "reportSha256": "D" * 64,
        }
        task["architectureReview"] = record_sha256(review)
        task["expectedMainCommit"] = BASE_SHA
        state["lastTransition"] = {
            "kind": "ARCHITECTURE_RECORDED", "actorGitHubLogin": "Duncan-Sparx-ZB",
            "taskRevision": 1, "candidateCommit": COMMIT, "artifactSha256": SHA,
            "previousRevision": 1,
        }
        self.write(self.head, "hq/reviews/architecture/GITHUB_SHARED_HQ/r01/Duncan-Sparx-ZB.json", review)
        self.write(self.head, "hq/tasks/GITHUB_SHARED_HQ.json", task)
        self.write(self.head, "hq/state/HQ_STATE.json", state)
        self.dashboard(self.head, state, task)
        with self.assertRaises(HQError):
            validate_transition(self.base, self.head, actor="Duncan-Sparx-ZB", base_sha=BASE_SHA, head_sha=HEAD_SHA)

        review["reviewerGitHubLogin"] = "Django-Sparx-ZB"
        review["candidateCommit"] = "d" * 40
        with self.assertRaises(HQError):
            validate_transition(self.base, self.head, actor="Django-Sparx-ZB", base_sha=BASE_SHA, head_sha=HEAD_SHA)

    def test_owner_cannot_act_as_lester_and_dashboard_has_no_authority(self):
        state = self.read(self.head, "hq/state/HQ_STATE.json")
        task = self.read(self.head, "hq/tasks/GITHUB_SHARED_HQ.json")
        artifact = {
            "taskId": "GITHUB_SHARED_HQ", "revision": 1, "sha256": SHA,
            "releaseTag": "shared-hq-r01", "sourceCommit": HEAD_SHA,
            "builderGitHubLogin": "Sparx-Owner-ZB", "immutable": True,
        }
        state.update({
            "revision": 1, "mainCommit": BASE_SHA,
            "lastTransition": {
                "kind": "ARTIFACT_REGISTERED", "actorGitHubLogin": "Sparx-Owner-ZB",
                "taskRevision": 1, "candidateCommit": HEAD_SHA,
                "artifactSha256": SHA, "previousRevision": 0,
            },
        })
        task.update({
            "revision": 1, "parentRevision": 0, "expectedMainCommit": BASE_SHA,
            "candidateCommit": HEAD_SHA, "status": "ARTIFACT_REGISTERED",
            "builderGitHubLogin": "Sparx-Owner-ZB", "artifactSha256": SHA,
            "artifactReleaseTag": "shared-hq-r01",
        })
        self.write(self.head, f"hq/artifacts/{SHA}.json", artifact)
        self.write(self.head, "hq/state/HQ_STATE.json", state)
        self.write(self.head, "hq/tasks/GITHUB_SHARED_HQ.json", task)
        self.dashboard(self.head, state, task)
        with self.assertRaisesRegex(HQError, "LESTER"):
            validate_transition(self.base, self.head, actor="Sparx-Owner-ZB", base_sha=BASE_SHA, head_sha=HEAD_SHA)

        shutil.rmtree(self.head)
        shutil.copytree(self.base, self.head)
        self.assertEqual(validate_transition(
            self.base, self.head, actor="Lester-Sparx", base_sha=BASE_SHA, head_sha=HEAD_SHA
        ), "DASHBOARD_ONLY")

    def test_old_review_copied_to_new_commit_or_artifact_is_rejected(self):
        self.make_registered(self.base)
        for stale_field, stale_value in (("candidateCommit", "d" * 40), ("artifactSha256", "E" * 64)):
            with self.subTest(stale_field=stale_field):
                if self.head.exists():
                    shutil.rmtree(self.head)
                shutil.copytree(self.base, self.head)
                state = self.read(self.head, "hq/state/HQ_STATE.json")
                task = self.read(self.head, "hq/tasks/GITHUB_SHARED_HQ.json")
                review = {
                    "kind": "QC", "taskId": task["taskId"], "revision": task["revision"],
                    "candidateCommit": task["candidateCommit"], "artifactSha256": task["artifactSha256"],
                    "reviewerGitHubLogin": "Duncan-Sparx-ZB", "result": "PASS", "reportSha256": "C" * 64,
                }
                review[stale_field] = stale_value
                task.update({"status": "QC_PASS", "qcReview": record_sha256(review), "expectedMainCommit": BASE_SHA})
                state["lastTransition"] = {
                    "kind": "QC_RECORDED", "actorGitHubLogin": "Duncan-Sparx-ZB",
                    "taskRevision": task["revision"], "candidateCommit": task["candidateCommit"],
                    "artifactSha256": task["artifactSha256"], "previousRevision": task["revision"],
                }
                self.write(self.head, "hq/reviews/qc/GITHUB_SHARED_HQ/r01/Duncan-Sparx-ZB.json", review)
                self.write(self.head, "hq/tasks/GITHUB_SHARED_HQ.json", task)
                self.write(self.head, "hq/state/HQ_STATE.json", state)
                self.dashboard(self.head, state, task)
                with self.assertRaises(HQError):
                    validate_transition(self.base, self.head, actor="Duncan-Sparx-ZB", base_sha=BASE_SHA, head_sha=HEAD_SHA)

    def test_valid_artifact_transition_plus_hidden_non_json_payload_is_rejected(self):
        state = self.read(self.head, "hq/state/HQ_STATE.json")
        task = self.read(self.head, "hq/tasks/GITHUB_SHARED_HQ.json")
        artifact = {
            "taskId": "GITHUB_SHARED_HQ", "revision": 1, "sha256": SHA,
            "releaseTag": "shared-hq-r01", "sourceCommit": HEAD_SHA,
            "builderGitHubLogin": "Lester-Sparx", "immutable": True,
        }
        state.update({
            "revision": 1, "mainCommit": BASE_SHA,
            "lastTransition": {
                "kind": "ARTIFACT_REGISTERED", "actorGitHubLogin": "Lester-Sparx",
                "taskRevision": 1, "candidateCommit": HEAD_SHA,
                "artifactSha256": SHA, "previousRevision": 0,
            },
        })
        task.update({
            "revision": 1, "parentRevision": 0, "expectedMainCommit": BASE_SHA,
            "candidateCommit": HEAD_SHA, "status": "ARTIFACT_REGISTERED",
            "builderGitHubLogin": "Lester-Sparx", "artifactSha256": SHA,
            "artifactReleaseTag": "shared-hq-r01",
        })
        self.write(self.head, f"hq/artifacts/{SHA}.json", artifact)
        self.write(self.head, "hq/state/HQ_STATE.json", state)
        self.write(self.head, "hq/tasks/GITHUB_SHARED_HQ.json", task)
        (self.head / "hq/artifacts/hidden-production.txt").write_text(
            "DRAW=5\nPARRY=1\nprincipalX=0.1\n", encoding="utf-8"
        )
        self.dashboard(self.head, state, task)
        with self.assertRaisesRegex(HQError, "NON-JSON FILE"):
            validate_transition(self.base, self.head, actor="Lester-Sparx", base_sha=BASE_SHA, head_sha=HEAD_SHA)

    def test_next_valid_qc_transition_modifying_existing_unknown_file_is_rejected(self):
        state, task = self.make_registered(self.base)
        hidden = self.base / "hq/artifacts/hidden-production.txt"
        hidden.write_text("DRAW=5\nPARRY=1\n", encoding="utf-8")
        shutil.rmtree(self.head)
        shutil.copytree(self.base, self.head)
        state = self.read(self.head, "hq/state/HQ_STATE.json")
        task = self.read(self.head, "hq/tasks/GITHUB_SHARED_HQ.json")
        roles = {"OWNER": "Sparx-Owner-ZB", "LESTER": "Lester-Sparx", "DUNCAN": "Duncan-Sparx-ZB", "DJANGO": "Django-Sparx-ZB"}
        task, qc = submit_review(
            task, actor="Duncan-Sparx-ZB", kind="QC", result="PASS",
            report_sha256="C" * 64, roles=roles,
        )
        task["expectedMainCommit"] = BASE_SHA
        state.update({
            "mainCommit": BASE_SHA,
            "lastTransition": {
                "kind": "QC_RECORDED", "actorGitHubLogin": "Duncan-Sparx-ZB",
                "taskRevision": 1, "candidateCommit": COMMIT,
                "artifactSha256": SHA, "previousRevision": 1,
            },
        })
        self.write(self.head, "hq/reviews/qc/GITHUB_SHARED_HQ/r01/Duncan-Sparx-ZB.json", qc)
        self.write(self.head, "hq/state/HQ_STATE.json", state)
        self.write(self.head, "hq/tasks/GITHUB_SHARED_HQ.json", task)
        (self.head / "hq/artifacts/hidden-production.txt").write_text(
            "DRAW=999\nPARRY=777\n", encoding="utf-8"
        )
        self.dashboard(self.head, state, task)
        with self.assertRaisesRegex(HQError, "NON-JSON FILE"):
            validate_transition(self.base, self.head, actor="Duncan-Sparx-ZB", base_sha=BASE_SHA, head_sha=HEAD_SHA)


if __name__ == "__main__": unittest.main()
