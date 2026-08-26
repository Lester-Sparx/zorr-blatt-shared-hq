# ZB Agent Controller v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real-execution ZB automation vertical slice where a private GitHub task for SALVADOR triggers a real OpenAI image-edit run and produces durable `RUNNING`, `RESULT_READY`, or `FAILED` evidence without opening a ChatGPT browser tab.

**Architecture:** A new private repository `Lester-Sparx/zorr-blatt-agent-runner` owns the GitHub Actions workflow, Python runner, tests, role prompt, and private task/result data. Public Shared HQ remains coordination-only; no production image bytes or API secrets enter it. The runner parses a fixed task contract, validates exactly one reference image, performs an idempotent OpenAI image-edit call, persists the result privately, and records state transitions only when durable evidence exists.

**Tech Stack:** GitHub Actions, Python 3.12, pytest, stdlib `urllib`/`json`/`hashlib` where practical, official OpenAI Python SDK, GitHub CLI/API only where needed by workflow scripting.

**Spec:** `docs/superpowers/specs/2026-08-26-zb-agent-controller-v0-design.md`

## Global Constraints

- v0 supports exactly `AGENT = SALVADOR` and `TASK_KIND = PRODUCTION_IMAGE_EDIT`.
- `ASSIGNED != RUNNING`.
- `RUNNING` may be recorded only after validation passes and a real OpenAI request is initiated.
- `RESULT_READY` may be recorded only after a non-empty supported image is persisted privately.
- `FAILED` is explicit; failures must never be represented as `ACTIVE` or `RUNNING` success.
- Production references/results stay private.
- Never write agent-controller code or art assets to `zorr-blatt-runtime`.
- Never store `OPENAI_API_KEY` in source, issue text, logs, artifacts, comments, or Shared HQ.
- Never execute arbitrary shell/code derived from issue text.
- No merge authority, OWNER LOCK authority, runtime activation, or browser-session automation.
- Exactly one reference image is accepted in v0.
- Duplicate events for the same immutable `TASK_ID` must not cause a second model call.
- Model name is configuration, not hard-wired into orchestration semantics.

---

## File Structure

The private runner repository will use this initial structure:

```text
zorr-blatt-agent-runner/
  .github/
    workflows/
      salvador-task.yml
  pyproject.toml
  src/
    zb_agent_runner/
      __init__.py
      cli.py
      task_contract.py
      state_machine.py
      references.py
      openai_images.py
      persistence.py
      github_events.py
      config.py
      prompts/
        salvador-production-image-edit.txt
  tests/
    test_task_contract.py
    test_state_machine.py
    test_references.py
    test_openai_images.py
    test_persistence.py
    test_cli.py
    test_workflow_contract.py
```

Responsibilities:

- `task_contract.py`: parse and validate the fixed machine-readable task block.
- `state_machine.py`: encode canonical states and allowed transitions.
- `references.py`: resolve/download exactly one private reference and validate MIME/size.
- `openai_images.py`: isolate OpenAI image-edit request/response handling behind a small interface.
- `persistence.py`: write result bytes + `result.json`, compute checksum, detect duplicates.
- `github_events.py`: format durable private issue comments/events without leaking private URLs.
- `config.py`: environment/config parsing, including model name and size limits.
- `cli.py`: orchestration only; no parsing or API details embedded.
- `prompts/salvador-production-image-edit.txt`: permanent role prompt for this task class.
- `salvador-task.yml`: GitHub event trigger, permissions, concurrency, and invocation.

---

### Task 1: Owner bootstrap and private repository boundary

**Files:**
- Owner action: create private repository `Lester-Sparx/zorr-blatt-agent-runner`
- Owner action: add Actions secret `OPENAI_API_KEY`
- Create: `README.md`
- Create: `.gitignore`
- Create: `pyproject.toml`

**Interfaces:**
- Consumes: approved design in Shared HQ PR #46.
- Produces: a private execution repository where all later tasks are implemented.

