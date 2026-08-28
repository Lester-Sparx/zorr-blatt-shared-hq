# ZB Communication Foundation Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Integrate the already validated Controller Daemon v1 and Reference Bridge v1 component boundaries onto the current single-account/Console `main` without importing unrelated SALVADOR canon work, rewriting historical evidence, mutating PR #103, or activating production.

**Architecture:** Reconstruct the daemon narrowly against current `main`, copy the bridge only from its bridge-specific validated range, and prove provenance with exact source heads. Current `zb_local_controller` remains the task/execution authority; `zb_reference_bridge` remains a sibling byte-transport process. The integration PR contains no Communication Orchestrator routing behavior.

**Tech Stack:** Python 3.12, pytest, Windows PowerShell Task Scheduler scripts, existing GitHub/`gh` local controller boundary.

**Spec:** `docs/superpowers/specs/2026-08-28-zb-communication-orchestrator-v0-design.md` at approved HEAD `9c9f0ebbf2bd5d5dc5b21578718f1ef356e278f9`.

**Global Constraints:**
- Execution branch MUST start from a fresh protected `main` read at implementation time; abort/rebase on CAS drift before opening PR B.
- Historical daemon authority source: `9e2ccfbaca88a95eac2e119e5eac720f9074dd35`.
- Historical Reference Bridge authority source: `cea94c518e6f5f3e58b084d58a28be9e8d2fa205`; bridge-specific range is `9e2ccfbaca88a95eac2e119e5eac720f9074dd35..cea94c518e6f5f3e58b084d58a28be9e8d2fa205`.
- Do NOT merge/cherry-pick the daemon lineage wholesale: it diverges from current `main` and contains unrelated canon-reference code, prompts, workflows, production policy, task-kind changes, and tests.
- Do NOT mutate or merge PR #103 and do NOT copy `zb-control/proofs/issue-102-event-proof.txt`.
- Current `ZB_AGENT_TASK_V0`, `ZB_AGENT_EVENT_V0`, SALVADOR backend semantics, single-account authority, Control Tower lock artifact, and Console read-only behavior must remain intact.
- Integration/merge is not production activation. No OWNER LOCK, canon mutation, automatic merge, or automatic activation.

---

## Task 1: Pin provenance and prove the extraction boundary

**Files:**
- Create: `agent-controller/foundation-integration-provenance.json`
- Create: `agent-controller/tests/test_foundation_integration_provenance.py`

- [ ] Write a RED test requiring a strict provenance document with exactly these component identities: daemon source HEAD `9e2ccf...`, bridge source HEAD `cea94c...`, bridge base `9e2ccf...`, approved Communication spec HEAD `9c9f0e...`, and the fresh execution base-main SHA captured when implementation starts.
- [ ] Require the provenance document to state `pr103Mutation=false`, `issue102ProofCopied=false`, `productionActivation=false`, `canonChange=false`, `ownerLock=false`.
- [ ] Run `cd agent-controller && python -m pytest tests/test_foundation_integration_provenance.py -q` and confirm RED because the manifest does not yet exist.
- [ ] Add the minimal JSON manifest satisfying the test. The execution-base SHA is the fresh protected-main SHA, never copied from this planning document if `main` moved.
- [ ] Run the same test and confirm GREEN.
- [ ] Commit: `test: pin communication foundation provenance`.

## Task 2: Reintroduce the daemon's instance lock as an isolated primitive

**Files:**
- Create: `agent-controller/src/zb_local_controller/instance_lock.py`
- Create: `agent-controller/tests/test_instance_lock.py`

- [ ] Port the daemon lock tests from the validated daemon source and add a regression proving a second processing instance fails closed while the first holds the lock.
- [ ] Run `python -m pytest tests/test_instance_lock.py -q` and confirm RED.
- [ ] Reconstruct `instance_lock.py` from the exact validated daemon source, adapting only imports/path defaults required by current `main`.
- [ ] Add a byte/semantic provenance assertion in the test or review note identifying every adaptation from source HEAD `9e2ccf...`.
- [ ] Run the targeted test and confirm GREEN.
- [ ] Run current `tests/test_controller.py` and `tests/test_cli.py` unchanged to prove no task-processing behavior changed yet.
- [ ] Commit: `feat: restore validated controller instance lock`.

## Task 3: Reintroduce daemon health and lifecycle runner without SALVADOR changes

**Files:**
- Create: `agent-controller/src/zb_local_controller/daemon_health.py`
- Create: `agent-controller/src/zb_local_controller/daemon_runner.py`
- Create: `agent-controller/tests/test_daemon_health.py`
- Create: `agent-controller/tests/test_daemon_runner.py`

