# ZORR BLATT — Agent Controller v0 Design

Status: **DESIGN / OWNER-APPROVAL PENDING FOR EXECUTION**

Authority repository: `Lester-Sparx/zorr-blatt-shared-hq`

Design branch: `agent-controller/v0-design`

## 1. Purpose

ZB currently has durable assignments in GitHub, but an assignment comment does not start a real model run. Agent Controller v0 closes that gap for one vertical slice first: **JINGO → SALVADOR → RESULT_READY**.

Core law:

```text
ASSIGNED != RUNNING.
RUNNING is emitted only when the runner is actually issuing the OpenAI image request.
RESULT_READY is emitted only after a real output artifact exists.
FAILED is explicit; failures must never be reported as ACTIVE or RUNNING.
```

The controller does not automate ChatGPT browser tabs. It executes SALVADOR through the OpenAI API from a GitHub Actions runner.

## 2. v0 scope

v0 supports exactly one agent role and one task kind:

```text
AGENT = SALVADOR
TASK_KIND = PRODUCTION_IMAGE_EDIT
```

The first production target is the approved middle-face simplification flow represented by Shared HQ issue #45.

v0 does not automate LESTER, DUNCAN, JINGO reasoning, merges, owner locks, runtime activation, or multi-agent fan-out. Those are later extensions after this vertical slice works.

## 3. Repositories and privacy boundary

`Lester-Sparx/zorr-blatt-shared-hq` is public and remains the public coordination/design plane. Production reference images and generated art must not be committed to it.

v0 therefore requires one dedicated private execution repository:

```text
Lester-Sparx/zorr-blatt-agent-runner
VISIBILITY = PRIVATE
```

This private repository contains:

- GitHub Actions workflow;
- the small Python runner;
- tests;
- private task issues and image attachments;
- a private generated-results branch.

No agent-controller code or art asset is written to `zorr-blatt-runtime`.

Public Shared HQ contains the design/spec and may contain a human-readable pointer to the private task, but v0 does not automatically publish execution state back to the public repository. Public projection is deliberately deferred until the private vertical slice is proven.

## 4. One-time owner prerequisites

Execution requires these one-time prerequisites:

1. An OpenAI API project/account with access to the selected image model and sufficient billing/usage capacity.
2. A usable OpenAI API key for that project.
3. Private repository `Lester-Sparx/zorr-blatt-agent-runner`.
4. Actions secret `OPENAI_API_KEY` in that private repository.

Repository creation and secret creation are owner-sensitive and are not available through the current connected GitHub tool, so those steps require direct owner action once.

No API key is stored in source, issues, logs, artifacts, comments, result metadata, or Shared HQ.

After these prerequisites are complete, normal SALVADOR task execution must not require opening a SALVADOR ChatGPT tab.

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

The issue body also contains the complete task-specific art direction.

Exactly one reference image must be resolvable from an attachment in the issue body or its comments. Private GitHub issue attachments are the v0 transport for production input images.

If no usable reference exists, the controller must not invoke image generation. It transitions to:

```text
STATE = WAITING_REFERENCE
```

and posts `SALVADOR_REFERENCE_REQUIRED` on the private issue.

## 6. Trigger

The private runner workflow listens to:

```text
issues: opened, edited, labeled
issue_comment: created
workflow_dispatch: manual diagnostic/recovery only
```

An event may start execution only when all of the following are true:

```text
AGENT == SALVADOR
TASK_KIND == PRODUCTION_IMAGE_EDIT
STATE == ASSIGNED or WAITING_REFERENCE
exactly one usable reference image is resolvable
OPENAI_API_KEY is available to the workflow
no terminal result already exists for TASK_ID
```

A comment containing a newly attached image can therefore move a task from `WAITING_REFERENCE` to real execution without opening a ChatGPT agent session.

