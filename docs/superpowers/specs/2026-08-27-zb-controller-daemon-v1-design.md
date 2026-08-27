# ZB Controller Daemon v1 Design

**Status:** OWNER-APPROVED DESIGN / SPEC REVIEW PENDING  
**Issue:** #73  
**Approved design decision:** `APPROVE ZB CONTROLLER DAEMON V1 DESIGN`  
**Base controller HEAD:** `425ad97c508c4f55f7d7052435a7a2cb4aa3b015`  
**Base controller branch:** `agent-controller/salvador-v1-task8-repair`

## 1. Purpose

ZB Controller Daemon v1 removes the manual PowerShell polling relay from the local ZORR BLATT agent workflow.

Today the controller already has a continuous loop, but production use has been driven manually with `--once`. Daemon v1 turns that existing controller into a current-user Windows background process that starts at logon, stays alive, prevents duplicate controller instances, exposes inspectable local health, and recovers from process failure without changing any task-state truth law.

The target operator experience after activation is:

```text
JINGO creates a valid GitHub task
        -> owner PC controller is already running
        -> controller discovers the task
        -> existing backend executes it
        -> GitHub receives truthful RUNNING / RESULT_READY / FAILED events
```

The owner must not need to open PowerShell for routine controller polling.

## 2. Scope Boundary

### Included in v1

- Windows current-user autostart at interactive logon.
- Continuous controller polling without `--once`.
- One-controller-instance protection across daemon and manual controller modes.
- Durable local PID/instance/heartbeat health evidence.
- Bounded rotating local logs.
- Explicit operational error classification.
- Automatic process restart after an unexpected daemon exit.
- Idempotent install, uninstall, status, enable/disable, start/stop/restart operations.
- Exact production config path and exact Python executable captured by deployment.
- Owner-PC live smoke proving autostart, single-instance behavior, restart, and real task consumption without manual controller invocation.

### Explicitly out of scope

- Reference-file transport from ChatGPT to Windows.
- Google Drive bridge implementation.
- Automatic creation of GitHub agent tasks by the daemon.
- ComfyUI installation, update, model download, model selection, or profile mutation.
- ComfyUI lifecycle management/autostart. Daemon v1 owns controller communication only.
- SALVADOR workflow, model, prompt, denoise, dimensions, or canon changes.
- Babylon integration.
- Native Windows Service / NSSM / pywin32 service.
- Tray UI.
- Remote desktop or arbitrary PC control.
- New paid services or remote inference.

Reference Bridge v1 is a separate subproject and begins only after Controller Daemon v1 passes independent QC and owner-PC live smoke.

## 3. Existing Truth That Must Not Change

Daemon v1 is a deployment/lifecycle layer around the accepted local controller. It must preserve the existing state machine exactly:

```text
ASSIGNED != RUNNING
```

`RUNNING` requires a real non-empty backend execution/prompt id. `RESULT_READY` requires real result bytes, checksum, and required production provenance. A local daemon heartbeat is never agent-task evidence and can never substitute for GitHub task-state evidence.

The accepted SALVADOR production profile remains external and unchanged:

- implementation authority: `425ad97c508c4f55f7d7052435a7a2cb4aa3b015`;
- model/profile/workflow/prompt/denoise/dimensions: unchanged by this project;
- no model substitution;
- no canon writeback.

## 4. Architectural Choice

v1 uses **Windows Task Scheduler + a controller daemon mode**, not a native Windows Service.

Reasoning:

- `gh` authentication already belongs to the interactive user profile;
- ComfyUI and production files are already user-session resources;
- current-user Task Scheduler avoids service-account credential duplication;
- native service privileges add no v1 product value;
- the scheduled task can enforce one scheduled instance and restart after process failure;
- the controller itself enforces a process lock, so correctness does not depend only on Task Scheduler.

The scheduled task is deployment infrastructure. The Python daemon owns controller-cycle health semantics. GitHub remains the durable task-state source of truth.

## 5. Runtime Flow

At Windows logon:

