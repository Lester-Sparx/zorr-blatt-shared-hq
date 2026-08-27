# ZB Controller Daemon v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the accepted ZB local controller into a current-user Windows daemon that starts at logon, runs continuously without manual PowerShell polling, enforces one controller instance, exposes bounded local health/log evidence, and restarts through Task Scheduler without changing any SALVADOR task-state truth law.

**Architecture:** Keep the existing `Controller` as the task-state/backend engine. Add isolated lifecycle units for OS-backed single-instance locking, daemon health/logging, and a daemon runner that repeatedly calls `Controller.run_once()`. Extend the CLI only for mode selection/wiring, and keep Windows Task Scheduler deployment in repository-owned PowerShell tooling under `agent-controller/deploy/windows/`.

**Tech Stack:** Python 3.12+, Python standard library only for daemon/lifecycle code (`msvcrt` on Windows, `fcntl` for non-Windows test/dev parity, `logging.handlers.RotatingFileHandler`, `json`, `hashlib`, `uuid`, `pathlib`), pytest, Windows PowerShell 5.1 Task Scheduler cmdlets, existing GitHub CLI and local ComfyUI backend.

**Spec:** `docs/superpowers/specs/2026-08-27-zb-controller-daemon-v1-design.md`

## Global Constraints

- Exact approved spec HEAD: `c20126f949e6e61298d9dd76a906349a71bbcb00`.
- Exact accepted controller base: `425ad97c508c4f55f7d7052435a7a2cb4aa3b015`.
- Implementation branch/worktree starts from the approved plan HEAD created from the spec branch; never implement on `main` or mutate the docs branch in place.
- Existing law remains unchanged: `ASSIGNED != RUNNING`; `RUNNING` requires a real non-empty backend execution id; `RESULT_READY` requires real bytes/checksum/provenance.
- SALVADOR model/profile/workflow/prompt/denoise/dimensions remain unchanged.
- No Reference Bridge, Google Drive transport, ComfyUI lifecycle/autostart, Babylon integration, canon mutation, paid services, native Windows Service, NSSM, pywin32 service, tray UI, or arbitrary PC control.
- Production daemon command is `python -m zb_local_controller --daemon --config <absolute-config-path>`.
- `--once`, `--daemon`, and `--daemon-preflight` are mutually exclusive; legacy no-flag continuous mode remains compatible but is not the production deployment contract.
- Every real controller-processing mode shares one OS-backed lock; preflight/status do not own the execution lock.
- Windows production lock uses `msvcrt.locking(..., LK_NBLCK, 1)`; POSIX `fcntl.flock(..., LOCK_EX | LOCK_NB)` exists only for equivalent non-Windows test/dev semantics.
- Default daemon runtime root: `D:\BLATT2\ZB_AGENT_RUNTIME\controller-daemon`.
- Rotating log bounds are fixed: `maxBytes = 2097152`, `backupCount = 5`.
- Task Scheduler canonical name: `ZB Controller Daemon v1`.
- Scheduler restart policy is fixed: 1 minute interval, 5 retries; execution time limit disabled; current-user interactive principal; limited run level; no plaintext Windows password.
- No merge and no production activation are authorized by this implementation plan.

---

## Planned File Structure

```text
agent-controller/
  config.example.json                         # add daemonRuntimeRoot example only
  README.md                                   # document daemon operations and non-goals
  src/zb_local_controller/
    config.py                                 # add daemon_runtime_root config field
    instance_lock.py                          # OS-backed global controller lock only
    daemon_health.py                          # atomic health snapshot + rotating logger
    daemon_runner.py                          # preflight + repeated Controller.run_once loop
    __main__.py                               # CLI mode selection/wiring + global lock ownership
  deploy/windows/
    ZbControllerDaemon.ps1                    # install/uninstall/status/start/stop/restart/enable/disable
  tests/
    test_config.py                            # daemonRuntimeRoot parsing regression
    test_instance_lock.py                     # lock acquisition/contention/release/stale-file cases
    test_daemon_health.py                     # health schema/atomicity/hash/log bounds
    test_daemon_runner.py                     # healthy/degraded/fatal/stop semantics
    test_cli.py                               # mode exclusivity/preflight/no-task-processing/global lock regression
    test_windows_deploy.py                    # static deployment contract/quoting/scope checks
```

