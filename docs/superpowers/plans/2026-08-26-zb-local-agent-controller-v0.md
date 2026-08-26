# ZB LOCAL Agent Controller v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a zero-budget Windows-local controller that discovers explicitly marked GitHub agent tasks, dispatches the SALVADOR vertical slice to local ComfyUI, and records truthful durable states `WAITING_REFERENCE`, `RUNNING`, `RESULT_READY`, or `FAILED` without requiring a ChatGPT browser tab.

**Architecture:** A long-running Python process on the owner's Windows PC polls Shared HQ for fixed-contract tasks, validates a canonical local inbox, dispatches through a backend registry, and records durable GitHub events through authenticated `gh`. SALVADOR's first backend is local ComfyUI at `http://127.0.0.1:8188`; orchestration is backend-agnostic so LESTER and DUNCAN adapters can be added later without rewriting controller state logic.

**Tech Stack:** Python 3.12, pytest, stdlib `subprocess`, `urllib.request`, `json`, `pathlib`, `hashlib`, GitHub CLI (`gh`), ComfyUI local HTTP API, Windows Task Scheduler only after functional acceptance.

**Spec:** `docs/superpowers/specs/2026-08-26-zb-agent-controller-v0-design.md`

## Global Constraints

- Zero paid inference/API dependencies. No `OPENAI_API_KEY`.
- First executable backend is exactly `AGENT = SALVADOR`, `TASK_KIND = PRODUCTION_IMAGE_EDIT`, `BACKEND = COMFYUI_LOCAL`.
- `ASSIGNED != RUNNING`.
- `RUNNING` is emitted only after ComfyUI returns a real non-empty `prompt_id`.
- `RESULT_READY` is emitted only after local `result.png` and `result.json` exist and checksum validation passes.
- `FAILED` is explicit; no optimistic `ACTIVE` state may substitute for execution evidence.
- Canonical inbox root: `D:\BLATT2\ZB_AGENT_INBOX`.
- Canonical result root: `D:\BLATT2\ZB_AGENT_RESULTS`.
- ComfyUI URL default: `http://127.0.0.1:8188`.
- ComfyUI install root default: `D:\BLATT2\ComfyUI_windows_portable`.
- Never execute arbitrary shell/code from GitHub issue text.
- Never accept issue-controlled filesystem paths or backend/model paths.
- No writes to `zorr-blatt-runtime`.
- No merge, OWNER LOCK, runtime activation, governance verdict, or browser-session automation authority.
- Exactly one active SALVADOR GPU job at a time in v0.
- Build and test controller logic with a mocked ComfyUI backend before requiring any production model download.

---

## File Structure

Implementation target repository/directory on the Windows machine:

```text
D:\BLATT2\zb-local-agent-controller\
  pyproject.toml
  README.md
  config.example.json
  src\
    zb_local_controller\
      __init__.py
      task_contract.py
      state_machine.py
      local_paths.py
      github_cli.py
      events.py
      controller.py
      config.py
      backends\
        __init__.py
        base.py
        comfyui.py
      workflows\
        salvador-production-image-edit.json
      prompts\
        salvador-production-image-edit.txt
  tests\
    test_task_contract.py
    test_state_machine.py
    test_local_paths.py
    test_events.py
    test_github_cli.py
    test_comfyui.py
    test_controller.py
  scripts\
    run-controller.cmd
```

Responsibilities:

- `task_contract.py`: strict parsing of `ZB_AGENT_TASK_V0` blocks.
- `state_machine.py`: exact legal state transitions.
- `local_paths.py`: safe fixed-root reference/result discovery and path traversal rejection.
- `github_cli.py`: fixed-argument `gh` reads/comments; never shell-source interpolation.
- `events.py`: sanitized durable event serialization.
- `backends/base.py`: backend interface.
- `backends/comfyui.py`: readiness, submission, polling, output collection.
- `controller.py`: polling, idempotency, dispatch, single-GPU lock, orchestration.
- `config.py`: local JSON/environment configuration, no issue-controlled backend/model selection.
- `workflows/*.json`: versioned ComfyUI workflow template with explicitly replaceable prompt/reference inputs only.
- `scripts/run-controller.cmd`: stable launcher used later by Task Scheduler.

