# ZORR BLATT — GitHub-Native Communication Base Design

Date: 2026-08-28
Status: OWNER-approved design candidate
Base main at design start: `0b9b77a9d82f45e7e1821dd6c9c26861a90cf688`
Tracker: issue `#106`
Existing communication bus: PR `#111` (DRAFT / OPEN / DO NOT MERGE)
Existing orchestrator implementation authority: PR `#110`

## 1. Purpose

Build the minimum reliable communication automation without depending on ChatGPT Work for GitHub writes.

The base must prove a deterministic happy path:

`GitHub comment -> GitHub Actions runner -> validate -> logical role stages -> OWNER gate`

Work is removed from the base transport/execution path because repeated physical tests showed event-triggered Work runs can read GitHub but may reject required GitHub writes, including writes to PR `#111` and tracker `#106`.

## 2. Control and execution model

- Normal ChatGPT conversation remains the human control plane for OWNER/DUNCAN supervision.
- GitHub is the durable state, event, evidence, and execution substrate for the base.
- GitHub Actions is the event runner.
- ChatGPT Work is not required by the base and is not used for routing, receipts, state persistence, or role execution.
- Logical roles remain `JINGO`, `LESTER`, `DUNCAN`, `DJANGO`.
- `OWNER` is never auto-executed.

## 3. Trigger

A single workflow listens to `issue_comment.created`.

Admission is strict:

- repository must be `Lester-Sparx/zorr-blatt-shared-hq`;
- issue/PR number must be `111`;
- source must be a top-level PR Conversation comment;
- source actor must be `Lester-Sparx`;
- first line must be exactly `ZB_AGENT_MESSAGE_V1`;
- message must bind to the currently configured proof task and approved authority values;
- ordinary prose, receipts, Owner Views, edits, inline review comments, and foreign actors are ignored or rejected fail-closed.

GitHub only dispatches this event to the base runner after the workflow file exists on the repository default branch. Therefore an unmerged implementation PR can be validated locally and by PR CI, but it cannot serve as the final remote `issue_comment.created` proof surface.

## 4. Runner shape

The implementation is intentionally small:

1. `.github/workflows/zb-communication-base.yml`
   - event trigger;
   - least required `GITHUB_TOKEN` permissions;
   - invokes one repository script;
   - no PAT, no external webhook, no polling.

2. `scripts/zb_communication_base.py`
   - strict parser for the minimum proof message;
   - exact binding checks;
   - idempotency guard using durable GitHub comments;
   - logical happy-path state machine;
   - writes receipts and Owner View through GitHub API using `GITHUB_TOKEN`;
   - stops at OWNER gate.

3. tests for parser, admission, idempotency, legal transition order, and OWNER stop.

No daemon, queue server, database, scheduler, retry worker, or external service is introduced for the minimum base.

## 5. Durable state

For the minimum base, durable evidence is written to tracker issue `#106`.

Each accepted root message produces a compact sequence of tracker comments for the proof correlation:

- `RECEIVED`
- `RUNNING`
- per-stage `RESULT = PASS`
- final `ZB_OWNER_VIEW_V0` with `OWNER_GATE_REQUIRED = TRUE`

Every write records enough identifiers to bind:

- source comment ID;
- message/correlation ID;
- task ID/revision;
- source actor;
- implementation PR/head provenance;
- exact protected-main SHA active for the proof;
- workflow run ID/attempt;
- logical stage;
- result.

The runner re-reads the just-created comment by exact remote ID and requires body equality before proceeding.

## 6. Happy-path role sequence

The minimum base executes these logical stages inside one workflow run:

1. `JINGO -> LESTER / ASSIGN`
2. `LESTER -> JINGO / RETURN`
3. `JINGO -> DUNCAN / QC_REQUEST`
4. `DUNCAN -> JINGO / QC_VERDICT`
5. `JINGO -> DJANGO / ARCH_REVIEW`
6. `DJANGO -> JINGO / ARCH_VERDICT`
7. `JINGO -> JINGO / CLOSE_REQUEST`
8. `OWNER_GATE_REQUIRED`