- [ ] **Step 1: Create the private repository**

Create `Lester-Sparx/zorr-blatt-agent-runner` with visibility `PRIVATE` and default branch `main`.

- [ ] **Step 2: Add the OpenAI secret**

In repository Settings → Secrets and variables → Actions, create repository secret:

```text
OPENAI_API_KEY
```

Do not expose the value in any issue, comment, workflow output, or commit.

- [ ] **Step 3: Add minimal project metadata**

`pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "zb-agent-runner"
version = "0.0.1"
requires-python = ">=3.12"
dependencies = [
  "openai>=1.0.0",
]

[project.optional-dependencies]
test = ["pytest>=8.0"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 4: Add privacy guardrails to README**

README must explicitly state:

```text
PRIVATE EXECUTION REPOSITORY
NO PUBLIC ART STORAGE
NO OPENAI_API_KEY IN SOURCE OR LOGS
NO RUNTIME REPOSITORY WRITES
```

- [ ] **Step 5: Verify setup**

Run:

```bash
python -m pip install -e '.[test]'
pytest -q
```

Expected: install succeeds; zero tests collected is acceptable only before Task 2.

- [ ] **Step 6: Commit**

```bash
git add README.md .gitignore pyproject.toml
git commit -m "chore: bootstrap private agent runner"
```

---

### Task 2: Task contract parser

**Files:**
- Create: `src/zb_agent_runner/__init__.py`
- Create: `src/zb_agent_runner/task_contract.py`
- Test: `tests/test_task_contract.py`

**Interfaces:**
- Consumes: raw GitHub issue body as `str`.
- Produces: `AgentTask` dataclass and `parse_task(body: str) -> AgentTask`.

- [ ] **Step 1: Write failing parser tests**

```python
from zb_agent_runner.task_contract import TaskContractError, parse_task

VALID = """ZB_AGENT_TASK_V0
TASK_ID = ZB-SALVADOR-20260826T150000Z-001
AGENT = SALVADOR
TASK_KIND = PRODUCTION_IMAGE_EDIT
STATE = ASSIGNED
PUBLIC_TRACKING_ISSUE = Lester-Sparx/zorr-blatt-shared-hq#45
REFERENCE = ATTACHMENT_REQUIRED
"""


def test_parse_valid_salvador_task():
    task = parse_task(VALID)
    assert task.task_id == "ZB-SALVADOR-20260826T150000Z-001"
    assert task.agent == "SALVADOR"
    assert task.task_kind == "PRODUCTION_IMAGE_EDIT"
    assert task.state == "ASSIGNED"


def test_rejects_unknown_agent():
    bad = VALID.replace("AGENT = SALVADOR", "AGENT = LESTER")
    try:
        parse_task(bad)
    except TaskContractError as exc:
        assert exc.code == "INVALID_AGENT"
    else:
        raise AssertionError("expected TaskContractError")
```

Add equivalent tests for missing marker, missing field, duplicate field, invalid state, invalid task kind, and malformed public tracking pointer.

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest tests/test_task_contract.py -q
```

Expected: FAIL because module/functions do not exist.

- [ ] **Step 3: Implement minimal parser**

Create immutable dataclass:

```python
@dataclass(frozen=True)
class AgentTask:
    task_id: str
    agent: str
    task_kind: str
    state: str
    public_tracking_issue: str | None
    reference_mode: str
```

Allowed fixed values in v0:

```python
ALLOWED_AGENTS = {"SALVADOR"}
ALLOWED_TASK_KINDS = {"PRODUCTION_IMAGE_EDIT"}
ALLOWED_INITIAL_STATES = {"ASSIGNED", "WAITING_REFERENCE"}
ALLOWED_REFERENCE_MODES = {"ATTACHMENT_REQUIRED"}
```

