# ZORR REFERENCE BRIDGE V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a separate, restart-safe local Reference Bridge process that validates one Google-Drive-synced image delivery against a durable GitHub `ZB_REFERENCE_DELIVERY_V1` event and atomically publishes the verified image into `D:\BLATT2\ZB_AGENT_INBOX\<TASK_ID>\` without modifying Controller Daemon v1.

**Architecture:** GitHub remains the task/control/evidence plane; Google Drive carries image bytes only. A new sibling Python package `zb_reference_bridge` runs independently from `zb_local_controller`, reuses the existing task parser semantics, validates delivery metadata + local bytes, journals acceptance/rejection, stages on `D:`, atomically publishes to the existing inbox, and posts only `ZB_REFERENCE_EVENT_V1` transport-result comments. Controller Daemon v1 stays byte-for-byte untouched.

**Tech Stack:** Python 3.12+, stdlib (`dataclasses`, `hashlib`, `json`, `pathlib`, `os`, `shutil`, `subprocess`, `time`, `uuid`, `logging`), existing `gh` CLI authentication, pytest 8+, Windows Task Scheduler PowerShell deployment. No new paid service or Python runtime dependency.

**Spec:** `docs/superpowers/specs/2026-08-27-zorr-reference-bridge-v1-design.md` at exact `d18a5c40bd64127fe0d81876c1e9d7b134fd360c` on branch `docs/zorr-reference-bridge-v1-design`.

## Global Constraints

- Implementation branch MUST start from Controller Daemon production exact `9e2ccfbaca88a95eac2e119e5eac720f9074dd35`.
- Do not modify any existing file under `agent-controller/src/zb_local_controller/`.
- Do not modify SALVADOR model/workflow/prompt/denoise/dimensions.
- Do not modify Controller Daemon deployment/runtime/config.
- Google Drive is byte transport only; GitHub issue body remains task authority.
- V1 accepts exactly one image per `TASK_ID`.
- Supported extensions remain `.png`, `.jpg`, `.jpeg`, `.webp`; source must be non-empty and <= 20 MiB.
- `UPLOAD_COMPLETE != LOCAL_REFERENCE_READY`.
- `REFERENCE_EVENT != AGENT_EVENT`; bridge code MUST NOT write `ZB_AGENT_EVENT_V0`.
- Destination derives only from validated `TASK_ID`; Drive/GitHub filenames never supply a destination path.
- Hard validation conflicts fail closed; no automatic overwrite/delete of an accepted inbox reference.
- Google Drive Desktop installation is NOT part of implementation tasks; it is an owner-PC post-QC setup/smoke gate.
- Every behavior change uses TDD: RED must execute and fail for the intended reason before GREEN implementation.
- Every task ends with focused tests and a commit.

## File Structure

Create a sibling package so Controller Daemon code remains untouched:

- `agent-controller/src/zb_reference_bridge/__init__.py` — package marker/version.
- `agent-controller/src/zb_reference_bridge/config.py` — immutable bridge config + fail-closed loader.
- `agent-controller/src/zb_reference_bridge/contracts.py` — parse/format `ZB_REFERENCE_DELIVERY_V1` and `ZB_REFERENCE_EVENT_V1`; parse terminal `ZB_AGENT_EVENT_V0` observation only.
- `agent-controller/src/zb_reference_bridge/github_cli.py` — bridge-specific read/post adapter over `gh`; imports existing `parse_task` but does not mutate controller adapter.
- `agent-controller/src/zb_reference_bridge/local_delivery.py` — safe delivery/task path derivation, full-read image validation, hash/MIME/magic checks, reparse/symlink rejection.
- `agent-controller/src/zb_reference_bridge/journal.py` — append-only JSON receipts/index and replay/conflict lookup.
- `agent-controller/src/zb_reference_bridge/publisher.py` — staging, staged re-hash, atomic publish, destination conflict checks, quarantine.
- `agent-controller/src/zb_reference_bridge/bridge.py` — one poll/cycle orchestration and recovery convergence.
- `agent-controller/src/zb_reference_bridge/instance_lock.py` — bridge-only OS process lock and distinct error codes.
- `agent-controller/src/zb_reference_bridge/health.py` — atomic health JSON + bounded rotating logs.
- `agent-controller/src/zb_reference_bridge/runner.py` — preflight + polling loop.
- `agent-controller/src/zb_reference_bridge/__main__.py` — CLI modes `--once`, `--daemon`, `--preflight`, `--status`.
- `agent-controller/reference-bridge.config.example.json` — documented non-production sample config.
- `agent-controller/deploy/windows/ZbReferenceBridge.ps1` — current-user Task Scheduler install/start/stop/restart/status/enable/disable/uninstall.
- `agent-controller/README.md` — additive Reference Bridge usage/authority section only.

