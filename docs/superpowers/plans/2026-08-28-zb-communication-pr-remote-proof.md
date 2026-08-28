# ZB Communication PR Remote Proof Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Create the permanent draft Communication PR and prove the real Variant A event path end-to-end through ChatGPT Work using remote GitHub IDs and fresh read-back, then stop at an explicit OWNER production-activation decision.

**Architecture:** The Communication PR is a long-lived comment bus, not an implementation branch and never a merge candidate. A GitHub top-level PR-comment event is delivered to ChatGPT Work without polling. Work uses the approved single transport identity and the DUNCAN-passed orchestrator contract to validate, execute logical roles, persist receipts, derive the next legal message, and update the existing owner-view surface consumed read-only by Console.

**Tech Stack:** GitHub pull request comments/events, ChatGPT Work event execution, connected GitHub transport `Lester-Sparx`, `ZB_AGENT_MESSAGE_V1`, `ZB_AGENT_RECEIPT_V1`, `ZB_OWNER_VIEW_V0`, Console v0.

**Spec:** `docs/superpowers/specs/2026-08-28-zb-communication-orchestrator-v0-design.md` at OWNER-approved HEAD `9c9f0ebbf2bd5d5dc5b21578718f1ef356e278f9`.

**Global Constraints:**
- Do not start this plan until Foundation Integration has DUNCAN PASS and Communication Orchestrator core has DUNCAN PASS at exact remote heads.
- Use a new permanent draft PR; never use PR #103 or implementation PRs as the message bus.
- The permanent PR remains draft/open and is never auto-merged.
- Message discovery must be GitHub event -> Work webhook; no scheduled/loop polling substitute.
- Live GitHub transport actor must be `Lester-Sparx`; logical roles remain derived protocol roles.
- Every authoritative write obeys remote ID + fresh exact-ID read-back MATCH.
- No OWNER auto-execution, no production activation by inference, no canon mutation, no OWNER LOCK.

---

## Task 1: Create the permanent Communication PR anchor only

**Files:**
- Create on a dedicated branch: `communication/ZB_COMMUNICATION_BUS_V0.md`

- [ ] Fresh-read protected `main` and create branch `zb-communication-bus-v0` from that exact SHA.
- [ ] Add exactly one inert anchor document stating `DO NOT MERGE`, `DRAFT FOREVER`, `NO OWNER LOCK`, `NO PRODUCTION CODE`, protocol version, tracker #106, and the exact DUNCAN-passed orchestrator candidate HEAD.
- [ ] Open a draft PR to `main` with title clearly marking it as permanent Communication Bus / DO NOT MERGE.
- [ ] Verify changed-file scope is anchor-only and record PR number, branch, base SHA, head SHA, creation actor, and draft/unmerged state.
- [ ] Persist canonical Communication PR identity to #106 and fresh-read the created evidence MATCH.

## Task 2: Configure exact Work event admission without polling

- [ ] Configure the Work event source to react only to new top-level conversation comments on the canonical Communication PR.
- [ ] Bind the Work handler configuration to repository, exact canonical PR number, protocol marker `ZB_AGENT_MESSAGE_V1`, and approved transport registry read from protected authority.
- [ ] Confirm receipts, owner views, reference events, SALVADOR events, review-thread comments, edited non-message comments, and unrelated prose do not enter logical-role execution.
- [ ] Record the platform/webhook configuration evidence available from the authorized Work surface. If no remote/config identifier can be obtained, record the gate as NOT PROVEN rather than claiming persistence.
- [ ] Do not replace an unavailable webhook with polling.

## Task 3: Create one disposable root message with exact bindings

- [ ] Create a disposable tracker/task specifically for communication proof; do not reuse #102 or mutate its historical chain.
- [ ] Fresh-read all task/PR/base/head/evidence bindings needed by the chosen proof fixture.
- [ ] Write one strict root `ZB_AGENT_MESSAGE_V1` on the permanent Communication PR using a new immutable `MESSAGE_ID`, producer `EVENT_ID`, chain `CORRELATION_ID`, `CAUSATION_MESSAGE_ID = NONE`, legal JINGO->LESTER transition, and `NO_AUTO_MERGE = TRUE`.
- [ ] Capture the returned GitHub message comment ID and fresh-read exact body/actor MATCH before considering the message recorded.

## Task 4: Prove webhook admission and LESTER truthful execution

- [ ] Obtain the real Work webhook/event execution evidence for the root message; event actor must resolve to `Lester-Sparx`.
- [ ] Work validates the canonical PR, live transport registry, strict message, causation, task/head/base/evidence/CAS, and expected LESTER gate.
- [ ] Persist `RECEIVED`; capture remote comment ID and fresh read-back MATCH.
- [ ] Start actual LESTER logical-role execution and obtain a real execution ID/evidence before writing `RUNNING`.
- [ ] Persist `RUNNING`; capture remote ID/read-back MATCH.
- [ ] Persist LESTER terminal RESULT or BLOCKED with exact evidence; capture remote ID/read-back MATCH.
- [ ] Verify duplicate delivery/reload does not execute LESTER twice.

## Task 5: Prove automatic JINGO return and DUNCAN handoff

- [ ] Only after LESTER terminal receipt read-back MATCH, verify the router emits exactly one next JINGO message with correct causation/correlation.
- [ ] Capture the new message remote ID and read-back MATCH.
- [ ] Execute JINGO on the actual Work surface; if task policy requires QC, JINGO emits exactly one DUNCAN `QC_REQUEST` message after its own terminal receipt is recorded.
- [ ] For every RECEIVED/RUNNING/RESULT stage, capture Work execution evidence plus GitHub remote IDs and fresh read-back MATCH.
- [ ] Verify no role-specific GitHub account appears as required authority.

