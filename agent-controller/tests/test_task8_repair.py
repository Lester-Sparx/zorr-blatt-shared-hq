import hashlib
import json

import pytest

from zb_local_controller.controller import Controller
from zb_local_controller.github_cli import GitHubIssue

PNG = b"\x89PNG\r\n\x1a\n" + b"result-bytes"
CANON_METADATA = {
    "taskKind": "CANON_REFERENCE_EDIT",
    "workflowVersion": "salvador-canon-reference-edit-v1",
    "canonPromptVersion": "salvador-canon-v1",
    "modelId": "local-model.safetensors",
    "workingWidth": 512,
    "workingHeight": 768,
    "sourceSha256": "a" * 64,
    "seed": 123,
    "denoise": 0.35,
}


def body(task_id):
    return f"""ZB_AGENT_TASK_V0
TASK_ID = {task_id}
AGENT = SALVADOR
TASK_KIND = CANON_REFERENCE_EDIT
STATE = ASSIGNED
REFERENCE = LOCAL_INBOX

No redesign. Preserve the same pose.
"""


class FakeGitHub:
    def __init__(self, issue):
        self.issue = issue
        self.posts = []

    def list_candidate_issues(self):
        return [self.issue]

    def post_comment(self, issue_number, event):
        self.posts.append((issue_number, event))
        self.issue = GitHubIssue(
            self.issue.number,
            self.issue.title,
            self.issue.body,
            self.issue.comments + (event,),
        )


class NeverSubmitBackend:
    def __init__(self):
        self.submit_calls = 0

    def ensure_ready(self):
        raise AssertionError("backend must not be reached without a reference")

    def submit(self, task, reference):
        self.submit_calls += 1
        raise AssertionError("submit must not be reached")


def make_controller(tmp_path, task_id):
    issue = GitHubIssue(59, "canon", body(task_id))
    gh = FakeGitHub(issue)
    backend = NeverSubmitBackend()
    inbox = tmp_path / "inbox"
    results = tmp_path / "results"
    inbox.mkdir()
    results.mkdir()
    controller = Controller(
        gh,
        inbox,
        results,
        {("SALVADOR", "CANON_REFERENCE_EDIT"): backend},
    )
    return controller, gh, backend, results


def seed_existing_result(results, task_id, extra=None):
    directory = results / task_id
    directory.mkdir()
    (directory / "result.png").write_bytes(PNG)
    digest = hashlib.sha256(PNG).hexdigest()
    metadata = {
        "taskId": task_id,
        "agent": "SALVADOR",
        "backend": "COMFYUI_LOCAL",
        "state": "RESULT_READY",
        "executionId": "existing-prompt-1",
        "sha256": digest,
    }
    metadata.update(extra or {})
    (directory / "result.json").write_text(json.dumps(metadata), encoding="utf-8")
    return digest


def test_canon_existing_legacy_smoke_result_never_republishes_result_ready(tmp_path):
    task_id = "ZB-SALVADOR-CANON-COLLISION-001"
    controller, gh, backend, results = make_controller(tmp_path, task_id)
    seed_existing_result(results, task_id)

    summary = controller.run_once()

    assert summary.submitted == 0
    assert backend.submit_calls == 0
    assert not any("STATE = RESULT_READY" in event for _, event in gh.posts)
    assert any("STATE = WAITING_REFERENCE" in event for _, event in gh.posts)


_REQUIRED_CANON_REDISCOVERY_FIELDS = tuple(CANON_METADATA) + ("promptId", "resultSha256")


@pytest.mark.parametrize("missing_field", _REQUIRED_CANON_REDISCOVERY_FIELDS)
def test_canon_existing_result_requires_complete_provenance_before_republish(tmp_path, missing_field):
    task_id = f"ZB-SALVADOR-CANON-MISSING-{missing_field.upper()}"
    controller, gh, _, results = make_controller(tmp_path, task_id)
    digest = hashlib.sha256(PNG).hexdigest()
    provenance = dict(CANON_METADATA)
    provenance.update({"promptId": "existing-prompt-1", "resultSha256": digest})
    provenance.pop(missing_field)
    seed_existing_result(results, task_id, provenance)

    controller.run_once()

    assert not any("STATE = RESULT_READY" in event for _, event in gh.posts)


def test_canon_existing_result_requires_prompt_and_result_sha_coherence(tmp_path):
    task_id = "ZB-SALVADOR-CANON-INCOHERENT-001"
    controller, gh, _, results = make_controller(tmp_path, task_id)
    provenance = dict(CANON_METADATA)
    provenance.update({"promptId": "different-prompt", "resultSha256": "b" * 64})
    seed_existing_result(results, task_id, provenance)

    controller.run_once()

    assert not any("STATE = RESULT_READY" in event for _, event in gh.posts)


def test_canon_existing_coherent_result_republishes_without_resubmit(tmp_path):
    task_id = "ZB-SALVADOR-CANON-REDISCOVER-001"
    controller, gh, backend, results = make_controller(tmp_path, task_id)
    digest = hashlib.sha256(PNG).hexdigest()
    provenance = dict(CANON_METADATA)
    provenance.update({"promptId": "existing-prompt-1", "resultSha256": digest})
    seed_existing_result(results, task_id, provenance)

    summary = controller.run_once()

    assert summary.submitted == 0
    assert backend.submit_calls == 0
    assert len(gh.posts) == 1
    assert "STATE = RESULT_READY" in gh.posts[0][1]
    assert "EXECUTION_ID = existing-prompt-1" in gh.posts[0][1]
    assert f"RESULT_SHA256 = {digest}" in gh.posts[0][1]