Tests:

- `agent-controller/tests/test_reference_bridge_config.py`
- `agent-controller/tests/test_reference_bridge_contracts.py`
- `agent-controller/tests/test_reference_bridge_github_cli.py`
- `agent-controller/tests/test_reference_bridge_local_delivery.py`
- `agent-controller/tests/test_reference_bridge_journal.py`
- `agent-controller/tests/test_reference_bridge_publisher.py`
- `agent-controller/tests/test_reference_bridge.py`
- `agent-controller/tests/test_reference_bridge_lock.py`
- `agent-controller/tests/test_reference_bridge_health.py`
- `agent-controller/tests/test_reference_bridge_runner.py`
- `agent-controller/tests/test_reference_bridge_cli.py`
- `agent-controller/tests/test_reference_bridge_windows_deploy.py`

---

### Task 1: Config + durable event contracts

**Files:**
- Create: `agent-controller/src/zb_reference_bridge/__init__.py`
- Create: `agent-controller/src/zb_reference_bridge/config.py`
- Create: `agent-controller/src/zb_reference_bridge/contracts.py`
- Test: `agent-controller/tests/test_reference_bridge_config.py`
- Test: `agent-controller/tests/test_reference_bridge_contracts.py`

**Interfaces:**
- Produces: `BridgeConfig`, `load_bridge_config(path: Path) -> BridgeConfig`.
- Produces: `ReferenceDelivery`, `ReferenceEvent`, `parse_delivery_event(body: str) -> ReferenceDelivery | None`, `format_reference_ready(...) -> str`, `format_reference_failed(...) -> str`, `latest_agent_terminal_state(comments: tuple[str, ...], task_id: str) -> str | None`.

- [ ] **Step 1: Write RED contract/config tests**

```python
from pathlib import Path
import json
import pytest
from zb_reference_bridge.config import load_bridge_config, BridgeConfigError
from zb_reference_bridge.contracts import parse_delivery_event


def test_load_bridge_config_requires_drive_sync_root(tmp_path: Path):
    p = tmp_path / "bridge.json"
    p.write_text(json.dumps({"repository": "Lester-Sparx/zorr-blatt-shared-hq"}), encoding="utf-8")
    with pytest.raises(BridgeConfigError) as exc:
        load_bridge_config(p)
    assert exc.value.code == "BRIDGE_CONFIG_INVALID"


def test_parse_delivery_event_accepts_canonical_schema():
    body = """ZB_REFERENCE_DELIVERY_V1
TASK_ID = ZB-REF-001
DELIVERY_ID = DELIV-001
DRIVE_FOLDER_ID = folder123
DRIVE_FILE_ID = file123
SOURCE_FILE_NAME = source.png
SIZE_BYTES = 8
SOURCE_SHA256 = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
MIME_TYPE = image/png
SOURCE_STATUS = OWNER_PROVIDED_REFERENCE
TRANSPORT = GOOGLE_DRIVE"""
    d = parse_delivery_event(body)
    assert d and d.task_id == "ZB-REF-001" and d.delivery_id == "DELIV-001"
```