Do not move daemon lifecycle logic into `controller.py`; the accepted task-state engine remains isolated.

---

### Task 1: Add daemon runtime configuration and the global controller instance lock

**Files:**
- Modify: `agent-controller/src/zb_local_controller/config.py`
- Create: `agent-controller/src/zb_local_controller/instance_lock.py`
- Modify: `agent-controller/tests/test_config.py`
- Create: `agent-controller/tests/test_instance_lock.py`

**Interfaces:**
- Produces: `ControllerConfig.daemon_runtime_root: Path`.
- Produces: `ControllerInstanceBusy(code="CONTROLLER_INSTANCE_BUSY")`.
- Produces: `ControllerInstanceLock(runtime_root: Path)` with `acquire()`, `release()`, `__enter__()`, `__exit__()`.
- Later tasks consume `ControllerInstanceLock` in the CLI only; the existing `Controller` does not import it.

- [ ] **Step 1: Write failing config coverage**

Append to `tests/test_config.py`:

```python
from pathlib import Path


def test_loads_daemon_runtime_root(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"daemonRuntimeRoot": r"D:\\BLATT2\\RUNTIME\\daemon"}), encoding="utf-8")
    config = load_config(path)
    assert config.daemon_runtime_root == Path(r"D:\BLATT2\RUNTIME\daemon")


def test_daemon_runtime_root_default_is_locked():
    from zb_local_controller.config import ControllerConfig
    assert ControllerConfig().daemon_runtime_root == Path(r"D:\BLATT2\ZB_AGENT_RUNTIME\controller-daemon")
```

- [ ] **Step 2: Run RED for config**

Run from `agent-controller/`:

```powershell
python -m pytest -q tests/test_config.py
```

Expected: new tests fail because `daemon_runtime_root` / `daemonRuntimeRoot` do not exist.

- [ ] **Step 3: Implement the minimal config extension**

In `src/zb_local_controller/config.py`, add exactly:

```python
daemon_runtime_root: Path = Path(r"D:\BLATT2\ZB_AGENT_RUNTIME\controller-daemon")
```

Add `"daemonRuntimeRoot"` to the existing allowlist and populate the dataclass with:

```python
daemon_runtime_root=Path(
    raw.get("daemonRuntimeRoot", str(ControllerConfig.daemon_runtime_root))
),
```

Do not add scheduler restart/log-size tuning to JSON config.

- [ ] **Step 4: Write failing lock tests**

Create `tests/test_instance_lock.py`:

```python
from pathlib import Path
import pytest
from zb_local_controller.instance_lock import ControllerInstanceBusy, ControllerInstanceLock


def test_first_lock_succeeds_and_second_fails(tmp_path):
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
        assert (tmp_path / "controller.lock").is_file()


def test_stale_lock_file_bytes_do_not_block_without_os_lock(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "controller.lock").write_bytes(b"stale metadata only")
    with ControllerInstanceLock(tmp_path):
        pass
```

- [ ] **Step 5: Run lock RED**

```powershell
python -m pytest -q tests/test_instance_lock.py
```

Expected: import/module failure because `instance_lock.py` does not exist.

- [ ] **Step 6: Implement OS-backed lock**

Create `src/zb_local_controller/instance_lock.py` with this public shape:

```python
from __future__ import annotations
import os
from pathlib import Path
from typing import BinaryIO


class ControllerInstanceBusy(RuntimeError):
    def __init__(self, code: str = "CONTROLLER_INSTANCE_BUSY"):
        self.code = code
        super().__init__(code)


class ControllerInstanceLock:
    def __init__(self, runtime_root: Path):
        self.runtime_root = Path(runtime_root)
        self.path = self.runtime_root / "controller.lock"
        self._handle: BinaryIO | None = None

    def acquire(self) -> None:
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            _lock_one_byte(handle)
        except OSError as exc:
            handle.close()
            raise ControllerInstanceBusy() from exc
        self._handle = handle

    def release(self) -> None:
        handle, self._handle = self._handle, None
        if handle is None:
            return
        try:
            _unlock_one_byte(handle)
        finally:
            handle.close()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False
```

