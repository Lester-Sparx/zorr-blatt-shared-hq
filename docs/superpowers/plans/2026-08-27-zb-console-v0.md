# ZB Console v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a zero-dependency, read-only PowerShell owner console where typing `zb` shows the real ZORR BLATT team/gate/scout state plus the latest cryptographically validated local output.

**Architecture:** Extend the existing `agent-controller` Python package with three focused modules: structured remote snapshot parsing, local result validation/discovery, and CLI rendering/commands. Remote state comes only from the latest valid `ZB_OWNER_VIEW_V0` snapshot in Shared HQ issue #39; local output comes only from validated `result.png` + `result.json` pairs under the configured result root. The console never writes GitHub/controller/canon state.

**Tech Stack:** Python 3.12+, stdlib only, existing `gh` CLI, PowerShell installer wrapper, pytest>=8 for tests.

**Spec:** `docs/superpowers/specs/2026-08-27-zb-console-v0-design.md`

## Global Constraints

- Read-only v0: no GitHub posts, no ComfyUI submission, no runtime mutation, no canon/OWNER LOCK changes.
- Remote source is only latest valid `ZB_OWNER_VIEW_V0` snapshot in Shared HQ issue #39.
- Missing/unverifiable remote state renders `UNKNOWN`; snapshot older than 2 hours renders `STALE`.
- Local official output requires matching SHA-256 between `result.json` and `result.png` plus valid PNG signature and parseable `createdAt`.
- `zb output` may open a validated image but must not create/modify/delete result files.
- Existing controller execution behavior and existing tests must remain unchanged.
- No new runtime dependency may be added.

---

## File Structure

Create:

- `agent-controller/src/zb_local_controller/owner_snapshot.py` — strict parser/model for `ZB_OWNER_VIEW_V0` comments and stale detection.
- `agent-controller/src/zb_local_controller/owner_output.py` — read-only result discovery, hash validation and Windows open helper.
- `agent-controller/src/zb_local_controller/console.py` — CLI command parsing, data collection and human-view rendering.
- `agent-controller/scripts/install-zb-console.ps1` — one-time editable install and command verification.
- `agent-controller/tests/test_owner_snapshot.py` — parser/stale/fallback tests.
- `agent-controller/tests/test_owner_output.py` — local result validation/discovery tests.
- `agent-controller/tests/test_console.py` — command/render/read-only behavior tests.

Modify:

- `agent-controller/src/zb_local_controller/github_cli.py` — add one read-only issue-comment fetch method.
- `agent-controller/pyproject.toml` — register `zb` console entry point.
- `agent-controller/README.md` — owner console install/use documentation and read-only boundary.

---

### Task 1: Structured Owner Snapshot Reader

**Files:**
- Create: `agent-controller/src/zb_local_controller/owner_snapshot.py`
- Modify: `agent-controller/src/zb_local_controller/github_cli.py`
- Test: `agent-controller/tests/test_owner_snapshot.py`
- Test: `agent-controller/tests/test_github_cli.py`

**Interfaces:**
- Produces `OwnerSnapshot`, `AgentView`, `GateView`, `parse_owner_view_comments(comments, now_utc)`.
- Produces `GitHubCLI.get_issue_comments(issue_number) -> tuple[str, ...]`.
- Consumed later by `console.py`.

- [ ] **Step 1: Write failing parser tests**

Add `test_owner_snapshot.py` with fixtures that prove: valid snapshot parsing; required-key rejection; unknown agent/status rejection; malformed newest comment falls back to older valid snapshot; two-hour stale boundary.

