# ZB Controller Daemon v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the accepted ZB local controller continuously on the owner Windows PC without manual PowerShell polling, with one-instance protection, local health/log evidence, current-user Task Scheduler autostart, bounded restart, and zero change to SALVADOR production truth laws.

**Architecture:** Keep the accepted `Controller` untouched as the task-state/backend engine. Add isolated lifecycle units for OS-backed locking, health/logging, startup preflight, and the repeated daemon loop. Keep Task Scheduler installation/control in one repository-owned Windows PowerShell script; no Windows Service, no Reference Bridge, and no ComfyUI lifecycle management.

**Tech Stack:** Python 3.12+, pytest, Python standard library (`msvcrt`, POSIX `fcntl` test/dev adapter, `logging.handlers.RotatingFileHandler`, `json`, `hashlib`, `uuid`, `pathlib`), Windows PowerShell 5.1 Task Scheduler cmdlets, existing GitHub CLI and ComfyUI integration.

**Spec:** `docs/superpowers/specs/2026-08-27-zb-controller-daemon-v1-design.md`

## Global Constraints

- Approved spec HEAD: `c20126f949e6e61298d9dd76a906349a71bbcb00`.
- Accepted controller base: `425ad97c508c4f55f7d7052435a7a2cb4aa3b015`.
- Production config path for owner-PC smoke: `D:\BLATT2\ZB_AGENT_CONFIG\salvador-canon-reference-edit.json`.
- Production working directory for owner-PC smoke: `D:\BLATT2\zb-local-agent-controller\agent-controller`.
- Default daemon runtime root: `D:\BLATT2\ZB_AGENT_RUNTIME\controller-daemon`.
- Production daemon CLI: `python -m zb_local_controller --daemon --config D:\BLATT2\ZB_AGENT_CONFIG\salvador-canon-reference-edit.json`.
- `--once`, `--daemon`, and `--daemon-preflight` are mutually exclusive.
- Legacy no-flag continuous mode remains compatible but is not the production deployment command.
- `--once`, `--daemon`, and legacy no-flag processing all require the same OS-backed execution lock.
- `--daemon-preflight` does not process tasks and does not acquire the execution lock when invoked as standalone maintenance.
- Production Windows locking uses `msvcrt.locking(..., LK_NBLCK, 1)`; POSIX `fcntl.flock(..., LOCK_EX | LOCK_NB)` exists only for non-Windows test/dev equivalence.
- Existing truth remains unchanged: `ASSIGNED != RUNNING`; `RUNNING` requires a real non-empty backend execution id; `RESULT_READY` requires real bytes, checksum, and production provenance.
- SALVADOR model/profile/workflow/prompt/denoise/dimensions remain unchanged.
- No Reference Bridge, Google Drive transport, ComfyUI autostart/update, Babylon integration, canon mutation, paid service, native Windows Service, NSSM, pywin32 service, tray UI, or arbitrary PC control.
- Log bounds are fixed: `2097152` bytes, `5` backups.
- Task Scheduler name is exactly `ZB Controller Daemon v1`.
- Restart policy is exactly 1 minute, 5 restart attempts, no execution time limit.
- Current-user interactive principal, `RunLevel Limited`, no stored plaintext Windows password.
- No merge and no production activation are authorized by this plan.

---

## Planned File Structure

```text
agent-controller/
  README.md
  config.example.json
  src/zb_local_controller/
    config.py
    instance_lock.py
    daemon_health.py
    daemon_runner.py
    __main__.py
  deploy/windows/
    ZbControllerDaemon.ps1
  tests/
    test_config.py
    test_instance_lock.py
    test_daemon_health.py
    test_daemon_runner.py
    test_cli.py
    test_windows_deploy.py
```

`controller.py`, SALVADOR backends, prompts, and workflows are not modified.

---

### Task 1: Daemon runtime config + OS-backed global controller lock

**Files:**
- Modify: `agent-controller/src/zb_local_controller/config.py`
- Create: `agent-controller/src/zb_local_controller/instance_lock.py`
- Modify: `agent-controller/tests/test_config.py`
- Create: `agent-controller/tests/test_instance_lock.py`