For this base proof, role work is deliberately minimal: verify the exact task, revision, protected-main binding, implementation provenance, evidence reference, and absence of forbidden mutations. It does not perform substantive production work.

## 7. Idempotency and replay

The runner must not execute the same root message twice.

Before `RUNNING`, it searches tracker `#106` for an existing terminal or in-progress record bound to the same immutable `MESSAGE_ID` and source comment ID.

If already processed, the workflow exits successfully as `NOOP_REPLAY` and writes no duplicate state.

This is sufficient for the minimum base. Advanced retry/dead-letter machinery remains deferred.

## 8. Permissions and safety

Workflow permissions are least-privilege and repository-local:

- `contents: read`
- `issues: write`
- `pull-requests: read`

No `contents: write`, no `actions: write`, no PAT, no role-account switching.

Forbidden in the base runner:

- merge or auto-merge;
- production activation;
- canon mutation;
- OWNER LOCK;
- PR `#103` mutation;
- issue `#102` historical-proof mutation;
- PR `#111` HEAD mutation;
- arbitrary shell execution from message content;
- arbitrary file writes;
- arbitrary issue/PR targets from untrusted body fields.

## 9. Failure behavior

Fail closed before role execution when admission or exact bindings fail.

A failure may write one compact tracker blocker only when the source itself has been authenticated and parsed safely. The runner never fabricates missing evidence and never claims PASS without fresh read-back evidence.

## 10. Testing

Required before implementation PR can be considered ready for OWNER activation review:

- parser accepts one valid minimal message;
- malformed or duplicate fields reject;
- foreign actor rejects;
- wrong PR rejects;
- stale authority/provenance binding rejects;
- wrong task/revision rejects;
- replay becomes NOOP without duplicate receipts;
- happy path reaches OWNER gate in exact order;
- OWNER is not auto-executed;
- forbidden mutation helpers do not exist in the runner;
- repository validation workflow passes on exact implementation HEAD.

PR CI proves the candidate code. It does not prove the final event trigger.

## 11. Activation and remote proof

Activation is a separate OWNER decision.

Sequence:

1. implementation PR is completed and verified while unmerged;
2. DUNCAN records exact implementation HEAD and verification evidence;
3. OWNER explicitly approves merge of that exact implementation HEAD;
4. implementation PR is merged to `main`;
5. protected `main` is fresh-read and the exact post-merge SHA becomes the proof `BASE_SHA`;
6. implementation PR/head remain provenance fields in the proof record;
7. one disposable fresh root `ZB_AGENT_MESSAGE_V1` is posted on PR `#111` using the post-merge `BASE_SHA`;
8. a real `issue_comment.created` workflow run must create fresh-read-matched tracker evidence ending at OWNER gate.

Merging the workflow enables the event runner but does not mean `PRODUCTION_ACTIVE = YES`. Production activation remains `NO`; this base is communication infrastructure only.

## 12. Deferred work

Not part of this minimum base:

- Work-based role execution;
- multi-run ping-pong buses;
- retry/backoff/dead-letter queues;
- production activation;
- merge automation;
- substantive production/canon tasks;
- negative matrix beyond the minimum safety tests above.

These may be layered only after the base happy path is physically proven.

## 13. Success criterion

The base is successful only when, after the separately approved implementation merge, a fresh root `ZB_AGENT_MESSAGE_V1` on PR `#111` causes a real `issue_comment.created` GitHub Actions run that:

- authenticates and binds the source;
- binds the exact active protected-main SHA plus implementation provenance;
- records and fresh-read-verifies durable tracker evidence;
- executes the exact seven logical stages in order;
- reaches `OWNER_GATE_REQUIRED`;
- does not execute OWNER;
- performs no merge, production activation, canon mutation, or OWNER LOCK.

Until that remote proof exists, `PRODUCTION_ACTIVE = NO` and no completion claim is allowed.
