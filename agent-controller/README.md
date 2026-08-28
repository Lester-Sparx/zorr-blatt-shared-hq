# ZB Local Agent Controller v0

Zero-budget Windows-local controller for fixed-contract ZORR BLATT agent tasks.

## Mocked-green boundary

Tasks 1–6 implement and test the controller machinery only. They do **not** download or require a production model and do **not** run live SALVADOR generation.

Implemented v0 mocked components:

- strict `ZB_AGENT_TASK_V0` parser;
- exact state transition table;
- fixed-root local inbox/result safety;
- durable metadata-only GitHub events through fixed `gh` argv;
- mocked ComfyUI evidence adapter where RUNNING requires a non-empty `prompt_id`;
- orchestration, duplicate suppression, atomic result persistence, restart-safe one-active-SALVADOR GPU locking, and durable event reconciliation;
- local accepted-execution journal for prompt/event crash recovery and a deployment-owned execution deadline (`maxExecutionSeconds`);
- Windows launcher and one-cycle CLI.

## Local target

```text
CONTROLLER_DIR = D:\BLATT2\zb-local-agent-controller
INBOX_ROOT = D:\BLATT2\ZB_AGENT_INBOX
RESULT_ROOT = D:\BLATT2\ZB_AGENT_RESULTS
COMFYUI_URL = http://127.0.0.1:8188
```

Python 3.12+ and authenticated GitHub CLI (`gh auth status`) are required for real polling.

## Verification

```powershell
python -m pytest -q
python -m zb_local_controller --once
```

`--once` returns `0` after a normal cycle, including no eligible tasks. Configuration failures such as missing/unauthed GitHub CLI return non-zero and never fabricate RUNNING.

Task Scheduler installation and live ComfyUI/model setup are deliberately deferred until after mocked Tasks 1–6 are accepted.

## Controller daemon deployment tooling

The repository includes `deploy/windows/ZbControllerDaemon.ps1` for current-user Task Scheduler lifecycle operations (`Install`, `Status`, `Start`, `Stop`, `Restart`, `Enable`, `Disable`, `Uninstall`). The daemon uses `daemonRuntimeRoot`, one-instance locking, bounded health/status semantics, and `--daemon-preflight` before installation.

This integration does **not** install, start, enable, or otherwise activate the daemon on the OWNER workstation. Those are later explicit owner-PC operations. Repository integration or merge therefore means `PRODUCTION_ACTIVE = NO`; it does not authorize production activation, canon mutation, auto-merge, or OWNER LOCK.

## Reference Bridge deployment tooling

`zb_reference_bridge` is a sibling byte-transport process. GitHub task/evidence state remains authoritative; the Drive sync root is only a transport source, and a cloud-synced file is not `REFERENCE_READY` until validation and atomic local publication succeed. The bridge emits only `ZB_REFERENCE_EVENT_V1`; it does not emit `ZB_AGENT_EVENT_V0` or Communication-Orchestrator messages and does not route logical roles.

The repository includes `deploy/windows/ZbReferenceBridge.ps1` for a separate current-user, non-elevated Task Scheduler entry. Installation, start, enablement, and physical owner-PC activation are **not** performed by this integration. Historical authorization is not proof that the physical bridge is active now, therefore `PRODUCTION_ACTIVE = NO` until a later explicit activation/proof gate.

## Read-only owner console

Install the local `zb` PowerShell command once:

```powershell
cd D:\BLATT2\zb-local-agent-controller
powershell -ExecutionPolicy Bypass -File .\scripts\install-zb-console.ps1
```

Use it from any working directory:

```powershell
zb
zb why
zb agents
zb gates
zb scout
zb output
zb watch
```

Console v0 is read-only. It reads the latest valid `ZB_OWNER_VIEW_V0`
snapshot from Shared HQ issue #39 and validated local results under the
configured result root. It cannot post comments, submit jobs, merge or
approve changes, activate production, mutate canon, or create OWNER LOCK.

`zb output` opens only a `result.png` whose PNG signature and SHA-256 match
its parseable `result.json`. A local result never establishes production or
canon approval by itself.

## Communication Orchestrator v0 — initial four-role core

The initial automated communication contour contains exactly four logical roles: `JINGO`, `LESTER`, `DUNCAN`, and `DJANGO`. `OWNER` is a human-only gate and is never auto-executed. SALVADOR, LYNCH, MAO, CHARLIE, and MEMORO remain outside this initial automated routing contour.

The repository package `zb_communication_orchestrator` is transport-agnostic deterministic authority logic. The external ChatGPT Work adapter supplies the authenticated top-level GitHub comment event, connected GitHub reads/writes, and the real logical-role execution surface. The repository handler does not poll GitHub for communication messages, store a PAT, switch GitHub accounts, launch role subprocesses, merge PRs, activate production, mutate canon, or create OWNER LOCK.

Live routing law is `ZB_AGENT_MESSAGE_V1 -> verified RECEIVED -> actual execution start -> verified RUNNING -> verified RESULT/BLOCKED/DEAD_LETTER -> verified owner view -> at most one next legal message`. Every authoritative write requires a remote comment ID plus fresh exact-ID read-back match before the transaction advances. The permanent Communication PR and real Work-webhook proof are separate downstream operational gates; this implementation does not create or activate them.
