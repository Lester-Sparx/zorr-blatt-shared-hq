# ZB Communication Orchestrator v0 — Variant A Design

Date: 2026-08-28  
Issue: #106  
Status: OWNER-APPROVED ARCHITECTURE / WRITTEN SPEC CANDIDATE  
Implementation: NOT AUTHORIZED BY THIS DOCUMENT ALONE

## 1. Decision

OWNER approved Variant A:

```text
permanent draft Communication PR
-> ZB_AGENT_MESSAGE_V1 structured comment
-> ChatGPT Work webhook, event-driven, no polling
-> authenticated transport check
-> logical-role legality router
-> durable RECEIVED receipt
-> RUNNING only after actual execution starts
-> RESULT or BLOCKED
-> automatic next legal message/gate
-> ZB_OWNER_VIEW_V0 projection
-> read-only Console
```

Variant B (GitHub Actions routing/writing with a PAT) is rejected. Variant C (local Codex CLI role launching) is not an authority path for v0.

## 2. Reuse-first foundation

This design extends existing ZORR BLATT infrastructure instead of creating a second controller architecture.

Authoritative foundation:

- issue #102 is a completed event-driven proof chain and remains historical evidence;
- PR #103 remains the unmerged proof/reference branch and is not repurposed as the Communication Orchestrator implementation PR;
- `Lester-Sparx` is the only approved GitHub transport actor;
- `OWNER`, `LESTER`, `DUNCAN`, `DJANGO`, and `JINGO` are logical protocol roles, not GitHub identities;
- existing transition legality, exact evidence binding, revision CAS, Control Tower integrity, and OWNER deny-by-default laws remain authoritative;
- existing `ZB_AGENT_TASK_V0` and `ZB_AGENT_EVENT_V0` remain SALVADOR/local-execution contracts and are not overloaded for logical-role communication;
- existing Controller Daemon and Reference Bridge are sibling foundation components and are not replaced by the orchestrator;
- `ZB_OWNER_VIEW_V0` remains the owner-facing durable projection consumed by Console v0;
- Console remains read-only.

No historical comment, historical role-specific login field, issue #102 receipt, PR #103 proof fixture, or pinned Control Tower artifact may be rewritten to make the new design appear cleaner.

## 3. Trust model

### 3.1 Transport identity

The only accepted live GitHub transport actor is the authenticated actor from the GitHub/Work event envelope and it MUST equal `Lester-Sparx`.

A string inside a comment such as `transportActor = Lester-Sparx`, `logicalRole = DUNCAN`, or an old role-specific GitHub username has zero authority by itself.

Transport identity proves only who carried the GitHub write. It does not prove a logical role.

### 3.2 Logical role

The router derives the next legal logical role from durable state, transition law, exact bindings, and prior verified receipts. The message may declare `FROM_ROLE` and `TO_ROLE`, but those are requests to validate, not authority claims.

Automatic logical-role execution in v0 is limited to:

- `JINGO`
- `LESTER`
- `DUNCAN`
- `DJANGO`

`OWNER` is never automatically executed by this router. A genuinely OWNER-only gate becomes `OWNER_ACTION_REQUIRED` in the owner projection and stops the automatic chain.

### 3.3 Deny by default

If transport, role legality, CAS, task binding, target HEAD, evidence, receipt read-back, or protocol version cannot be proven, the router MUST NOT infer success. It emits or attempts to emit a BLOCKED/dead-letter record and stops that transition.

## 4. Communication surface

### 4.1 Permanent draft Communication PR

Create one dedicated long-lived draft PR after implementation review. It is an event surface, not a merge candidate.

Recommended properties:

- branch: dedicated communication-bus branch;
- base: `main`;
- exactly one protocol anchor file is sufficient to keep the PR open;
- title/body explicitly state `DO NOT MERGE` and `NO OWNER LOCK`;
- structured top-level PR Conversation comments are the v0 message transport;
- comment creation is the event source for the Work webhook;
- normal operation does not mutate the PR HEAD;
- the PR is never used to carry production implementation code.

The permanent communication PR MUST NOT be PR #103.

### 4.2 Webhook law

The communication path is event-driven. Polling GitHub to discover `ZB_AGENT_MESSAGE_V1` is forbidden as a substitute for the Work webhook.