**Interfaces:**
- Produces `ControllerConfig.daemon_runtime_root: Path`.
- Produces `ControllerInstanceBusy` with code `CONTROLLER_INSTANCE_BUSY`.
- Produces `ControllerInstanceLock(runtime_root: Path)` context manager.

- [ ] **Step 1: Write RED config tests**

Append to `tests/test_config.py`:

```python
from pathlib import Path


def test_loads_daemon_runtime_root(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"daemonRuntimeRoot": r"D:\\BLATT2\\RUNTIME\\daemon"}), encoding="utf-8")
    assert load_config(path).daemon_runtime_root == Path(r"D:\BLATT2\RUNTIME\daemon")


def test_default_daemon_runtime_root_is_locked():
    from zb_local_controller.config import ControllerConfig
    assert ControllerConfig().daemon_runtime_root == Path(r"D:\BLATT2\ZB_AGENT_RUNTIME\controller-daemon")
```

- [ ] **Step 2: Verify RED**

```powershell
python -m pytest -q tests/test_config.py
```

Expected: new tests fail because the field/key are absent.

- [ ] **Step 3: Implement config extension**

Add to `ControllerConfig`:

```python
daemon_runtime_root: Path = Path(r"D:\BLATT2\ZB_AGENT_RUNTIME\controller-daemon")
```

Add `daemonRuntimeRoot` to the strict JSON allowlist and construct:

```python
daemon_runtime_root=Path(raw.get("daemonRuntimeRoot", str(ControllerConfig.daemon_runtime_root))),
```

Do not expose log-size or scheduler-restart tuning in JSON.

- [ ] **Step 4: Write RED lock tests**

Create `tests/test_instance_lock.py`:

```python
import pytest
from zb_local_controller.instance_lock import ControllerInstanceBusy, ControllerInstanceLock


def test_first_lock_succeeds_and_concurrent_second_fails(tmp_path):
    first = ControllerInstanceLock(tmp_path)
    second = ControllerInstanceLock(tmp_path)
    first.acquire()
    try:
        with pytest.raises(ControllerInstanceBusy) as exc:
            second.acquire()
        assert exc.value.code == "CONTROLLER_INSTANCE_BUSY"
    finally:
        first.release()


def test_release_allows_later_acquisition(tmp_path):
    first = ControllerInstanceLock(tmp_path)
    first.acquire()
    first.release()
    with ControllerInstanceLock(tmp_path):
        assert (tmp_path / "controller.lock").exists()


def test_stale_file_bytes_without_os_lock_do_not_block(tmp_path):
    (tmp_path / "controller.lock").write_bytes(b"stale")
    with ControllerInstanceLock(tmp_path):
        pass
```

- [ ] **Step 5: Verify RED**

```powershell
python -m pytest -q tests/test_instance_lock.py
```

Expected: import failure because the module does not exist.

- [ ] **Step 6: Implement lock**

Create `src/zb_local_controller/instance_lock.py` with:

```python
from __future__ import annotations
import os
from pathlib import Path


class ControllerInstanceBusy(RuntimeError):
    def __init__(self):
        self.code = "CONTROLLER_INSTANCE_BUSY"
        super().__init__(self.code)


if os.name == "nt":
    import msvcrt
    def _lock(handle):
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    def _unlock(handle):
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl
    def _lock(handle):
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    def _unlock(handle):
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class ControllerInstanceLock:
    def __init__(self, runtime_root: Path):
        self.runtime_root = Path(runtime_root)
        self.path = self.runtime_root / "controller.lock"
        self._handle = None

    def acquire(self):
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        try:
            _lock(handle)
        except OSError as exc:
            handle.close()
            raise ControllerInstanceBusy() from exc
        self._handle = handle
        return self

    def release(self):
        handle, self._handle = self._handle, None
        if handle is None:
            return
        try:
            _unlock(handle)
        finally:
            handle.close()

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False
```

Do not delete the file to break a live lock.

