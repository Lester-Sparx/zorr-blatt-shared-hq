import hashlib
import json
from pathlib import Path

from zb_local_controller.backends.base import BackendError, BackendPollResult
from zb_local_controller.controller import Controller
from zb_local_controller.github_cli import GitHubCLIError, GitHubIssue

PNG = b"\x89PNG\r\n\x1a\n" + b"result-bytes"


def body(task_id, state="ASSIGNED"):
    return f"""ZB_AGENT_TASK_V0
TASK_ID = {task_id}
AGENT = SALVADOR
TASK_KIND = PRODUCTION_IMAGE_EDIT
STATE = {state}
REFERENCE = LOCAL_INBOX

Simplify without redesign.
"""


class FakeGitHub:
    def __init__(self, issues, log=None, on_post=None):
        self.issues = {i.number: i for i in issues}
        self.posts = []
        self.log = log if log is not None else []
        self.on_post = on_post

    def list_candidate_issues(self):
        return list(self.issues.values())

    def post_comment(self, issue_number, event):
        self.log.append(("post", event))
        self.posts.append((issue_number, event))
        issue = self.issues[issue_number]
        self.issues[issue_number] = GitHubIssue(issue.number, issue.title, issue.body, issue.comments + (event,))
        if self.on_post:
            self.on_post(issue_number, event)




class FlakyGitHub(FakeGitHub):
    def __init__(self, issues, fail_state):
        super().__init__(issues)
        self.fail_state = fail_state
        self.failed_once = False

    def post_comment(self, issue_number, event):
        if not self.failed_once and f"STATE = {self.fail_state}" in event:
            self.failed_once = True
            raise GitHubCLIError("GH_COMMENT_FAILED")
        super().post_comment(issue_number, event)


class FakeBackend:
    def __init__(self, prompt_id="prompt-123", polls=None, fail_ready=None, fail_submit=None, log=None):
        self.prompt_id = prompt_id
        self.polls = list(polls or [BackendPollResult("RUNNING")])
        self.fail_ready = fail_ready
        self.fail_submit = fail_submit
        self.submit_calls = 0
        self.poll_calls = 0
        self.log = log if log is not None else []

    def ensure_ready(self):
        self.log.append(("ready", None))
        if self.fail_ready:
            raise BackendError(self.fail_ready)

    def submit(self, task, reference):
        self.submit_calls += 1
        self.log.append(("submit", task.task_id))
        if self.fail_submit:
            raise BackendError(self.fail_submit)
        return self.prompt_id

    def poll(self, execution_id):
        self.poll_calls += 1
        self.log.append(("poll", execution_id))
        return self.polls.pop(0) if self.polls else BackendPollResult("RUNNING")

    def collect(self, execution_id):
        self.log.append(("collect", execution_id))
        return PNG