- [ ] **Step 2: Run RED**

Run from `agent-controller/`:

```bash
python -m pytest -q tests/test_reference_bridge_config.py tests/test_reference_bridge_contracts.py
```

Expected: FAIL because `zb_reference_bridge` does not exist.

- [ ] **Step 3: Implement minimal config + strict parsers/formatters**

Required data shape:

```python
@dataclass(frozen=True)
class BridgeConfig:
    repository: str
    drive_sync_root: Path
    drive_drop_folder_id: str
    inbox_root: Path = Path(r"D:\BLATT2\ZB_AGENT_INBOX")
    runtime_root: Path = Path(r"D:\BLATT2\ZB_AGENT_RUNTIME\reference-bridge")
    quarantine_root: Path = Path(r"D:\BLATT2\ZB_REFERENCE_QUARANTINE")
    poll_interval_seconds: float = 5.0
    cloud_retry_timeout_seconds: float = 300.0
    max_source_bytes: int = 20 * 1024 * 1024
```

`load_bridge_config` must reject unknown keys, missing/empty `driveSyncRoot` or `driveDropFolderId`, non-positive polling/retry values, and any `maxSourceBytes` value other than `20 * 1024 * 1024` for v1.

`parse_delivery_event` must require the exact marker and exact keys from the approved spec; malformed/duplicate/unknown fields return `None` or raise one dedicated `ReferenceContractError("REFERENCE_DELIVERY_EVENT_INVALID")`, consistently tested. `latest_agent_terminal_state` may observe only matching `ZB_AGENT_EVENT_V0` with `STATE = FAILED|RESULT_READY`.

- [ ] **Step 4: Run GREEN + regression slice**

```bash
python -m pytest -q tests/test_reference_bridge_config.py tests/test_reference_bridge_contracts.py tests/test_task_contract.py tests/test_events.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/zb_reference_bridge tests/test_reference_bridge_config.py tests/test_reference_bridge_contracts.py
git commit -m "feat: add reference bridge contracts and config"
```

---

### Task 2: Bridge GitHub discovery/evidence adapter

**Files:**
- Create: `agent-controller/src/zb_reference_bridge/github_cli.py`
- Test: `agent-controller/tests/test_reference_bridge_github_cli.py`

**Interfaces:**
- Consumes: existing `zb_local_controller.task_contract.parse_task` and `AgentTask` without modifying them.
- Produces: `BridgeIssue(number, title, body, comments)`, `BridgeGitHubCLI.list_task_issues()`, `BridgeGitHubCLI.post_reference_event(issue_number, body)`.

- [ ] **Step 1: Write RED tests for authenticated list/post and fail-closed output parsing**

```python
def test_list_task_issues_uses_open_task_search_and_comments(fake_runner):
    gh = BridgeGitHubCLI("Lester-Sparx/zorr-blatt-shared-hq", runner=fake_runner)
    issues = gh.list_task_issues()
    assert issues[0].number == 92
    assert "ZB_AGENT_TASK_V0" in issues[0].body
```

Also assert command includes `--state open`, `--search ZB_AGENT_TASK_V0`, `--limit 1000`, and `--json number,title,body,comments`; invalid JSON => `BRIDGE_GH_OUTPUT_INVALID`; failed list => `BRIDGE_GH_ISSUE_LIST_FAILED`; failed comment => `BRIDGE_GH_COMMENT_FAILED`.

- [ ] **Step 2: Run RED**

```bash
python -m pytest -q tests/test_reference_bridge_github_cli.py
```

Expected: FAIL because adapter is absent.

- [ ] **Step 3: Implement bridge-only `gh` adapter**

Use `subprocess.run(..., capture_output=True, text=True, shell=False)` and `gh auth status` preflight. Do not edit `zb_local_controller/github_cli.py`.