Implement `_lock_one_byte` / `_unlock_one_byte` with Windows production authority:

```python
if os.name == "nt":
    import msvcrt
    def _lock_one_byte(handle):
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    def _unlock_one_byte(handle):
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl
    def _lock_one_byte(handle):
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    def _unlock_one_byte(handle):
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
```

Do not delete the lock file as a correctness mechanism.

- [ ] **Step 7: Run GREEN and commit**

```powershell
python -m pytest -q tests/test_config.py tests/test_instance_lock.py
git add src/zb_local_controller/config.py src/zb_local_controller/instance_lock.py tests/test_config.py tests/test_instance_lock.py
git commit -m "feat: add controller daemon runtime lock"
```

Expected: focused tests PASS.

---

### Task 2: Add atomic daemon health evidence and bounded rotating logs

**Files:**
- Create: `agent-controller/src/zb_local_controller/daemon_health.py`
- Create: `agent-controller/tests/test_daemon_health.py`

**Interfaces:**
- Produces: `DAEMON_SCHEMA_VERSION = "zb-controller-daemon-v1"`.
- Produces: `DaemonHealthWriter(runtime_root, repository, config_path, poll_interval_seconds, pid, instance_id)`.
- Produces: `write(state, last_cycle=None, last_error_code=None)` where state is one of `STARTING|HEALTHY|DEGRADED|FATAL|STOPPING`.
- Produces: `configure_daemon_logger(runtime_root, instance_id, pid) -> logging.Logger`.
- Produces: `config_sha256(path: Path) -> str`.

- [ ] **Step 1: Write failing health tests**

Create `tests/test_daemon_health.py` with concrete cases:

```python
import hashlib
import json
import logging.handlers
from zb_local_controller.daemon_health import (
    DAEMON_SCHEMA_VERSION,
    DaemonHealthWriter,
    config_sha256,
    configure_daemon_logger,
)


def test_config_sha256_hashes_raw_bytes(tmp_path):
    path = tmp_path / "config.json"
    path.write_bytes(b'{"x":1}\n')
    assert config_sha256(path) == hashlib.sha256(b'{"x":1}\n').hexdigest()


def test_health_writer_emits_exact_minimum_schema(tmp_path):
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    writer = DaemonHealthWriter(
        tmp_path / "runtime",
        repository="Lester-Sparx/zorr-blatt-shared-hq",
        config_path=config,
        poll_interval_seconds=15.0,
        pid=1234,
        instance_id="11111111-1111-1111-1111-111111111111",
    )
    writer.write("HEALTHY", last_cycle={"discovered": 4, "processed": 1, "submitted": 0, "skipped": 3})
    data = json.loads((tmp_path / "runtime" / "health.json").read_text(encoding="utf-8"))
    assert data["schemaVersion"] == DAEMON_SCHEMA_VERSION
    assert data["state"] == "HEALTHY"
    assert data["pid"] == 1234
    assert data["lastCycle"]["processed"] == 1
    assert data["lastErrorCode"] is None
    assert data["configSha256"] == config_sha256(config)


def test_rotating_logger_uses_locked_bounds(tmp_path):
    logger = configure_daemon_logger(tmp_path, "instance", 4321)
    handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
    assert len(handlers) == 1
    assert handlers[0].maxBytes == 2097152
    assert handlers[0].backupCount == 5
```

Also add an atomicity regression by monkeypatching `os.replace` and asserting the destination is written only through a sibling temporary file; do not write partial JSON directly to `health.json`.

- [ ] **Step 2: Run RED**

```powershell
python -m pytest -q tests/test_daemon_health.py
```

Expected: module import failure.

- [ ] **Step 3: Implement health writer and logger**

Create `src/zb_local_controller/daemon_health.py` with these locked constants:

```python
DAEMON_SCHEMA_VERSION = "zb-controller-daemon-v1"
HEALTH_STATES = {"STARTING", "HEALTHY", "DEGRADED", "FATAL", "STOPPING"}
LOG_MAX_BYTES = 2 * 1024 * 1024
LOG_BACKUP_COUNT = 5
```

`config_sha256` must hash `Path(path).read_bytes()` directly.

`DaemonHealthWriter.write(...)` must build the exact minimum payload from the spec, use UTC `Z` timestamps, retain one immutable `startedAtUtc` per writer instance, and write atomically:

```python
tmp = self.path.with_suffix(".json.tmp")
tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
os.replace(tmp, self.path)
```

When `last_cycle` is a `RunSummary`, serialize exactly its four integer fields; when absent, write `lastCycle: null`.

`configure_daemon_logger` must use `RotatingFileHandler(runtime_root / "controller-daemon.log", maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8")`, UTC timestamps, PID, and instance id. Disable propagation to avoid duplicate console/root log lines.

- [ ] **Step 4: Run GREEN and commit**

```powershell
python -m pytest -q tests/test_daemon_health.py
git add src/zb_local_controller/daemon_health.py tests/test_daemon_health.py
git commit -m "feat: add controller daemon health evidence"
```

Expected: focused tests PASS.

---

### Task 3: Add non-mutating daemon preflight and the repeated daemon runner

**Files:**
- Create: `agent-controller/src/zb_local_controller/daemon_runner.py`
- Create: `agent-controller/tests/test_daemon_runner.py`

**Interfaces:**
- Consumes: existing `Controller.run_once() -> RunSummary`.
- Consumes: existing `GitHubCLI.ensure_authenticated()` and `GitHubCLIError` / `GitHubConfigurationError`.
- Produces: `DaemonPreflightError(code: str)`.
- Produces: `run_daemon_preflight(config, config_path, github) -> None`.
- Produces: `DaemonRunner(controller, health, logger, poll_interval_seconds, sleep_fn=time.sleep).run() -> int`.

- [ ] **Step 1: Write failing preflight tests**

Create `tests/test_daemon_runner.py` beginning with:

```python
from pathlib import Path
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


def test_preflight_authenticates_without_discovering_tasks(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    runtime = tmp_path / "runtime"
    github = AuthOnlyGitHub()
    run_daemon_preflight(ControllerConfig(daemon_runtime_root=runtime), config_path, github)
    assert github.auth_calls == 1
    assert github.list_calls == 0
    assert runtime.is_dir()
```

Add a test that a non-writable/runtime-root creation failure is surfaced as `DaemonPreflightError("DAEMON_RUNTIME_UNWRITABLE")`; use monkeypatch to make the probe write fail deterministically instead of depending on host filesystem permissions.

- [ ] **Step 2: Write failing daemon-loop tests**

Add:

```python
from zb_local_controller.controller import RunSummary
from zb_local_controller.github_cli import GitHubCLIError
from zb_local_controller.daemon_runner import DaemonRunner


class FakeHealth:
    def __init__(self): self.writes = []
    def write(self, state, last_cycle=None, last_error_code=None):
        self.writes.append((state, last_cycle, last_error_code))


class SequenceController:
    def __init__(self, values): self.values = iter(values)
    def run_once(self):
        value = next(self.values)
        if isinstance(value, BaseException): raise value
        return value


def test_daemon_marks_healthy_after_cycle_and_repeats_until_stop():
    health = FakeHealth()
    sleeps = []
    controller = SequenceController([RunSummary(4, 1, 0, 3), KeyboardInterrupt()])
    code = DaemonRunner(controller, health, logger=_test_logger(), poll_interval_seconds=15, sleep_fn=sleeps.append).run()
    assert code == 0
    assert health.writes[0][0] == "STARTING"
    assert health.writes[1][0] == "HEALTHY"
    assert health.writes[-1][0] == "STOPPING"
    assert sleeps == [15]


def test_transient_github_error_marks_degraded_then_retries():
    health = FakeHealth()
    controller = SequenceController([GitHubCLIError("GH_ISSUE_LIST_FAILED"), KeyboardInterrupt()])
    sleeps = []
    code = DaemonRunner(controller, health, logger=_test_logger(), poll_interval_seconds=15, sleep_fn=sleeps.append).run()
    assert code == 0
    assert any(state == "DEGRADED" and error == "GH_ISSUE_LIST_FAILED" for state, _, error in health.writes)
    assert sleeps == [15]


def test_unexpected_exception_marks_fatal_and_returns_nonzero():
    health = FakeHealth()
    controller = SequenceController([RuntimeError("boom")])
    code = DaemonRunner(controller, health, logger=_test_logger(), poll_interval_seconds=15, sleep_fn=lambda _: None).run()
    assert code != 0
    assert health.writes[-1][0] == "FATAL"
```