- [ ] **Step 7: Run GREEN and commit**

```powershell
python -m pytest -q tests/test_config.py tests/test_instance_lock.py
git add src/zb_local_controller/config.py src/zb_local_controller/instance_lock.py tests/test_config.py tests/test_instance_lock.py
git commit -m "feat: add controller daemon runtime lock"
```

---

### Task 2: Atomic health.json + bounded rotating logs

**Files:**
- Create: `agent-controller/src/zb_local_controller/daemon_health.py`
- Create: `agent-controller/tests/test_daemon_health.py`

**Interfaces:**
- `DAEMON_SCHEMA_VERSION = "zb-controller-daemon-v1"`.
- `DaemonHealthWriter(...).write(state, last_cycle=None, last_error_code=None)`.
- `configure_daemon_logger(runtime_root, instance_id, pid)`.
- `config_sha256(path)`.

- [ ] **Step 1: Write RED health tests**

Create `tests/test_daemon_health.py`:

```python
import hashlib
import json
import logging.handlers
from zb_local_controller.daemon_health import DaemonHealthWriter, config_sha256, configure_daemon_logger


def test_config_sha256_hashes_raw_config_bytes(tmp_path):
    path = tmp_path / "config.json"
    path.write_bytes(b"{}\n")
    assert config_sha256(path) == hashlib.sha256(b"{}\n").hexdigest()


def test_health_schema_and_cycle_summary(tmp_path):
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    writer = DaemonHealthWriter(tmp_path / "runtime", "Lester-Sparx/zorr-blatt-shared-hq", config, 15.0, 1234, "11111111-1111-1111-1111-111111111111")
    writer.write("HEALTHY", {"discovered": 4, "processed": 1, "submitted": 0, "skipped": 3})
    data = json.loads((tmp_path / "runtime" / "health.json").read_text(encoding="utf-8"))
    assert data["schemaVersion"] == "zb-controller-daemon-v1"
    assert data["state"] == "HEALTHY"
    assert data["pid"] == 1234
    assert data["lastCycle"] == {"discovered": 4, "processed": 1, "submitted": 0, "skipped": 3}
    assert data["lastErrorCode"] is None


def test_rotating_logger_has_locked_bounds(tmp_path):
    logger = configure_daemon_logger(tmp_path, "instance", 4321)
    handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
    assert len(handlers) == 1
    assert handlers[0].maxBytes == 2097152
    assert handlers[0].backupCount == 5
```

Add one test monkeypatching `os.replace` and asserting `health.json` is replaced from a sibling `.tmp` file rather than written directly.

- [ ] **Step 2: Verify RED**

```powershell
python -m pytest -q tests/test_daemon_health.py
```

Expected: import failure.

- [ ] **Step 3: Implement health/logging**

Create `daemon_health.py` with fixed constants:

```python
DAEMON_SCHEMA_VERSION = "zb-controller-daemon-v1"
HEALTH_STATES = {"STARTING", "HEALTHY", "DEGRADED", "FATAL", "STOPPING"}
LOG_MAX_BYTES = 2097152
LOG_BACKUP_COUNT = 5
```

`DaemonHealthWriter` must preserve one `startedAtUtc`, generate UTC `Z` timestamps, include repository/config hash/poll interval/PID/instance id, and atomically write:

```python
tmp = self.path.with_suffix(".json.tmp")
tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
os.replace(tmp, self.path)
```

`configure_daemon_logger` must use `RotatingFileHandler(runtime_root / "controller-daemon.log", maxBytes=2097152, backupCount=5, encoding="utf-8")`, UTC timestamps, PID, instance id, and `logger.propagate = False`.

Health/logs must never contain config contents, tokens, prompt text, or image bytes.

- [ ] **Step 4: Run GREEN and commit**

```powershell
python -m pytest -q tests/test_daemon_health.py
git add src/zb_local_controller/daemon_health.py tests/test_daemon_health.py
git commit -m "feat: add controller daemon health evidence"
```

---

### Task 3: Non-mutating preflight + repeated daemon cycle runner