```text
Task Scheduler
  -> exact python.exe
  -> python -m zb_local_controller --daemon --config <production-config>
  -> acquire controller instance lock
  -> write STARTING health snapshot
  -> validate configuration + GitHub authentication
  -> enter repeated controller cycles
  -> write heartbeat after each cycle
```

For each cycle:

```text
DaemonRunner
  -> Controller.run_once()
  -> existing GitHub discovery / backend / state logic
  -> health snapshot only
  -> sleep pollIntervalSeconds
```

The daemon does not interpret artistic intent, modify task bodies, create production tasks, or alter backend policy.

## 6. CLI Contract

The existing `--once` interface remains valid for tests and explicit maintenance when no other controller instance owns the lock.

v1 adds an explicit production daemon mode:

```text
python -m zb_local_controller --daemon --config <path>
```

`--once`, `--daemon`, and `--daemon-preflight` are mutually exclusive.

The existing no-flag continuous behavior remains as a legacy compatibility mode and must acquire the same global execution lock as `--once` and `--daemon`. It is not used by the production scheduled task.

The production scheduled task always uses `--daemon`.

v1 requires a non-mutating preflight mode:

```text
python -m zb_local_controller --daemon-preflight --config <path>
```

Preflight validates configuration, writable runtime paths, Python/runtime compatibility, and GitHub authentication. It must not discover, submit, or poll agent tasks and must not require a running ComfyUI instance.

## 7. Global Single-Instance Law

A daemon alone is insufficient protection because an operator could accidentally launch `--once` while the daemon is already running. Therefore v1 introduces one **controller instance lock** shared by all real controller execution modes.

Lock root comes from `daemonRuntimeRoot` and defaults to:

```text
D:\BLATT2\ZB_AGENT_RUNTIME\controller-daemon\
```

Default lock file:

```text
controller.lock
```

Rules:

- daemon acquires an exclusive OS-backed lock before any GitHub task processing;
- `--once` and legacy continuous controller execution acquire the same lock;
- preflight/status operations do not acquire the execution lock;
- a second controller process must fail before task discovery or backend submission;
- lock contention produces machine-readable `CONTROLLER_INSTANCE_BUSY`;
- stale file presence alone is not proof of a live lock; correctness comes from the OS lock, not file existence;
- process exit releases the lock automatically;
- no force-delete of a live lock is permitted.

The implementation uses only Python standard-library OS locking: `msvcrt.locking(..., LK_NBLCK, ...)` on Windows. A POSIX `fcntl.flock(..., LOCK_EX | LOCK_NB)` adapter is permitted only to preserve equivalent unit-test/development semantics outside Windows; Windows `msvcrt` behavior is the production authority. No third-party lock dependency is allowed in v1.

## 8. Daemon Configuration and Health Model

`ControllerConfig` gains exactly one daemon path setting in v1:

```text
daemonRuntimeRoot
```

Default:

```text
D:\BLATT2\ZB_AGENT_RUNTIME\controller-daemon
```

No daemon log-size or scheduler-restart tuning is exposed as production config in v1; those values are locked below so deployments do not silently drift.

Daemon health is **local operational evidence**, not production canon and not agent task state.

Files under `daemonRuntimeRoot`:

```text
health.json
controller-daemon.log
controller-daemon.log.1 ... bounded backups
controller.lock
```

`health.json` is replaced atomically. Minimum schema:

```json
{
  "schemaVersion": "zb-controller-daemon-v1",
  "state": "HEALTHY",
  "pid": 1234,
  "instanceId": "uuid",
  "startedAtUtc": "2026-08-27T00:00:00Z",
  "heartbeatAtUtc": "2026-08-27T00:00:15Z",
  "repository": "Lester-Sparx/zorr-blatt-shared-hq",
  "configSha256": "64-hex",
  "pollIntervalSeconds": 15.0,
  "lastCycle": {
    "discovered": 4,
    "processed": 0,
    "submitted": 0,
    "skipped": 4
  },
  "lastErrorCode": null
}
```

Allowed health states:

- `STARTING` — process owns the lock and is validating startup.
- `HEALTHY` — most recent controller cycle completed normally.
- `DEGRADED` — a recoverable operational dependency failed, no task-state fabrication occurred, daemon will retry.
- `FATAL` — non-recoverable startup/runtime condition caused a non-zero exit.
- `STOPPING` — graceful stop path when available.

