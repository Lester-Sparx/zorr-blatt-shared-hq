# ZB Communication Orchestrator v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Implement the deterministic, deny-by-default protocol core for Variant A: strict `ZB_AGENT_MESSAGE_V1` admission, logical-role legality, exact binding/CAS/evidence checks, durable receipts with fresh read-back, idempotency/retry/dead-letter, automatic next legal message, and `ZB_OWNER_VIEW_V0` projection compatible with Console v0.

**Architecture:** Add a transport-agnostic package `zb_communication_orchestrator` containing pure protocol, authority, ledger, persistence, and router logic. External ChatGPT Work is the event/execution adapter; repository code MUST NOT replace the Work webhook with polling, PAT-backed Actions, or a second local controller. Network/execution surfaces are injected through narrow ports so unit tests can prove state truth without pretending an LLM/Work execution occurred.

**Tech Stack:** Python 3.12, dataclasses/typing/hashlib/json from stdlib, pytest, existing Shared HQ validators and Console parser.

**Spec:** `docs/superpowers/specs/2026-08-28-zb-communication-orchestrator-v0-design.md` at OWNER-approved HEAD `9c9f0ebbf2bd5d5dc5b21578718f1ef356e278f9`.

**Global Constraints:**
- Start PR C only from the exact DUNCAN-passed foundation candidate from the separate Foundation Integration plan, or stack directly on that candidate if it is intentionally unmerged. Record the exact base SHA.
- Only authenticated event-envelope transport `Lester-Sparx` is accepted for live routing. A comment body claim has no transport authority.
- Logical role is derived from legal durable state; `FROM_ROLE`/`TO_ROLE` are claims to validate, not authentication.
- `OWNER` is never auto-executed. OWNER-only boundary produces a durable stop/owner-action projection.
- Original message body is immutable for a `MESSAGE_ID`; retry attempt numbers live only in receipts.
- `READ_BACK_REQUIRED = TRUE` is not proof. Runtime advances only after fresh read of the exact remote comment ID matches the intended canonical body.
- `RUNNING` requires actual execution-start evidence/ID from the execution adapter.
- No auto-merge, production activation, canon mutation, OWNER LOCK, role-account switching, PAT router, or GitHub polling trigger.
- Existing `ZB_AGENT_TASK_V0`, `ZB_AGENT_EVENT_V0`, Controller Daemon, Reference Bridge, and local SALVADOR execution semantics remain separate.

---

## Task 1: Define strict message contracts with canonical serialization

**Files:**
- Create: `agent-controller/src/zb_communication_orchestrator/__init__.py`
- Create: `agent-controller/src/zb_communication_orchestrator/contracts.py`
- Create: `agent-controller/tests/test_communication_contracts.py`

- [ ] Write RED tests for the exact canonical `ZB_AGENT_MESSAGE_V1` field order from the approved spec, valid IDs, 40-hex SHA/`NONE`, 64-hex evidence hash/`NONE`, positive revision/`NONE`, allowed roles/message kinds, and mandatory `NO_AUTO_MERGE = TRUE`.
- [ ] Add RED cases for unknown fields, duplicate fields, wrong order, multiline machine values, invalid repo, invalid SHA/hash, illegal `OWNER` sender/target, and unsupported marker/version.
- [ ] Add canonical body hashing tests so the same `MESSAGE_ID` can be collision-checked against immutable canonical content.
- [ ] Run `cd agent-controller && python -m pytest tests/test_communication_contracts.py -q` and confirm RED.
- [ ] Implement immutable dataclasses, strict parser, canonical formatter, and body digest with no permissive fallback.
- [ ] Run targeted tests GREEN.
- [ ] Commit: `feat: define strict communication message contract`.

## Task 2: Define strict receipt contracts without circular read-back claims

**Files:**
- Modify: `agent-controller/src/zb_communication_orchestrator/contracts.py`
- Create: `agent-controller/tests/test_communication_receipts.py`