```python
from datetime import datetime, timezone
from zb_local_controller.owner_snapshot import parse_owner_view_comments

VALID = """ZB_OWNER_VIEW_V0
UPDATED_AT = 2026-08-27T01:00:00Z
OVERALL_STATUS = WAITING
SPARX_ACTION = NONE
WHY = Duncan verdict required before Task 9.
SCOUT_LAST_CHECK = 2026-08-27T00:50:00Z
SCOUT_SUMMARY = NONE
AGENT = JINGO | WORKING | coordinates | NONE | NONE | wait for Duncan
AGENT = LESTER | WAITING | repair ready | repair complete | Duncan QC | wait
AGENT = DUNCAN | WORKING | independent QC | NONE | NONE | PASS or CHANGES_REQUIRED
AGENT = SALVADOR | WAITING | production visual | NONE | gate | model smoke
AGENT = LYNCH | WORKING | research | NONE | NONE | continue
AGENT = MAO | WORKING | performance research | NONE | NONE | report
AGENT = CHARLIE | WAITING | model board | NONE | NONE | start
AGENT = MEMORO | WAITING | truth audit | NONE | NONE | start
GATE = DUNCAN_QC | WAITING | exact candidate under review
GATE = REAL_MODEL_SMOKE | WAITING | locked until Duncan PASS
"""


def test_parses_latest_valid_snapshot():
    now = datetime(2026, 8, 27, 1, 30, tzinfo=timezone.utc)
    snapshot = parse_owner_view_comments(("noise", VALID), now)
    assert snapshot is not None
    assert snapshot.overall_status == "WAITING"
    assert snapshot.sparx_action is None
    assert snapshot.agents["LESTER"].status == "WAITING"
    assert snapshot.gates["DUNCAN_QC"].status == "WAITING"
    assert snapshot.is_stale is False


def test_malformed_newest_comment_does_not_hide_last_valid_snapshot():
    now = datetime(2026, 8, 27, 1, 30, tzinfo=timezone.utc)
    snapshot = parse_owner_view_comments((VALID, "ZB_OWNER_VIEW_V0\nUPDATED_AT = broken"), now)
    assert snapshot is not None
    assert snapshot.why == "Duncan verdict required before Task 9."


def test_snapshot_older_than_two_hours_is_stale():
    now = datetime(2026, 8, 27, 3, 0, 1, tzinfo=timezone.utc)
    snapshot = parse_owner_view_comments((VALID,), now)
    assert snapshot is not None
    assert snapshot.is_stale is True
```

- [ ] **Step 2: Run parser tests and verify failure**

Run from `agent-controller`:

```powershell
python -m pytest tests/test_owner_snapshot.py -q
```

Expected: import/module failure because `owner_snapshot.py` does not exist.

- [ ] **Step 3: Implement strict snapshot models/parser**

Implement immutable dataclasses and parser in `owner_snapshot.py`:

```python
@dataclass(frozen=True)
class AgentView:
    name: str
    status: str
    doing: str
    done: str | None
    blocker: str | None
    next: str

@dataclass(frozen=True)
class GateView:
    name: str
    status: str
    reason: str

@dataclass(frozen=True)
class OwnerSnapshot:
    updated_at: datetime
    overall_status: str
    sparx_action: str | None
    why: str
    scout_last_check: datetime | None
    scout_summary: str | None
    agents: dict[str, AgentView]
    gates: dict[str, GateView]
    is_stale: bool


def parse_owner_view_comments(comments: tuple[str, ...], now_utc: datetime) -> OwnerSnapshot | None:
    ...
```

Parser rules must exactly implement the spec: marker first; exact required scalar keys; allowed statuses; allowed agent names; `NONE` -> `None`; ISO UTC parse; iterate comments newest-to-oldest and return first valid snapshot; stale when `now_utc - updated_at > timedelta(hours=2)`.

- [ ] **Step 4: Add failing GitHub read-method tests**

Extend `tests/test_github_cli.py` with a fake runner expectation for:

```text
gh issue view 39 --repo Lester-Sparx/zorr-blatt-shared-hq --json comments
```

and JSON output:

```json
{"comments":[{"body":"one"},{"body":"two"}]}
```

