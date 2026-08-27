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

## ZB Controller Daemon v1 operations

Daemon v1 is a lifecycle/deployment layer around the accepted controller. It does not change controller task-state truth or SALVADOR production settings.

Preflight is non-mutating and does not discover/process tasks or require ComfyUI:

```powershell
python -m zb_local_controller --daemon-preflight --config 'D:\BLATT2\ZB_AGENT_CONFIG\salvador-canon-reference-edit.json'
```

Manual foreground daemon execution for maintenance:

```powershell
python -m zb_local_controller --daemon --config 'D:\BLATT2\ZB_AGENT_CONFIG\salvador-canon-reference-edit.json'
```

Install the current-user scheduled task after the separate QC/live-smoke gate authorizes owner-PC deployment:

```powershell
.\deploy\windows\ZbControllerDaemon.ps1 -Action Install -ConfigPath 'D:\BLATT2\ZB_AGENT_CONFIG\salvador-canon-reference-edit.json' -WorkingDirectory 'D:\BLATT2\zb-local-agent-controller\agent-controller'
```

Read scheduler + local health evidence without controller processing:

```powershell
.\deploy\windows\ZbControllerDaemon.ps1 -Action Status -ConfigPath 'D:\BLATT2\ZB_AGENT_CONFIG\salvador-canon-reference-edit.json'
```

`--once` remains maintenance/testing-only once the daemon is active. It uses the same OS-backed controller lock and returns `CONTROLLER_INSTANCE_BUSY` while the daemon owns that lock.

Daemon v1 explicitly does **not**:

- start, stop, install, update, or otherwise manage ComfyUI;
- move ChatGPT attachments or implement any Reference Bridge / Google Drive transport;
- create GitHub agent tasks;
- change the SALVADOR model/profile/workflow/prompt/denoise/dimensions;
- integrate Babylon;
- mutate canon or activate production.

Owner-PC Task Scheduler registration and live daemon smoke are a later gate after DUNCAN independent QC; they are not part of implementation verification.

## ZORR Reference Bridge v1 — implementation boundary

Reference Bridge v1 is a **separate sibling process** (`zb_reference_bridge`). GitHub remains task authority and durable evidence; Google Drive carries image bytes only. The bridge validates one `ZB_REFERENCE_DELIVERY_V1` against the exact task, synced source size/SHA256/extension/MIME/magic, stages on the local `D:` volume, atomically publishes into `D:\BLATT2\ZB_AGENT_INBOX\<TASK_ID>\`, and posts only `ZB_REFERENCE_EVENT_V1` transport results.

Important authority rules:

- cloud upload or Drive sync completion is **not** local reference readiness;
- `REFERENCE_READY` is emitted only after validated atomic inbox publish;
- Reference Bridge never writes `ZB_AGENT_EVENT_V0` and never executes SALVADOR tasks;
- Controller Daemon remains independent and unchanged;
- accepted inbox references are never automatically overwritten or deleted on conflict.

Operator commands after the separate independent-QC and owner-PC setup gates:

```powershell
python -m zb_reference_bridge --preflight --config .\reference-bridge.local.json
python -m zb_reference_bridge --once --config .\reference-bridge.local.json
python -m zb_reference_bridge --status --config .\reference-bridge.local.json
.\deploy\windows\ZbReferenceBridge.ps1 -Action Install -ConfigPath .\reference-bridge.local.json -WorkingDirectory 'D:\BLATT2\zb-local-agent-controller\agent-controller'
```

`reference-bridge.config.example.json` is explicitly non-production. Google Drive for desktop is required later on the owner PC, but **is not installed by this implementation**. The exact private Drive drop-folder ID and exact local sync root are discovered/materialized only during the post-Duncan owner-PC setup gate. Mirror/local-backed Drive mode is preferred there to reduce placeholder ambiguity, while bridge byte validation remains authoritative regardless of sync mode.

No production Reference Bridge config is created or activated by this implementation, and no owner-PC smoke is performed before independent QC.