- [ ] Write RED tests for `ZB_AGENT_RECEIPT_V1` and exact states `RECEIVED|RUNNING|RESULT|BLOCKED|DEAD_LETTER`.
- [ ] Require `SOURCE_COMMENT_ID`, unique `RECEIPT_ID`, `TRANSPORT_ACTOR`, `LOGICAL_ROLE`, task/head/execution/result/evidence bindings, positive `ATTEMPT`, and literal `READ_BACK_REQUIRED = TRUE`.
- [ ] Add a test proving receipt formatter has no `READ_BACK=MATCH` or equivalent self-attestation field.
- [ ] Add state consistency tests: `RUNNING` requires non-`NONE` execution ID; terminal RESULT/BLOCKED must carry a result code; DEAD_LETTER must carry a failure result code.
- [ ] Run targeted test RED, implement minimal strict parser/formatter, run GREEN.
- [ ] Commit: `feat: define durable communication receipts`.

## Task 3: Normalize and validate the Work webhook event envelope

**Files:**
- Create: `agent-controller/src/zb_communication_orchestrator/admission.py`
- Create: `agent-controller/src/zb_communication_orchestrator/ports.py`
- Create: `agent-controller/tests/test_communication_admission.py`

- [ ] Define a small immutable `WebhookEnvelope` containing producer event ID, repository, PR number, top-level comment ID/body, authenticated actor, and event type.
- [ ] Write RED tests accepting only the configured canonical Communication PR, repository `Lester-Sparx/zorr-blatt-shared-hq`, top-level comment event, actor `Lester-Sparx`, and body beginning with strict `ZB_AGENT_MESSAGE_V1`.
- [ ] Reject receipt comments, owner-view comments, Reference Bridge events, SALVADOR events, unrelated prose, foreign actors, wrong PR, edited/review-thread events, and missing authenticated actor with exact failure codes.
- [ ] Ensure no code path discovers messages by listing/polling GitHub.
- [ ] Run targeted tests RED, implement admission, run GREEN.
- [ ] Commit: `feat: admit only canonical Work message events`.

## Task 4: Build the durable GitHub port and WRITE/read-back transaction helper

**Files:**
- Modify: `agent-controller/src/zb_communication_orchestrator/ports.py`
- Create: `agent-controller/src/zb_communication_orchestrator/persistence.py`
- Create: `agent-controller/tests/test_communication_persistence.py`

- [ ] Define a `GitHubPort` protocol for fresh reads only: fetch PR metadata/head, fetch protected-main/ref content required by authority, fetch issue/PR comments, write top-level comment returning remote ID, read exact comment ID.
- [ ] Write RED tests for successful write -> remote ID -> fresh exact-ID read -> canonical body equality.
- [ ] Add failure tests for missing ID, write exception, 404/read exception, body mismatch, wrong remote actor/body mutation, and ambiguous acknowledgement.
- [ ] Add reconciliation test: write succeeded but acknowledgement was lost; retry must fresh-read/reconcile the same intended receipt and must not imply a second execution.
- [ ] Implement `persist_and_verify(...)` returning a verified remote receipt reference only after MATCH.
- [ ] Run targeted tests GREEN.
- [ ] Commit: `feat: enforce receipt write read-back law`.

## Task 5: Load live transport registry and derive role legality from authority state

**Files:**
- Create: `agent-controller/src/zb_communication_orchestrator/authority.py`
- Create: `agent-controller/tests/test_communication_authority.py`