- [ ] **Step 4: Run GREEN + existing GitHub adapter regression**

```bash
python -m pytest -q tests/test_reference_bridge_github_cli.py tests/test_github_cli.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/zb_reference_bridge/github_cli.py tests/test_reference_bridge_github_cli.py
git commit -m "feat: add reference bridge github adapter"
```

---

### Task 3: Local Drive delivery validation

**Files:**
- Create: `agent-controller/src/zb_reference_bridge/local_delivery.py`
- Test: `agent-controller/tests/test_reference_bridge_local_delivery.py`

**Interfaces:**
- Produces: `ValidatedSource(path: Path, size_bytes: int, sha256: str, extension: str, mime_type: str)`.
- Produces: `validate_delivery_source(config: BridgeConfig, delivery: ReferenceDelivery) -> ValidatedSource | None`; `None` means transient/not-yet-readable only.
- Hard failures raise `ReferenceValidationError(code)`.

- [ ] **Step 1: Write RED tests covering safe path, full read, byte count/hash/magic/MIME, count, and traversal/reparse rejection**

```python
def test_hash_mismatch_fails_closed(tmp_path, config, delivery):
    folder = config.drive_sync_root / delivery.delivery_id
    folder.mkdir(parents=True)
    (folder / "source.png").write_bytes(b"\x89PNG\r\n\x1a\nwrong")
    with pytest.raises(ReferenceValidationError) as exc:
        validate_delivery_source(config, delivery)
    assert exc.value.code == "REFERENCE_HASH_MISMATCH"
```

Required test matrix: invalid delivery ID traversal, absent folder => `None`, absent/not-readable file => `None`, extra image => `REFERENCE_SOURCE_COUNT_INVALID`, >20 MiB => `REFERENCE_TOO_LARGE`, extension/magic mismatch, MIME mismatch, size mismatch, hash mismatch, symlink/reparse escape, canonical PNG/JPEG/WEBP success.

- [ ] **Step 2: Run RED**

```bash
python -m pytest -q tests/test_reference_bridge_local_delivery.py
```

Expected: FAIL.

- [ ] **Step 3: Implement validator**

Safe delivery grammar for v1:

```python
_DELIVERY_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
```

Build local folder only as `config.drive_sync_root / delivery.delivery_id`. Reject symlinks; on Windows also reject reparse-point escapes using `os.lstat`/file attributes where available. Read the entire file before hash validation. Never trust `SOURCE_FILE_NAME` as a path; require `Path(name).name == name` and exact basename match.

- [ ] **Step 4: Run GREEN**

```bash
python -m pytest -q tests/test_reference_bridge_local_delivery.py tests/test_local_paths.py
```

Expected: PASS; existing Controller local path tests unchanged.

- [ ] **Step 5: Commit**

```bash
git add src/zb_reference_bridge/local_delivery.py tests/test_reference_bridge_local_delivery.py
git commit -m "feat: validate synced reference deliveries"
```

---

### Task 4: Append-only journal, atomic publisher, quarantine

**Files:**
- Create: `agent-controller/src/zb_reference_bridge/journal.py`
- Create: `agent-controller/src/zb_reference_bridge/publisher.py`
- Test: `agent-controller/tests/test_reference_bridge_journal.py`
- Test: `agent-controller/tests/test_reference_bridge_publisher.py`

**Interfaces:**
- Produces: `DeliveryReceipt(delivery_id, task_id, source_sha256, state, issue_number, created_at_utc, error_code=None)`.
- Produces: `ReferenceJournal.lookup_delivery(delivery_id)`, `lookup_task(task_id)`, `append(receipt)`.
- Produces: `publish_reference(config, delivery, source) -> PublishResult(state: "PUBLISHED"|"ALREADY_PRESENT", final_path: Path)`.
- Produces: `quarantine_delivery(config, delivery, source_path, error_code) -> Path`.