Parser must reject unknown/duplicate keys instead of ignoring them.

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_task_contract.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/zb_agent_runner/task_contract.py src/zb_agent_runner/__init__.py tests/test_task_contract.py
git commit -m "feat: parse fixed Salvador task contract"
```

---

### Task 3: Canonical state machine

**Files:**
- Create: `src/zb_agent_runner/state_machine.py`
- Test: `tests/test_state_machine.py`

**Interfaces:**
- Produces: `can_transition(current: str, target: str) -> bool` and `require_transition(current: str, target: str) -> None`.

- [ ] **Step 1: Write failing transition tests**

```python
from zb_agent_runner.state_machine import can_transition


def test_allowed_transitions():
    assert can_transition("ASSIGNED", "WAITING_REFERENCE")
    assert can_transition("ASSIGNED", "RUNNING")
    assert can_transition("WAITING_REFERENCE", "RUNNING")
    assert can_transition("RUNNING", "RESULT_READY")
    assert can_transition("RUNNING", "FAILED")


def test_forbidden_transitions():
    assert not can_transition("ASSIGNED", "RESULT_READY")
    assert not can_transition("RESULT_READY", "RUNNING")
    assert not can_transition("FAILED", "RUNNING")
```

- [ ] **Step 2: Verify failure**

```bash
pytest tests/test_state_machine.py -q
```

- [ ] **Step 3: Implement exact table**

```python
ALLOWED_TRANSITIONS = {
    "ASSIGNED": {"WAITING_REFERENCE", "RUNNING"},
    "WAITING_REFERENCE": {"RUNNING"},
    "RUNNING": {"RESULT_READY", "FAILED"},
    "RESULT_READY": set(),
    "FAILED": set(),
}
```

Unknown states must raise a deterministic `StateTransitionError` in `require_transition`.

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_state_machine.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/zb_agent_runner/state_machine.py tests/test_state_machine.py
git commit -m "feat: add Agent Controller v0 state machine"
```

---

### Task 4: Reference resolution and validation

**Files:**
- Create: `src/zb_agent_runner/references.py`
- Create: `src/zb_agent_runner/config.py`
- Test: `tests/test_references.py`

**Interfaces:**
- Consumes: candidate attachment URL + authenticated byte loader callable.
- Produces: `ReferenceImage(content: bytes, mime_type: str, filename: str)`.

- [ ] **Step 1: Write failing tests**

Cover:

```python
missing reference -> ReferenceRequired
more than one reference -> ReferenceValidationError("TOO_MANY_REFERENCES")
image/png -> accepted
image/jpeg -> accepted
image/webp -> accepted
text/html -> rejected
bytes > configured max -> rejected
zero bytes -> rejected
```

Use an in-memory fake loader; tests must not access the network.

- [ ] **Step 2: Verify failure**

```bash
pytest tests/test_references.py -q
```

- [ ] **Step 3: Implement config**

`config.py` must expose:

```python
DEFAULT_MAX_REFERENCE_BYTES = 20 * 1024 * 1024
SUPPORTED_IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}
DEFAULT_IMAGE_MODEL = "gpt-image-2-2026-04-21"
```

Allow model override only through an environment variable owned by deployment configuration, never through issue text.

- [ ] **Step 4: Implement validation**