Duplicate events must be idempotent. GitHub Actions `concurrency` uses `TASK_ID` so two runs for the same task cannot execute concurrently.

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
WAITING_REFERENCE -> RUNNING
RUNNING -> RESULT_READY
RUNNING -> FAILED
```

No other transition is valid in v0.

`RUNNING` is recorded immediately before the runner issues the real OpenAI API request, after all task/reference validation and idempotency checks have passed. A queued or merely-started GitHub workflow is not `RUNNING`.

If the API call then fails, the next durable transition is `FAILED`.

`RESULT_READY` is written only after output bytes have been validated as a non-empty supported image and persisted privately.

## 8. SALVADOR role prompt

The private runner owns a versioned role prompt file. The prompt establishes permanent SALVADOR production-simplification laws for this task class:

- no redesign;
- preserve identity and silhouette-relevant face/body/hair/costume/weapon/asymmetry when present in the supplied reference;
- remove micro-detail and visual noise;
- enlarge/clarify major forms;
- reduce unnecessary internal lines;
- graphite / production pencil when requested;
- obey exact view count and orientation;
- do not invent missing reference facts;
- return exactly one result when one result is requested.

Task-specific issue text is appended after the permanent role prompt.

## 9. OpenAI image execution

v0 uses the OpenAI image-edit API with the model name isolated in configuration.

Initial implementation target:

```text
MODEL = gpt-image-2-2026-04-21
MODE = IMAGE EDIT
INPUT = one reference image + SALVADOR role prompt + task art direction
OUTPUT = one image
```

Current OpenAI documentation lists GPT Image 2 as supporting image input/output and the image-edit endpoint. Pinning the published snapshot prevents silent model-alias drift during v0 validation. A future model migration changes configuration, not orchestration semantics.

The controller records only non-secret execution metadata: model snapshot, request start/end timestamps, workflow run ID, task ID, result byte size, and output checksum.

## 10. Result persistence

Production image bytes remain private.

v0 uses a dedicated branch in the private runner repository:

```text
generated-results
```

Canonical paths:

```text
results/<TASK_ID>/result.png
results/<TASK_ID>/result.json
```

The generated-results branch is never merged into the runner code branch/main.

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

No prompt secrets, API key material, or signed private attachment URL is persisted in result metadata.

## 11. Durable issue events

The private task issue is the v0 human-readable execution log.

Material events use this format:

```text
ZB_AGENT_EVENT_V0
TASK_ID = ...
AGENT = SALVADOR
STATE = WAITING_REFERENCE | RUNNING | RESULT_READY | FAILED
WORKFLOW_RUN_ID = ...
RESULT_PATH = results/<TASK_ID>/result.png | NONE
ERROR_CODE = <stable code | NONE>
```

For compatibility with the existing handoff language, the runner additionally posts:

```text
SALVADOR_RUNNING
```

when entering `RUNNING`, and:

```text
SALVADOR_RESULT_READY
```

when entering `RESULT_READY`.

The event must never contain `OPENAI_API_KEY`, raw API responses, or signed private attachment URLs.

## 12. Error behavior

Input errors are not model failures.

```text
missing reference -> WAITING_REFERENCE
multiple references -> FAILED / INPUT_REFERENCE_COUNT_INVALID
invalid task contract -> FAILED / TASK_CONTRACT_INVALID before model call
missing OPENAI_API_KEY -> FAILED / OPENAI_KEY_MISSING
OpenAI request/API error -> FAILED / OPENAI_REQUEST_FAILED
empty/invalid image output -> FAILED / OUTPUT_IMAGE_INVALID
result persistence failure -> FAILED / RESULT_PERSIST_FAILED
```

The private issue receives a concise durable failure event with the stable error code. Full stack traces remain in Actions logs and must not expose secrets.

## 13. Security

Required minimum workflow permissions:

```text
contents: write
issues: write
```

Everything else defaults to `none` where GitHub permits.

Additional laws:

- never execute arbitrary shell/code from issue text;
- never interpolate issue body directly into shell commands;
- validate task fields against fixed vocabularies;
- accepted reference count is exactly one;
- implementation must set an explicit input-image byte-size cap;
- accept only explicitly supported image MIME types;
- never log `OPENAI_API_KEY`;
- never publish production image bytes to public Shared HQ;
- no writes to runtime repository;
- no merge, governance-verdict, activation, or owner-lock authority in the runner.

## 14. Idempotency and duplicate protection

Each task has one immutable `TASK_ID`.

Before calling OpenAI, the runner checks `generated-results` for an existing terminal result for that task and checks the issue's durable events. If a terminal result exists, it exits successfully without another model call.

The workflow concurrency key is derived from the same `TASK_ID`.

A SHA-256 result checksum makes duplicate persistence detectable.

## 15. Testing

v0 must have tests for:

- task-block parsing;
- allowed and forbidden state transitions;
- missing reference -> `WAITING_REFERENCE` with zero OpenAI calls;
- `WAITING_REFERENCE` plus a later attachment -> `RUNNING` path;
- duplicate event -> zero second OpenAI call;
- invalid MIME and oversized input rejection;
- multiple reference rejection;
- OpenAI failure -> `FAILED`;
- valid mocked image output -> `RESULT_READY` only after private persistence;
- durable event serialization excludes secret/private signed URL data;
- workflow has least-privilege permissions and concurrency keyed by task ID.

A live smoke test uses a non-sensitive disposable reference image first. Production art is not used until the mocked and disposable-image paths are green.

## 16. Acceptance criteria

Agent Controller v0 passes only if one end-to-end private test proves:

```text
private issue ASSIGNED
-> GitHub Action actually runs
-> validated reference exists
-> SALVADOR_RUNNING is durably recorded at real API-call start
-> real OpenAI image-edit request executes
-> exactly one image is generated
-> private result.png + result.json are persisted
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
- automatic public Control Room projection;
- Control Room file-upload UI;
- general-purpose autonomous shell execution;
- arbitrary model/tool selection from issue text.

## 18. Rollout order

1. Complete one-time private repository/OpenAI secret prerequisites.
2. Implement parser/state machine with mocked OpenAI client.
3. Implement private issue attachment resolution and input validation.
4. Implement GPT Image edit call.
5. Implement `generated-results` persistence and metadata.
6. Add idempotency/concurrency.
7. Run disposable-image end-to-end smoke.
8. Only then run the approved SALVADOR production-sheet task.
9. After v0 proves stable, design public Control Room projection and additional agents separately.

## 19. Owner-visible meaning

After v0 is deployed, the owner creates/assigns one SALVADOR task in the private runner repository and no longer has to open a SALVADOR ChatGPT tab or relay prompts between agents.

The visible distinction is exact:

```text
ASSIGNED = queued work exists
WAITING_REFERENCE = task is valid but no executable reference is available
RUNNING = the real OpenAI image request is being issued/executed
RESULT_READY = a real persisted private image exists
FAILED = execution did not succeed
```

The controller must never use optimistic status language unsupported by durable execution evidence.