Existing local Controller/Daemon polling for SALVADOR task execution is a separate already-existing execution mechanism. It does not become authority for logical-role communication and is not removed by this design.

## 5. `ZB_AGENT_MESSAGE_V1`

A live message is a strict machine-readable top-level comment. Unknown fields, duplicate fields, malformed identifiers, unsupported protocol versions, or multiline machine values fail closed.

Canonical field order:

```text
ZB_AGENT_MESSAGE_V1
MESSAGE_ID = <opaque globally unique id>
EVENT_ID = <opaque globally unique producer event id>
CORRELATION_ID = <stable chain id>
CAUSATION_MESSAGE_ID = <prior message id or NONE>
TASK_ID = <canonical task id>
FROM_ROLE = JINGO|LESTER|DUNCAN|DJANGO
TO_ROLE = JINGO|LESTER|DUNCAN|DJANGO
MESSAGE_KIND = ASSIGN|RETURN|QC_REQUEST|QC_VERDICT|ARCH_REVIEW|ARCH_VERDICT|CLOSE_REQUEST
TARGET_REPO = Lester-Sparx/zorr-blatt-shared-hq
TARGET_ISSUE = <number or NONE>
TARGET_PR = <number or NONE>
BASE_SHA = <40 lowercase hex or NONE>
TARGET_HEAD_SHA = <40 lowercase hex or NONE>
TASK_REVISION = <positive integer or NONE>
EVIDENCE_REF = <durable remote evidence reference or NONE>
EVIDENCE_SHA256 = <64 lowercase hex or NONE>
EXPECTED_GATE = <non-empty symbolic gate>
ATTEMPT = <positive integer>
NO_AUTO_MERGE = TRUE
```

Human-readable direction may follow after one blank line, but it has no power to weaken the machine fields or repository law.

### 5.1 IDs

- `MESSAGE_ID` identifies one logical message and is the primary idempotency key.
- `EVENT_ID` identifies one producer event that caused the message.
- `CORRELATION_ID` is stable across the whole handoff chain.
- `CAUSATION_MESSAGE_ID` creates the exact parent edge. `NONE` is legal only for an authorized chain root.
- GitHub comment ID is transport evidence and is captured after the write; it is not substituted for `MESSAGE_ID`.

### 5.2 Exact binding

The router MUST read the referenced issue/PR and verify every required live binding before the target logical role is allowed to execute.

When a target PR exists, `TARGET_HEAD_SHA` is mandatory and MUST equal the fresh remote PR HEAD. When a protected-main transition is involved, `BASE_SHA` and applicable revision CAS MUST match current authority. Evidence-required gates MUST have exact durable evidence, not merely a prose claim that evidence exists.

## 6. Durable receipt state machine

Every authoritative stage is persisted as a separate top-level comment and then freshly read back.

```text
MESSAGE
  -> RECEIVED
  -> RUNNING      only if actual logical-role execution starts
  -> RESULT       successful/negative verdict with exact evidence
     or BLOCKED   fail-closed result
  -> next MESSAGE only after terminal receipt READ-BACK MATCH
```

The receipt marker is:

```text
ZB_AGENT_RECEIPT_V1
MESSAGE_ID = <message id>
EVENT_ID = <event id>
CORRELATION_ID = <chain id>
SOURCE_COMMENT_ID = <GitHub message comment id>
RECEIPT_ID = <globally unique receipt id>
STATE = RECEIVED|RUNNING|RESULT|BLOCKED|DEAD_LETTER
TRANSPORT_ACTOR = Lester-Sparx
LOGICAL_ROLE = JINGO|LESTER|DUNCAN|DJANGO
TASK_ID = <task id>
TARGET_HEAD_SHA = <bound head or NONE>
EXECUTION_ID = <actual execution id or NONE>
RESULT_CODE = <symbolic result or NONE>
EVIDENCE_REF = <remote evidence reference or NONE>
EVIDENCE_SHA256 = <hash or NONE>
ATTEMPT = <positive integer>
READ_BACK = MATCH
```

A record is authoritative only after the writer performs a fresh remote read and the read-back body/remote ID matches what was written.

Repository law:

```text
no remote ID/read-back = NOT PERSISTED
WRITE + READ-BACK + MATCH = RECORDED
```