**Files:**
- Create: `agent-controller/src/zb_local_controller/daemon_runner.py`
- Create: `agent-controller/tests/test_daemon_runner.py`

**Interfaces:**
- `DaemonPreflightError(code)`.
- `run_daemon_preflight(config, config_path, github)`.
- `DaemonRunner(controller, health, logger, poll_interval_seconds, sleep_fn=time.sleep).run()`.

- [ ] **Step 1: Write RED preflight tests**

```python
from zb_local_controller.config import ControllerConfig
from zb_local_controller.daemon_runner import run_daemon_preflight


class AuthOnlyGitHub:
    def __init__(self):
        self.auth_calls = 0
        self.list_calls = 0
    def ensure_authenticated(self):
        self.auth_calls += 1
    def list_candidate_issues(self):
        self.list_calls += 1
        raise AssertionError("preflight must not discover tasks")


def test_preflight_authenticates_without_task_discovery(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    github = AuthOnlyGitHub()
    run_daemon_preflight(ControllerConfig(daemon_runtime_root=tmp_path / "runtime"), config_path, github)
    assert github.auth_calls == 1
    assert github.list_calls == 0
```

Add a deterministic monkeypatch test that probe-file write failure raises `DaemonPreflightError` with `DAEMON_RUNTIME_UNWRITABLE`.

- [ ] **Step 2: Write RED daemon runner tests**

```python
import logging
from zb_local_controller.controller import RunSummary
from zb_local_controller.github_cli import GitHubCLIError
from zb_local_controller.daemon_runner import DaemonRunner


class FakeHealth:
    def __init__(self): self.writes = []
    def write(self, state, last_cycle=None, last_error_code=None): self.writes.append((state, last_cycle, last_error_code))


def logger():
    result = logging.Logger("daemon-test")
    result.addHandler(logging.NullHandler())
    return result


class SequenceController:
    def __init__(self, values): self.values = iter(values)
    def run_once(self):
        value = next(self.values)
        if isinstance(value, BaseException):
            raise value
        return value


def test_healthy_cycle_then_graceful_stop():
    health = FakeHealth()
    sleeps = []
    controller = SequenceController([RunSummary(4, 1, 0, 3), KeyboardInterrupt()])
    code = DaemonRunner(controller, health, logger(), 15.0, sleeps.append).run()
    assert code == 0
    assert health.writes[0][0] == "HEALTHY"
    assert health.writes[-1][0] == "STOPPING"
    assert sleeps == [15.0]


def test_transient_github_error_degrades_and_retries():
    health = FakeHealth()
    sleeps = []
    controller = SequenceController([GitHubCLIError("GH_ISSUE_LIST_FAILED"), KeyboardInterrupt()])
    assert DaemonRunner(controller, health, logger(), 15.0, sleeps.append).run() == 0
    assert ("DEGRADED", None, "GH_ISSUE_LIST_FAILED") in health.writes
    assert sleeps == [15.0]


def test_unexpected_exception_is_fatal_and_nonzero():
    health = FakeHealth()
    controller = SequenceController([RuntimeError("boom")])
    assert DaemonRunner(controller, health, logger(), 15.0, lambda _: None).run() != 0
    assert health.writes[-1][0] == "FATAL"
```

- [ ] **Step 3: Verify RED**

```powershell
python -m pytest -q tests/test_daemon_runner.py
```

- [ ] **Step 4: Implement preflight**

`run_daemon_preflight` must:

1. Require `config_path.is_file()`.
2. Require Python 3.12+.
3. Create `config.daemon_runtime_root`.
4. Write, flush, and delete a unique probe file under that root.
5. Call `github.ensure_authenticated()`.
6. Never call `list_candidate_issues`, backend readiness, controller execution, or ComfyUI.

Runtime-path/probe failure maps to `DAEMON_RUNTIME_UNWRITABLE`. Existing GitHub authentication/configuration exceptions keep their original codes.

- [ ] **Step 5: Implement runner**

`DaemonRunner.run()` handles only cycle-time health. Startup `STARTING` is owned by CLI Task 4 after the global lock is acquired.