- [ ] **Step 1: Write RED tests for append-only identity and crash-safe publish**

```python
def test_existing_conflicting_task_reference_is_never_overwritten(config, delivery, source):
    final = config.inbox_root / delivery.task_id
    final.mkdir(parents=True)
    (final / "source.png").write_bytes(b"different")
    with pytest.raises(PublishError) as exc:
        publish_reference(config, delivery, source)
    assert exc.value.code == "REFERENCE_DESTINATION_CONFLICT"
```

Also test: atomic temp receipt + `os.replace`, same delivery changed hash => conflict, same task changed hash => conflict, same task same hash under new delivery => idempotent, stage re-hash mismatch => failure, final folder absent => atomic rename, crash-recovery case where final already contains exact source but journal is missing => `ALREADY_PRESENT`.

- [ ] **Step 2: Run RED**

```bash
python -m pytest -q tests/test_reference_bridge_journal.py tests/test_reference_bridge_publisher.py
```

Expected: FAIL.

- [ ] **Step 3: Implement journal/publisher**

Journal storage: one immutable JSON receipt per delivery under `runtime_root/receipts/<DELIVERY_ID>.json`, written to `.tmp` then `os.replace`; an in-memory index is rebuilt from receipts at startup. Never rewrite an existing receipt with different identity.

Publisher stages to `runtime_root/staging/<DELIVERY_ID>-<uuid>/source.<ext>` on `D:`, verifies staged SHA again, then `os.replace(staging_task_dir, inbox_root / task_id)` only when destination is absent. If exact accepted bytes are already present, return `ALREADY_PRESENT`; conflicting destination never mutates.

- [ ] **Step 4: Run GREEN**

```bash
python -m pytest -q tests/test_reference_bridge_journal.py tests/test_reference_bridge_publisher.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/zb_reference_bridge/journal.py src/zb_reference_bridge/publisher.py tests/test_reference_bridge_journal.py tests/test_reference_bridge_publisher.py
git commit -m "feat: add atomic reference publishing and receipts"
```

---

### Task 5: Bridge cycle orchestration + durable reference events

**Files:**
- Create: `agent-controller/src/zb_reference_bridge/bridge.py`
- Test: `agent-controller/tests/test_reference_bridge.py`

**Interfaces:**
- Consumes Tasks 1-4.
- Produces: `BridgeCycleSummary(discovered, waiting, accepted, rejected, skipped)`.
- Produces: `ReferenceBridge.run_once() -> BridgeCycleSummary`.

- [ ] **Step 1: Write RED end-to-end unit tests with fake GitHub + temp Drive/inbox/runtime roots**

```python
def test_valid_delivery_publishes_then_posts_reference_ready(bridge_fixture):
    summary = bridge_fixture.bridge.run_once()
    assert summary.accepted == 1
    assert (bridge_fixture.inbox / "ZB-REF-001" / "source.png").is_file()
    assert "STATE = REFERENCE_READY" in bridge_fixture.github.posted[-1]
```

Required scenarios: no delivery event => skip; event but Drive folder absent => waiting/no comment; terminal `ZB_AGENT_EVENT_V0` => `REFERENCE_TASK_TERMINAL`; task ID mismatch => fail closed; valid publish => ready event only after final file exists; hard validation failure => quarantine + failed event; GitHub ready-post failure after publish => local receipt remains and next cycle retries event without re-publishing; exact replay => idempotent; conflicting replay => failed event/quarantine.

- [ ] **Step 2: Run RED**

```bash
python -m pytest -q tests/test_reference_bridge.py
```

Expected: FAIL.

- [ ] **Step 3: Implement orchestration**

For each open valid task issue: parse task using existing `parse_task`; reject non-`LOCAL_INBOX`; parse delivery comments; process unfinalized deliveries; observe terminal agent state; validate source; publish; append receipt; post `ZB_REFERENCE_EVENT_V1`. Keep transport state entirely separate from controller execution state.

