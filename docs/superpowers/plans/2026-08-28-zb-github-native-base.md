# GitHub-Native Communication Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the minimum event-driven ZORR BLATT communication runner on GitHub Actions so one authenticated root comment on PR #111 executes the logical happy path and stops at the human OWNER gate without ChatGPT Work writes.

**Architecture:** One `issue_comment.created` workflow on default branch calls one Python standard-library runner. The runner strictly authenticates the event and root message, writes all durable state to tracker #106 through repository-local `GITHUB_TOKEN`, fresh-reads every write by exact comment ID, executes the seven logical stages in-process, and stops at `OWNER_GATE_REQUIRED`. PR #111 remains only the immutable event surface.

**Tech Stack:** GitHub Actions, Python 3 standard library, `unittest`, GitHub REST API through `urllib.request`, existing repository `hq-validate` CI.

**Spec:** `docs/superpowers/specs/2026-08-28-zb-github-native-base-design.md` at approved PR #116 HEAD `81c44232b72b4a98c8ad0ac2ea6a0a2876f988bc`

## Global Constraints

- Repository: `Lester-Sparx/zorr-blatt-shared-hq`.
- Event surface: PR `#111`, top-level `issue_comment.created` only.
- Transport actor: `Lester-Sparx` only.
- Tracker: issue `#106` only.
- Task: `ZB_GITHUB_NATIVE_BASE_R01`, revision `1`.
- Approved design HEAD: `81c44232b72b4a98c8ad0ac2ea6a0a2876f988bc`.
- Logical roles: `JINGO`, `LESTER`, `DUNCAN`, `DJANGO`; OWNER is never auto-executed.
- No PAT, external webhook, polling, scheduler, database, queue server, daemon, auto-merge, production activation, canon mutation, OWNER LOCK, PR #103 mutation, issue #102 mutation, or PR #111 HEAD mutation.
- Workflow permissions: `contents: read`, `issues: write`, `pull-requests: read` only.
- Every authoritative tracker write must satisfy `WRITE -> exact remote comment ID -> fresh GET by that ID -> exact body MATCH` before continuing.
- Final remote event proof is post-merge only because `issue_comment` workflows must exist on default branch.

---

### Task 1: Strict root message parser and admission

**Files:**
- Create: `scripts/zb_communication_base.py`
- Create: `tests/test_zb_communication_base.py`

**Interfaces:**
- Consumes: GitHub event JSON plus source comment body.
- Produces: `RootMessage`, `EventContext`, `parse_root_message(body)`, `admit_event(event, expected_base_sha)`.

- [ ] **Step 1: Write failing parser/admission tests**

Create `tests/test_zb_communication_base.py` using `unittest` and `tests/_support.py` import conventions. Cover one valid message, duplicate field rejection, unknown field rejection, wrong actor, wrong issue number, non-PR issue, wrong marker, wrong task/revision/design HEAD, stale `BASE_SHA`, and `NO_AUTO_MERGE != TRUE`.

Use this canonical fixture:

```python
VALID_BODY = """ZB_AGENT_MESSAGE_V1
MESSAGE_ID = zb-native-r01-msg-001
EVENT_ID = zb-native-r01-evt-001
CORRELATION_ID = zb-native-r01
CAUSATION_MESSAGE_ID = NONE
TASK_ID = ZB_GITHUB_NATIVE_BASE_R01
FROM_ROLE = JINGO
TO_ROLE = LESTER
MESSAGE_KIND = ASSIGN
BASE_SHA = {base_sha}
TASK_REVISION = 1
DESIGN_HEAD = 81c44232b72b4a98c8ad0ac2ea6a0a2876f988bc
NO_AUTO_MERGE = TRUE
"""
```

- [ ] **Step 2: Run targeted tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_zb_communication_base -v
```

Expected: import or missing-symbol failures for the new runner.

- [ ] **Step 3: Implement the minimal parser and event admission**

Define:

```python
class ProtocolError(ValueError):
    pass