- [ ] Port RED tests for schema/versioned health, PID/instance identity, heartbeat freshness, fatal/degraded states, and bounded lifecycle behavior.
- [ ] Add explicit tests that health state never fabricates GitHub task state and that a healthy daemon does not imply ComfyUI/SALVADOR availability.
- [ ] Run both test files and confirm RED.
- [ ] Reconstruct `daemon_health.py` and `daemon_runner.py` from exact source HEAD `9e2ccf...` with no canon imports or model/profile behavior.
- [ ] Run both targeted tests and confirm GREEN.
- [ ] Commit: `feat: restore validated controller daemon lifecycle`.

## Task 4: Integrate daemon CLI/config narrowly onto current controller

**Files:**
- Modify: `agent-controller/src/zb_local_controller/config.py`
- Modify: `agent-controller/src/zb_local_controller/__main__.py`
- Modify: `agent-controller/config.example.json`
- Modify: `agent-controller/tests/test_config.py`
- Modify: `agent-controller/tests/test_cli.py`

- [ ] Add RED tests for exactly one new controller config field: `daemonRuntimeRoot`; reject unknown canon/model/profile keys that are absent from current `main`.
- [ ] Add RED CLI tests for `--daemon`, `--daemon-preflight`, and one-instance enforcement across `--once` and daemon task-processing modes.
- [ ] Assert existing default behavior and `--once` semantics remain unchanged.
- [ ] Run `python -m pytest tests/test_config.py tests/test_cli.py -q` and confirm the new cases RED.
- [ ] Make the smallest config/CLI integration. Do not import `canon_reference_edit`, `production_policy`, canon prompt/workflow, or add a new task kind.
- [ ] Run targeted tests GREEN, then `python -m pytest tests/test_controller.py tests/test_task_contract.py tests/test_events.py -q` GREEN.
- [ ] Commit: `feat: integrate daemon modes on current controller`.

## Task 5: Restore Windows daemon deployment as deployment-only infrastructure

**Files:**
- Create: `agent-controller/deploy/windows/ZbControllerDaemon.ps1`
- Create: `agent-controller/tests/test_windows_deploy.py`
- Modify: `agent-controller/README.md`

- [ ] Port RED tests for idempotent install/status/enable/disable/start/stop/uninstall behavior, current-user scheduling, restart policy, correct command line, and no admin-dependent hidden mutation.
- [ ] Run `python -m pytest tests/test_windows_deploy.py -q` and confirm RED.
- [ ] Restore the validated PowerShell script from daemon HEAD `9e2ccf...`; adjust only paths/options required by the narrowed current config.
- [ ] Document that install/start is a later owner-PC gate and is not performed by this PR.
- [ ] Run the targeted test GREEN.
- [ ] Commit: `feat: restore controller daemon deployment tooling`.

## Task 6: Import Reference Bridge contracts and pure local primitives from the bridge-only range

**Files:**
- Create: `agent-controller/src/zb_reference_bridge/__init__.py`
- Create: `agent-controller/src/zb_reference_bridge/contracts.py`
- Create: `agent-controller/src/zb_reference_bridge/config.py`
- Create: `agent-controller/src/zb_reference_bridge/instance_lock.py`
- Create: `agent-controller/src/zb_reference_bridge/journal.py`
- Create: `agent-controller/src/zb_reference_bridge/local_delivery.py`
- Create: `agent-controller/src/zb_reference_bridge/publisher.py`
- Create: corresponding `agent-controller/tests/test_reference_bridge_contracts.py`, `test_reference_bridge_config.py`, `test_reference_bridge_lock.py`, `test_reference_bridge_journal.py`, `test_reference_bridge_local_delivery.py`, `test_reference_bridge_publisher.py`

- [ ] Copy the bridge tests first from the exact `9e2ccf...cea94c...` range and add one regression that current `ZB_AGENT_TASK_V0` legality is not broadened by bridge integration.
- [ ] Run these bridge tests and confirm RED because package files are absent.
- [ ] Copy the pure bridge implementation files from exact bridge HEAD `cea94c...` byte-for-byte wherever they have no current-main dependency conflict.
- [ ] Where current `zb_local_controller.task_contract` is imported, preserve current task legality; do not import historical CANON task-kind changes merely to satisfy a test.
- [ ] Run targeted tests GREEN.
- [ ] Commit: `feat: integrate validated reference bridge primitives`.

## Task 7: Integrate Reference Bridge GitHub boundary, runner, health, and CLI