Do not infer MIME solely from filename. Require content-type metadata from the resolved attachment and reject unsupported values.

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_references.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/zb_agent_runner/config.py src/zb_agent_runner/references.py tests/test_references.py
git commit -m "feat: validate private Salvador references"
```

---

### Task 5: SALVADOR permanent role prompt

**Files:**
- Create: `src/zb_agent_runner/prompts/salvador-production-image-edit.txt`
- Test: `tests/test_openai_images.py`

**Interfaces:**
- Consumes: permanent role prompt + task-specific art direction.
- Produces: deterministic composed prompt string.

- [ ] **Step 1: Add role prompt**

The prompt must encode these exact laws in plain language:

```text
You are SALVADOR, ZORR BLATT art-production agent.
This task class is production simplification, not redesign.
Preserve identity and the major defining forms visible in the supplied reference.
Do not invent facts absent from the reference.
Remove micro-detail and visual noise; clarify major forms and reduce unnecessary internal lines.
Obey requested view count/orientation exactly.
When graphite/production pencil is requested, use confident production pencil with controlled roughness and minimal shading.
Return exactly one image when one image is requested.
```

- [ ] **Step 2: Add failing prompt-composition test**

Assert permanent prompt appears before task-specific direction and task text cannot override the fixed `AGENT`/`TASK_KIND` contract.

- [ ] **Step 3: Implement prompt composer in `openai_images.py`**

Expose:

```python
def compose_prompt(role_prompt: str, task_direction: str) -> str:
    ...
```

- [ ] **Step 4: Run test**

```bash
pytest tests/test_openai_images.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/zb_agent_runner/prompts/salvador-production-image-edit.txt src/zb_agent_runner/openai_images.py tests/test_openai_images.py
git commit -m "feat: add permanent Salvador image-edit prompt"
```

---

### Task 6: OpenAI image-edit adapter

**Files:**
- Modify: `src/zb_agent_runner/openai_images.py`
- Test: `tests/test_openai_images.py`

**Interfaces:**
- Consumes: `ReferenceImage`, composed prompt, configured model, injected OpenAI client.
- Produces: `GeneratedImage(content: bytes, mime_type: str)`.

- [ ] **Step 1: Write failing adapter tests with fake client**

Required tests:

```text
client called exactly once
configured model passed through
reference bytes passed as image input
prompt passed through
API exception -> ImageGenerationError("OPENAI_REQUEST_FAILED")
empty image -> ImageGenerationError("EMPTY_IMAGE_OUTPUT")
non-image response -> ImageGenerationError("INVALID_IMAGE_OUTPUT")
valid bytes -> GeneratedImage
```

- [ ] **Step 2: Verify failure**

```bash
pytest tests/test_openai_images.py -q
```

- [ ] **Step 3: Implement adapter behind dependency injection**

Do not construct the OpenAI client at import time. Provide a small function/class whose client is injected for tests and created only in CLI runtime.

- [ ] **Step 4: Ensure no response body/prompt is logged by adapter**

Only stable error codes should escape; raw SDK exceptions may be chained internally but not posted to issue comments.

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_openai_images.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/zb_agent_runner/openai_images.py tests/test_openai_images.py
git commit -m "feat: add OpenAI Salvador image-edit adapter"
```

---

### Task 7: Private result persistence and idempotency

**Files:**
- Create: `src/zb_agent_runner/persistence.py`
- Test: `tests/test_persistence.py`

**Interfaces:**
- Consumes: task ID + `GeneratedImage` + metadata.
- Produces: persisted `result.png`, `result.json`, SHA-256 checksum, terminal-result existence check.

- [ ] **Step 1: Write failing persistence tests**

Use a temporary directory and assert:

```text
non-empty image persisted
result.json contains taskId/agent/state/model/workflowRunId/sha256/bytes/createdAt
checksum matches bytes
existing terminal result is detected before generation
zero-byte image cannot be persisted as RESULT_READY
```

- [ ] **Step 2: Verify failure**

```bash
pytest tests/test_persistence.py -q
```

- [ ] **Step 3: Implement filesystem persistence abstraction**

Expose an interface that can later be backed by a generated-results branch or artifact store without changing orchestration semantics.

Initial local layout:

```text
results/<TASK_ID>/result.png
results/<TASK_ID>/result.json
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_persistence.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/zb_agent_runner/persistence.py tests/test_persistence.py
git commit -m "feat: persist private Salvador results idempotently"
```

---

### Task 8: Durable private issue events