@dataclass(frozen=True)
class RootMessage:
    message_id: str
    event_id: str
    correlation_id: str
    causation_message_id: str
    task_id: str
    from_role: str
    to_role: str
    message_kind: str
    base_sha: str
    task_revision: int
    design_head: str
    no_auto_merge: bool

@dataclass(frozen=True)
class EventContext:
    repository: str
    issue_number: int
    comment_id: int
    actor: str
    run_id: str
    run_attempt: str
    github_sha: str
```

`parse_root_message()` must require exactly the eleven named fields above after the exact marker, reject duplicates/unknowns, require `TASK_ID = ZB_GITHUB_NATIVE_BASE_R01`, revision `1`, approved design HEAD, `JINGO -> LESTER / ASSIGN`, `CAUSATION_MESSAGE_ID = NONE`, 40-hex `BASE_SHA`, and `NO_AUTO_MERGE = TRUE`.

`admit_event()` must require repository `Lester-Sparx/zorr-blatt-shared-hq`, issue number `111`, event action `created`, a `pull_request` object on the issue payload, actor `Lester-Sparx`, and `message.base_sha == expected_base_sha`.

- [ ] **Step 4: Run targeted tests and verify GREEN**

Run the same unittest command. Expected: all Task 1 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/zb_communication_base.py tests/test_zb_communication_base.py
git commit -m "feat: add native communication admission"
```

---

### Task 2: Repository-local GitHub API port and fresh read-back persistence

**Files:**
- Modify: `scripts/zb_communication_base.py`
- Modify: `tests/test_zb_communication_base.py`

**Interfaces:**
- Consumes: `GITHUB_TOKEN`, repository name, tracker `106`.
- Produces: `GitHubPort`, `GitHubApi`, `write_and_verify(body)`, `list_tracker_comments()`.

- [ ] **Step 1: Write failing persistence tests**

Add a fake port whose `create_tracker_comment()` returns an ID and whose `read_comment(id)` returns a configurable body. Test:

```python
self.assertEqual(write_and_verify(port, "BODY"), 9001)
```

and require `PersistenceError` when read-back ID/body/container differs. Also test that the port has no merge, contents-write, workflow-write, issue-update, or PR-update method.

- [ ] **Step 2: Run targeted tests and verify RED**

```bash
python3 -m unittest tests.test_zb_communication_base -v
```

Expected: missing `GitHubApi` / persistence symbols.

- [ ] **Step 3: Implement the minimal REST adapter**

Use only Python standard library:

```python
class GitHubPort(Protocol):
    def create_tracker_comment(self, body: str) -> int: ...
    def read_comment(self, comment_id: int) -> dict: ...
    def list_tracker_comments(self) -> list[dict]: ...

class PersistenceError(RuntimeError):
    pass
```

`GitHubApi` must call only:

- `POST /repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106/comments`
- `GET /repos/Lester-Sparx/zorr-blatt-shared-hq/issues/comments/{id}`
- `GET /repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106/comments?per_page=100&page=N`

with `Authorization: Bearer <GITHUB_TOKEN>`, GitHub JSON headers, finite network timeout, and no body-derived URL components.

`write_and_verify()` must create, capture numeric ID, perform a new exact-ID GET, require issue URL ending `/issues/106`, require exact body equality, then return the ID.

- [ ] **Step 4: Run targeted tests and verify GREEN**

