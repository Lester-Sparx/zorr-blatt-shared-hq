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