---

### Task 1: Bootstrap local controller project and strict task contract

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/zb_local_controller/__init__.py`
- Create: `src/zb_local_controller/task_contract.py`
- Test: `tests/test_task_contract.py`

**Interfaces:**
- Consumes: GitHub issue body as `str`.
- Produces: immutable `AgentTask` and `parse_task(body: str) -> AgentTask`.

- [ ] **Step 1: Write failing parser tests**

```python
from zb_local_controller.task_contract import TaskContractError, parse_task

VALID = """ZB_AGENT_TASK_V0
TASK_ID = ZB-SALVADOR-20260826T160000Z-001
AGENT = SALVADOR
TASK_KIND = PRODUCTION_IMAGE_EDIT
STATE = ASSIGNED
REFERENCE = LOCAL_INBOX

Simplify the supplied face reference without redesign.
"""


def test_parse_valid_task():
    task = parse_task(VALID)
    assert task.task_id == "ZB-SALVADOR-20260826T160000Z-001"
    assert task.agent == "SALVADOR"
    assert task.task_kind == "PRODUCTION_IMAGE_EDIT"
    assert task.state == "ASSIGNED"
    assert task.reference == "LOCAL_INBOX"
    assert "Simplify the supplied face reference" in task.direction


def test_rejects_unknown_agent():
    bad = VALID.replace("AGENT = SALVADOR", "AGENT = LESTER")
    try:
        parse_task(bad)
    except TaskContractError as exc:
        assert exc.code == "INVALID_AGENT"
    else:
        raise AssertionError("expected TaskContractError")
```

Add explicit tests for missing marker, duplicate field, missing field, invalid task kind, invalid state, invalid reference mode, unknown machine key, and empty task direction.

- [ ] **Step 2: Run the test to prove RED**

```powershell
python -m pytest tests/test_task_contract.py -q
```

Expected: import/module failure.

- [ ] **Step 3: Implement the minimal parser**

Use:

```python
@dataclass(frozen=True)
class AgentTask:
    task_id: str
    agent: str
    task_kind: str
    state: str
    reference: str
    direction: str
```

Fixed v0 vocabularies:

```python
ALLOWED_AGENTS = {"SALVADOR"}
ALLOWED_TASK_KINDS = {"PRODUCTION_IMAGE_EDIT"}
ALLOWED_STATES = {"ASSIGNED", "WAITING_REFERENCE"}
ALLOWED_REFERENCE_MODES = {"LOCAL_INBOX"}
```

Machine keys are exactly `TASK_ID`, `AGENT`, `TASK_KIND`, `STATE`, `REFERENCE`; reject extras and duplicates.

- [ ] **Step 4: Run parser tests**

```powershell
python -m pytest tests/test_task_contract.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add pyproject.toml README.md src/zb_local_controller tests/test_task_contract.py
git commit -m "feat: bootstrap local controller task contract"
```

---

### Task 2: State machine and fixed local path boundary

**Files:**
- Create: `src/zb_local_controller/state_machine.py`
- Create: `src/zb_local_controller/local_paths.py`
- Test: `tests/test_state_machine.py`
- Test: `tests/test_local_paths.py`

**Interfaces:**
- Produces: `can_transition(current, target) -> bool`.
- Produces: `resolve_reference(inbox_root: Path, task_id: str) -> ReferenceImage | None`.
- Produces: `result_paths(result_root: Path, task_id: str) -> tuple[Path, Path]`.

- [ ] **Step 1: Write failing state tests**

```python
from zb_local_controller.state_machine import can_transition


def test_allowed_transitions():
    assert can_transition("ASSIGNED", "WAITING_REFERENCE")
    assert can_transition("ASSIGNED", "STARTING_BACKEND")
    assert can_transition("WAITING_REFERENCE", "STARTING_BACKEND")
    assert can_transition("STARTING_BACKEND", "RUNNING")
    assert can_transition("STARTING_BACKEND", "FAILED")
    assert can_transition("RUNNING", "RESULT_READY")
    assert can_transition("RUNNING", "FAILED")