**Files:**
- Create: `agent-controller/src/zb_reference_bridge/github_cli.py`
- Create: `agent-controller/src/zb_reference_bridge/bridge.py`
- Create: `agent-controller/src/zb_reference_bridge/runner.py`
- Create: `agent-controller/src/zb_reference_bridge/health.py`
- Create: `agent-controller/src/zb_reference_bridge/__main__.py`
- Create: `agent-controller/reference-bridge.config.example.json`
- Create: `agent-controller/tests/test_reference_bridge.py`
- Create: `agent-controller/tests/test_reference_bridge_github_cli.py`
- Create: `agent-controller/tests/test_reference_bridge_runner.py`
- Create: `agent-controller/tests/test_reference_bridge_health.py`
- Create: `agent-controller/tests/test_reference_bridge_cli.py`

- [ ] Port RED tests first, preserving bridge laws: GitHub is task/evidence authority, Drive transports bytes only, cloud sync is not readiness, `REFERENCE_READY` requires validated atomic local publish, terminal SALVADOR task state stops stale delivery, and bridge never emits `ZB_AGENT_EVENT_V0`.
- [ ] Run the targeted bridge suite and confirm RED.
- [ ] Copy/adapt the exact validated implementation from `cea94c...`; preserve fail-closed read/parse behavior.
- [ ] Add a regression that bridge GitHub comments do not become `ZB_AGENT_MESSAGE_V1` and bridge never routes logical roles.
- [ ] Run the bridge suite GREEN.
- [ ] Commit: `feat: integrate validated reference bridge runtime`.

## Task 8: Restore Windows Reference Bridge deployment without activating it

**Files:**
- Create: `agent-controller/deploy/windows/ZbReferenceBridge.ps1`
- Create: `agent-controller/tests/test_reference_bridge_windows_deploy.py`
- Modify: `agent-controller/README.md`

- [ ] Port RED deployment tests from bridge HEAD `cea94c...`.
- [ ] Restore the exact deployment script where compatible; require current-user task behavior and explicit config path.
- [ ] Document the existing truth gap: historical owner authorization exists, but physical production activation was not proven by the later durable record. Therefore this integration PR must report `PRODUCTION_ACTIVE = NO`.
- [ ] Run targeted deployment tests GREEN.
- [ ] Commit: `feat: restore reference bridge deployment tooling`.

## Task 9: Full foundation regression and forbidden-diff audit

**Files:**
- Verify all files changed by Tasks 1-8.
- Verify unchanged: `.github/zb/roles.yml`, `hq/policy/control-tower-v1.lock.json`, `agent-controller/src/zb_local_controller/controller.py` unless a lock integration is strictly required and independently tested, `agent-controller/src/zb_local_controller/task_contract.py`, SALVADOR workflow/prompt/backend files.

- [ ] Run `cd agent-controller && python -m pytest -q`; require zero failures.
- [ ] Run root repository suite using the same command invoked by current `hq-validate`; require zero failures.
- [ ] Run/inspect Control Tower integrity and single-account role-separation checks from protected-base workflow behavior.
- [ ] Compare candidate against fresh base and fail the task if any canon prompt/workflow/model/profile file, #102 proof fixture, PR #103 artifact, lock record, or role registry is unintentionally changed.
- [ ] Verify no new PAT/secret, auto-merge command, production activation command, canon mutation command, or OWNER LOCK command is introduced.
- [ ] Commit only if all verification is fresh and GREEN: `test: verify communication foundation integration`.

## Task 10: Open PR B and stop at independent DUNCAN QC

- [ ] Fresh-read protected `main`; if it differs from the execution base used in Task 1, rebase/re-run the full verification before opening the PR.
- [ ] Open a dedicated foundation-integration PR to `main`, explicitly listing daemon source HEAD `9e2ccf...`, bridge source HEAD `cea94c...`, execution base SHA, exact candidate HEAD, and excluded historical canon scope.
- [ ] Record required workflow/check run IDs and exact candidate HEAD.
- [ ] DUNCAN independently verifies provenance, changed-file scope, full tests, current single-account authority, Control Tower integrity, daemon truth semantics, bridge truth semantics, and absence of activation.
- [ ] Persist DUNCAN verdict with WRITE -> fresh READ-BACK -> MATCH.
- [ ] Do not merge automatically. A PASS only makes this foundation candidate legally available to the next stacked implementation contour.

**Plan exit condition:** `FOUNDATION_INTEGRATION_CANDIDATE = DUNCAN PASS`, exact candidate HEAD and remote evidence are recorded, production remains inactive, and PR #103/#102 history is untouched.