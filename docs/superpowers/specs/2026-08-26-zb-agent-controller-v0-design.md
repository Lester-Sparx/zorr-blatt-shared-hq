# ZORR BLATT — Agent Controller v0 Design

Status: **DESIGN / OWNER-APPROVAL PENDING FOR EXECUTION**

Authority repository: `Lester-Sparx/zorr-blatt-shared-hq`

Design branch: `agent-controller/v0-design`

## 1. Purpose

ZB currently has durable assignments in GitHub, but an assignment comment does not start a real model run. Agent Controller v0 closes that gap for one vertical slice first: **JINGO → SALVADOR → RESULT_READY**.

Core law:

```text
ASSIGNED != RUNNING.
RUNNING is emitted only after a real OpenAI API request has started.
RESULT_READY is emitted only after a real output artifact exists.
FAILED is explicit; failures must never be reported as ACTIVE or RUNNING.
```

The controller does not automate ChatGPT browser tabs. It executes SALVADOR through the OpenAI API from a GitHub Actions runner.

## 2. v0 scope

v0 supports exactly one agent role:

```text
AGENT = SALVADOR
TASK_KIND = PRODUCTION_IMAGE_EDIT
```

The first target task is the approved middle-face production simplification flow represented by Shared HQ issue #45.

v0 does not automate LESTER, DUNCAN, JINGO reasoning, merges, owner locks, runtime activation, or multi-agent fan-out. Those are later extensions after this vertical slice works.

## 3. Repositories and privacy boundary

`Lester-Sparx/zorr-blatt-shared-hq` is public and remains the public/sanitized coordination plane. Production reference images and generated art must not be committed to it.

v0 therefore requires one dedicated private execution repository:

```text
Lester-Sparx/zorr-blatt-agent-runner
VISIBILITY = PRIVATE
```

This repository contains:

- GitHub Actions workflow;
- the small Python runner;
- tests;
- private task issues and image attachments;
- generated result artifacts or private result files.

No agent-controller code or art asset is written to `zorr-blatt-runtime`.

Public Shared HQ may receive only sanitized state transitions such as task ID, agent, state, workflow run ID, timestamps, and a private-result pointer that does not reveal image bytes or secrets.

## 4. One-time owner setup

Because repository creation and Actions secret APIs are owner-sensitive and are not available through the current connected GitHub tool, v0 has exactly two manual owner setup actions:

1. Create private repository `Lester-Sparx/zorr-blatt-agent-runner`.
2. In that private repository add Actions secret `OPENAI_API_KEY`.

No API key is stored in source, issues, logs, artifacts, comments, or Shared HQ.

After those one-time actions, normal task execution must not require opening a SALVADOR ChatGPT tab.

## 5. Task contract

Each executable SALVADOR task is a private GitHub issue in `zorr-blatt-agent-runner`.

Required machine-readable block:

```text
ZB_AGENT_TASK_V0
TASK_ID = ZB-SALVADOR-<UTC timestamp>-<sequence>
AGENT = SALVADOR
TASK_KIND = PRODUCTION_IMAGE_EDIT
STATE = ASSIGNED
PUBLIC_TRACKING_ISSUE = <owner/repo#number | NONE>
REFERENCE = ATTACHMENT_REQUIRED
```

The issue body also contains the complete art direction. The reference image is attached to that private issue or supplied as another private repository attachment URL.

If no usable reference image exists, the controller must not invoke image generation. It transitions to:

```text
STATE = WAITING_REFERENCE
```

and posts `SALVADOR_REFERENCE_REQUIRED`.

## 6. Trigger

The private runner workflow listens to GitHub issue lifecycle events on the private repository.

The workflow may start execution only when all of the following are true:

```text
AGENT == SALVADOR
TASK_KIND == PRODUCTION_IMAGE_EDIT
STATE == ASSIGNED
exactly one usable reference image is resolvable
OPENAI_API_KEY is available to the workflow
```

Duplicate events must be idempotent. A task with a terminal state must not execute again unless an explicit future retry command is added by a later version.

GitHub Actions `concurrency` uses `TASK_ID` so two runs for the same task cannot execute concurrently.

## 7. State machine

Canonical v0 states:

```text
ASSIGNED
WAITING_REFERENCE
RUNNING
RESULT_READY
FAILED
```

Allowed transitions:

```text
ASSIGNED -> WAITING_REFERENCE
ASSIGNED -> RUNNING
RUNNING -> RESULT_READY
RUNNING -> FAILED
```

No other transition is valid in v0.

`RUNNING` is written only after the runner has validated input and immediately before/at successful initiation of the real OpenAI API call. A workflow merely being queued or started is not sufficient.

`RESULT_READY` is written only after output bytes have been validated as a non-empty supported image and persisted in the private execution repository or as a private Actions artifact.

## 8. SALVADOR role prompt

The runner owns a versioned role prompt file. The prompt establishes permanent SALVADOR production-simplification laws for this task class:

- no redesign;
- preserve identity, silhouette-relevant face shape, hair/body/costume/weapon/asymmetry when present in the supplied reference;
- remove micro-detail and visual noise;
- enlarge/clarify major forms;
- reduce unnecessary internal lines;
- graphite / production pencil when requested;
- obey exact view count and orientation;
- do not invent missing reference facts;
- return one result when one result is requested.

Task-specific issue text is appended after the permanent role prompt.

## 9. OpenAI image execution

v0 uses the OpenAI image API with a pinned image model snapshot rather than a floating alias when available. Initial implementation target:

```text
MODEL = gpt-image-2-2026-04-21
MODE = IMAGE EDIT
INPUT = one reference image + SALVADOR role prompt + task art direction
OUTPUT = one image
```

The current OpenAI API documentation lists GPT Image 2 as supporting image input/output and the image-edit endpoint. The implementation must isolate the model name in configuration so a future model migration does not change orchestration semantics.

The controller records only non-secret execution metadata: model snapshot, request start/end timestamps, workflow run ID, task ID, result byte size, and output checksum.

## 10. Result persistence

Production image bytes remain private.

Preferred v0 persistence:

```text
results/<TASK_ID>/result.png
results/<TASK_ID>/result.json
```

inside the private runner repository on a dedicated generated-results branch, or a private Actions artifact if repository-file persistence proves unnecessarily complex during implementation.

`result.json` contains:

```json
{
  "taskId": "...",
  "agent": "SALVADOR",
  "state": "RESULT_READY",
  "model": "gpt-image-2-2026-04-21",
  "workflowRunId": 0,
  "sha256": "...",
  "bytes": 0,
  "createdAt": "..."
}
```

No prompt secrets, API key material, or signed private attachment URL is persisted in public state.

## 11. Public projection

If `PUBLIC_TRACKING_ISSUE` is present, the runner may publish a sanitized comment to that Shared HQ issue after each material transition:

```text
ZB_AGENT_EVENT_V0
TASK_ID = ...
AGENT = SALVADOR
STATE = RUNNING | RESULT_READY | FAILED | WAITING_REFERENCE
WORKFLOW_RUN_ID = ...
PRIVATE_RESULT = AVAILABLE | NONE
```

The public comment must not include private attachment URLs, image bytes, API responses, or secrets.

Cross-repository publication requires a credential with write access to the public Shared HQ repository. This credential is a separate implementation decision and must use least privilege. If no safe cross-repository credential is configured in v0, public projection is deferred and the private issue remains the authoritative live state.

Control Room integration is not a prerequisite for v0 execution; it is a later consumer of these sanitized transitions.

## 12. Error behavior

Input errors are not model failures.

```text
missing reference -> WAITING_REFERENCE
invalid task contract -> workflow fails before model call
missing OPENAI_API_KEY -> FAILED with configuration error
OpenAI request/API error -> FAILED
empty/invalid image output -> FAILED
persistence failure after valid generation -> FAILED
```

The issue receives a concise durable failure event with a stable error code. Full stack traces remain in Actions logs and must not expose secrets.

## 13. Security

Required minimum workflow permissions:

```text
contents: write   # only if private result branch persistence is selected
issues: write
```

Everything else defaults to `none` where GitHub permits.

Additional laws:

- never execute arbitrary shell/code from issue text;
- never interpolate issue body directly into shell commands;
- validate task fields against fixed vocabularies;
- cap accepted reference count at one for v0;
- cap input image byte size in implementation;
- accept only supported image MIME types;
- never log `OPENAI_API_KEY`;
- never publish private image URLs to public Shared HQ;
- no writes to runtime repository;
- no merge or owner-lock authority in the runner.

## 14. Idempotency and duplicate protection

Each task has one immutable `TASK_ID`.

Before calling OpenAI, the runner checks for an existing terminal event/result for that task. If found, it exits successfully without another model call.

A lock/concurrency key uses the same `TASK_ID`.

A result checksum makes duplicate persistence detectable.

## 15. Testing

v0 must have tests for:

- task-block parsing;
- allowed/forbidden state transitions;
- missing reference -> `WAITING_REFERENCE` with zero OpenAI calls;
- duplicate event -> zero second OpenAI call;
- invalid MIME/oversized input rejection;
- OpenAI failure -> `FAILED`;
- valid mocked image output -> `RESULT_READY` only after persistence;
- sanitized public event contains no private URL/API key data;
- workflow has least-privilege permissions and concurrency keyed by task ID.

A live smoke test uses a non-sensitive disposable reference image first. Production art is not used until the mocked/throwaway path is green.

## 16. Acceptance criteria

Agent Controller v0 passes only if one end-to-end private test proves:

```text
private issue ASSIGNED
-> GitHub Action actually runs
-> real OpenAI image-edit request starts
-> SALVADOR_RUNNING is durably recorded
-> exactly one image is generated
-> private result is persisted
-> SALVADOR_RESULT_READY is durably recorded
-> duplicate trigger does not generate a second image
```

Failure at any step is not a pass.

## 17. Non-goals

Not in v0:

- waking or controlling ChatGPT browser sessions;
- multi-agent orchestration;
- automatic DUNCAN QC;
- automatic merge;
- automatic OWNER LOCK;
- runtime activation;
- public storage of art;
- Control Room file-upload UI;
- general-purpose autonomous shell execution;
- arbitrary model/tool selection from issue text.

## 18. Rollout order

1. Create private runner repository and secret.
2. Implement parser/state machine with mocked OpenAI client.
3. Implement private reference download and validation.
4. Implement GPT Image edit call.
5. Persist private result and metadata.
6. Add idempotency/concurrency.
7. Run disposable-image end-to-end smoke.
8. Only then run the approved SALVADOR production-sheet task.
9. After v0 proves stable, design Control Room public projection and additional agents separately.

## 19. Owner-visible meaning

After v0 is deployed, the owner should be able to create/assign one SALVADOR task and then stop acting as a message courier. The visible distinction is exact:

```text
ASSIGNED = queued work exists
RUNNING = a real API execution is in progress/has started
RESULT_READY = a real persisted image exists
FAILED = execution did not succeed
```

The controller must never use optimistic status language unsupported by durable execution evidence.