Define `_test_logger()` with a `logging.Logger` carrying a `NullHandler` so tests never rely on root logger configuration.

- [ ] **Step 3: Run RED**

```powershell
python -m pytest -q tests/test_daemon_runner.py
```

Expected: module import failure.

- [ ] **Step 4: Implement preflight**

In `daemon_runner.py`, `run_daemon_preflight` must:

1. Require the config path to exist as a regular file.
2. Require Python `>= 3.12`.
3. Create `config.daemon_runtime_root`.
4. Write+flush+delete a uniquely named probe file under that root.
5. Call `github.ensure_authenticated()`.
6. Never call `list_candidate_issues`, backend readiness, `Controller.run_once`, or ComfyUI.

Map runtime path/probe failures to `DaemonPreflightError("DAEMON_RUNTIME_UNWRITABLE")`. Let existing GitHub configuration exceptions retain their own code so CLI can report them without fabricating task state.

- [ ] **Step 5: Implement daemon runner**

`DaemonRunner.run()` must perform this exact state flow:

```python
self.health.write("STARTING")
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
    except BaseException as exc:
        code = getattr(exc, "code", exc.__class__.__name__)
        self.logger.exception("controller daemon fatal: %s", code)
        self.health.write("FATAL", last_error_code=str(code))
        return 1
    self.sleep_fn(self.poll_interval_seconds)
```

Do not catch/translate normal task-level backend failures that the existing `Controller` already converts to GitHub task events.

- [ ] **Step 6: Run GREEN and commit**

```powershell
python -m pytest -q tests/test_daemon_runner.py
git add src/zb_local_controller/daemon_runner.py tests/test_daemon_runner.py
git commit -m "feat: add controller daemon runner"
```

Expected: focused tests PASS.

---

### Task 4: Wire daemon/preflight CLI modes and enforce the global lock across every processing mode

**Files:**
- Modify: `agent-controller/src/zb_local_controller/__main__.py`
- Modify: `agent-controller/tests/test_cli.py`

**Interfaces:**
- Consumes: `ControllerInstanceLock`.
- Consumes: `DaemonHealthWriter`, `configure_daemon_logger`.
- Consumes: `run_daemon_preflight`, `DaemonRunner`.
- Keeps existing `main(argv=None, github_factory=..., backend_registry_factory=...) -> int` compatibility; additional dependency-injection kwargs are allowed only if they make unit tests deterministic.

- [ ] **Step 1: Write failing parser/mode tests**

Append concrete tests to `tests/test_cli.py`:

```python
import json
import pytest


def _config_file(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"daemonRuntimeRoot": str(tmp_path / "runtime")}), encoding="utf-8")
    return path


def test_daemon_and_once_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        main(["--daemon", "--once"])


def test_daemon_requires_explicit_config_path():
    assert main(["--daemon"], github_factory=NoIssuesGitHub, backend_registry_factory=registry) != 0


def test_preflight_does_not_list_candidate_tasks(tmp_path):
    config = _config_file(tmp_path)
    class PreflightGitHub(NoIssuesGitHub):
        def ensure_authenticated(self): pass
        def list_candidate_issues(self):
            raise AssertionError("preflight must not discover tasks")
    assert main(["--daemon-preflight", "--config", str(config)], github_factory=PreflightGitHub, backend_registry_factory=registry) == 0
```

- [ ] **Step 2: Add global-lock regression before implementation**

Use the real OS-backed lock and a temp config:

```python
from zb_local_controller.config import load_config
from zb_local_controller.instance_lock import ControllerInstanceLock


def test_once_fails_before_github_discovery_when_daemon_lock_is_owned(tmp_path):
    config_path = _config_file(tmp_path)
    config = load_config(config_path)
    calls = {"list": 0}
    class CountingGitHub(NoIssuesGitHub):
        def list_candidate_issues(self):
            calls["list"] += 1
            return []
    with ControllerInstanceLock(config.daemon_runtime_root):
        code = main(["--once", "--config", str(config_path)], github_factory=CountingGitHub, backend_registry_factory=registry)
    assert code != 0
    assert calls["list"] == 0
```