If the write succeeds but read-back cannot be proven, the transition stays non-terminal and retry logic may verify/reconcile the same intended receipt. It MUST NOT create a second logical execution merely because acknowledgement was lost.

## 7. Truthful `RUNNING`

`RECEIVED` means only that the event passed transport/protocol/legality admission and was durably acknowledged.

`RUNNING` is forbidden until the target logical-role execution has actually started on an execution surface and an execution identifier/evidence exists. A queued Work task, webhook delivery, GitHub comment, or assignment is not `RUNNING`.

This preserves the existing ZB law `ASSIGNED != RUNNING`.

## 8. Router legality

The router operates on explicit transition tables and repository authority, not free-form model choice.

For every inbound message it MUST:

1. verify the event came from the canonical Communication PR and allowed event type;
2. verify authenticated transport actor is currently approved;
3. strictly parse `ZB_AGENT_MESSAGE_V1`;
4. reject a previously terminal `MESSAGE_ID` as a replay without re-executing it;
5. load the current durable correlation state;
6. verify causation edge and expected next role/message kind;
7. fresh-read exact task/issue/PR/base/head bindings;
8. verify required evidence and CAS;
9. reject any attempt to cross an OWNER-only boundary;
10. persist/read-back `RECEIVED`;
11. start the target logical-role execution;
12. only then persist/read-back `RUNNING`;
13. persist/read-back `RESULT` or `BLOCKED` with exact result evidence;
14. derive and emit at most one next legal `ZB_AGENT_MESSAGE_V1`.

No result may be upgraded from FAIL/BLOCKED to PASS by routing logic.

## 9. Generalized role flow

The proven #102 loop is a foundation example, not a hard-coded workflow for all tasks.

Typical implementation flow:

```text
JINGO ASSIGN -> LESTER
LESTER RESULT -> JINGO
JINGO QC_REQUEST -> DUNCAN
DUNCAN QC_VERDICT -> JINGO
JINGO ARCH_REVIEW -> DJANGO        only when architecture review is legally required
DJANGO ARCH_VERDICT -> JINGO
JINGO CLOSE_REQUEST -> terminal chain state
```

A task-specific policy may omit DJANGO when architecture review is not required, but it may not skip DUNCAN or OWNER gates that repository law requires.

The router cannot merge a PR, activate production, mutate canon, or create an OWNER LOCK as the consequence of a PASS. It may only surface that the next gate requires OWNER action.

## 10. Idempotency, retry, timeout, and dead letter

### 10.1 Idempotency

The durable idempotency key is `MESSAGE_ID` plus exact task/correlation binding. A second delivery of the same valid message:

- may repair a missing read-back receipt;
- may return the already-recorded terminal result;
- MUST NOT invoke the logical role twice once actual execution is known to have started or completed.

A reused `MESSAGE_ID` with different canonical content is `MESSAGE_ID_COLLISION` and BLOCKED.

### 10.2 Retry

Retry applies to transport/persistence/execution-delivery failures, not to changing a logical verdict. Attempts increment `ATTEMPT` but retain the same `MESSAGE_ID` and correlation binding.

Retry policy is bounded and must be configuration-backed. No infinite retry loop is allowed.

### 10.3 Timeout

Every RUNNING execution has a bounded deadline. Timeout produces a durable BLOCKED result with the execution identifier and timeout evidence. A timeout never implies that underlying work was successful.

### 10.4 Dead letter

After bounded retries are exhausted or an unrecoverable protocol/authority error occurs, write/read-back a `STATE = DEAD_LETTER` receipt when remote persistence is available, update the owner projection to BLOCKED, and stop automatic forwarding for that message.

Dead-letter recovery requires a new legally-caused message or explicit authorized operator action; it never silently reuses a stale HEAD/evidence binding.

## 11. Legacy and foreign events

Historical evidence is immutable and remains readable.

For live v0 routing:

- only `ZB_AGENT_MESSAGE_V1` on the canonical Communication PR is executable input;
- older role-specific GitHub login comments are historical evidence only;
- `ZB_AGENT_EVENT_V0` remains a local SALVADOR execution event and is not interpreted as a logical-role handoff;
- a live event whose authenticated transport actor is not approved is rejected;
- a body that claims an approved actor cannot override a foreign authenticated event actor;
- unsupported future/old communication protocol markers are ignored or BLOCKED according to strict parser policy, never guessed.