```python
while True:
    try:
        summary = self.controller.run_once()
        self.health.write("HEALTHY", last_cycle=summary)
    except GitHubCLIError as exc:
        code = str(exc) or exc.__class__.__name__
        self.logger.warning("controller cycle degraded: %s", code)
        self.health.write("DEGRADED", last_error_code=code)
    except KeyboardInterrupt:
        self.health.write("STOPPING")
        return 0
    except Exception as exc:
        code = str(getattr(exc, "code", exc.__class__.__name__))
        self.logger.exception("controller daemon fatal: %s", code)
        self.health.write("FATAL", last_error_code=code)
        return 1
    self.sleep_fn(self.poll_interval_seconds)
```

Normal backend/task failures already converted by `Controller` remain task-level outcomes and do not kill the daemon.

- [ ] **Step 6: Run GREEN and commit**

```powershell
python -m pytest -q tests/test_daemon_runner.py
git add src/zb_local_controller/daemon_runner.py tests/test_daemon_runner.py
git commit -m "feat: add controller daemon runner"
```

---

### Task 4: CLI modes + startup ordering + global lock enforcement

**Files:**
- Modify: `agent-controller/src/zb_local_controller/__main__.py`
- Modify: `agent-controller/tests/test_cli.py`

**Interfaces:**
- Existing `main()` remains callable by current tests.
- Daemon startup order is authoritative: load config -> create GitHub adapter -> acquire lock -> create health/logger -> write STARTING -> run preflight -> construct backends/controller -> run daemon.

- [ ] **Step 1: Write RED mode tests**

Append to `tests/test_cli.py`:

```python
import json
import pytest


def daemon_config(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"daemonRuntimeRoot": str(tmp_path / "runtime")}), encoding="utf-8")
    return path


def test_daemon_and_once_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        main(["--daemon", "--once"])


def test_daemon_requires_explicit_config():
    assert main(["--daemon"], github_factory=NoIssuesGitHub, backend_registry_factory=registry) == 2


def test_preflight_mode_does_not_discover_tasks(tmp_path):
    path = daemon_config(tmp_path)
    class PreflightGitHub(NoIssuesGitHub):
        def ensure_authenticated(self): pass
        def list_candidate_issues(self): raise AssertionError("must not list tasks")
    assert main(["--daemon-preflight", "--config", str(path)], github_factory=PreflightGitHub, backend_registry_factory=registry) == 0
```

- [ ] **Step 2: Write RED global-lock test**

```python
from zb_local_controller.config import load_config
from zb_local_controller.instance_lock import ControllerInstanceLock


def test_once_is_rejected_before_github_discovery_when_lock_owned(tmp_path):
    path = daemon_config(tmp_path)
    cfg = load_config(path)
    calls = {"list": 0}
    class CountingGitHub(NoIssuesGitHub):
        def list_candidate_issues(self):
            calls["list"] += 1
            return []
    with ControllerInstanceLock(cfg.daemon_runtime_root):
        code = main(["--once", "--config", str(path)], github_factory=CountingGitHub, backend_registry_factory=registry)
    assert code == 3
    assert calls["list"] == 0
```

Add the equivalent legacy no-flag test by monkeypatching `Controller.run_forever` to fail if called while another lock owner exists.

- [ ] **Step 3: Verify RED**

```powershell
python -m pytest -q tests/test_cli.py
```

- [ ] **Step 4: Implement parser**

Use one argparse mutually-exclusive group:

```python
mode = parser.add_mutually_exclusive_group()
mode.add_argument("--once", action="store_true")
mode.add_argument("--daemon", action="store_true")
mode.add_argument("--daemon-preflight", action="store_true")
parser.add_argument("--config", type=Path)
```

`--daemon` and `--daemon-preflight` without `--config` print `CONFIGURATION_ERROR DAEMON_CONFIG_REQUIRED` and return `2` before backend construction.

- [ ] **Step 5: Implement standalone preflight**

Standalone preflight does not acquire the execution lock:

```python
config = load_config(args.config)
github = github_factory(config.repository)
run_daemon_preflight(config, args.config, github)
print("ZB_CONTROLLER_DAEMON_PREFLIGHT PASS")
return 0
```

Do not construct backend registry or `Controller`.

- [ ] **Step 6: Implement daemon startup in the correct race-free order**

Daemon path must follow this exact order:

```python
config = load_config(args.config)
github = github_factory(config.repository)
with ControllerInstanceLock(config.daemon_runtime_root):
    instance_id = str(uuid.uuid4())
    health = DaemonHealthWriter(
        config.daemon_runtime_root,
        config.repository,
        args.config,
        config.poll_interval_seconds,
        os.getpid(),
        instance_id,
    )
    logger = configure_daemon_logger(config.daemon_runtime_root, instance_id, os.getpid())
    health.write("STARTING")
    try:
        run_daemon_preflight(config, args.config, github)
    except Exception as exc:
        code = str(getattr(exc, "code", exc.__class__.__name__))
        health.write("FATAL", last_error_code=code)
        raise
    backend_registry = backend_registry_factory(config)
    controller = Controller(
        github,
        config.inbox_root,
        config.result_root,
        backend_registry,
        poll_interval_seconds=config.poll_interval_seconds,
        max_execution_seconds=config.max_execution_seconds,
    )
    return DaemonRunner(controller, health, logger, config.poll_interval_seconds).run()
```

No GitHub task discovery or backend submission occurs before the lock is owned and preflight has passed.

- [ ] **Step 7: Lock `--once` and legacy no-flag modes**

Both paths use `with ControllerInstanceLock(config.daemon_runtime_root):` before constructing/running the processing controller. Preserve existing `CYCLE_COMPLETE discovered=... processed=... submitted=... skipped=...` output exactly.

Catch `ControllerInstanceBusy`, print `CONTROLLER_INSTANCE_BUSY` to stderr, return `3`.

Keep `ConfigurationError`, `GitHubConfigurationError`, and `DaemonPreflightError` mapped to `CONFIGURATION_ERROR <code>` and exit `2`.

- [ ] **Step 8: Run GREEN and commit**

```powershell
python -m pytest -q tests/test_cli.py tests/test_config.py tests/test_instance_lock.py tests/test_daemon_health.py tests/test_daemon_runner.py
git add src/zb_local_controller/__main__.py tests/test_cli.py
git commit -m "feat: add controller daemon cli modes"
```

---

### Task 5: Current-user Task Scheduler deployment/control/status

**Files:**
- Create: `agent-controller/deploy/windows/ZbControllerDaemon.ps1`
- Create: `agent-controller/tests/test_windows_deploy.py`

**Interface:**
- `-Action Install|Uninstall|Status|Start|Stop|Restart|Enable|Disable`.
- `Install` requires `-ConfigPath` and `-WorkingDirectory`; `-PythonExe` is optional and resolves through `Get-Command python` when omitted.
- Canonical task only: `ZB Controller Daemon v1`.

- [ ] **Step 1: Write RED deployment-contract tests**

```python
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "deploy" / "windows" / "ZbControllerDaemon.ps1"


def text(): return SCRIPT.read_text(encoding="utf-8")


def test_canonical_name_and_commands_are_declared():
    source = text()
    assert "ZB Controller Daemon v1" in source
    assert "-m zb_local_controller --daemon --config" in source
    assert "--daemon-preflight" in source


def test_locked_scheduler_policy_is_declared():
    source = text()
    for token in (
        "MultipleInstances IgnoreNew",
        "RestartCount 5",
        "New-TimeSpan -Minutes 1",
        "ExecutionTimeLimit ([TimeSpan]::Zero)",
        "DontStopIfGoingOnBatteries",
        "AllowStartIfOnBatteries",
        "StartWhenAvailable",
        "RunLevel Limited",
        "LogonType Interactive",
    ):
        assert token in source


def test_no_service_or_elevation_fallback():
    source = text().lower()
    assert "runlevel highest" not in source
    assert "new-service" not in source
    assert "nssm" not in source
    assert "-password" not in source
```

