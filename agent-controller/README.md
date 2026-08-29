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

## SALVADOR v1 CANON_REFERENCE_EDIT — implemented, not activated

`CANON_REFERENCE_EDIT` is a separate production-capable local ComfyUI path beside the existing disposable `PRODUCTION_IMAGE_EDIT` / `ImageInvert` smoke path. The production path is reference-first img2img only: one existing drawn character reference is deterministically staged and normalized without crop or upscale, then processed by the repository-owned canon prompt and SD1.5-class img2img workflow.

The exact checkpoint filename is deployment-owned configuration (`canonModelName`). The example configuration intentionally leaves it empty, so the production backend fails closed and remains deactivated until an operator selects an already-installed compatible model after the independent QC gate. No model is downloaded or auto-selected by the controller.

Operator flow:

```text
1. Put exactly one drawn reference in D:\BLATT2\ZB_AGENT_INBOX\<TASK_ID>\ where <TASK_ID> is the task's strict machine ID.
2. Configure the exact already-installed SD1.5-class checkpoint filename as canonModelName in local deployment config.
3. Create a GitHub task with TASK_KIND = CANON_REFERENCE_EDIT.
4. Run controller from the agent-controller working directory with that local config.
5. RUNNING requires a real prompt_id; RESULT_READY requires local result files/checksum/provenance.
6. Implementation merge is not production activation.
```

The task text cannot choose a filesystem path or checkpoint filename. Chat attachment -> Windows inbox transport is not part of SALVADOR v1.

`PRODUCTION_ACTIVATION = NO` until the separately owned QC/live-smoke/owner activation gates are completed.