## 12. Foundation integration boundary

Current protected `main` contains the merged single-account migration and Console v0, while daemon/Reference Bridge implementation history exists on the separate PR #103 lineage.

Before production activation of the orchestrator, create a separate **foundation-integration PR** that integrates only the already-approved daemon + Reference Bridge component boundaries onto current `main`.

Rules:

- do not merge or mutate PR #103 to accomplish this;
- do not copy the #102 proof fixture into the integration PR;
- do not blindly merge unrelated SALVADOR/canon changes from the historical branch;
- bind extracted component code to exact approved/validated component commits and tests;
- preserve existing Controller/SALVADOR truth semantics;
- no production activation merely because foundation code is integrated;
- DUNCAN independent QC is required for the integration candidate.

The Communication Orchestrator implementation PR is separate from this foundation-integration PR.

## 13. Reference Bridge relationship

Reference Bridge transports validated reference bytes. It does not become the agent-message router.

Its existing laws remain:

- GitHub remains task/evidence authority;
- `ZB_REFERENCE_DELIVERY_V1` is not `ZB_AGENT_MESSAGE_V1`;
- `REFERENCE_READY` requires validated local atomic publish;
- Reference Bridge never fabricates SALVADOR `ZB_AGENT_EVENT_V0` execution truth;
- accepted destination conflicts fail closed.

The orchestrator may observe durable Reference Bridge evidence when a task gate requires it, but it does not move image bytes itself.

## 14. Controller/Daemon relationship

The existing local Controller remains responsible for local agent backend execution, including its execution journal/result persistence and truthful SALVADOR events.

The orchestrator does not replace `ZB_AGENT_TASK_V0`, backend submission, ComfyUI execution, local result hashing, or daemon instance/health semantics.

When a logical-role flow creates or advances a local execution task, it must do so through the existing legal task contract rather than a second hidden queue.

## 15. Owner view and Console

After each terminal communication receipt, the orchestrator generates one canonical `ZB_OWNER_VIEW_V0` snapshot on the existing owner-view surface and persists it using the same WRITE -> READ-BACK -> MATCH law.

The snapshot is a projection, never the source of truth.

It MUST expose:

- overall communication status;
- current correlation/task;
- last legal role transition;
- current running role only when a RUNNING receipt exists;
- blocker/dead-letter reason;
- exact next gate;
- whether OWNER action is required;
- relevant evidence IDs/hashes through stable summarized fields/gates.

Console remains read-only and may only read/interpret the snapshot and validated local output.

Current Console parser does not contain a DJANGO agent row. Implementation must update the Console owner-snapshot contract and tests atomically with the new producer, or otherwise represent DJANGO through a version-compatible gate projection. It is forbidden to emit a snapshot that the deployed parser silently cannot parse and then call the Console integrated.

## 16. Security boundaries

Forbidden in v0:

- PAT-backed GitHub Actions router/writer;
- role-specific account switching;
- impersonating DUNCAN/LESTER/DJANGO/JINGO as GitHub users;
- treating a comment body role claim as authenticated role authority;
- polling as the Work communication trigger;
- executing PR-head workflow code with privileged base credentials;
- auto-merge;
- automatic production activation;
- canon mutation;
- OWNER LOCK creation;
- rewriting historical evidence;
- modifying pinned Control Tower artifact bytes.

Secrets remain outside repository content. The single approved GitHub transport is reused; the design introduces no second PAT transport identity.

## 17. Failure codes required by v0

At minimum, implementation must represent and test:

- `TRANSPORT_ACTOR_REJECTED`
- `COMMUNICATION_PR_MISMATCH`
- `MESSAGE_PROTOCOL_INVALID`
- `MESSAGE_ID_COLLISION`
- `REPLAY_TERMINAL`
- `CAUSATION_MISMATCH`
- `ROLE_TRANSITION_ILLEGAL`
- `TARGET_HEAD_STALE`
- `BASE_CAS_MISMATCH`
- `TASK_REVISION_MISMATCH`
- `EVIDENCE_MISSING`
- `EVIDENCE_MISMATCH`
- `OWNER_GATE_REQUIRED`
- `RECEIPT_WRITE_FAILED`
- `RECEIPT_READ_BACK_MISMATCH`
- `EXECUTION_START_FAILED`
- `EXECUTION_TIMEOUT`
- `RETRY_EXHAUSTED`
- `DEAD_LETTERED`
- `OWNER_VIEW_PERSISTENCE_FAILED`