**Files:**
- Create: `src/zb_agent_runner/github_events.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces sanitized private issue event bodies:

```text
SALVADOR_RUNNING
SALVADOR_REFERENCE_REQUIRED
SALVADOR_RESULT_READY
SALVADOR_FAILED
```

plus machine block:

```text
ZB_AGENT_EVENT_V0
TASK_ID = ...
AGENT = SALVADOR
STATE = ...
WORKFLOW_RUN_ID = ...
ERROR_CODE = ... | NONE
PRIVATE_RESULT = AVAILABLE | NONE
```

- [ ] **Step 1: Write failing sanitizer tests**

Pass fake secrets/private URLs into the event formatter and assert they never appear in output.

- [ ] **Step 2: Implement event formatter**

Formatter accepts only explicit safe fields. It must not accept a raw exception object or raw API response.

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_cli.py -q
```

- [ ] **Step 4: Commit**

```bash
git add src/zb_agent_runner/github_events.py tests/test_cli.py
git commit -m "feat: add durable sanitized agent events"
```

---

### Task 9: Orchestrator CLI

**Files:**
- Create: `src/zb_agent_runner/cli.py`
- Modify: `pyproject.toml`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes environment + issue JSON/body/reference metadata.
- Coordinates parser → idempotency → reference validation → RUNNING event → OpenAI call → persistence → RESULT_READY/FAILED event.

- [ ] **Step 1: Write failing orchestration tests using fakes**

Required exact cases:

```text
ASSIGNED + no reference -> WAITING_REFERENCE, zero OpenAI calls
WAITING_REFERENCE + now-valid reference -> RUNNING -> RESULT_READY
ASSIGNED + valid reference -> RUNNING -> RESULT_READY
existing RESULT_READY -> clean exit, zero OpenAI calls
OpenAI error after RUNNING -> FAILED
persistence error after valid generation -> FAILED
RESULT_READY event occurs only after persist() succeeds
```

Track event order in a list and assert ordering, not just membership.

- [ ] **Step 2: Verify failure**

```bash
pytest tests/test_cli.py -q
```

- [ ] **Step 3: Implement orchestration function**

Expose testable function:

```python
def run_task(
    *,
    issue_body: str,
    task_direction: str,
    reference_candidates: list[str],
    workflow_run_id: int,
    dependencies: RunnerDependencies,
) -> int:
    ...
```

The function must contain no direct shell execution.

- [ ] **Step 4: Add console entry point**

`pyproject.toml`:

```toml
[project.scripts]
zb-agent-runner = "zb_agent_runner.cli:main"
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_cli.py -q
```

Expected: PASS.

- [ ] **Step 6: Run full suite**

```bash
pytest -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/zb_agent_runner/cli.py pyproject.toml tests/test_cli.py
git commit -m "feat: orchestrate real Salvador task execution"
```

---

### Task 10: GitHub Actions workflow contract

**Files:**
- Create: `.github/workflows/salvador-task.yml`
- Test: `tests/test_workflow_contract.py`

**Interfaces:**
- Consumes: private issue event.
- Produces: one runner invocation per eligible task with least privilege and task-scoped concurrency.

- [ ] **Step 1: Write failing static workflow tests**

Parse workflow text and assert it contains:

```text
issues: write
contents: write only if result branch persistence is used
no pull-requests write
no actions write
no deployments write
concurrency keyed by task identity/issue identity
environment OPENAI_API_KEY from secrets.OPENAI_API_KEY
Python 3.12
```

Also assert issue body is passed as a file/env payload, never interpolated unquoted into a shell command.

- [ ] **Step 2: Verify failure**

```bash
pytest tests/test_workflow_contract.py -q
```

- [ ] **Step 3: Implement workflow**

Trigger initially on private issue creation/edit events sufficient to resume `WAITING_REFERENCE` after attachment metadata becomes available.

Use a deterministic eligibility precheck before installing dependencies or invoking OpenAI.

Set:

```yaml
permissions:
  contents: write
  issues: write
```

Only if branch-based result persistence is selected. If artifact-only persistence is selected during implementation, reduce `contents` to `read`.