- [ ] Write RED tests that the live transport registry is loaded from fresh protected-base `.github/zb/roles.yml`, accepts only `Lester-Sparx`, and treats logical roles independently from actor identity.
- [ ] Model explicit legal role/message transitions for `JINGO`, `LESTER`, `DUNCAN`, `DJANGO`; never include automatic OWNER execution.
- [ ] Add tests proving a body claim `logicalRole=DUNCAN` or `TO_ROLE=DUNCAN` cannot bypass expected transition order.
- [ ] Add tests for task-policy-required DUNCAN and optional/required DJANGO gates; illegal skip is `ROLE_TRANSITION_ILLEGAL`.
- [ ] Add OWNER-boundary tests returning `OWNER_GATE_REQUIRED` without merge/lock/activation action.
- [ ] Run targeted tests RED, implement explicit transition tables/derivation, run GREEN.
- [ ] Commit: `feat: derive logical role authority from legal state`.

## Task 6: Verify exact issue/PR/base/head/revision/evidence bindings

**Files:**
- Modify: `agent-controller/src/zb_communication_orchestrator/authority.py`
- Create: `agent-controller/src/zb_communication_orchestrator/bindings.py`
- Create: `agent-controller/tests/test_communication_bindings.py`

- [ ] Write RED tests for fresh target PR HEAD equality, protected-base SHA equality, task revision CAS, issue/task identity, evidence reference existence, and evidence SHA256 match.
- [ ] Cover exact failures `TARGET_HEAD_STALE`, `BASE_CAS_MISMATCH`, `TASK_REVISION_MISMATCH`, `EVIDENCE_MISSING`, `EVIDENCE_MISMATCH`.
- [ ] Require HEAD when `TARGET_PR != NONE`; reject stale evidence that points to a prior candidate HEAD.
- [ ] Ensure historical role-specific login comments are readable as history but never satisfy a live authority binding.
- [ ] Implement narrow verifiers using fresh `GitHubPort` reads.
- [ ] Run targeted tests GREEN.
- [ ] Commit: `feat: bind communication gates to exact remote state`.

## Task 7: Build correlation ledger, causation, replay, and collision protection

**Files:**
- Create: `agent-controller/src/zb_communication_orchestrator/ledger.py`
- Create: `agent-controller/tests/test_communication_ledger.py`

- [ ] Write RED tests reconstructing one correlation from durable message/receipt comments.
- [ ] Verify `CAUSATION_MESSAGE_ID` matches the exact prior legal message; `NONE` is accepted only for an authorized root.
- [ ] Duplicate webhook delivery of the same immutable message returns existing state and does not execute again.
- [ ] Reused `MESSAGE_ID` with different canonical body is `MESSAGE_ID_COLLISION`.
- [ ] Terminal message replay is `REPLAY_TERMINAL` and never emits another downstream message.
- [ ] Corrupted/incomplete receipts are ignored as authority unless their remote identity/read-back evidence is supplied as verified by the adapter transaction state.
- [ ] Implement deterministic ledger reconstruction and run tests GREEN.
- [ ] Commit: `feat: add communication correlation ledger`.

## Task 8: Define truthful logical-role execution port

**Files:**
- Modify: `agent-controller/src/zb_communication_orchestrator/ports.py`
- Create: `agent-controller/src/zb_communication_orchestrator/execution.py`
- Create: `agent-controller/tests/test_communication_execution.py`

- [ ] Define a `RoleExecutor` port used by ChatGPT Work adapter, with explicit start result containing a real execution ID and later terminal result/evidence.
- [ ] Write RED tests proving queued/accepted webhook delivery is not execution start and cannot produce `RUNNING`.
- [ ] Add failures `EXECUTION_START_FAILED` and `EXECUTION_TIMEOUT`; timeout never upgrades to success.
- [ ] Do not implement a fake local LLM runner or Codex subprocess. Unit tests use deterministic fakes only.
- [ ] Implement execution state dataclasses/validation and run GREEN.
- [ ] Commit: `feat: model truthful logical role execution`.

## Task 9: Implement router transaction through RECEIVED -> RUNNING -> terminal

**Files:**
- Create: `agent-controller/src/zb_communication_orchestrator/router.py`
- Create: `agent-controller/tests/test_communication_router.py`