Assert `get_issue_comments(39) == ("one", "two")`. Add failures for invalid JSON and non-zero return code.

- [ ] **Step 5: Implement `GitHubCLI.get_issue_comments`**

Add only the read method; do not change `post_comment` or candidate-task behavior.

```python
def get_issue_comments(self, issue_number: int) -> tuple[str, ...]:
    self.ensure_authenticated()
    args = [
        "gh", "issue", "view", str(int(issue_number)),
        "--repo", self.repository,
        "--json", "comments",
    ]
    result = self._runner(args, capture_output=True, text=True, shell=False)
    if result.returncode != 0:
        raise GitHubCLIError("GH_READ_FAILED")
    try:
        raw = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise GitHubCLIError("GH_OUTPUT_INVALID") from exc
    return tuple(str(item.get("body") or "") for item in raw.get("comments") or [])
```

- [ ] **Step 6: Run focused tests**

```powershell
python -m pytest tests/test_owner_snapshot.py tests/test_github_cli.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/zb_local_controller/owner_snapshot.py src/zb_local_controller/github_cli.py tests/test_owner_snapshot.py tests/test_github_cli.py
git commit -m "feat: add structured owner snapshot reader"
```

---

### Task 2: Validated Local Output Discovery

**Files:**
- Create: `agent-controller/src/zb_local_controller/owner_output.py`
- Test: `agent-controller/tests/test_owner_output.py`

**Interfaces:**
- Produces `OutputView`.
- Produces `find_latest_valid_output(result_root: Path) -> OutputView | None`.
- Produces `open_output(path: Path) -> None`.
- Consumed later by `console.py`.

- [ ] **Step 1: Write failing local-output tests**

Create temporary task folders with `result.png` and `result.json`. Use a minimal valid PNG byte fixture beginning with `b"\x89PNG\r\n\x1a\n"` and deterministic payload bytes.

Required tests:

```python
def test_latest_valid_output_uses_created_at(tmp_path): ...
def test_hash_mismatch_is_ignored(tmp_path): ...
def test_wrong_task_id_is_ignored(tmp_path): ...
def test_non_result_ready_is_ignored(tmp_path): ...
def test_bad_png_signature_is_ignored(tmp_path): ...
def test_invalid_newest_falls_back_to_older_valid(tmp_path): ...
```

Expected `OutputView` fields:

```python
@dataclass(frozen=True)
class OutputView:
    task_id: str
    agent: str
    state: str
    created_at: datetime
    sha256: str
    path: Path
    execution_id: str | None
```

- [ ] **Step 2: Run and verify failure**

```powershell
python -m pytest tests/test_owner_output.py -q
```

Expected: module import failure.

- [ ] **Step 3: Implement validator/discovery**

Scan only direct task directories beneath `result_root`; never follow a result path outside the root. Validate exact metadata/hash/signature rules from the spec. Parse `createdAt` as UTC-aware datetime. Ignore malformed candidates and choose max valid `created_at`.

Implement Windows opener:

```python
def open_output(path: Path) -> None:
    if os.name != "nt" or not hasattr(os, "startfile"):
        raise RuntimeError("OUTPUT_OPEN_UNSUPPORTED")
    os.startfile(str(path))
```

Do not call this function during discovery.

- [ ] **Step 4: Add opener injection test**

Do not execute the real Windows viewer in tests. Test `console.py` later through an injected opener; here only verify invalid/missing path is rejected before any open attempt if validation helper is called.

- [ ] **Step 5: Run focused tests**

```powershell
python -m pytest tests/test_owner_output.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/zb_local_controller/owner_output.py tests/test_owner_output.py
git commit -m "feat: add validated owner output discovery"
```

---

### Task 3: Read-only `zb` CLI and Human-View Renderer

**Files:**
- Create: `agent-controller/src/zb_local_controller/console.py`
- Test: `agent-controller/tests/test_console.py`