Health does not contain GitHub tokens, model bytes, prompt text, reference image bytes, or other secrets.

`configSha256` is a hash of the config file bytes, not the config contents.

## 9. Logging

Use Python standard-library logging with a rotating file handler.

Required properties:

- UTF-8 text;
- UTC timestamps;
- PID and daemon instance id;
- INFO for startup, cycle summary, shutdown;
- WARNING for recoverable dependency failures;
- ERROR/exception trace for fatal unexpected failure;
- bounded disk usage.

Locked v1 bounds:

```text
maxBytes = 2097152
backupCount = 5
```

Logs must not print GitHub credentials, full config contents, image bytes, or secret environment variables.

## 10. Error Classification and Recovery

### Fatal before task processing

Examples:

- invalid controller configuration;
- invalid/unavailable required Python runtime;
- runtime root cannot be created/written;
- GitHub CLI unavailable;
- GitHub authentication invalid at daemon startup;
- controller instance lock already owned by another process.

Behavior:

- write `FATAL` when possible;
- do not process tasks;
- exit non-zero;
- scheduled-task restart policy retries according to the locked bounded settings.

### Recoverable operational failure

Example:

- transient GitHub command/list failure represented by the existing operational GitHub error class rather than authentication/configuration failure.

Behavior:

- write `DEGRADED` with a narrow error code;
- do not invent task state;
- preserve existing local execution journal semantics;
- sleep/back off at least the configured poll interval;
- retry next cycle.

### Unexpected exception

Behavior:

- log traceback;
- write `FATAL` when possible;
- release process lock by process termination;
- exit non-zero;
- Task Scheduler restarts the daemon according to the locked restart policy.

Backend/task failures already handled by the existing `Controller` remain task-level outcomes and must not automatically kill the daemon.

## 11. Task Scheduler Deployment Contract

Scheduled task canonical name:

```text
ZB Controller Daemon v1
```

Required deployment properties:

- trigger: current owner user logon;
- principal: current user interactive token;
- run level: limited/current-user, not elevated administrator by default;
- action executable: the exact `python.exe` resolved during install;
- action arguments: `-m zb_local_controller --daemon --config "<absolute-config-path>"`;
- working directory: exact deployed `agent-controller` directory;
- multiple instance policy: ignore/reject new scheduled instance;
- start when available: enabled;
- restart on process failure: enabled;
- restart interval: exactly 1 minute;
- restart count: exactly 5;
- execution time limit: disabled for the long-running daemon;
- do not stop merely because the machine switches to battery power;
- task may stop at user logoff and will start again on the next logon;
- installation must not require storing the user's plaintext Windows password.

If Windows policy prevents current-user task creation without elevation, installation fails explicitly; it must not silently fall back to an elevated/system service.

## 12. Deployment Operations

Repository-owned Windows deployment tooling lives under:

```text
agent-controller/deploy/windows/
```

Required operator capabilities:

- install/update daemon task idempotently;
- uninstall it idempotently;
- read status without mutating task processing;
- start;
- stop;
- restart;
- enable;
- disable.

Install rules:

- resolve and record exact Python executable;
- require absolute production config path;
- require absolute working directory;
- run `--daemon-preflight` before replacing a known-good registration;
- create/update the scheduled task deterministically;
- start the task after successful install unless explicitly suppressed for QC;
- repeated install with identical inputs converges to the same task definition.

Uninstall rules:

- stop the scheduled task if running;
- unregister only the canonical daemon task;
- do not delete user production config;
- do not delete SALVADOR results/inbox;
- runtime health/log deletion is optional only when explicitly requested.

## 13. Status Contract

The status operation combines Task Scheduler state with local health evidence. It must never call `Controller.run_once()`.

Machine-readable output includes at least:

```text
ZB_CONTROLLER_DAEMON_STATUS_V1
TASK_REGISTERED = YES|NO
TASK_ENABLED = YES|NO
TASK_STATE = <scheduler state>
HEALTH_STATE = STARTING|HEALTHY|DEGRADED|FATAL|STOPPING|MISSING|STALE
PID = <integer|NONE>
PID_ALIVE = YES|NO|UNKNOWN
INSTANCE_ID = <uuid|NONE>
HEARTBEAT_AGE_SEC = <number|NONE>
CONFIG_SHA256 = <64-hex|NONE>
```

