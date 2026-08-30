# LESTER Programming School R01 — Design

Status: OWNER-DIRECTED R02 BASE CANDIDATE
Date: 2026-08-30
Tracker: #216
Base main: `b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1`

## Goal

Create the smallest durable base that lets DUNCAN PRIME teach and evaluate LESTER as his personal programming assistant without inventing historical competence, merging discipline with skill, or building another agent framework.

## Existing systems reused

This design reuses, rather than replaces:

1. `DUNCAN_CONTEXT_NEXT_V1` and the DUNCAN Fortress fail-closed learning pattern.
2. `SHERIFF_POLICY_V1` + SHERIFF verdict history for discipline and incident learning.
3. `SHERIFF_SCOREBOARD_V1` as the separate discipline/league surface.
4. Permanent Archive V1 as authoritative RAW history.
5. PR #205 Unified Archive Restore patterns for verified lessons and task-specific retrieval; R01 does not copy its entire stale branch into main.
6. Existing GitHub Actions and Python standard-library test environment.

No second archive, scheduler, durable database service, message bus, model-training service, or generic agent framework is added.

## External OSS study and adoption rule

R01 studies ready-made patterns, but imports no heavy framework dependency.

- SWE-bench: real repository task/patch evaluation model; MIT.
- SWE-agent / mini-SWE-agent: bounded coding task execution/evaluation patterns; MIT; upstream recommends the simpler mini-SWE-agent path for new work.
- OpenHands core/evaluation: coding-agent task/evaluation patterns; core outside `enterprise/` is MIT.
- pytest: test-first verification; MIT.
- Hypothesis: changed/unseen/property-based testing pattern; MPL-2.0; optional future use only, not an R01 dependency.
- Ruff and Pyright: lint/type-check teaching targets; MIT; optional future exercises, not an R01 dependency.
- Existing ZORR actionlint/zizmor/Gitleaks remain the supply-chain/security checks already integrated by DUNCAN Fortress.

Adoption law: `EXISTING ZORR -> STANDARD LIBRARY/NATIVE -> MATURE OSS -> MINIMAL GLUE`.

## Identity and authority

`DUNCAN PRIME = teacher / curriculum owner / reviewer`

`LESTER = DUNCAN PRIME personal programming assistant / implementation learner`

`SHERIFF = independent discipline and integrity control`

These roles must not collapse:

- DUNCAN may propose a skill update from verified evidence.
- LESTER may not self-award competence.
- SHERIFF discipline never becomes technical competence.
- A high technical skill state never cancels a SHERIFF HOLD.
- OWNER authority and existing merge/canon/production gates remain unchanged.

## R01 skill model

Use the same compact evidence-state vocabulary already accepted by DUNCAN Fortress:

`UNTESTED / FAILED / PARTIAL / PROVEN`

This R01 deliberately does not add `OPERATIONAL` or `PRODUCTION_PROVEN`; those can be a later slice after real evidence exists.

`PROVEN` means evidence-based transfer, not reading or one lucky success.

Per-domain state is derived from verified evidence:

- `UNTESTED`: no verified execution/transfer result.
- `FAILED`: one or more verified failures and zero verified passes.
- `PARTIAL`: at least one verified pass, but PROVEN gate is not met.
- `PROVEN`: at least two verified PASS results, including at least one verified changed/unseen `TRANSFER` PASS.

Study/read-only events are recorded for curriculum context but never promote skill state.

Unverified outcomes never promote or demote competence.

## Programming domain catalog

R01 ships a deterministic catalog covering the programming work DUNCAN is expected to teach LESTER:

1. `python`
2. `typescript_javascript`
3. `git_github`
4. `testing_tdd`
5. `debugging_root_cause`
6. `software_architecture`
7. `oss_reuse`
8. `ci_cd_automation`
9. `security_supply_chain`
10. `data_storage_search`
11. `graphics_realtime`
12. `computer_vision`
13. `ai_agent_integration`
14. `performance_reliability`
15. `windows_linux_runtime`
16. `math_scientific_computing`

The catalog is an R01 curriculum map, not a claim that LESTER already knows any of these domains.

## Evidence contract

Each training/evaluation record uses `LESTER_PROGRAMMING_EVIDENCE_V1` fields:

- `evidenceId`: immutable non-empty identifier.
- `agentId`: exactly `LESTER`.
- `domain`: one catalog domain.
- `taskKind`: non-empty deterministic task category.
- `mode`: `STUDY`, `EXECUTION`, or `TRANSFER`.
- `result`: `PASS` or `FAIL`.
- `verified`: boolean.
- `sourceRef`: non-empty durable GitHub/archive evidence reference.
- `exactHead`: 40-hex commit SHA for EXECUTION/TRANSFER; empty is allowed only for STUDY.
- `sequence`: non-negative integer used only for deterministic ordering/provenance.

Malformed evidence fails closed. Duplicate `evidenceId` with different bytes is an integrity error.

## Derived profile

`LESTER_PROGRAMMING_PROFILE_V1` is deterministic derived state, not authority.

For each domain and each observed task kind it records:

- state;
- study events;
- verified passes;
- verified failures;
- verified transfer passes;
- evidence IDs/source refs;
- last sequence.

The profile also records:

- `agentId = LESTER`;
- catalog version;
- `historicalBackfill = false`;
- `disciplineSource = hq/sheriff/SHERIFF_SCOREBOARD_V1.json`;
- explicit statement that discipline is separate from competence.

R01 ships a neutral bootstrap profile with every domain `UNTESTED` and zero invented evidence.

## DUNCAN next-training-target selection

DUNCAN needs one deterministic answer to: `what should LESTER learn next?`

`choose_next_training_target(profile, preferred_domains=None)`:

1. Consider `preferred_domains` in caller-supplied order when present; otherwise use catalog order.
2. Prefer lower skill state in order `FAILED < UNTESTED < PARTIAL < PROVEN` for remediation-first learning.
3. Within equal state, prefer fewer verified attempts.
4. Break all remaining ties by catalog order.
5. Return domain, state, reason, and recommended next mode:
   - `FAILED` -> `EXECUTION` remediation task;
   - `UNTESTED` -> `EXECUTION` baseline task;
   - `PARTIAL` -> `TRANSFER` changed/unseen task;
   - all `PROVEN` -> first preferred/catalog domain with `TRANSFER` maintenance challenge.

SHERIFF HOLD/HARD_HOLD remains a separate execution gate; target selection does not erase it.

## Failure and integrity behavior

Fail closed on:

- unknown domain;
- invalid mode/result;
- missing durable sourceRef;
- missing/invalid exactHead for EXECUTION/TRANSFER;
- negative sequence;
- duplicate evidence ID with conflicting content;
- malformed profile/catalog.

Do not guess historical skill from old chat summaries, old PR volume, or agent self-report.

## Files

Create:

- `scripts/lester_programming_school.py` — deterministic validation/profile/next-target library + JSON CLI.
- `hq/training/LESTER_PROGRAMMING_DOMAIN_CATALOG_V1.json` — curriculum catalog only.
- `hq/training/LESTER_PROGRAMMING_PROFILE_V1.json` — neutral derived bootstrap.
- `tests/test_lester_programming_school.py` — TDD/behavior/regression tests.
- `docs/LESTER_PROGRAMMING_SCHOOL_R01.md` — operator/agent contract and evidence law.

Do not modify SHERIFF scoring formulas or DUNCAN Night School reducer in R01.

## Acceptance

`LESTER_PROGRAMMING_SCHOOL_R01 = PASS` requires on one exact candidate HEAD:

1. Domain catalog parses and contains exactly the 16 declared unique domains.
2. Neutral bootstrap contains no historical claims and all domains are `UNTESTED`.
3. STUDY and unverified PASS cannot promote skill.
4. One verified EXECUTION PASS produces `PARTIAL`, not `PROVEN`.
5. Two verified PASS results without a changed/unseen TRANSFER remain `PARTIAL`.
6. Two verified PASS results with at least one verified TRANSFER PASS produce `PROVEN`.
7. Verified FAIL with no verified PASS produces `FAILED`.
8. Task-kind state is derived separately inside its domain.
9. Next-target selection is deterministic and remediation/transfer aware.
10. Duplicate conflicting evidence fails closed.
11. Discipline source is referenced but never numerically copied into technical skill.
12. Focused tests, repository validation, full unittest suite and relevant CI all PASS.
13. Fresh GitHub readback matches the exact candidate.
14. `main` remains unchanged; merge is a separate gate.