Recovery invariant: if final inbox exact source exists but ready event is absent, treat local publish as accepted data-plane truth, rebuild/retain receipt, and retry only the reference event.

- [ ] **Step 4: Run GREEN + controller regression**

```bash
python -m pytest -q tests/test_reference_bridge.py tests/test_controller.py tests/test_task_contract.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/zb_reference_bridge/bridge.py tests/test_reference_bridge.py
git commit -m "feat: orchestrate validated reference delivery"
```

---

### Task 6: Bridge-only lock, health, runner, preflight

**Files:**
- Create: `agent-controller/src/zb_reference_bridge/instance_lock.py`
- Create: `agent-controller/src/zb_reference_bridge/health.py`
- Create: `agent-controller/src/zb_reference_bridge/runner.py`
- Test: `agent-controller/tests/test_reference_bridge_lock.py`
- Test: `agent-controller/tests/test_reference_bridge_health.py`
- Test: `agent-controller/tests/test_reference_bridge_runner.py`

**Interfaces:**
- Produces: `BridgeInstanceLock(runtime_root)` with `REFERENCE_BRIDGE_INSTANCE_BUSY` and `REFERENCE_BRIDGE_RUNTIME_UNWRITABLE`.
- Produces: atomic `health.json` schema `zb-reference-bridge-v1`.
- Produces: `run_preflight(config, github)`, `run_bridge_forever(bridge, config, health, sleep=time.sleep)`.

- [ ] **Step 1: Write RED tests**

Test second bridge lock fails; invalid runtime root has distinct code; health write is atomic; preflight checks GitHub auth + Drive root + inbox/runtime/quarantine writability without moving source files; loop heartbeat updates and maps transient scan exceptions to `DEGRADED`, unrecoverable startup failures to `FATAL`, Ctrl+C to `STOPPING`.

- [ ] **Step 2: Run RED**

```bash
python -m pytest -q tests/test_reference_bridge_lock.py tests/test_reference_bridge_health.py tests/test_reference_bridge_runner.py
```

Expected: FAIL.

- [ ] **Step 3: Implement minimal lifecycle components**

Health minimum fields:

```json
{
  "schema": "zb-reference-bridge-v1",
  "pid": 123,
  "instanceId": "uuid",
  "state": "HEALTHY",
  "heartbeatUtc": "2026-08-27T00:00:00Z",
  "configSha256": "...",
  "driveRootReachable": true,
  "githubReachable": true,
  "lastPollUtc": "...",
  "acceptedCount": 0,
  "rejectedCount": 0,
  "lastErrorCode": null
}
```

Logs use `logging.handlers.RotatingFileHandler`, `maxBytes=1_048_576`, `backupCount=5`.

- [ ] **Step 4: Run GREEN**

```bash
python -m pytest -q tests/test_reference_bridge_lock.py tests/test_reference_bridge_health.py tests/test_reference_bridge_runner.py tests/test_daemon_health.py tests/test_daemon_runner.py tests/test_instance_lock.py
```

Expected: PASS; daemon lifecycle regressions unchanged.

- [ ] **Step 5: Commit**

```bash
git add src/zb_reference_bridge/instance_lock.py src/zb_reference_bridge/health.py src/zb_reference_bridge/runner.py tests/test_reference_bridge_lock.py tests/test_reference_bridge_health.py tests/test_reference_bridge_runner.py
git commit -m "feat: add reference bridge runtime lifecycle"
```

---

### Task 7: CLI + Windows Task Scheduler deployment

**Files:**
- Create: `agent-controller/src/zb_reference_bridge/__main__.py`
- Create: `agent-controller/deploy/windows/ZbReferenceBridge.ps1`
- Test: `agent-controller/tests/test_reference_bridge_cli.py`
- Test: `agent-controller/tests/test_reference_bridge_windows_deploy.py`

