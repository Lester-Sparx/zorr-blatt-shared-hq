# SHERIFF V1 ONE-PASS Windows Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the fragile runtime-patched Windows deployment path with one canonical, idempotent `SheriffHost.ps1` that preflights all known host prerequisites, repairs them, starts the proven SHERIFF runtime, and performs the existing production verify gate without indefinite native-command hangs.

**Architecture:** One PowerShell 5.1-compatible production script owns PRECHECK -> REPAIR -> optional one-shot reboot resume -> INSTALL -> VERIFY. Native tools run through one bounded process runner that captures stdout/stderr/exit code. Legacy `ZbSheriffV1.ps1` and `BootstrapSheriffV1Host.ps1` remain only as migration reference and are removed from the authoritative runner path.

**Tech Stack:** Windows PowerShell 5.1, Windows optional features/capabilities, Podman 5.8.5 on Windows 10 / Podman 6.1.0 on Windows 11, Docker Compose CLI 5.5.0 provider, Task Scheduler, existing SHERIFF V1 Compose/runtime.

**Spec:** `docs/superpowers/specs/2026-08-29-sheriff-one-pass-base-design.md`

## Global Constraints

- Authoritative SHERIFF runtime remains `47a92fc4a0d685e1a892285c568a59dfc5ccac82`.
- Windows 10 supported floor remains build `19043`; owner-PC observed build is `19044`.
- Windows 10 runtime pin remains Podman `v5.8.5`, SHA256 `a2d78a2460dc4745684ee443ced8878fbf3a2fe4d8c620a290500e85367d2a33`, WSL provider.
- Windows 11 runtime pin remains Podman `v6.1.0`, SHA256 `1958aac22abb3a9cf7b52626c71ba1a26015c323f0b5fa74671e303b22b043d3`.
- Compose remains `v5.5.0`, SHA256 `51e1e61195f3616896265487ed64551095f3bd27ac7fbd5758d3538c3bfa1b19`.
- No SHERIFF policy/schema/service/event-semantic change.
- No Docker Desktop, OpenSSH Server, new daemon, self-hosted runner, or V2 work.
- Production PASS requires fresh owner-PC evidence; CI PASS is not production PASS.

---

### Task 1: Canonical one-pass host installer + RED behavior tests

**Files:**
- Create: `config/sheriff/deploy/windows/SheriffHost.ps1`
- Create: `tests/sheriff_windows_one_pass_behavior.ps1`
- Modify: `tests/test_sheriff_windows_runtime_selection.py`

**Interfaces:**
- Produces user actions: `RunToPass`, `Preflight`, `Verify`, `Status`, `Uninstall`.
- Produces pure planning function `Get-RepairPlan([pscustomobject]$State)` for deterministic behavior tests.
- Produces native runner `Invoke-NativeProcess(FilePath, Arguments, TimeoutSeconds)` returning `ExitCode`, `StdOut`, `StdErr` and throwing `NATIVE_TIMEOUT:*` on timeout.

- [ ] Write RED tests proving: no `Patch-*` critical path; WSL/OpenSSH repair ordering; missing VM -> init/start; existing VM -> no init; expected native stderr is data, not PowerShell termination; native process timeout is bounded; repeat healthy RunToPass plans no destructive repair; exact runtime/pins retained.
- [ ] Run RED tests and prove failure because `SheriffHost.ps1` does not yet exist.
- [ ] Implement the minimal canonical installer by consolidating already-proven host/runtime functions directly, with one bounded native runner and full precheck.
- [ ] Run Windows behavior + Python contract tests to GREEN.
- [ ] Commit exact Task 1 candidate.

### Task 2: Make ONE-PASS the only authoritative runner path

**Files:**
- Modify: `config/sheriff/deploy/windows/RUN_TO_PRODUCTION_PASS.cmd`
- Modify: `.github/workflows/sheriff-windows-bootstrap-validate.yml`
- Modify: `tests/test_sheriff_windows_production.py`

**Interfaces:**
- `RUN_TO_PRODUCTION_PASS.cmd` calls only `SheriffHost.ps1 -Action RunToPass`.
- Windows workflow parses `SheriffHost.ps1` with Windows PowerShell 5.1 and executes deterministic one-pass behavior tests.

- [ ] Write/adjust RED assertions that the runner and workflow must reference `SheriffHost.ps1` and must not invoke legacy bootstrap/deployer patch flow.
- [ ] Run RED.
- [ ] Switch runner/workflow to canonical installer; mark legacy scripts non-authoritative without deleting historical evidence.
- [ ] Run focused tests to GREEN.
- [ ] Commit Task 2.

### Task 3: Fresh exact-HEAD verification + independent QC

**Files:** no production changes unless a concrete failing gate requires repair.

- [ ] Run `hq-validate`.
- [ ] Run `sheriff-oss-validate`.
- [ ] Run Windows PowerShell 5.1 one-pass validation.
- [ ] Run full `sheriff-runtime-e2e`.
- [ ] Independently review exact candidate HEAD for first-install, repeat-install, timeout, reboot-resume, and Windows10/11 selection regressions.
- [ ] Repair only evidenced findings, then rerun all affected gates.
- [ ] Merge only exact reviewed HEAD with SHA lock.

### Task 4: One physical owner-PC run and durable closure

**Files:** final launcher artifact only; no new installer generation.

- [ ] Build one launcher that downloads the exact merged `SheriffHost.ps1`, verifies exact Git blob/hash, and executes `RunToPass`; no substring checks.
- [ ] Owner runs it once.
- [ ] If it returns a new physical blocker, repair that boundary only inside `SheriffHost.ps1`; do not create another wrapper generation.
- [ ] When physical VERIFY proves `TASK_REGISTERED=YES`, `TASK_ENABLED=YES`, `STACK_SERVICES_RUNNING=PASS`, `SHERIFF_LIVE_PATH=PASS`, `WORKER_RESTART=PASS`, `SHERIFF_V1_24_7_PRODUCTION_ACTIVE=YES`, `BLOCKER=NONE`, post exact evidence to issue #181.
- [ ] Record `SHERIFF_V1_BASE = PASS / LOCKED` and stop changing the base.