def test_terminal_states_do_not_restart():
    assert not can_transition("RESULT_READY", "RUNNING")
    assert not can_transition("FAILED", "RUNNING")
```

- [ ] **Step 2: Write failing path tests**

```python
from pathlib import Path
import pytest
from zb_local_controller.local_paths import PathBoundaryError, resolve_reference


def test_rejects_task_id_path_traversal(tmp_path: Path):
    with pytest.raises(PathBoundaryError):
        resolve_reference(tmp_path, "..\\outside")


def test_missing_reference_returns_none(tmp_path: Path):
    assert resolve_reference(tmp_path, "ZB-SALVADOR-X-001") is None


def test_exactly_one_png_is_accepted(tmp_path: Path):
    d = tmp_path / "ZB-SALVADOR-X-001"
    d.mkdir()
    (d / "ref.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 32)
    ref = resolve_reference(tmp_path, "ZB-SALVADOR-X-001")
    assert ref.path.name == "ref.png"
```

Add tests for two supported images -> `REFERENCE_COUNT_INVALID`, unsupported extension, zero-byte file, and >20 MiB input.

- [ ] **Step 3: Implement exact state table and path safety**

The task directory must be constructed only as `inbox_root / task_id` after validating `task_id` against `^[A-Z0-9_-]+$`; do not normalize arbitrary issue-supplied paths.

Accepted extensions are `.png`, `.jpg`, `.jpeg`, `.webp`. Validate magic bytes for PNG/JPEG/WEBP before acceptance.

- [ ] **Step 4: Run tests**

```powershell
python -m pytest tests/test_state_machine.py tests/test_local_paths.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/zb_local_controller/state_machine.py src/zb_local_controller/local_paths.py tests/test_state_machine.py tests/test_local_paths.py
git commit -m "feat: add state and local path safety"
```

---

### Task 3: Durable GitHub events through fixed `gh` commands

**Files:**
- Create: `src/zb_local_controller/events.py`
- Create: `src/zb_local_controller/github_cli.py`
- Test: `tests/test_events.py`
- Test: `tests/test_github_cli.py`

**Interfaces:**
- Produces: `format_event(...) -> str`.
- Produces: `GitHubCLI.list_candidate_issues() -> list[GitHubIssue]`.
- Produces: `GitHubCLI.post_comment(issue_number: int, body: str) -> None`.

- [ ] **Step 1: Write failing event sanitizer test**

```python
from zb_local_controller.events import format_event


def test_result_event_contains_metadata_not_local_path():
    body = format_event(
        task_id="ZB-SALVADOR-X-001",
        state="RESULT_READY",
        execution_id="prompt-123",
        result_sha256="abc123",
        error_code=None,
    )
    assert "STATE = RESULT_READY" in body
    assert "EXECUTION_ID = prompt-123" in body
    assert "D:\\" not in body
```

Add assertions for compatibility lines `SALVADOR_RUNNING`, `SALVADOR_RESULT_READY`, `SALVADOR_REFERENCE_REQUIRED` in their matching states only.

- [ ] **Step 2: Write failing `gh` argument tests**

Inject a fake subprocess runner and assert the command is an argument list, e.g.:

```python
[
  "gh", "issue", "comment", "45",
  "--repo", "Lester-Sparx/zorr-blatt-shared-hq",
  "--body", event_body,
]
```

No `shell=True`; no command string concatenation.

- [ ] **Step 3: Implement GitHub CLI adapter**

Before polling, run `gh auth status`; if it fails raise `GitHubConfigurationError("GH_NOT_AUTHENTICATED")`.

Candidate discovery must query only open issues containing marker `ZB_AGENT_TASK_V0`, then strict parser decides eligibility.

- [ ] **Step 4: Run tests**

```powershell
python -m pytest tests/test_events.py tests/test_github_cli.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/zb_local_controller/events.py src/zb_local_controller/github_cli.py tests/test_events.py tests/test_github_cli.py
git commit -m "feat: add durable GitHub event adapter"
```

---

### Task 4: Backend interface and mocked ComfyUI evidence law

**Files:**
- Create: `src/zb_local_controller/backends/base.py`
- Create: `src/zb_local_controller/backends/comfyui.py`
- Create: `src/zb_local_controller/backends/__init__.py`
- Test: `tests/test_comfyui.py`

**Interfaces:**
- `ensure_ready() -> None`.
- `submit(task, reference) -> str` where returned `str` is the real `prompt_id`.
- `poll(execution_id) -> BackendPollResult`.
- `collect(execution_id) -> bytes`.

- [ ] **Step 1: Write failing mocked HTTP tests**

Required tests:

```text
GET /system_stats success -> ready
unreachable backend -> BACKEND_UNAVAILABLE
POST /prompt without prompt_id -> SUBMIT_EVIDENCE_MISSING
POST /prompt with prompt_id -> returns that exact id
history says running -> RUNNING
history says completed with output -> COMPLETE
history says execution error -> FAILED
collect returns non-empty PNG bytes
```

The HTTP transport must be injectable so tests use no real network.

- [ ] **Step 2: Implement ComfyUI client**

Use stdlib JSON/HTTP. `RUNNING` evidence is the non-empty `prompt_id` from `/prompt`. Never infer execution from HTTP 200 alone.

Workflow JSON is loaded from a versioned file; only allowlisted prompt/reference input fields may be replaced from task/reference data.

- [ ] **Step 3: Run tests**

```powershell
python -m pytest tests/test_comfyui.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```powershell
git add src/zb_local_controller/backends tests/test_comfyui.py
git commit -m "feat: add ComfyUI backend evidence adapter"
```

---

### Task 5: Controller orchestration, idempotency, and single-GPU lock

**Files:**
- Create: `src/zb_local_controller/controller.py`
- Create: `src/zb_local_controller/config.py`
- Create: `config.example.json`
- Test: `tests/test_controller.py`

**Interfaces:**
- `Controller.run_once() -> RunSummary`.
- `Controller.run_forever() -> None` using configurable default poll interval 15 seconds.

- [ ] **Step 1: Write failing orchestration tests**

Use fake GitHub and fake backend. Prove:

```text
ASSIGNED + no reference -> exactly one WAITING_REFERENCE event, zero submit calls
WAITING_REFERENCE + later reference -> submit once
submit returns prompt_id -> RUNNING posted after submit returns, not before
backend failure before prompt_id -> FAILED, never RUNNING
backend complete -> persist output then RESULT_READY
existing result.json -> zero submit calls
existing durable RESULT_READY -> zero submit calls
second active SALVADOR task while one lock held -> zero submit calls for second task
```

- [ ] **Step 2: Implement result persistence**

Write `result.png` and then `result.json` atomically enough for v0: image to temporary file, `os.replace`, compute SHA-256, metadata to temporary JSON, `os.replace`.

Metadata schema:

```json
{
  "taskId": "ZB-SALVADOR-X-001",
  "agent": "SALVADOR",
  "backend": "COMFYUI_LOCAL",
  "state": "RESULT_READY",
  "executionId": "prompt-123",
  "sha256": "...",
  "bytes": 12345,
  "createdAt": "2026-08-26T00:00:00Z"
}
```

- [ ] **Step 3: Implement registry with one allowed v0 mapping**

```python
{
    ("SALVADOR", "PRODUCTION_IMAGE_EDIT"): comfyui_backend,
}
```

Unknown mappings are rejected; never dispatch based on arbitrary issue-provided module names.

- [ ] **Step 4: Run orchestration suite**

```powershell
python -m pytest tests -q
```

Expected: all tests PASS with no production model installed.

- [ ] **Step 5: Commit**

```powershell
git add src/zb_local_controller/controller.py src/zb_local_controller/config.py config.example.json tests/test_controller.py
git commit -m "feat: orchestrate truthful local agent states"
```

---

### Task 6: Local launcher and mocked end-to-end dry run

**Files:**
- Create: `scripts/run-controller.cmd`
- Create: `src/zb_local_controller/__main__.py`
- Modify: `README.md`

**Interfaces:**
- `python -m zb_local_controller --once` processes one polling cycle.
- `python -m zb_local_controller` runs continuously.

- [ ] **Step 1: Add CLI smoke path**

`--once` must return non-zero for configuration failures and zero when a cycle completes normally, including no eligible tasks.

- [ ] **Step 2: Add Windows launcher**

```bat
@echo off
cd /d D:\BLATT2\zb-local-agent-controller
python -m zb_local_controller
```

No Task Scheduler installation yet.

- [ ] **Step 3: Run full mocked verification**

```powershell
python -m pytest -q
python -m zb_local_controller --once
```

Expected: tests PASS; dry cycle either reports no eligible tasks or an explicit configuration error if `gh` authentication has not yet been configured. It must never fabricate RUNNING.

- [ ] **Step 4: Commit**

```powershell
git add scripts/run-controller.cmd src/zb_local_controller/__main__.py README.md
git commit -m "feat: add local controller launcher"
```

---

### Task 7: Live ComfyUI disposable smoke — only after Tasks 1–6 are green

**Files:**
- Create/Modify: `src/zb_local_controller/workflows/salvador-production-image-edit.json`
- Create: `src/zb_local_controller/prompts/salvador-production-image-edit.txt`
- Modify: local `config.json` only; do not commit machine-specific secrets.

**Interfaces:**
- Real local ComfyUI at `http://127.0.0.1:8188`.
- One lightweight workflow/model compatible with 4 GB VRAM.

- [ ] **Step 1: Verify ComfyUI readiness without a model call**

```powershell
Invoke-WebRequest http://127.0.0.1:8188/system_stats -UseBasicParsing
```

Expected: HTTP success.

- [ ] **Step 2: Configure one disposable non-production reference**

Create:

```text
D:\BLATT2\ZB_AGENT_INBOX\ZB-SALVADOR-SMOKE-001\reference.png
```

Use a non-sensitive test image, not the approved production face reference.

- [ ] **Step 3: Create one smoke GitHub task**

Issue body machine block:

```text
ZB_AGENT_TASK_V0
TASK_ID = ZB-SALVADOR-SMOKE-001
AGENT = SALVADOR
TASK_KIND = PRODUCTION_IMAGE_EDIT
STATE = ASSIGNED
REFERENCE = LOCAL_INBOX

Disposable smoke: make a minimal visible edit while preserving the reference subject.
```

- [ ] **Step 4: Run one real controller cycle**

Expected durable evidence order:

```text
ComfyUI returns prompt_id
-> SALVADOR_RUNNING
-> output exists
-> result.png + result.json persist
-> SALVADOR_RESULT_READY
```

- [ ] **Step 5: Prove duplicate protection**

Run another cycle with the same issue unchanged. Expected: no second ComfyUI submission and no second generated image.

- [ ] **Step 6: Record exact smoke evidence in the LESTER build issue**

Required handoff:

```text
LESTER_LOCAL_CONTROLLER_READY
TESTS = PASS
SMOKE_TASK = ZB-SALVADOR-SMOKE-001
COMFYUI_PROMPT_ID = <real id>
RESULT_SHA256 = <real sha256>
DUPLICATE_SUBMISSION = NO
OWNER_ACTION_REQUIRED = <YES|NO>
```

No production SALVADOR face task runs until this handoff exists.

---

## Self-review checklist

- Spec coverage: parser, states, safe local roots, GitHub CLI, ComfyUI evidence, idempotency, single-GPU lock, local persistence, zero-paid boundary, and live disposable acceptance are each mapped to a task.
- Placeholder scan: no `TBD`, `TODO`, or unspecified implementation step is permitted.
- Type/name consistency: `AgentTask`, `RUNNING`, `RESULT_READY`, `COMFYUI_LOCAL`, `prompt_id`, canonical inbox/result roots, and task vocabulary match the approved spec.
- Scope: LESTER/DUNCAN local reasoning adapters are intentionally excluded from v0 implementation; only the adapter boundary is built now.