- [ ] Write a RED happy-path test: admitted JINGO->LESTER message -> exact legality/bindings -> persisted/read-back RECEIVED -> executor actually starts -> persisted/read-back RUNNING -> terminal RESULT -> persisted/read-back terminal -> exactly one derived next JINGO message.
- [ ] Assert no execution starts if RECEIVED persistence/read-back fails.
- [ ] Assert no next message is emitted until terminal receipt is read back MATCH.
- [ ] Add negative-verdict test proving FAIL/BLOCKED cannot be upgraded by routing.
- [ ] Add OWNER-gate test proving chain stops and no owner execution/merge/lock/activation command exists.
- [ ] Implement smallest transaction coordinator using Tasks 1-8 modules.
- [ ] Run targeted tests GREEN.
- [ ] Commit: `feat: route one legal communication transaction`.

## Task 10: Add bounded retry, timeout, and dead-letter behavior

**Files:**
- Create: `agent-controller/src/zb_communication_orchestrator/retry.py`
- Modify: `agent-controller/src/zb_communication_orchestrator/router.py`
- Create: `agent-controller/tests/test_communication_retry.py`

- [ ] Write RED tests for bounded configured attempts while preserving byte-for-byte original message content and same `MESSAGE_ID`.
- [ ] Require incrementing `ATTEMPT` only in receipt records.
- [ ] Test transport/persistence retry separately from logical verdict; a FAIL verdict is never retried into PASS.
- [ ] After retry exhaustion, persist/read-back `DEAD_LETTER`, update terminal state, and emit no automatic next message.
- [ ] Add timeout test with execution ID/evidence and exact `EXECUTION_TIMEOUT` result.
- [ ] Implement minimal retry policy object and router integration; run GREEN.
- [ ] Commit: `feat: add bounded communication recovery`.

## Task 11: Produce canonical owner projection and add DJANGO to Console contract

**Files:**
- Create: `agent-controller/src/zb_communication_orchestrator/owner_view.py`
- Create: `agent-controller/tests/test_communication_owner_view.py`
- Modify: `agent-controller/src/zb_local_controller/owner_snapshot.py`
- Modify: `agent-controller/tests/test_owner_snapshot.py`
- Modify if required by test: `agent-controller/src/zb_local_controller/console.py`
- Modify if required by test: `agent-controller/tests/test_console.py`

- [ ] Write RED tests formatting a complete `ZB_OWNER_VIEW_V0` after each terminal communication receipt, exposing current correlation/task in stable descriptive fields/gates, last legal transition, true running role only when RUNNING exists, blocker/dead-letter, next gate, OWNER action requirement, and evidence summary.
- [ ] Add `DJANGO` to the required owner-snapshot agent set atomically and update existing parser/Console fixtures.
- [ ] Test that a producer snapshot accepted by `owner_snapshot.py` renders in Console; forbid producer/parser version skew.
- [ ] Keep Console read-only; no route/approve/merge action is added to `console.py`.
- [ ] Persist owner view through the same `persist_and_verify` helper; failure is `OWNER_VIEW_PERSISTENCE_FAILED` and blocks automatic forwarding if the spec-required projection cannot be recorded.
- [ ] Run `python -m pytest tests/test_communication_owner_view.py tests/test_owner_snapshot.py tests/test_console.py -q` GREEN.
- [ ] Commit: `feat: project communication state to owner console`.

## Task 12: Add single webhook handler surface with injected Work/GitHub adapters

**Files:**
- Create: `agent-controller/src/zb_communication_orchestrator/handler.py`
- Create: `agent-controller/tests/test_communication_handler.py`
- Modify: `agent-controller/README.md`