Expected: persistence tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/zb_communication_base.py tests/test_zb_communication_base.py
git commit -m "feat: add tracker persistence boundary"
```

---

### Task 3: Idempotent happy-path state machine and OWNER stop

**Files:**
- Modify: `scripts/zb_communication_base.py`
- Modify: `tests/test_zb_communication_base.py`

**Interfaces:**
- Consumes: accepted `RootMessage`, `EventContext`, `GitHubPort`.
- Produces: `run_base(message, context, port) -> str` with terminal values `OWNER_GATE_REQUIRED` or `NOOP_REPLAY`.

- [ ] **Step 1: Write failing state-machine tests**

Assert exact ordered logical stages:

```python
EXPECTED_STAGES = [
    ("JINGO", "LESTER", "ASSIGN"),
    ("LESTER", "JINGO", "RETURN"),
    ("JINGO", "DUNCAN", "QC_REQUEST"),
    ("DUNCAN", "JINGO", "QC_VERDICT"),
    ("JINGO", "DJANGO", "ARCH_REVIEW"),
    ("DJANGO", "JINGO", "ARCH_VERDICT"),
    ("JINGO", "JINGO", "CLOSE_REQUEST"),
]
```

The fake port must observe tracker bodies in this order:

1. `ZB_AGENT_RECEIPT_V1 / STATE = RECEIVED`
2. `ZB_AGENT_RECEIPT_V1 / STATE = RUNNING`
3. seven `ZB_AGENT_RECEIPT_V1 / STATE = RESULT / RESULT_CODE = PASS` records, one per stage
4. `ZB_OWNER_VIEW_V0 / OWNER_GATE_REQUIRED = TRUE / OWNER_ACTION_REQUIRED = TRUE`

Also test:

- no string representing an OWNER execution stage exists;
- a second run with an existing RECEIVED/RUNNING/RESULT record for the same `MESSAGE_ID + SOURCE_COMMENT_ID` returns `NOOP_REPLAY` and creates zero comments;
- malformed existing tracker records do not grant replay status.

- [ ] **Step 2: Run targeted tests and verify RED**

Expected: missing state-machine symbols.

- [ ] **Step 3: Implement minimal deterministic state machine**

Render compact immutable records with these mandatory fields on every receipt:

```text
MESSAGE_ID
CORRELATION_ID
SOURCE_COMMENT_ID
TASK_ID
TASK_REVISION
BASE_SHA
DESIGN_HEAD
SOURCE_ACTOR
WORKFLOW_RUN_ID
WORKFLOW_RUN_ATTEMPT
LOGICAL_FROM_ROLE
LOGICAL_TO_ROLE
MESSAGE_KIND
STATE
RESULT_CODE
PRODUCTION_ACTIVE = NO
```

Use `EXECUTION_ID = github-actions:<run_id>:<run_attempt>` on RUNNING/RESULT records. Role work is only exact binding verification plus sequence progression; it performs no external mutation besides tracker comments.

Before writing RECEIVED, scan tracker comments for a record with exact `MESSAGE_ID` and `SOURCE_COMMENT_ID` and a recognized state `RECEIVED|RUNNING|RESULT|BLOCKED`; if found, return `NOOP_REPLAY` without writes.

After each `write_and_verify()`, proceed to the next state. If any read-back fails, raise and stop immediately.

- [ ] **Step 4: Run targeted tests and verify GREEN**

Expected: exact order, replay, and OWNER-stop tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/zb_communication_base.py tests/test_zb_communication_base.py
git commit -m "feat: add native communication happy path"
```

---

### Task 4: Event entrypoint and least-privilege GitHub Actions workflow

**Files:**
- Modify: `scripts/zb_communication_base.py`
- Create: `.github/workflows/zb-communication-base.yml`
- Modify: `tests/test_zb_communication_base.py`

**Interfaces:**
- Consumes: `GITHUB_EVENT_PATH`, `GITHUB_REPOSITORY`, `GITHUB_RUN_ID`, `GITHUB_RUN_ATTEMPT`, `GITHUB_SHA`, `GITHUB_TOKEN`.
- Produces: process exit 0 for ignored/replay/success; non-zero for authenticated protocol failure.

- [ ] **Step 1: Write failing entrypoint/workflow-shape tests**

Tests must load the YAML as text (no new YAML dependency) and require all of:

```text
issue_comment:
  types: [created]
contents: read
issues: write
pull-requests: read
```

and reject `contents: write`, `actions: write`, `pull-requests: write`, `workflow_dispatch`, schedules, PAT/secrets other than `${{ github.token }}`.

Add entrypoint tests using temporary event JSON and fake/injected port factory so ordinary prose exits cleanly without GitHub writes while a valid event invokes `run_base()`.