def add_ref(root: Path, task_id: str):
    d = root / task_id; d.mkdir(parents=True, exist_ok=True)
    (d / "ref.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"ref")


def make_controller(tmp_path, gh, backend):
    inbox = tmp_path / "inbox"; inbox.mkdir(exist_ok=True)
    results = tmp_path / "results"; results.mkdir(exist_ok=True)
    c = Controller(gh, inbox, results, {("SALVADOR", "PRODUCTION_IMAGE_EDIT"): backend})
    return c, inbox, results


def test_assigned_without_reference_posts_waiting_once_and_never_submits(tmp_path):
    issue = GitHubIssue(1, "task", body("ZB-SALVADOR-X-001"))
    gh = FakeGitHub([issue]); backend = FakeBackend()
    c, _, _ = make_controller(tmp_path, gh, backend)
    c.run_once(); c.run_once()
    waiting = [p for _, p in gh.posts if "STATE = WAITING_REFERENCE" in p]
    assert len(waiting) == 1
    assert backend.submit_calls == 0


def test_waiting_reference_later_appears_submits_once(tmp_path):
    task_id = "ZB-SALVADOR-X-002"
    gh = FakeGitHub([GitHubIssue(2, "task", body(task_id))]); backend = FakeBackend()
    c, inbox, _ = make_controller(tmp_path, gh, backend)
    c.run_once()
    add_ref(inbox, task_id)
    c.run_once()
    assert backend.submit_calls == 1
    assert any("STATE = RUNNING" in p for _, p in gh.posts)


def test_running_is_posted_only_after_submit_returns_prompt_id(tmp_path):
    log = []
    task_id = "ZB-SALVADOR-X-003"
    gh = FakeGitHub([GitHubIssue(3, "task", body(task_id))], log=log)
    backend = FakeBackend(log=log)
    c, inbox, _ = make_controller(tmp_path, gh, backend); add_ref(inbox, task_id)
    c.run_once()
    submit_index = next(i for i, x in enumerate(log) if x[0] == "submit")
    running_index = next(i for i, x in enumerate(log) if x[0] == "post" and "STATE = RUNNING" in x[1])
    assert submit_index < running_index
    assert "EXECUTION_ID = prompt-123" in log[running_index][1]


def test_backend_failure_before_prompt_id_posts_failed_never_running(tmp_path):
    task_id = "ZB-SALVADOR-X-004"
    gh = FakeGitHub([GitHubIssue(4, "task", body(task_id))]); backend = FakeBackend(fail_ready="BACKEND_UNAVAILABLE")
    c, inbox, _ = make_controller(tmp_path, gh, backend); add_ref(inbox, task_id)
    c.run_once()
    assert any("STATE = FAILED" in p for _, p in gh.posts)
    assert not any("STATE = RUNNING" in p for _, p in gh.posts)


def test_backend_complete_persists_before_result_ready(tmp_path):
    task_id = "ZB-SALVADOR-X-005"
    seen = {"persisted_before_post": False}
    gh = FakeGitHub([GitHubIssue(5, "task", body(task_id))])
    backend = FakeBackend(polls=[BackendPollResult("COMPLETE")])
    c, inbox, results = make_controller(tmp_path, gh, backend); add_ref(inbox, task_id)
    def on_post(_n, event):
        if "STATE = RESULT_READY" in event:
            seen["persisted_before_post"] = (results / task_id / "result.png").exists() and (results / task_id / "result.json").exists()
    gh.on_post = on_post
    c.run_once()
    meta = json.loads((results / task_id / "result.json").read_text())
    assert seen["persisted_before_post"]
    assert meta["state"] == "RESULT_READY"
    assert meta["executionId"] == "prompt-123"
    assert meta["sha256"] == hashlib.sha256(PNG).hexdigest()
    assert any("STATE = RESULT_READY" in p for _, p in gh.posts)


def test_existing_valid_result_json_prevents_resubmit(tmp_path):
    task_id = "ZB-SALVADOR-X-006"
    gh = FakeGitHub([GitHubIssue(6, "task", body(task_id))]); backend = FakeBackend()
    c, inbox, results = make_controller(tmp_path, gh, backend); add_ref(inbox, task_id)
    d = results / task_id; d.mkdir()
    (d / "result.png").write_bytes(PNG)
    (d / "result.json").write_text(json.dumps({"taskId": task_id, "state": "RESULT_READY", "sha256": hashlib.sha256(PNG).hexdigest()}))
    c.run_once()
    assert backend.submit_calls == 0


def test_existing_durable_result_ready_prevents_resubmit(tmp_path):
    task_id = "ZB-SALVADOR-X-007"
    terminal = f"ZB_AGENT_EVENT_V0\nTASK_ID = {task_id}\nSTATE = RESULT_READY\nEXECUTION_ID = prompt-old"
    gh = FakeGitHub([GitHubIssue(7, "task", body(task_id), (terminal,))]); backend = FakeBackend()
    c, inbox, _ = make_controller(tmp_path, gh, backend); add_ref(inbox, task_id)
    c.run_once()
    assert backend.submit_calls == 0


def test_second_salvador_task_does_not_submit_while_lock_held(tmp_path):
    ids = ["ZB-SALVADOR-X-008", "ZB-SALVADOR-X-009"]
    issues = [GitHubIssue(8, "a", body(ids[0])), GitHubIssue(9, "b", body(ids[1]))]
    gh = FakeGitHub(issues); backend = FakeBackend(polls=[BackendPollResult("RUNNING"), BackendPollResult("RUNNING")])
    c, inbox, _ = make_controller(tmp_path, gh, backend)
    for task_id in ids: add_ref(inbox, task_id)
    c.run_once(); c.run_once()
    assert backend.submit_calls == 1


def test_durable_failed_is_terminal_and_never_resubmits(tmp_path):
    task_id = "ZB-SALVADOR-X-010"
    failed = f"ZB_AGENT_EVENT_V0\nTASK_ID = {task_id}\nSTATE = FAILED\nEXECUTION_ID = prompt-old\nERROR_CODE = BACKEND_EXECUTION_FAILED"
    gh = FakeGitHub([GitHubIssue(10, "task", body(task_id), (failed,))])
    backend = FakeBackend()
    c, inbox, _ = make_controller(tmp_path, gh, backend)
    add_ref(inbox, task_id)

    c.run_once()

    assert backend.submit_calls == 0


def test_restart_reconstructs_running_before_any_new_submission(tmp_path):
    assigned_id = "ZB-SALVADOR-X-011"
    running_id = "ZB-SALVADOR-X-012"
    running = f"ZB_AGENT_EVENT_V0\nTASK_ID = {running_id}\nSTATE = RUNNING\nEXECUTION_ID = prompt-existing"
    issues = [
        GitHubIssue(11, "new", body(assigned_id)),
        GitHubIssue(12, "active", body(running_id), (running,)),
    ]
    gh = FakeGitHub(issues)
    backend = FakeBackend(polls=[BackendPollResult("RUNNING")])
    c, inbox, _ = make_controller(tmp_path, gh, backend)
    add_ref(inbox, assigned_id)
    add_ref(inbox, running_id)

    c.run_once()

    assert backend.submit_calls == 0
    assert backend.poll_calls == 1


def test_result_ready_publication_failure_is_healed_without_regeneration(tmp_path):
    task_id = "ZB-SALVADOR-X-013"
    gh = FlakyGitHub([GitHubIssue(13, "task", body(task_id))], fail_state="RESULT_READY")
    backend = FakeBackend(polls=[BackendPollResult("COMPLETE")])
    c, inbox, results = make_controller(tmp_path, gh, backend)
    add_ref(inbox, task_id)

    c.run_once()
    assert (results / task_id / "result.png").exists()
    assert (results / task_id / "result.json").exists()
    assert not any("STATE = RESULT_READY" in p for _, p in gh.posts)

    c.run_once()

    assert backend.submit_calls == 1
    assert any("STATE = RESULT_READY" in p for _, p in gh.posts)


def test_running_publication_failure_survives_restart_without_resubmit(tmp_path):
    task_id = "ZB-SALVADOR-X-014"
    gh = FlakyGitHub([GitHubIssue(14, "task", body(task_id))], fail_state="RUNNING")
    backend = FakeBackend(polls=[BackendPollResult("RUNNING")])
    c1, inbox, results = make_controller(tmp_path, gh, backend)
    add_ref(inbox, task_id)

    try:
        c1.run_once()
    except GitHubCLIError:
        pass
    assert backend.submit_calls == 1
    assert not any("STATE = RUNNING" in p for _, p in gh.posts)

    c2 = Controller(gh, inbox, results, {("SALVADOR", "PRODUCTION_IMAGE_EDIT"): backend})
    c2.run_once()

    assert backend.submit_calls == 1
    assert any("STATE = RUNNING" in p for _, p in gh.posts)


def test_malformed_task_id_is_isolated_and_next_issue_still_processes(tmp_path):
    bad = GitHubIssue(15, "bad", body("..\\outside"))
    good_id = "ZB-SALVADOR-X-015"
    good = GitHubIssue(16, "good", body(good_id))
    gh = FakeGitHub([bad, good])
    backend = FakeBackend()
    c, inbox, _ = make_controller(tmp_path, gh, backend)
    add_ref(inbox, good_id)

    c.run_once()

    assert backend.submit_calls == 1
    assert any("STATE = RUNNING" in p for _, p in gh.posts)


class FakeClock:
    def __init__(self, value=1000.0):
        self.value = value

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


def test_running_execution_times_out_without_replacement_submission(tmp_path):
    task_id = "ZB-SALVADOR-X-016"
    gh = FakeGitHub([GitHubIssue(17, "task", body(task_id))])
    backend = FakeBackend(polls=[BackendPollResult("RUNNING")])
    clock = FakeClock()
    inbox = tmp_path / "inbox"; inbox.mkdir()
    results = tmp_path / "results"; results.mkdir()
    c = Controller(
        gh,
        inbox,
        results,
        {("SALVADOR", "PRODUCTION_IMAGE_EDIT"): backend},
        max_execution_seconds=30.0,
        clock=clock,
    )
    add_ref(inbox, task_id)

    c.run_once()
    assert backend.submit_calls == 1
    clock.advance(31.0)
    c.run_once()
    c.run_once()

    assert backend.submit_calls == 1
    assert any("STATE = FAILED" in p and "ERROR_CODE = EXECUTION_TIMEOUT" in p for _, p in gh.posts)
