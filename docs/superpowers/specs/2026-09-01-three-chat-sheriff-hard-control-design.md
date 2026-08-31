# ZORR Three-Chat SHERIFF Hard Control R01 — Design

STATUS = OWNER APPROVED
SCOPE = CHAT A / CHAT B / CHAT C on the ZORR studio route

## Goal

Make the approved universal SHERIFF law an enforceable invariant for the three-chat production topology without creating a second agent framework, daemon, archive, or source of truth.

## Existing authority reused

- `ZORR_EXECUTION_CONSTITUTION.md`
- `AGENTS.md`
- existing SHERIFF policy/control-plane
- `studio/ZORR_THREE_CHAT_ORCHESTRATION_R01.md`
- `studio/ZORR_MASTER_CHAT_BOOTSTRAP_R01.md`
- trackers #249 / #250 / #251
- active production gate #248, subject to future fresh durable supersession

GitHub remains the durable source of truth. The shared law constrains roles; it does not replace their trackers.

## Architecture

Add one shared studio law file, `studio/ZORR_SHERIFF_THREE_CHAT_LAW_R01.md`. Bind both the master bootstrap and the three-chat orchestration contract to fresh-read it on every restart. Add one stdlib validator, `scripts/validate_three_chat_sheriff.py`, and run it inside existing `hq-validate`; do not create a new workflow.

The validator is fail-closed and static by design. It does not attempt to infer live GitHub state. Instead it prevents durable contracts from encoding known unsafe semantics that let future chats drift: hardcoded current HEADs, missing role/tracker bindings, missing shared-law wiring, and loss of core gate/promotion distinctions.

## Enforced invariants

1. CHAT A remains CHARACTER / COSTUME -> POSE and tracker #249.
2. CHAT B remains WORLD / CAMERA / S001 PREP and tracker #250.
3. CHAT C remains DUNCAN PRIME MASTER / INTEGRATOR and tracker #251.
4. `studio/ZORR_SHERIFF_THREE_CHAT_LAW_R01.md` is mandatory in bootstrap and orchestration boot paths.
5. No bootstrap/orchestration/law may hardcode a 40-hex SHA as a `CURRENT ... HEAD` claim. Current HEAD must be fresh-read from GitHub.
6. Shared law must preserve distinct PASS types: SPEC / STATIC / CI / RUNTIME / VISUAL / PHYSICAL / PRODUCTION.
7. Shared law must preserve the two-same-fails path-change rule.
8. Shared law must preserve one-active-gate, no-competing-locks, artifact-over-activity, durable write+readback, conflict visibility, OWNER taste provenance, protected authority, and MASTER-only cross-workstream promotion.
9. Workstream B may prepare downstream contracts while an upstream gate is active, but cannot self-promote downstream production PASS.
10. CHAT C coordinates/arbitrates/promotes and must not become a duplicate executor for A/B.

## Failure behavior

Validation failure blocks `hq-validate` with one exact error signature. Missing evidence never becomes PASS by inference.

Initial error signatures include:

- `SHERIFF_LAW_MISSING`
- `MASTER_SHERIFF_BINDING_MISSING`
- `ORCHESTRATION_SHERIFF_BINDING_MISSING`
- `CURRENT_HEAD_LITERAL_FORBIDDEN:<path>`
- `CHAT_A_TRACKER_BINDING_MISSING`
- `CHAT_B_TRACKER_BINDING_MISSING`
- `CHAT_C_TRACKER_BINDING_MISSING`
- `SHERIFF_INVARIANT_MISSING:<token>`

## TDD acceptance

RED: tests are committed first and `hq-validate` must fail because the shared law/validator/wiring do not yet exist.

GREEN: minimal implementation adds the law, validator, bootstrap/orchestration wiring, and existing-workflow validator step. The exact candidate HEAD must pass full `hq-validate` and fresh read-back.

No merge and no production mutation are part of R01 implementation.