- [ ] **Step 2: Run targeted tests and verify RED**

Expected: missing workflow/entrypoint behavior.

- [ ] **Step 3: Implement entrypoint and workflow**

Workflow shape:

```yaml
name: zb-communication-base
on:
  issue_comment:
    types: [created]
permissions:
  contents: read
  issues: write
  pull-requests: read
jobs:
  route:
    if: github.event.issue.number == 111 && github.event.comment.user.login == 'Lester-Sparx'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run ZB communication base
        env:
          GITHUB_TOKEN: ${{ github.token }}
        run: python3 scripts/zb_communication_base.py
```

Entrypoint reads only the GitHub event file and environment. It first ignores non-marker bodies. For a marker body it parses strictly, admits the event, constructs `GitHubApi`, then calls `run_base()`.

- [ ] **Step 4: Run targeted and full repository tests**

```bash
python3 -m unittest tests.test_zb_communication_base -v
python3 scripts/hq_validate.py
python3 -m unittest discover -s tests -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/zb-communication-base.yml scripts/zb_communication_base.py tests/test_zb_communication_base.py
git commit -m "feat: add GitHub-native communication workflow"
```

---

### Task 5: Implementation PR verification, OWNER merge gate, and post-merge remote proof

**Files:**
- No additional implementation files unless tests expose a defect.
- Durable evidence: implementation PR comments and tracker issue `#106`.

**Interfaces:**
- Consumes: exact implementation PR HEAD, CI evidence, explicit OWNER merge command.
- Produces: post-merge `issue_comment.created` proof ending at OWNER gate.

- [ ] **Step 1: Open implementation PR from a fresh branch based on protected `main`**

The implementation PR must include only:

- `.github/workflows/zb-communication-base.yml`
- `scripts/zb_communication_base.py`
- `tests/test_zb_communication_base.py`

Its body binds approved design PR #116 HEAD `81c44232b72b4a98c8ad0ac2ea6a0a2876f988bc` and the approved plan HEAD.

- [ ] **Step 2: Verify exact implementation HEAD**

Require fresh `hq-validate` success and review the PR diff for forbidden mutation surfaces. Record exact HEAD and workflow run/job IDs in PR and #106 with fresh read-back MATCH.

- [ ] **Step 3: Stop at explicit OWNER merge gate**

Do not merge until OWNER explicitly approves the exact implementation HEAD. Use merge commit method so implementation provenance remains directly visible in the post-merge commit ancestry.

- [ ] **Step 4: After OWNER merge, fresh-read protected main**

Capture exact post-merge `main` SHA. Verify the workflow exists at `.github/workflows/zb-communication-base.yml` on that exact SHA. `PRODUCTION_ACTIVE` remains `NO`.

- [ ] **Step 5: Post one fresh disposable root message on PR #111**

Use a new unique `MESSAGE_ID`, exact post-merge `BASE_SHA`, task `ZB_GITHUB_NATIVE_BASE_R01`, revision `1`, approved design HEAD, and `NO_AUTO_MERGE = TRUE`.

- [ ] **Step 6: Verify the real event run**

Require a real `zb-communication-base` workflow run caused by that comment and fresh-read tracker records proving:

```text
RECEIVED
RUNNING
7 ordered RESULT = PASS stages
ZB_OWNER_VIEW_V0
OWNER_GATE_REQUIRED = TRUE
OWNER_ACTION_REQUIRED = TRUE
PRODUCTION_ACTIVE = NO
```

No OWNER execution record may exist.

- [ ] **Step 7: Record base proof result**

Only after all exact-ID read-backs match, record:

```text
ZB106_GITHUB_NATIVE_BASE_REMOTE_PROOF_V1
BASE_AUTOMATION = PASS
CHAIN_REACHED_OWNER_GATE = YES
WORK_DEPENDENCY = NONE
POLLING = NO
PRODUCTION_ACTIVE = NO
```

Do not claim production activation and do not continue into deferred retry/dead-letter/negative-matrix work in this base plan.