Also add the equivalent lock test for legacy no-flag continuous wiring by injecting a controller whose `run_forever()` would fail if reached while the lock is owned.

- [ ] **Step 3: Run RED**

```powershell
python -m pytest -q tests/test_cli.py
```

Expected: new daemon flags/config/global-lock tests fail.

- [ ] **Step 4: Implement explicit mode parsing**

In `__main__.py`, replace the standalone `--once` flag with an argparse mutually-exclusive group:

```python
mode = parser.add_mutually_exclusive_group()
mode.add_argument("--once", action="store_true")
mode.add_argument("--daemon", action="store_true")
mode.add_argument("--daemon-preflight", action="store_true")
parser.add_argument("--config", type=Path)
```

If `--daemon` or `--daemon-preflight` is selected without `--config`, print `CONFIGURATION_ERROR DAEMON_CONFIG_REQUIRED` to stderr and return `2` before constructing backends.

- [ ] **Step 5: Wire preflight without task/backend work**

For `--daemon-preflight`:

```python
config = load_config(args.config)
github = github_factory(config.repository)
run_daemon_preflight(config, args.config, github)
print("ZB_CONTROLLER_DAEMON_PREFLIGHT PASS")
return 0
```

Do not build the backend registry or construct `Controller` in preflight mode.

- [ ] **Step 6: Wire one global execution lock for all processing modes**

After loading config and before any candidate-issue discovery:

```python
with ControllerInstanceLock(config.daemon_runtime_root):
    github = github_factory(config.repository)
    backend_registry = backend_registry_factory(config)
    controller = Controller(...)
    if args.once:
        summary = controller.run_once()
        print(...existing CYCLE_COMPLETE format...)
        return 0
    if args.daemon:
        instance_id = str(uuid.uuid4())
        health = DaemonHealthWriter(...)
        logger = configure_daemon_logger(config.daemon_runtime_root, instance_id, os.getpid())
        return DaemonRunner(controller, health, logger, config.poll_interval_seconds).run()
    controller.run_forever()
    return 0
```

For daemon mode, call `run_daemon_preflight(config, args.config, github)` **before** constructing `Controller`/backends and before starting the health loop, while still outside task processing. After preflight passes, acquire the global execution lock and start the runner.

Catch `ControllerInstanceBusy` at CLI boundary, print exactly `CONTROLLER_INSTANCE_BUSY` to stderr, and return `3`.

Do not change existing `CYCLE_COMPLETE` text for `--once`.

- [ ] **Step 7: Preserve current configuration/GitHub error behavior**

Keep `ConfigurationError` and `GitHubConfigurationError` mapped to `CONFIGURATION_ERROR <code>` / exit `2`. Map `DaemonPreflightError` the same way with its exact code. `KeyboardInterrupt` from legacy no-flag mode remains a clean exit and the context manager releases the lock.

- [ ] **Step 8: Run GREEN + regression and commit**

```powershell
python -m pytest -q tests/test_cli.py tests/test_config.py tests/test_instance_lock.py tests/test_daemon_health.py tests/test_daemon_runner.py
git add src/zb_local_controller/__main__.py tests/test_cli.py
git commit -m "feat: add controller daemon cli modes"
```

Expected: focused daemon tests and all pre-existing CLI tests PASS.

---

### Task 5: Add idempotent current-user Windows Task Scheduler deployment tooling

**Files:**
- Create: `agent-controller/deploy/windows/ZbControllerDaemon.ps1`
- Create: `agent-controller/tests/test_windows_deploy.py`

**Interfaces:**
- PowerShell script accepts `-Action Install|Uninstall|Status|Start|Stop|Restart|Enable|Disable`.
- `Install` additionally requires absolute `-ConfigPath`, absolute `-WorkingDirectory`, and optional `-PythonExe` defaulting to the current `python.exe` resolved with `Get-Command python`.
- Canonical task name is exactly `ZB Controller Daemon v1`.
- Status output begins `ZB_CONTROLLER_DAEMON_STATUS_V1` and never runs the controller.

- [ ] **Step 1: Write failing static deployment-contract tests**

Create `tests/test_windows_deploy.py`:

```python
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "deploy" / "windows" / "ZbControllerDaemon.ps1"


def source():
    return SCRIPT.read_text(encoding="utf-8")


def test_deployment_script_declares_canonical_task_and_daemon_command():
    text = source()
    assert "ZB Controller Daemon v1" in text
    assert "-m zb_local_controller --daemon --config" in text
    assert "--daemon-preflight" in text


def test_deployment_script_locks_scheduler_policy():
    text = source()
    for required in (
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
        assert required in text


def test_deployment_script_has_no_elevation_or_plaintext_password_fallback():
    lowered = source().lower()
    assert "runlevel highest" not in lowered
    assert "-password" not in lowered
    assert "nssm" not in lowered
    assert "new-service" not in lowered


def test_status_path_does_not_invoke_controller_processing():
    text = source()
    status_block = text.split('"Status" {', 1)[1].split('}', 1)[0]
    assert "zb_local_controller" not in status_block
    assert "run_once" not in status_block
```

The test intentionally validates declared locked settings without requiring a real Windows scheduler in CI.

- [ ] **Step 2: Run RED**

```powershell
python -m pytest -q tests/test_windows_deploy.py
```

Expected: file-not-found failure.

- [ ] **Step 3: Implement parameter validation and common helpers**

Start `ZbControllerDaemon.ps1` as PowerShell 5.1-safe ASCII/UTF-8 text:

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

For install, resolve all three paths to absolute filesystem paths. Reject missing/nonexistent config, working directory, or python executable. Do not request admin elevation.

- [ ] **Step 4: Implement install/update with preflight-first law**

Before replacing/creating registration:

```powershell
& $PythonExe -m zb_local_controller --daemon-preflight --config $ConfigPath
if ($LASTEXITCODE -ne 0) { throw "DAEMON_PREFLIGHT_FAILED" }
```

Build action exactly so Task Scheduler launches the deployed controller directory:

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

Repeated install with identical values must converge through `-Force`, not create alternate task names.

- [ ] **Step 5: Implement lifecycle actions narrowly against the canonical task**

Use only these cmdlets against `$TaskName`:

- `Start-ScheduledTask`
- `Stop-ScheduledTask`
- `Enable-ScheduledTask`
- `Disable-ScheduledTask`
- `Unregister-ScheduledTask -Confirm:$false`

`Restart` is `Stop-ScheduledTask`, bounded wait for stopped/not-running state, then `Start-ScheduledTask`. `Uninstall` is idempotent: if task does not exist, return success.

No lifecycle action deletes config, inbox, result, model, or SALVADOR files.

- [ ] **Step 6: Implement non-mutating status**

Read only:

- `Get-ScheduledTask -TaskName $TaskName`
- `Get-ScheduledTaskInfo -TaskName $TaskName`
- `D:\BLATT2\ZB_AGENT_RUNTIME\controller-daemon\health.json` only as the default fallback; when install-time config exposes another daemon runtime root, status must read that root from the supplied `-ConfigPath` using JSON parsing, without invoking Python/controller processing.

Output exactly these keys, one per line:

```text
ZB_CONTROLLER_DAEMON_STATUS_V1
TASK_REGISTERED = YES|NO
TASK_ENABLED = YES|NO
TASK_STATE = <scheduler state>
HEALTH_STATE = STARTING|HEALTHY|DEGRADED|FATAL|STOPPING|MISSING|STALE
PID = <integer or NONE>
PID_ALIVE = YES|NO|UNKNOWN
INSTANCE_ID = <uuid or NONE>
HEARTBEAT_AGE_SEC = <number or NONE>
CONFIG_SHA256 = <64-hex or NONE>
```

Mark health `STALE` when age exceeds `max(60, 3 * pollIntervalSeconds)` from the health JSON. A missing/invalid health file reports `MISSING` and never `HEALTHY`.

- [ ] **Step 7: Run GREEN and commit**

```powershell
python -m pytest -q tests/test_windows_deploy.py
git add deploy/windows/ZbControllerDaemon.ps1 tests/test_windows_deploy.py
git commit -m "feat: add Windows controller daemon deployment"
```

Expected: deployment-contract tests PASS.

---

### Task 6: Document the production daemon boundary, run full verification, and prepare exact-head handoff

