# ZORR BLATT — LOCAL Agent Controller v0 Design

Status: **ZERO-BUDGET LOCAL REDESIGN / WRITTEN SPEC FOR OWNER REVIEW**

Authority repository: `Lester-Sparx/zorr-blatt-shared-hq`

Design branch: `agent-controller/v0-design`

Supersedes the paid OpenAI-API version of this spec. The previous paid design remains in Git history only and MUST NOT be implemented.

## 1. Purpose

ZB needs real agent execution without making SPARX relay messages between ChatGPT tabs and without paid model/API usage.

Core law:

```text
ASSIGNED != RUNNING.
RUNNING requires evidence that a real local backend accepted execution.
RESULT_READY requires a real persisted result.
FAILED is explicit.
NO PAID CLOUD MODEL/API IS REQUIRED BY v0.
```

The controller does not automate ChatGPT browser tabs. It runs continuously on SPARX's Windows PC and uses GitHub only as durable coordination/state.

## 2. Recommended architecture

v0 uses a **local daemon**, not a public self-hosted GitHub Actions runner.

```text
JINGO / GitHub task
        |
        v
ZB LOCAL AGENT CONTROLLER (Windows PC)
        |
        +--> SALVADOR adapter --> local ComfyUI --> image result
        |
        +--> future LESTER adapter --> local code/LLM backend
        |
        +--> future DUNCAN adapter --> local QC backend
        |
        v
GitHub durable state: RUNNING / RESULT_READY / FAILED
```

Why local daemon is selected:

- zero per-call cost;
- can inspect local inbox files immediately;
- can call `127.0.0.1` services such as ComfyUI directly;
- can continue while no ChatGPT agent tab is open;
- avoids exposing a self-hosted runner to a public repository;
- supports later multiple local backends behind one dispatch interface.

## 3. v0 scope

The controller core is multi-agent-capable, but the first real backend is intentionally one vertical slice:

```text
AGENT = SALVADOR
TASK_KIND = PRODUCTION_IMAGE_EDIT
BACKEND = COMFYUI_LOCAL
```

v0 proves the automation machinery itself:

```text
GitHub ASSIGNED
-> local controller discovers task
-> validates task + local reference
-> ensures ComfyUI is reachable
-> submits real ComfyUI prompt
-> receives prompt_id
-> records SALVADOR_RUNNING
-> waits for real output
-> persists result locally
-> records SALVADOR_RESULT_READY
```

LESTER and DUNCAN adapters are phase-2 extensions after this state/evidence loop is proven. v0 must expose an adapter interface so they can be added without rewriting orchestration.

## 4. Cost boundary

v0 must not require:

- OpenAI API billing;
- any paid inference API;
- paid orchestration service;
- paid GitHub runner;
- paid image generation service.

Allowed resources are existing local hardware, electricity, normal internet access to GitHub, and free/open-source local software/models.

No `OPENAI_API_KEY` exists in this architecture.

## 5. Existing local environment

Current known machine target:

```text
OS = Windows
GPU = NVIDIA GeForce RTX 3050 Laptop GPU
VRAM = 4 GB
RAM = 16 GB
COMFYUI_URL = http://127.0.0.1:8188
COMFYUI_INSTALL = D:\BLATT2\ComfyUI_windows_portable
```

The controller MUST NOT hard-code GPU-specific model names. ComfyUI workflow/model configuration is external configuration so models can be changed later without changing orchestration semantics.

v0 implementation and tests are built with a mocked ComfyUI adapter first. A production model is installed/configured only after controller logic is green.

## 6. GitHub as durable queue/state

Shared HQ remains the durable coordination plane.

Executable task issues use a fixed block:

```text
ZB_AGENT_TASK_V0
TASK_ID = ZB-SALVADOR-<UTC>-<sequence>
AGENT = SALVADOR
TASK_KIND = PRODUCTION_IMAGE_EDIT
STATE = ASSIGNED
REFERENCE = LOCAL_INBOX
```

Task-specific direction follows the machine-readable block.

The local controller polls only explicitly marked ZB agent tasks. It never executes arbitrary issue text as shell or code.

## 7. Local inbox/result boundary

Production images do not need to be uploaded to public Shared HQ.

Canonical local roots:

```text
D:\BLATT2\ZB_AGENT_INBOX\
D:\BLATT2\ZB_AGENT_RESULTS\
```

For task `TASK_ID`, reference discovery is constrained to:

```text
D:\BLATT2\ZB_AGENT_INBOX\<TASK_ID>\
```

The controller constructs this path itself. Issue text cannot supply arbitrary filesystem paths.

Exactly one supported reference file is accepted in v0:

```text
.png
.jpg / .jpeg
.webp
```

Results are persisted to:

```text
D:\BLATT2\ZB_AGENT_RESULTS\<TASK_ID>\result.png
D:\BLATT2\ZB_AGENT_RESULTS\<TASK_ID>\result.json
```

`result.json` records task ID, agent, backend, state, timestamps, ComfyUI prompt ID, output byte size, and SHA-256 checksum.

## 8. Reference behavior

If an executable task is discovered but no valid local reference exists:

```text
STATE = WAITING_REFERENCE
EVENT = SALVADOR_REFERENCE_REQUIRED
```

The controller keeps watching. When exactly one valid reference later appears in that task's fixed inbox directory, the task becomes eligible automatically. SPARX does not need to reopen a ChatGPT agent tab.

If more than one candidate reference exists, execution stops with stable error `REFERENCE_COUNT_INVALID` rather than guessing.

## 9. State machine

Canonical states:

```text
ASSIGNED
WAITING_REFERENCE
STARTING_BACKEND
RUNNING
RESULT_READY
FAILED
```

Allowed transitions:

```text
ASSIGNED -> WAITING_REFERENCE
ASSIGNED -> STARTING_BACKEND
WAITING_REFERENCE -> STARTING_BACKEND
STARTING_BACKEND -> RUNNING
STARTING_BACKEND -> FAILED
RUNNING -> RESULT_READY
RUNNING -> FAILED
```

`STARTING_BACKEND` means the controller is making ComfyUI ready/submitting work. It is not owner-visible proof of execution.

For SALVADOR, `RUNNING` may be recorded only after ComfyUI has accepted the workflow and returned a real `prompt_id`.

`RESULT_READY` may be recorded only after a non-empty supported output image exists in the canonical local result directory and its checksum/metadata have been written.

## 10. Controller process

The local controller is a small long-running Python process with no paid SDK dependency.

Responsibilities:

- poll GitHub for eligible task issues;
- parse fixed task contract;
- track durable events and idempotency;
- inspect fixed local inbox;
- dispatch by `AGENT` and `TASK_KIND` through a backend registry;
- post durable GitHub events using authenticated GitHub CLI;
- persist local result metadata;
- never execute arbitrary commands derived from issue content.

Suggested process cadence:

```text
POLL_INTERVAL_SECONDS = 15
```

This is configuration, not governance authority.

## 11. GitHub authentication

v0 uses the official GitHub CLI (`gh`) authenticated once on the local Windows account.

The controller shells out only to fixed, preconstructed `gh` commands whose user-controlled values are passed as arguments, not interpolated into shell source.

No GitHub PAT is written into repository files or issue text.

If `gh` is not authenticated, the controller enters configuration failure and does not pretend agents are running.

## 12. SALVADOR / ComfyUI adapter

Adapter contract:

```text
ensure_ready() -> BackendReady | error
submit(task, reference) -> execution_id
poll(execution_id) -> RUNNING | COMPLETE | FAILED
collect(execution_id) -> result image
```

For ComfyUI:

- base URL defaults to `http://127.0.0.1:8188`;
- workflow JSON is versioned in the controller codebase;
- task text fills only approved prompt fields;
- model/checkpoint names come from local config/workflow, never issue-controlled arbitrary paths;
- real `prompt_id` returned by ComfyUI is the execution evidence used before posting `SALVADOR_RUNNING`;
- history/output API is polled until success/failure/timeout;
- output is copied to the canonical task result directory.

If ComfyUI is down, v0 may attempt to launch the known local `run_nvidia_gpu.bat` through a fixed configured path, then wait for readiness. Failure becomes `BACKEND_UNAVAILABLE`.

## 13. SALVADOR task laws

The adapter owns a versioned production prompt/rules file. For production simplification:

- no redesign;
- preserve identity and defining forms visible in supplied reference;
- do not invent missing reference facts;
- reduce micro-detail and visual noise;
- clarify major forms and reduce unnecessary internal lines;
- obey requested view count/orientation;
- graphite / production pencil when requested;
- return one result when one result is requested.

Task-specific art direction is data; it cannot change controller privileges or backend selection.

## 14. Durable events

Material issue comments use:

```text
ZB_AGENT_EVENT_V0
TASK_ID = ...
AGENT = SALVADOR
STATE = WAITING_REFERENCE | RUNNING | RESULT_READY | FAILED
BACKEND = COMFYUI_LOCAL
EXECUTION_ID = <prompt_id | NONE>
RESULT_SHA256 = <sha256 | NONE>
ERROR_CODE = <stable code | NONE>
```

Compatibility lines:

```text
SALVADOR_RUNNING
SALVADOR_RESULT_READY
SALVADOR_REFERENCE_REQUIRED
```

Public comments never contain image bytes or arbitrary local filesystem contents.

## 15. Idempotency

Each task has immutable `TASK_ID`.

Before dispatch, controller checks:

1. existing durable terminal event on issue;
2. existing canonical local `result.json` for task;
3. active in-memory execution lock for task.

If a valid `RESULT_READY` already exists, the task is not generated again.

One controller process may execute at most one active SALVADOR image task at a time in v0 to protect 4 GB VRAM.

## 16. Startup / always-on behavior

After functional acceptance, installer configures Windows Task Scheduler or Startup entry so the controller starts at user login.

Controller startup must not automatically run unrelated GitHub issues. It only processes tasks matching the fixed contract and allowed agent/task vocabulary.

ComfyUI may be started lazily only when a SALVADOR task actually requires it.

## 17. Security

Hard requirements:

- no paid API secrets;
- no arbitrary shell/code execution from issue text;
- fixed allowlist for agent/task kinds;
- fixed local root directories;
- reject path traversal;
- supported image extension + magic/content validation;
- input byte-size cap;
- one active GPU task at a time;
- no writes to `zorr-blatt-runtime`;
- no merge, OWNER LOCK, runtime activation, or governance-verdict authority;
- browser ChatGPT sessions are not automated;
- public GitHub state contains metadata only, not production image bytes.

## 18. Testing

Implementation must prove with automated tests:

- strict task parser;
- allowed/forbidden state transitions;
- path traversal rejection;
- missing reference -> `WAITING_REFERENCE`;
- later local reference -> automatic eligibility;
- multiple reference rejection;
- duplicate task -> no second backend submission;
- mocked ComfyUI submission returns execution ID before RUNNING event;
- backend failure -> FAILED;
- RESULT_READY only after result image + metadata persistence;
- event formatter never leaks local image bytes;
- only allowlisted task/agent values dispatch;
- single-GPU-task lock works.

Mocked tests come before any live model download/configuration requirement.

## 19. Acceptance criteria

Controller v0 passes only when one disposable end-to-end test proves:

```text
GitHub task = ASSIGNED
-> local controller discovers task without manual chat relay
-> reference is found in fixed local inbox
-> local ComfyUI accepts real workflow and returns prompt_id
-> SALVADOR_RUNNING is durably posted
-> exactly one local image completes
-> result.png + result.json exist
-> SALVADOR_RESULT_READY is durably posted
-> duplicate discovery does not run a second generation
```

Only after that test passes may the approved production face-sheet reference be used.

## 20. Non-goals for v0

Not in the first vertical slice:

- paid OpenAI or other cloud inference;
- browser-tab automation;
- full local LESTER reasoning backend;
- full local DUNCAN reasoning backend;
- automatic merge;
- OWNER LOCK;
- runtime activation;
- public image storage;
- Control Room file-upload UI.

The orchestration interface must nevertheless be designed so LESTER and DUNCAN adapters can be added next without replacing the controller core.

## 21. Rollout order

1. Replace obsolete paid implementation plan.
2. LESTER implements controller/parser/state machine with mocked backend.
3. Implement fixed local inbox/result persistence and GitHub CLI adapter.
4. Implement mocked ComfyUI backend contract.
5. Run all controller tests without downloading a production model.
6. Configure one lightweight ComfyUI workflow/model compatible with 4 GB VRAM.
7. Run disposable local end-to-end smoke.
8. Run SALVADOR production face-sheet task.
9. Design/implement LESTER local backend.
10. Design/implement DUNCAN local QC backend.
11. Feed durable states into Control Room.

## 22. Owner-visible meaning

After v0 deployment:

```text
ASSIGNED = real queued task exists
WAITING_REFERENCE = controller saw it but executable image is absent
RUNNING = local ComfyUI returned a real execution id
RESULT_READY = real local persisted output exists
FAILED = execution failed with durable reason
```

SPARX no longer needs to open a SALVADOR ChatGPT tab to make an assigned image task execute.