- [ ] **Step 2: Verify RED**

```powershell
python -m pytest -q tests/test_windows_deploy.py
```

- [ ] **Step 3: Implement script header/path validation**

```powershell
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("Install","Uninstall","Status","Start","Stop","Restart","Enable","Disable")]
  [string]$Action,
  [string]$ConfigPath,
  [string]$WorkingDirectory,
  [string]$PythonExe
)
$ErrorActionPreference = "Stop"
$TaskName = "ZB Controller Daemon v1"
```

For `Install`, resolve exact absolute config/working-dir/python paths and fail if any required path is missing. No self-elevation.

- [ ] **Step 4: Implement preflight-first idempotent install**

Run before `Register-ScheduledTask`:

```powershell
& $PythonExe -m zb_local_controller --daemon-preflight --config $ConfigPath
if ($LASTEXITCODE -ne 0) { throw "DAEMON_PREFLIGHT_FAILED" }
```

Build task exactly:

```powershell
$Arguments = '-m zb_local_controller --daemon --config "' + $ConfigPath + '"'
$TaskAction = New-ScheduledTaskAction -Execute $PythonExe -Argument $Arguments -WorkingDirectory $WorkingDirectory
$TaskTrigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$UserId = if ($env:USERDOMAIN) { "$env:USERDOMAIN\$env:USERNAME" } else { $env:USERNAME }
$Principal = New-ScheduledTaskPrincipal -UserId $UserId -LogonType Interactive -RunLevel Limited
$Settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
$Task = New-ScheduledTask -Action $TaskAction -Trigger $TaskTrigger -Principal $Principal -Settings $Settings
Register-ScheduledTask -TaskName $TaskName -InputObject $Task -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
```

Repeated identical install converges on the same task definition.

- [ ] **Step 5: Implement lifecycle actions narrowly**

Use only the canonical task name with `Start-ScheduledTask`, `Stop-ScheduledTask`, `Enable-ScheduledTask`, `Disable-ScheduledTask`, and `Unregister-ScheduledTask -Confirm:$false`.

`Restart` = stop -> bounded wait until not Running -> start. `Uninstall` succeeds when already absent. Never delete config/inbox/results/runtime unless a future explicit gate adds that behavior.

- [ ] **Step 6: Implement read-only status contract**

Status reads scheduler state plus `health.json` from `daemonRuntimeRoot` in the supplied config file, defaulting to `D:\BLATT2\ZB_AGENT_RUNTIME\controller-daemon` if the key is absent. It never calls Python/controller processing.

Output:

```text
ZB_CONTROLLER_DAEMON_STATUS_V1
TASK_REGISTERED = YES|NO
TASK_ENABLED = YES|NO
TASK_STATE = scheduler-state
HEALTH_STATE = STARTING|HEALTHY|DEGRADED|FATAL|STOPPING|MISSING|STALE
PID = integer-or-NONE
PID_ALIVE = YES|NO|UNKNOWN
INSTANCE_ID = uuid-or-NONE
HEARTBEAT_AGE_SEC = number-or-NONE
CONFIG_SHA256 = sha256-or-NONE
```

Mark `STALE` when heartbeat age is greater than `max(60, 3 * pollIntervalSeconds)`.

- [ ] **Step 7: Run GREEN and commit**

```powershell
python -m pytest -q tests/test_windows_deploy.py
git add deploy/windows/ZbControllerDaemon.ps1 tests/test_windows_deploy.py
git commit -m "feat: add Windows controller daemon deployment"
```

---

### Task 6: Docs, full regression, scope proof, exact-head handoff

**Files:**
- Modify: `agent-controller/config.example.json`
- Modify: `agent-controller/README.md`

- [ ] **Step 1: Add daemon config example**

Add:

```json
"daemonRuntimeRoot": "D:\\BLATT2\\ZB_AGENT_RUNTIME\\controller-daemon"
```

No SALVADOR production values change.

- [ ] **Step 2: Document exact production operations**

README must include:

```powershell
python -m zb_local_controller --daemon-preflight --config 'D:\BLATT2\ZB_AGENT_CONFIG\salvador-canon-reference-edit.json'
python -m zb_local_controller --daemon --config 'D:\BLATT2\ZB_AGENT_CONFIG\salvador-canon-reference-edit.json'
.\deploy\windows\ZbControllerDaemon.ps1 -Action Install -ConfigPath 'D:\BLATT2\ZB_AGENT_CONFIG\salvador-canon-reference-edit.json' -WorkingDirectory 'D:\BLATT2\zb-local-agent-controller\agent-controller'
.\deploy\windows\ZbControllerDaemon.ps1 -Action Status -ConfigPath 'D:\BLATT2\ZB_AGENT_CONFIG\salvador-canon-reference-edit.json'
```

Document that `--once` is maintenance/testing only once daemon is active and returns `CONTROLLER_INSTANCE_BUSY` while the daemon owns the lock. Explicitly state daemon does not start ComfyUI, move ChatGPT attachments, create tasks, change SALVADOR profile, or implement Reference Bridge v1.

- [ ] **Step 3: Run focused daemon suite**

```powershell
python -m pytest -q tests/test_config.py tests/test_instance_lock.py tests/test_daemon_health.py tests/test_daemon_runner.py tests/test_cli.py tests/test_windows_deploy.py
```

Expected: PASS.

- [ ] **Step 4: Run full regression + compile**

```powershell
python -m pytest -q
python -m compileall -q src
```

Expected: all tests PASS and compile exits 0. Record the fresh exact test count.

- [ ] **Step 5: Prove scope integrity against the accepted controller base**

```powershell
git diff --name-only 425ad97c508c4f55f7d7052435a7a2cb4aa3b015...HEAD
```

Allowed implementation paths are only:

```text
agent-controller/README.md
agent-controller/config.example.json
agent-controller/src/zb_local_controller/config.py
agent-controller/src/zb_local_controller/instance_lock.py
agent-controller/src/zb_local_controller/daemon_health.py
agent-controller/src/zb_local_controller/daemon_runner.py
agent-controller/src/zb_local_controller/__main__.py
agent-controller/deploy/windows/ZbControllerDaemon.ps1
agent-controller/tests/test_config.py
agent-controller/tests/test_instance_lock.py
agent-controller/tests/test_daemon_health.py
agent-controller/tests/test_daemon_runner.py
agent-controller/tests/test_cli.py
agent-controller/tests/test_windows_deploy.py
```

The approved spec/plan docs may also be ancestors of the implementation branch. No backend/prompt/workflow file may change.

- [ ] **Step 6: Commit docs**

```powershell
git add README.md config.example.json
git commit -m "docs: document controller daemon v1"
```

- [ ] **Step 7: Fresh verification-before-completion on final HEAD**

```powershell
python -m pytest -q
python -m compileall -q src
git status --short
git rev-parse HEAD
git branch --show-current
git diff --name-only 425ad97c508c4f55f7d7052435a7a2cb4aa3b015...HEAD
```

Completion claim requires real observed values for: final implementation HEAD, branch, Python version, full pytest count/result, compile PASS, focused daemon PASS, lock contention PASS, preflight non-mutation PASS, deployment-contract PASS, scope integrity PASS, clean worktree, `MERGE = NO`, `PRODUCTION_ACTIVATION = NO`, and `NEXT = DUNCAN INDEPENDENT QC`.

Durable handoff marker is exactly `LESTER_ZB_CONTROLLER_DAEMON_V1_IMPLEMENTATION_READY`.

---

## Post-Implementation Gate Sequence

Lester stops after exact-head implementation handoff. JINGO then assigns DUNCAN independent QC against that exact HEAD. Only DUNCAN PASS authorizes owner-PC live Windows smoke. Live smoke must prove real scheduled-task registration, daemon start without manual controller invocation, healthy heartbeat, duplicate `--once` rejection, forced-process restart recovery, and one controlled task consumption. Production activation is a separate gate after live smoke. Reference Bridge v1 starts only after Controller Daemon v1 is production-active.
