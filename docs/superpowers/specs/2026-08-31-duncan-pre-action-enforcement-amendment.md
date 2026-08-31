# DUNCAN Pre-Action Enforcement Amendment

**Status:** sandbox design amendment to Unified Archive Restore V1 / PR #205.

## Goal

Close the verified-learning loop with one deterministic decision point before a substantive action. Reuse the existing Unified Archive / SHERIFF lesson corpus and existing execution laws. Add no daemon, database, model service, runner, polling loop, or dependency.

## Root cause

The current chain is:

`ERROR -> SHERIFF VERDICT -> CLOSED LESSON -> TRAINING_CORPUS -> OPTIMIZED POLICY -> restart policy prefix -> agent action`

The chain has no mandatory deterministic veto immediately before `agent action`. SHERIFF V1 evaluates already-emitted agent events; it is not a wrapper around native ChatGPT connector/tool calls. Therefore memory and learning can be correct while behavior still repeats a known process error.

For a serial prevention chain with stage reliabilities `r_i`, effective prevention reliability is `R = product(r_i)`. A missing mandatory pre-action stage is `r_pre_action = 0`, so `R = 0` regardless of upstream lesson quality.

## Design

Extend the existing `scripts/hq_unified_archive.py` instead of creating a new framework.

Add `evaluate_pre_action(context, learning_policy=None) -> dict` and a `pre-action` CLI subcommand. Input is explicit structured state; the function does not infer operational truth from prose.

Decision schema: `ZB_PRE_ACTION_DECISION_V1`.

Decision values:
- `ALLOW` — proposed action may proceed.
- `WAIT` — an active attempt already owns the path; only result/evidence read is legal.
- `BLOCK` — proposed action violates an execution invariant.
- `OWNER_REQUIRED` — a proven external boundary requires human action.

Allowed action kinds:
- `EXECUTE_PRODUCT_STEP`
- `READ_ACTIVE_RESULT`
- `READ_REQUIRED_EVIDENCE`
- `SEARCH_ASSET`
- `VERIFY_PREREQUISITE`
- `PROCESS_MUTATION`
- `REQUEST_OWNER_ACTION`
- `CLAIM_PASS`
- `IMAGE_MUTATION`

Required context fields:
- `action`
- `directlyAdvancesPhysicalResult`
- `activeAttempt`
- `exactOwnerInputProvided`
- `prerequisiteAlreadyProven`
- `provenProcessBlocker`
- `processMutationCountForBlocker`
- `newPhysicalBlocker`
- `provenExternalBoundary`
- `freshVerificationEvidence`
- `explicitOwnerImageMutationCommand`

All booleans must be real JSON booleans; process mutation count must be a non-negative integer. Missing/invalid context fails closed with `UnifiedArchiveError`.

## Decision priority

1. `IMAGE_MUTATION` without an explicit OWNER image-mutation command -> `BLOCK / OWNER_IMAGE_MUTATION_COMMAND_REQUIRED`.
2. While `activeAttempt=true`, every action except `READ_ACTIVE_RESULT` and `READ_REQUIRED_EVIDENCE` -> `WAIT / ACTIVE_ATTEMPT_OWNS_PATH`.
3. `SEARCH_ASSET` while `exactOwnerInputProvided=true` -> `BLOCK / EXACT_OWNER_INPUT_SUPERSEDES_SEARCH`.
4. `VERIFY_PREREQUISITE` while `prerequisiteAlreadyProven=true` -> `BLOCK / PREREQUISITE_ALREADY_PROVEN`.
5. `PROCESS_MUTATION` without `provenProcessBlocker=true` -> `BLOCK / PROCESS_MUTATION_REQUIRES_PROVEN_PROCESS_BLOCKER`.
6. A second process mutation for the same blocker (`processMutationCountForBlocker >= 1`) without `newPhysicalBlocker=true` -> `BLOCK / REPEAT_PROCESS_MUTATION_REQUIRES_NEW_BLOCKER`.
7. `REQUEST_OWNER_ACTION` without `provenExternalBoundary=true` -> `BLOCK / OWNER_IS_NOT_A_COURIER`; with a proven boundary -> `OWNER_REQUIRED / PROVEN_EXTERNAL_BOUNDARY`.
8. `CLAIM_PASS` without `freshVerificationEvidence=true` -> `BLOCK / FRESH_VERIFICATION_REQUIRED`.
9. Any action that does not directly advance the physical result is blocked unless it is `READ_ACTIVE_RESULT` or `READ_REQUIRED_EVIDENCE` -> `BLOCK / NO_DIRECT_PRODUCT_PROGRESS`.
10. Otherwise -> `ALLOW / PRE_ACTION_GATE_PASS`.

## Learning integration

`pre-action` may receive `--archive-root` + `--query`. It must call the existing `build_learning_policy()` and return the verified lesson status, lesson IDs, and policy prefix with the decision. Fresher physical evidence still outranks learned policy.

This amendment does not pretend natural-language lessons can safely become arbitrary executable code. Hard routing comes from explicit invariants; verified lessons are deterministically surfaced at the decision point. Future machine-actionable remediation codes may extend the gate only through their own TDD gate.

## Bootstrap binding

`AGENTS.md` must require the pre-action decision before substantive execution when the Unified Archive learning layer is available. Non-`ALLOW` decisions are terminal for that proposed action. `WAIT` means read the active attempt, not mutate the path.

Repository policy cannot physically intercept native ChatGPT tool calls at the product platform boundary; do not claim otherwise. It can hard-gate any execution surface that invokes this function and provide a mandatory fail-closed protocol for agent bootstrap.

## Acceptance replay

The 2026-08-31 OpenToonz incident must replay as:
- exact asset + `SEARCH_ASSET` -> BLOCK;
- already proven runtime + `VERIFY_PREREQUISITE` -> BLOCK;
- workflow edit without a proven workflow/process blocker -> BLOCK;
- another path mutation while a run is active -> WAIT;
- OWNER relay without proven external boundary -> BLOCK.

Normal exact-asset product execution -> ALLOW.

Additional gates:
- PASS claim without fresh evidence -> BLOCK;
- image mutation without direct OWNER command -> BLOCK;
- proven external boundary -> OWNER_REQUIRED;
- first minimal process repair after a proven process blocker -> ALLOW.

## Constraints

- sandbox only until independent verification;
- no production SHERIFF mutation;
- no new daemon/service/runner/framework/dependency;
- no polling;
- no model-weight claim;
- no automatic merge or production activation;
- TDD RED must precede production-code changes.