- [ ] **Step 4: Add concurrency**

Concurrency must prevent two executions for the same issue/task from overlapping and must not cancel a currently running valid generation merely because a duplicate edit event arrives.

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_workflow_contract.py -q
pytest -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/salvador-task.yml tests/test_workflow_contract.py
git commit -m "ci: run Salvador tasks from private issues"
```

---

### Task 11: Disposable end-to-end smoke

**Files:**
- No source changes expected unless smoke reveals a defect.
- Private issue: disposable SALVADOR test task.

**Interfaces:**
- Proves actual GitHub Actions → OpenAI → persistence path.

- [ ] **Step 1: Create a non-sensitive disposable reference image**

Use a simple synthetic image containing no production art or personal data.

- [ ] **Step 2: Create private task issue**

Use exact block:

```text
ZB_AGENT_TASK_V0
TASK_ID = ZB-SALVADOR-SMOKE-001
AGENT = SALVADOR
TASK_KIND = PRODUCTION_IMAGE_EDIT
STATE = ASSIGNED
PUBLIC_TRACKING_ISSUE = NONE
REFERENCE = ATTACHMENT_REQUIRED
```

Task direction requests a trivial visible edit suitable for verification.

- [ ] **Step 3: Attach exactly one reference**

Verify workflow triggers automatically.

- [ ] **Step 4: Verify durable ordering**

Required evidence:

```text
SALVADOR_RUNNING
then real OpenAI request succeeds
then result file/artifact exists and is non-empty
then SALVADOR_RESULT_READY
```

Capture workflow run ID and result checksum.

- [ ] **Step 5: Trigger a duplicate issue event**

Edit whitespace or otherwise trigger the workflow without changing immutable task ID.

Expected:

```text
no second OpenAI generation
same terminal result remains authoritative
workflow exits successfully/idempotently
```

- [ ] **Step 6: Record smoke evidence in a private issue comment**

Include task ID, workflow run ID, checksum, result byte count, and `DUPLICATE_CALL_COUNT = 0` for the second trigger.

- [ ] **Step 7: Commit any smoke-driven fixes only after tests reproduce the defect**

Use TDD for every discovered bug.

---

### Task 12: First production SALVADOR run

**Files:**
- Private task issue created from Shared HQ issue #45 direction.
- No production art committed to Shared HQ.

**Interfaces:**
- Consumes: the owner-approved middle face reference.
- Produces: exactly one private production image and durable result metadata.

- [ ] **Step 1: Create private production task**

Copy the approved art direction from Shared HQ issue #45 into the private runner issue, preserving the fixed task contract.

- [ ] **Step 2: Attach the exact approved middle-reference source**

If the source is still the three-variant sheet, task direction must explicitly identify the approved middle variant. Do not crop/alter the reference unless owner approves that preprocessing.

- [ ] **Step 3: Verify real execution state**

Do not tell owner work is running until durable `SALVADOR_RUNNING` exists from the runner.

- [ ] **Step 4: Verify result**

Required:

```text
exactly one output image
non-empty image bytes
result checksum
SALVADOR_RESULT_READY
```

- [ ] **Step 5: Owner review**

Surface the private result to SPARX for visual approval. Do not mark artistic acceptance merely because generation technically succeeded.

---

## Self-Review Results

- Spec coverage: all v0 states, privacy rules, idempotency, OpenAI invocation, result persistence, failure semantics, and disposable smoke acceptance criteria have implementation tasks.
- Placeholder scan: no `TBD`, `TODO`, or unspecified generic “handle errors” steps remain.
- Type/interface consistency: task parser, state machine, image adapter, persistence layer, event formatter, and CLI boundaries are named consistently across tasks.
- Scope check: this plan covers only the SALVADOR vertical slice. Public Control Room projection, LESTER/DUNCAN automation, merge orchestration, and browser-chat control remain explicitly out of scope.