**Interfaces:**
- CLI: `python -m zb_reference_bridge --config <path> --once|--daemon|--preflight|--status`.
- PowerShell actions: `Install|Uninstall|Status|Start|Stop|Restart|Enable|Disable`.
- Scheduled task name: `ZB Reference Bridge v1`.

- [ ] **Step 1: Write RED CLI/deployment tests**

CLI tests assert exactly one processing mode, preflight is non-mutating, lock acquired before task discovery in `--once/--daemon`, busy exits non-zero with `REFERENCE_BRIDGE_INSTANCE_BUSY`, status rejects malformed/stale health fail-closed.

Static PowerShell test must assert: current-user `AtLogOn`, `Interactive`, `Limited`, `IgnoreNew`, `StartWhenAvailable`, restart count 5, restart interval 1 minute, execution time limit disabled, exact action `python -m zb_reference_bridge --daemon --config ...`, and separate task name from Controller Daemon.

- [ ] **Step 2: Run RED**

```bash
python -m pytest -q tests/test_reference_bridge_cli.py tests/test_reference_bridge_windows_deploy.py
```

Expected: FAIL.

- [ ] **Step 3: Implement CLI and deployment script**

Install order: resolve paths -> `--preflight` -> register scheduled task -> start scheduled task. Status must report at least `TASK_REGISTERED`, `TASK_ENABLED`, `TASK_STATE`, `HEALTH_STATE`, `PID`, `PID_ALIVE`, `INSTANCE_ID`, `HEARTBEAT_AGE_SEC`, `CONFIG_SHA256`, `DRIVE_ROOT_REACHABLE`.

Uninstall performs bounded stop then unregister only the Reference Bridge task; it must never stop/uninstall `ZB Controller Daemon v1`.

- [ ] **Step 4: Run GREEN + daemon deployment regression**

```bash
python -m pytest -q tests/test_reference_bridge_cli.py tests/test_reference_bridge_windows_deploy.py tests/test_cli.py tests/test_windows_deploy.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/zb_reference_bridge/__main__.py deploy/windows/ZbReferenceBridge.ps1 tests/test_reference_bridge_cli.py tests/test_reference_bridge_windows_deploy.py
git commit -m "feat: deploy reference bridge daemon"
```

---

### Task 8: Example config, docs, full verification, implementation handoff

**Files:**
- Create: `agent-controller/reference-bridge.config.example.json`
- Modify: `agent-controller/README.md`
- Test: all tests.

**Interfaces:**
- Produces operator documentation only; no production config is created or activated.

- [ ] **Step 1: Add sample config and README authority/operations section**

Sample config must be explicitly non-production:

```json
{
  "repository": "Lester-Sparx/zorr-blatt-shared-hq",
  "driveSyncRoot": "G:\\My Drive\\ZORR_REFERENCE_DROP",
  "driveDropFolderId": "EXAMPLE_FOLDER_ID_NOT_PRODUCTION",
  "inboxRoot": "D:\\BLATT2\\ZB_AGENT_INBOX",
  "runtimeRoot": "D:\\BLATT2\\ZB_AGENT_RUNTIME\\reference-bridge",
  "quarantineRoot": "D:\\BLATT2\\ZB_REFERENCE_QUARANTINE",
  "pollIntervalSeconds": 5,
  "cloudRetryTimeoutSeconds": 300,
  "maxSourceBytes": 20971520
}
```

README must state: Drive Desktop is required later on owner PC; exact sync root/folder ID are discovered during the post-QC setup gate; cloud upload alone is not readiness; Controller Daemon remains independent.

- [ ] **Step 2: Run focused Reference Bridge suite**

```bash
python -m pytest -q tests/test_reference_bridge_config.py tests/test_reference_bridge_contracts.py tests/test_reference_bridge_github_cli.py tests/test_reference_bridge_local_delivery.py tests/test_reference_bridge_journal.py tests/test_reference_bridge_publisher.py tests/test_reference_bridge.py tests/test_reference_bridge_lock.py tests/test_reference_bridge_health.py tests/test_reference_bridge_runner.py tests/test_reference_bridge_cli.py tests/test_reference_bridge_windows_deploy.py
```