**Interfaces:**
- Consumes `GitHubCLI.get_issue_comments(39)`.
- Consumes `parse_owner_view_comments(...)`.
- Consumes `find_latest_valid_output(...)` and `open_output(...)`.
- Produces `main(argv=None, *, github_factory=GitHubCLI, now_factory=..., sleeper=time.sleep, opener=open_output) -> int`.

- [ ] **Step 1: Write failing full-status render test**

Use a fake GitHub object returning a valid snapshot and a temp valid local output. Capture stdout.

Assert default `main([])` contains in order:

```text
SPARX CONTROL
AGENTS
GATES
LAST REAL OUTPUT
SCOUT
WHY WAITING
```

Also assert it contains `SPARX ACTION: NOTHING NEEDED`, `LESTER`, `DUNCAN_QC`, task id and real output path.

- [ ] **Step 2: Write failing subcommand tests**

Add tests for:

```text
zb why
zb agents
zb gates
zb scout
zb output
```

`zb output` must call an injected opener exactly once with the validated path. With no valid output it must print `NO VALID OUTPUT FOUND`, not call opener, and return non-zero.

- [ ] **Step 3: Write failure/degraded-mode tests**

Fake `GitHubConfigurationError("GH_CLI_UNAVAILABLE")`, `GitHubConfigurationError("GH_NOT_AUTHENTICATED")`, and `GitHubCLIError("GH_READ_FAILED")`. In every case, if a valid local result exists, assert output metadata is still shown while remote fields say `UNKNOWN` and the error appears only in a short details line.

- [ ] **Step 4: Implement parser and renderer**

`argparse` command grammar:

```text
zb [watch|why|agents|gates|scout|output] [--config PATH]
```

Use `ControllerConfig` / `load_config` only to obtain repository and `result_root`; do not instantiate `Controller` or a ComfyUI backend.

Default output is ASCII-safe. Do not depend on emoji or ANSI color support for correctness. Example header:

```text
+================ ZORR BLATT STUDIO ================+
| STATUS: WAITING                                    |
| SPARX ACTION: NOTHING NEEDED                       |
+====================================================+
```

Each agent renders as a compact block with name, status, doing, blocker and next. `UNKNOWN` remote state remains explicit.

- [ ] **Step 5: Implement `watch` without writes**

Factor `render_once(...)` separately. `watch` loops:

```python
while True:
    clear_console()
    render_once(...)
    sleeper(10.0)
```

Catch `KeyboardInterrupt` and return `0`. In tests inject a sleeper that raises `KeyboardInterrupt` after first refresh. Assert GitHub fake exposes no write call and local fixture mtimes/content are unchanged.

- [ ] **Step 6: Run console tests**

```powershell
python -m pytest tests/test_console.py -q
```

Expected: PASS.

- [ ] **Step 7: Run all new feature tests together**

```powershell
python -m pytest tests/test_owner_snapshot.py tests/test_owner_output.py tests/test_console.py tests/test_github_cli.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add src/zb_local_controller/console.py tests/test_console.py
git commit -m "feat: add read-only ZB owner console"
```

---

### Task 4: `zb` Command Installation and Documentation

**Files:**
- Modify: `agent-controller/pyproject.toml`
- Create: `agent-controller/scripts/install-zb-console.ps1`
- Modify: `agent-controller/README.md`
- Test: `agent-controller/tests/test_console.py`

**Interfaces:**
- Produces project script `zb = zb_local_controller.console:main`.
- Produces one-time installer that performs editable local install and verifies command availability.

- [ ] **Step 1: Add failing metadata assertion**

Extend `test_console.py` to read `pyproject.toml` with `tomllib` and assert:

```python
assert data["project"]["scripts"]["zb"] == "zb_local_controller.console:main"
```

- [ ] **Step 2: Run test and verify failure**

```powershell
python -m pytest tests/test_console.py -q
```