- [ ] Write RED tests for a single `handle_webhook(envelope, github, executor, config)` path that performs admission and router processing exactly once.
- [ ] Ensure self-generated receipts/owner views are ignored by admission and cannot recursively trigger logical execution.
- [ ] Ensure handler contains no sleep loop, list/poll loop, PAT, Actions writer, GitHub-account impersonation, subprocess role launcher, merge call, activation call, or lock mutation.
- [ ] Document the Work adapter contract: authenticated GitHub comment event invokes this logical handler contract; Work supplies actual role execution and connected GitHub operations; repository core remains deterministic authority logic.
- [ ] Run targeted tests GREEN.
- [ ] Commit: `feat: expose event-driven orchestrator handler`.

## Task 13: Security and historical-boundary regression suite

**Files:**
- Create: `agent-controller/tests/test_communication_security.py`
- Modify: root tests only if a new positive regression is required; do not weaken existing validators.

- [ ] Test every minimum spec failure code: `TRANSPORT_ACTOR_REJECTED`, `COMMUNICATION_PR_MISMATCH`, `MESSAGE_PROTOCOL_INVALID`, `MESSAGE_ID_COLLISION`, `REPLAY_TERMINAL`, `CAUSATION_MISMATCH`, `ROLE_TRANSITION_ILLEGAL`, `TARGET_HEAD_STALE`, `BASE_CAS_MISMATCH`, `TASK_REVISION_MISMATCH`, `EVIDENCE_MISSING`, `EVIDENCE_MISMATCH`, `OWNER_GATE_REQUIRED`, `RECEIPT_WRITE_FAILED`, `RECEIPT_READ_BACK_MISMATCH`, `EXECUTION_START_FAILED`, `EXECUTION_TIMEOUT`, `RETRY_EXHAUSTED`, `DEAD_LETTERED`, `OWNER_VIEW_PERSISTENCE_FAILED`.
- [ ] Add regressions that historical `builderGitHubLogin`/`reviewerGitHubLogin`/old DUNCAN account comments cannot become live handoffs.
- [ ] Add regression that `ZB_AGENT_EVENT_V0` stays SALVADOR-only and `ZB_REFERENCE_DELIVERY_V1`/`ZB_REFERENCE_EVENT_V1` stay Reference Bridge-only.
- [ ] Run targeted suite GREEN.
- [ ] Commit: `test: enforce orchestrator security boundaries`.

## Task 14: Full verification of PR C candidate

- [ ] Run `cd agent-controller && python -m pytest -q`; require zero failures.
- [ ] Run current root Shared HQ test/validation suite from protected-base workflow behavior; require zero failures.
- [ ] Verify `.github/zb/roles.yml` still has one approved transport actor and logical roles unchanged.
- [ ] Verify Control Tower artifact/hash integrity and existing CAS/persistence-boundary tests.
- [ ] Scan candidate diff for forbidden strings/surfaces: PAT/token secret storage, account switching, GitHub polling for communication messages, auto-merge, production activation, canon mutation, OWNER LOCK creation.
- [ ] Verify PR #103 and issue #102 evidence were not modified.
- [ ] Record exact candidate HEAD and fresh workflow/check run IDs.

## Task 15: Open PR C and perform independent DUNCAN QC

- [ ] Open dedicated Communication Orchestrator TDD PR, separate from foundation PR and separate from the permanent Communication PR.
- [ ] Bind PR body to OWNER-approved spec HEAD `9c9f0e...`, exact foundation candidate base, exact candidate HEAD, test counts, and forbidden-operation declarations.
- [ ] DUNCAN independently verifies all 20 acceptance-matrix families from the spec, exact diff, transport/role separation, receipt law, replay protection, Console/DJANGO integration, and absence of dangerous command surfaces.
- [ ] Persist DUNCAN verdict to tracker #106 and PR C using WRITE -> fresh READ-BACK -> MATCH.
- [ ] Do not merge automatically and do not activate production.

**Plan exit condition:** `ORCHESTRATOR_CORE = DUNCAN PASS` at one exact PR C HEAD, with event-driven core and Console projection verified, while actual Work webhook/Communication PR remote proof remains a separate downstream operational gate.