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