Expected: FAIL because `[project.scripts]` is missing.

- [ ] **Step 3: Add entry point**

Modify `pyproject.toml`:

```toml
[project.scripts]
zb = "zb_local_controller.console:main"
```

No dependency changes.

- [ ] **Step 4: Add installer script**

`install-zb-console.ps1` must:

```powershell
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
python -m pip install -e $repo
$cmd = Get-Command zb -ErrorAction Stop
& zb --help | Out-Null
Write-Host "ZB_CONSOLE_READY = $($cmd.Source)"
```

It must not request admin rights, edit execution policy, start the controller, start ComfyUI, download a model, or alter PowerShell profile.

- [ ] **Step 5: Update README with exact owner workflow**

Document:

```powershell
cd D:\BLATT2\zb-local-agent-controller
powershell -ExecutionPolicy Bypass -File .\scripts\install-zb-console.ps1
zb
zb why
zb output
zb watch
```

Also document that v0 is read-only and `zb output` only opens a hash-validated result.

- [ ] **Step 6: Run tests**

```powershell
python -m pytest tests/test_console.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add pyproject.toml scripts/install-zb-console.ps1 README.md tests/test_console.py
git commit -m "feat: expose zb PowerShell owner command"
```

---

### Task 5: Regression and Read-only Gate

**Files:**
- Test: all `agent-controller/tests/*.py`
- No production code changes unless a failing test reveals a defect in Tasks 1–4.

**Interfaces:**
- Produces exact candidate evidence for DUNCAN.

- [ ] **Step 1: Run complete controller suite**

```powershell
python -m pytest -q
```

Expected: every pre-existing controller test plus all new console tests PASS.

- [ ] **Step 2: Run compile check**

```powershell
python -m compileall -q src tests
```

Expected: exit 0.

- [ ] **Step 3: Run local read-only smoke with GitHub available**

```powershell
zb
zb agents
zb gates
zb scout
zb why
```

Expected: only reads; no new GitHub comments, controller submissions, or result-file changes.

- [ ] **Step 4: Run local output smoke**

```powershell
zb output
```

Expected: opens the latest validated `result.png`; output path and hash displayed first. For the current disposable smoke, it may open the black/white test image and must not label it production-approved.

- [ ] **Step 5: Verify no write-capable command surface**

```powershell
zb approve
zb run
zb submit
```

Expected: argparse error / unsupported command; no side effects.

- [ ] **Step 6: Capture exact candidate evidence**

Record candidate HEAD, full pytest count/result, compile result, `zb` smoke output and confirmation that GitHub issue/comment count did not change during read-only smoke.

- [ ] **Step 7: Commit only if verification required test/document correction**

If no files changed, do not create an empty commit.

- [ ] **Step 8: Handoff to DUNCAN**

Required handoff:

```text
LESTER_ZB_CONSOLE_V0_READY
HEAD = <exact sha>
FULL_TESTS = <count> PASS
COMPILE = PASS
READ_ONLY_SMOKE = PASS
OUTPUT_OPEN_SMOKE = PASS
WRITE_COMMANDS = ABSENT
NEXT = DUNCAN INDEPENDENT QC
```

No merge, production activation, or OWNER LOCK is authorized by implementation completion.

---

## Plan Self-Review

- Spec coverage: commands, snapshot source, stale/unknown behavior, output hash validation, degraded GitHub mode, read-only boundary, installation and QC are each assigned to explicit tasks.
- Placeholder scan: no `TBD`, `TODO`, `implement later`, or unspecified test steps remain.
- Type consistency: `OwnerSnapshot`, `AgentView`, `GateView`, `OutputView`, `GitHubCLI.get_issue_comments`, `parse_owner_view_comments`, `find_latest_valid_output`, `open_output` and `console.main` names are consistent across tasks.
- Scope: one subsystem only — read-only owner console. Web UI and write actions remain non-goals.