## Task 6: Prove DUNCAN gate and return to JINGO

- [ ] Work derives `logicalRole=DUNCAN` from legal state; it must not accept body role claims as authority.
- [ ] Persist/read-back DUNCAN RECEIVED, truthful RUNNING, and terminal QC verdict with exact candidate/evidence bindings.
- [ ] On PASS or FAIL, emit the legal JINGO return only after DUNCAN terminal receipt read-back MATCH.
- [ ] A FAIL/BLOCKED verdict remains FAIL/BLOCKED; router cannot upgrade it.
- [ ] Capture every message/receipt remote ID, Work execution ID, and read-back result.

## Task 7: Exercise DJANGO path with a separate architecture-required fixture

- [ ] Use a second disposable proof fixture whose policy legally requires architecture review; do not force DJANGO into a task where architecture review is not required.
- [ ] Prove JINGO -> DJANGO `ARCH_REVIEW`, DJANGO RECEIVED/RUNNING/terminal verdict, and JINGO return with exact causation and remote read-back receipts.
- [ ] Verify owner-view producer emits a valid DJANGO row and current Console parser accepts/renders it.
- [ ] Keep the first proof fixture and second architecture fixture under distinct `CORRELATION_ID`s.

## Task 8: Prove replay, stale binding, and foreign-transport denial

- [ ] Redeliver an already terminal webhook event/message and prove no second logical execution occurs; record `REPLAY_TERMINAL` or equivalent existing-terminal handling.
- [ ] Submit a fixture with stale `TARGET_HEAD_SHA` and prove BLOCKED `TARGET_HEAD_STALE` with no target role execution.
- [ ] Submit a fixture with mismatched evidence hash and prove `EVIDENCE_MISMATCH`.
- [ ] Where the Work/GitHub test surface permits a non-authoritative actor fixture safely, prove foreign authenticated transport is rejected. If the platform cannot safely generate such an actor event, rely on exact unit/QC evidence and record remote foreign-actor proof as NOT EXECUTED rather than impersonating a role/account.
- [ ] Verify legacy role-specific comments remain historical and do not trigger execution.

## Task 9: Prove owner-view persistence and read-only Console

- [ ] After each terminal communication transaction, write canonical `ZB_OWNER_VIEW_V0` to the existing owner-view surface through WRITE -> fresh READ-BACK -> MATCH.
- [ ] Verify snapshot reflects actual correlation/task, last transition, running role only when backed by RUNNING, blocker/dead-letter, next gate, and OWNER action requirement.
- [ ] Run Console against the remote owner-view snapshot and record read-only output evidence; Console must not expose approve/route/merge/activate/lock mutation actions.
- [ ] If owner-view persistence fails, automatic forwarding stops with `OWNER_VIEW_PERSISTENCE_FAILED` rather than presenting stale success.

## Task 10: Prove bounded retry/dead-letter on a disposable failure

- [ ] Trigger a safe disposable transport/execution failure that can exercise the configured bounded retry path without changing a logical verdict.
- [ ] Verify immutable original message body/MESSAGE_ID across attempts and increasing ATTEMPT only in receipt records.
- [ ] Exhaust the configured bound and persist/read-back DEAD_LETTER.
- [ ] Verify no automatic next message is emitted from dead-letter state and owner view becomes BLOCKED with exact reason.

## Task 11: Assemble one immutable remote proof receipt

- [ ] Record in #106 a compact `ZB106_COMMUNICATION_REMOTE_PROOF_V1` containing: canonical Communication PR number/base/head, Work event/config evidence ID if available, every fixture correlation/message/comment/receipt ID, all actual execution IDs, exact target heads/evidence hashes, owner-view comment IDs, Console evidence reference, and failure/replay fixture outcomes.
- [ ] Include explicit assertions: `POLLING=NO`, `TRANSPORT=Lester-Sparx`, `ROLE_ACCOUNT_SWITCHING=NO`, `AUTO_MERGE=NO`, `PRODUCTION_ACTIVATION=NO`, `CANON_CHANGE=NO`, `OWNER_LOCK=NO`.
- [ ] Fresh-read the proof comment by exact remote ID and compare body MATCH.
- [ ] DUNCAN independently rereads the underlying evidence rather than trusting the summary receipt and records PASS/FAIL/BLOCKED with read-back.

## Task 12: Stop at explicit OWNER activation gate

- [ ] If and only if all required remote proof and DUNCAN evidence is PASS, set `PRODUCTION_READY = YES / NOT ACTIVE` in the owner projection.
- [ ] Request a separate explicit OWNER production-activation decision bound to exact foundation candidate, orchestrator candidate, canonical Communication PR, and remote proof evidence.
- [ ] Do not infer activation from spec approval, plan approval, code merge, DUNCAN PASS, or successful proof.
- [ ] Even after activation, permanent Communication PR remains draft/unmerged and OWNER LOCK remains a separate authority action not created by this system.

**Plan exit condition:** either `REMOTE_PROOF = PASS / PRODUCTION_READY = YES / ACTIVE = NO` awaiting explicit OWNER activation, or a precise BLOCKED record with exact missing/failing remote evidence. No polling fallback and no false PASS are permitted.