Expected: all PASS.

- [ ] **Step 3: Run full regression + compile**

```bash
python -m pytest -q
python -m compileall -q src
```

Expected: all tests PASS; compile returns 0.

- [ ] **Step 4: Scope verification**

Run:

```bash
git diff --name-only 9e2ccfbaca88a95eac2e119e5eac720f9074dd35...HEAD
```

Required: no changed path under `agent-controller/src/zb_local_controller/`; no SALVADOR prompt/workflow/model config changes; only Reference Bridge package/tests/deploy/docs/example config plus the plan/spec documentation branch artifacts when intentionally carried.

- [ ] **Step 5: Commit docs and produce handoff**

```bash
git add README.md reference-bridge.config.example.json
git commit -m "docs: document reference bridge v1"
```

Implementation-ready handoff format:

```text
LESTER_REFERENCE_BRIDGE_V1_IMPLEMENTATION_READY
EXACT_HEAD = <implementation sha>
BRANCH = agent-controller/reference-bridge-v1-implementation
BASE = 9e2ccfbaca88a95eac2e119e5eac720f9074dd35
SPEC_HEAD = d18a5c40bd64127fe0d81876c1e9d7b134fd360c
PLAN_HEAD = <exact plan sha>
TASKS_1_8 = COMPLETE
REFERENCE_BRIDGE_TESTS = <exact pytest result>
FULL_TESTS = <exact pytest result>
COMPILE = PASS
CONTROLLER_DAEMON_FILES_CHANGED = NO
SALVADOR_SCOPE_CHANGED = NO
GOOGLE_DRIVE_DESKTOP_INSTALLED = NO
OWNER_PC_SMOKE = NOT RUN
MERGE = NO
PRODUCTION_ACTIVATION = NO
NEXT = DUNCAN INDEPENDENT QC
```

---

## Execution / Review Gates

1. OWNER implementation authorization references exact PLAN_HEAD.
2. LESTER creates isolated worktree from exact base `9e2ccfbaca88a95eac2e119e5eac720f9074dd35` using `superpowers:using-git-worktrees`.
3. LESTER executes Tasks 1-8 with strict TDD and task-level commits using `superpowers:subagent-driven-development` (recommended).
4. LESTER runs `superpowers:verification-before-completion` before handoff.
5. DUNCAN independently QC's exact implementation HEAD; implementer self-verification cannot award independent PASS.
6. Only after DUNCAN PASS: owner-PC Google Drive Desktop official installation/sign-in + private drop folder creation + local sync-root discovery + bridge config materialization.
7. Disposable owner-PC smoke proves: producer upload -> `ZB_REFERENCE_DELIVERY_V1` -> Drive Desktop sync -> local bridge validation -> atomic inbox publish -> `REFERENCE_READY` -> existing Controller detects the reference, with no manual file copy.
8. Smoke must also prove hash mismatch/conflict fails closed and Controller Daemon remains running/unmodified.
9. OWNER production activation is a separate final decision. No merge/production activation before it.

## Plan Self-Review Result

- Spec coverage: all approved sections mapped to Tasks 1-8 or post-QC owner-PC gate.
- Placeholder scan: no `TBD`/`TODO`/unspecified implementation steps remain.
- Type/interface consistency: delivery/config/journal/publisher/orchestrator interfaces are named once and consumed consistently.
- Scope isolation: zero planned edits to `zb_local_controller`; no ComfyUI/SALVADOR/Babylon/canon scope.
- Transport feasibility repair preserved: Drive carries one image only; durable delivery manifest/commit marker is `ZB_REFERENCE_DELIVERY_V1` in GitHub.