A heartbeat is `STALE` when it is older than:

```text
max(60 seconds, 3 * pollIntervalSeconds)
```

A stale health file cannot be reported as healthy merely because the scheduled task exists.

## 14. Shutdown / Disable Semantics

The owner must always be able to stop automation intentionally.

- `Stop` stops the current scheduled task process but leaves future logon/start capability intact.
- `Disable` prevents automatic/start requests until re-enabled.
- `Enable` restores registration eligibility but does not fabricate a running state.
- `Restart` is stop then start against the canonical scheduled task.
- `Uninstall` removes the scheduled task registration.

No stop/disable operation may mutate GitHub task states to `FAILED` merely because the local daemon was intentionally stopped.

## 15. Relationship to ComfyUI

Controller Daemon v1 does **not** start or update ComfyUI.

If a production task arrives while the configured backend is unavailable, the existing backend/controller failure semantics remain authoritative. A future backend-lifecycle gate may add on-demand/autostart behavior, but it must not be smuggled into communication daemon v1.

This separation is intentional: controller communication and GPU application lifecycle are independent concerns.

## 16. Relationship to Reference Bridge v1

Reference Bridge v1 is not implemented by this spec.

After Daemon v1 production activation, the next architecture gate evaluates a transport such as:

```text
ChatGPT attachment
  -> connected Google Drive drop
  -> owner-PC Drive sync
  -> validated local bridge
  -> D:\BLATT2\ZB_AGENT_INBOX\<TASK_ID>\
```

The bridge must have its own file-integrity, task-id binding, duplicate, and security rules. Daemon v1 must not assume that bridge exists.

## 17. Proposed Code Boundaries

The implementation plan may refine filenames, but responsibilities must remain separated:

- `instance_lock` unit — OS-backed exclusive controller lock only.
- `daemon_health` unit — atomic health snapshot + rotating logger configuration.
- `daemon_runner` unit — cycle loop, error classification, heartbeat, shutdown.
- existing `Controller` — task state machine and backend coordination; do not absorb scheduler/deployment concerns.
- CLI entrypoint — mode selection and wiring only.
- Windows deployment scripts — scheduled-task installation/control/status; no agent-state logic.

Do not turn `controller.py` into a daemon/deployment monolith.

## 18. Automated Test Requirements

### Instance lock

- first lock acquisition succeeds;
- concurrent second acquisition fails before task discovery;
- release permits a later process to acquire;
- stale lock-file bytes alone do not block a new process when no OS lock is held.

### Health

- STARTING/HEALTHY/DEGRADED/FATAL records use the exact schema;
- atomic replacement never exposes partial JSON in unit tests;
- config SHA is stable for identical bytes;
- no config contents or credentials are written;
- heartbeat updates after each cycle.

### Daemon runner

- healthy cycles repeat and preserve `RunSummary` values in health;
- recoverable GitHub operational error marks DEGRADED then retries;
- fatal configuration/auth failure performs zero task processing and exits non-zero;
- unexpected exception produces fatal evidence and non-zero exit;
- backend task-level failure does not terminate the daemon when the existing controller reports normally;
- stop signal/KeyboardInterrupt releases the lock.

### CLI

- `--once`, `--daemon`, and `--daemon-preflight` are mutually exclusive;
- all task-processing modes, including legacy no-flag continuous mode, share the same execution lock;
- preflight does not discover or submit tasks;
- existing `--once` behavior remains regression-tested when no daemon owns the lock.

### Deployment tooling

Automated tests verify declared task settings and command quoting without requiring a real Windows scheduler. Real registration is verified only in owner-PC live smoke.

Full existing controller/SALVADOR test suite must remain green.

## 19. Independent QC Requirements

DUNCAN reviews an exact implementation HEAD and independently verifies:

- scope matches this spec;
- no SALVADOR production profile drift;
- full automated tests and compile checks;
- instance lock actually precedes task discovery;
- health is not confused with task truth;
- fatal/recoverable classifications do not fabricate GitHub states;
- logs are bounded and do not leak secrets;
- deployment task definition is current-user, non-elevated by default, one-instance, autostarting, and restart-capable;
- uninstall/control operations cannot delete canon/results/config;
- no Reference Bridge/Babylon/ComfyUI lifecycle scope leaked in.

DUNCAN PASS authorizes owner-PC live smoke only, not production activation.

## 20. Owner-PC Live Smoke

Live smoke is disposable and uses the exact DUNCAN-approved implementation HEAD.

Required checks:

1. Fresh implementation is installed on the owner PC.
2. Existing controller tests pass locally.
3. Daemon preflight passes against the real production config and `gh` auth.
4. Install registers canonical scheduled task with expected current-user settings.
5. Starting the scheduled task produces a fresh `HEALTHY` heartbeat without manual `--once`.
6. Attempting a second controller process is rejected before GitHub discovery/backend submission.
7. A disposable valid agent task is created while daemon is already running; daemon discovers/processes it without the owner invoking the controller manually.
8. Durable task events preserve the existing truthful state law.
9. Kill the daemon process unexpectedly; Task Scheduler restarts it within the configured restart policy window and a new instance id/heartbeat appears.
10. Disable the scheduled task; confirm it does not auto-run. Re-enable/start; confirm health returns.
11. Run status and verify scheduler state, PID liveness, heartbeat freshness, and config SHA are coherent.
12. Verify no SALVADOR runtime-profile change, model change, prompt change, denoise change, dimension change, canon writeback, or duplicate task submission occurred.

A production character image is not required for this infrastructure smoke. Prefer a disposable non-canon controller/backend fixture unless a live SALVADOR backend proof is explicitly separately authorized.

## 21. Acceptance Criteria

Controller Daemon v1 passes only if all are true:

1. No routine PowerShell controller polling is required after Windows logon.
2. Canonical scheduled task starts the daemon in the current user context.
3. Exact Python executable, working directory, and config path are deterministic and inspectable.
4. All task-processing modes share one OS-backed instance lock.
5. A second controller cannot reach task discovery/submission while the lock is owned.
6. Health heartbeat is atomic, inspectable, freshness-aware, and separate from GitHub task truth.
7. Logs are bounded and secret-safe.
8. Transient operational failures retry without state fabrication.
9. Fatal startup/auth/config failure fails closed.
10. Unexpected process failure is restarted by Task Scheduler under the exact bounded policy.
11. Owner can status/start/stop/restart/enable/disable/uninstall without modifying production task truth.
12. Existing controller/SALVADOR tests pass with no semantic regression.
13. DUNCAN independently passes the exact implementation HEAD.
14. Owner-PC live smoke passes autostart, duplicate rejection, real task consumption, restart, and disable/enable checks.
15. SALVADOR profile and canon remain unchanged.

## 22. Authority and Gate Law

Design approval authorizes this formal spec only.

Spec approval authorizes implementation planning only.

Implementation planning approval/authorization is required before LESTER writes production code. LESTER implementation does not self-approve. DUNCAN independent QC is required before owner-PC live smoke. Live smoke PASS does not itself authorize merge or unrelated integrations.

No merge and no production activation occur without their explicit later gates.

## 23. Required Sequence

```text
OWNER DESIGN APPROVAL
  -> FORMAL SPEC
  -> OWNER SPEC REVIEW
  -> IMPLEMENTATION PLAN
  -> LESTER TDD IMPLEMENTATION
  -> DUNCAN INDEPENDENT QC
  -> OWNER-PC LIVE AUTOSTART/RESTART SMOKE
  -> OWNER PRODUCTION ACTIVATION GATE
  -> REFERENCE BRIDGE v1 DESIGN/FEASIBILITY GATE
```

## 24. Success Definition

ZB Controller Daemon v1 succeeds when the owner logs into Windows and the local controller becomes a continuously available, one-instance, observable, self-recovering communication worker that consumes valid GitHub tasks without manual polling commands, while preserving every existing SALVADOR/task-state truth boundary.