All are deny-by-default conditions.

## 18. TDD acceptance matrix

Implementation planning must create RED tests before production code for at least:

1. strict valid/invalid `ZB_AGENT_MESSAGE_V1` parsing;
2. allowed transport and foreign actor rejection;
3. logical role derived from legal transition, not body authority;
4. exact target PR HEAD and base/revision CAS mismatch rejection;
5. evidence binding match/mismatch;
6. receipt write + fresh read-back + exact match;
7. lost acknowledgement reconciliation without duplicate logical execution;
8. duplicate webhook delivery idempotency;
9. message-ID collision rejection;
10. RUNNING impossible before actual execution evidence;
11. bounded retry and timeout;
12. dead-letter stop/no auto-forward;
13. automatic next-message emission only after terminal receipt read-back;
14. OWNER gate stops routing and never locks/merges;
15. legacy actor comments never become live handoffs;
16. `ZB_AGENT_EVENT_V0` remains SALVADOR-only;
17. Reference Bridge contract remains independent;
18. Console owner-view integration, including DJANGO representation;
19. Control Tower hash/integrity regression;
20. no auto-merge/activation/canon/OWNER LOCK command surface.

After mocked tests pass, a remote proof must use one disposable communication chain on the permanent draft Communication PR and demonstrate exact remote comment IDs plus fresh read-back matches for MESSAGE -> RECEIVED -> RUNNING -> RESULT/BLOCKED -> next MESSAGE.

## 19. PR decomposition

The implementation sequence is intentionally split:

### PR A — this design/spec

Docs only. No executable behavior.

### PR B — foundation integration

Daemon + Reference Bridge only, extracted/rebased safely onto current main with exact provenance and independent DUNCAN QC. No Communication Orchestrator behavior.

### PR C — Communication Orchestrator TDD implementation

Protocol parser, event admission, logical-role router, durable receipt/read-back layer, idempotency/retry/dead-letter, owner-view producer, and required Console compatibility changes.

### PR D — permanent Communication PR / remote proof surface

Communication anchor only. Draft forever / no merge intent. Used for event-driven proof and then operations after all gates.

No PR is automatically merged. Passing implementation/QC does not activate production.

## 20. Activation gates

Production-ready requires all of the following, independently evidenced:

1. written spec owner review;
2. implementation plan review;
3. PR B foundation integration candidate and DUNCAN QC;
4. PR C TDD suite and static/contract verification;
5. DUNCAN independent QC of exact PR C HEAD;
6. permanent draft Communication PR created with no-merge contract;
7. real Work webhook proof with `transportActor=Lester-Sparx` and logical-role routing;
8. remote WRITE -> READ-BACK -> MATCH receipts for each proof stage;
9. owner-view snapshot read-back match and Console read-only proof;
10. explicit OWNER production activation decision if production activation is desired.

No step creates an OWNER LOCK.

## 21. Non-goals

This design does not redesign SALVADOR, ComfyUI, Reference Bridge file transport, Controller task execution, canon workflow, runtime architecture, or Control Tower. It does not add a general-purpose chat platform, database, message broker, PAT bot, or second GitHub account.

## 22. Design verdict

Variant A is internally consistent with the completed single-account migration and #102 event-driven proof.

The key invariant is:

```text
ONE GITHUB TRANSPORT
+ AUTHENTICATED EVENT
+ STRICT MESSAGE CONTRACT
+ DERIVED LOGICAL ROLE
+ EXACT CAS/EVIDENCE BINDING
+ IDEMPOTENT EXECUTION
+ WRITE/READ-BACK RECEIPTS
= AUTOMATED COMMUNICATION WITHOUT AUTHORITY COLLAPSE
```

DESIGN = READY FOR OWNER WRITTEN-SPEC REVIEW  
IMPLEMENTATION = NOT STARTED  
AUTO_MERGE = NO  
PRODUCTION_ACTIVATION = NO  
CANON_CHANGE = NO  
OWNER_LOCK = NO