**Files:**
- Modify: `agent-controller/config.example.json`
- Modify: `agent-controller/README.md`
- Verify: full `agent-controller/tests/`

**Interfaces:**
- Documentation must describe only Controller Daemon v1 operations; Reference Bridge remains a separate future gate.

- [ ] **Step 1: Update example config**

Add exactly one daemon field to `config.example.json`:

```json
"daemonRuntimeRoot": "D:\\BLATT2\\ZB_AGENT_RUNTIME\\controller-daemon"
```

Keep the existing production SALVADOR model/workflow/prompt/denoise/size fields byte-for-byte equivalent except for JSON comma placement needed by this addition.

- [ ] **Step 2: Add README daemon section**

Document:

```text
Production daemon mode:
python -m zb_local_controller --daemon --config <absolute-config-path>

Preflight:
python -m zb_local_controller --daemon-preflight --config <absolute-config-path>

Windows deployment:
.\deploy\windows\ZbControllerDaemon.ps1 -Action Install -ConfigPath <absolute-config> -WorkingDirectory <absolute-agent-controller-dir>

Status:
.\deploy\windows\ZbControllerDaemon.ps1 -Action Status -ConfigPath <absolute-config>
```

Explicitly state:

- `--once` is maintenance/testing only once daemon is active and fails with `CONTROLLER_INSTANCE_BUSY` while daemon owns the lock.
- Daemon does not start ComfyUI, move ChatGPT attachments, create tasks, change SALVADOR profile, or mutate canon.
- Reference Bridge v1 is not part of this implementation.

- [ ] **Step 3: Run focused daemon suite**

```powershell
python -m pytest -q tests/test_config.py tests/test_instance_lock.py tests/test_daemon_health.py tests/test_daemon_runner.py tests/test_cli.py tests/test_windows_deploy.py
```

Expected: PASS.

- [ ] **Step 4: Run full existing controller regression**

```powershell
python -m pytest -q
python -m compileall -q src
```

Expected: all tests PASS and compile exits 0. Record the exact test count from this fresh run in the implementation handoff; do not reuse an earlier count.

- [ ] **Step 5: Verify SALVADOR scope integrity**

Run:

```powershell
git diff --name-only 425ad97c508c4f55f7d7052435a7a2cb4aa3b015...HEAD
```

Allowed implementation paths are only the daemon/config/CLI/deployment/docs/tests listed in this plan. No files under `src/zb_local_controller/backends/`, `prompts/`, or `workflows/` may change. If any do, stop and remove unrelated changes before handoff.

- [ ] **Step 6: Commit documentation**

```powershell
git add README.md config.example.json
git commit -m "docs: document controller daemon v1"
```

- [ ] **Step 7: Run verification-before-completion fresh on final HEAD**

After the documentation commit, rerun:

```powershell
python -m pytest -q
python -m compileall -q src
git status --short
git rev-parse HEAD
git diff --name-only 425ad97c508c4f55f7d7052435a7a2cb4aa3b015...HEAD
```

Required evidence before any completion claim:

- exact final implementation commit SHA;
- exact implementation branch name;
- fresh Python version;
- fresh full pytest count/result;
- compile PASS;
- focused daemon suite PASS;
- lock contention regression PASS;
- preflight non-mutation regression PASS;
- Windows deployment-contract tests PASS;
- scope integrity PASS;
- clean worktree;
- merge = NO;
- production activation = NO;
- next owner = DUNCAN independent QC.

The durable handoff must be named `LESTER_ZB_CONTROLLER_DAEMON_V1_IMPLEMENTATION_READY` and must contain real observed values for every evidence item above. Do not use guessed or inherited test counts, branch names, or commit SHAs.

---

## Post-Implementation Gate Sequence

The implementation issue stops after Lester's exact-head handoff. JINGO then creates a separate DUNCAN independent-QC assignment against that exact HEAD. Only a DUNCAN PASS authorizes the owner-PC live Windows smoke. The live smoke must then prove real Task Scheduler registration, automatic daemon start, healthy heartbeat, duplicate `--once` rejection, forced-process restart recovery, and one disposable/controlled task consumption without manually invoking the controller. Production activation is a separate OWNER/JINGO gate after that smoke; Reference Bridge v1 starts only after Controller Daemon v1 is production-active.
