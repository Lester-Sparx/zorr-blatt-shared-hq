# DUNCAN Pre-Action Enforcement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic fail-closed pre-action decision to the existing Unified Archive learning layer so known process-loop failures are stopped before the next operational action.

**Architecture:** Reuse `scripts/hq_unified_archive.py`, its verified SHERIFF lessons, and its existing CLI. Add one pure decision function plus one CLI subcommand, then bind the existing restart map in `AGENTS.md`. No new service, database, runner, framework, dependency, or SHERIFF runtime change.

**Tech Stack:** Python stdlib, unittest, existing SQLite FTS5 learning layer, GitHub Actions validation already used by PR #205.

**Spec:** `docs/superpowers/specs/2026-08-31-duncan-pre-action-enforcement-amendment.md`

## Global Constraints

- Sandbox branch `duncan/sandbox` / PR #205 only until independent verification.
- TDD RED before production-code changes.
- No production SHERIFF mutation.
- No new daemon/service/runner/framework/dependency.
- No polling.
- No automatic merge or production activation.
- Do not claim a hard platform interceptor for native ChatGPT tool calls.

---

### Task 1: Deterministic pre-action decision core

**Files:**
- Modify: `scripts/hq_unified_archive.py`
- Create: `tests/test_hq_unified_archive_pre_action.py`

**Interfaces:**
- Consumes: explicit context dictionary defined by the amendment.
- Produces: `evaluate_pre_action(context: dict[str, Any], learning_policy: dict[str, Any] | None = None) -> dict[str, Any]` with schema `ZB_PRE_ACTION_DECISION_V1` and decision `ALLOW|WAIT|BLOCK|OWNER_REQUIRED`.

- [ ] **Step 1: Write failing behavior tests**

Create tests that replay all five 2026-08-31 loop actions and assert the exact decision/reason. Add positive-path tests for product execution, proven process repair, proven OWNER boundary, PASS evidence, and explicit image mutation authorization. Add fail-closed invalid-context tests.

- [ ] **Step 2: Run focused test and verify RED**

Run: `python -m unittest tests.test_hq_unified_archive_pre_action -v`
Expected: FAIL because `evaluate_pre_action` / `ZB_PRE_ACTION_DECISION_V1` do not exist yet.

- [ ] **Step 3: Implement minimal pure decision function**

Add only the schema constant, action set, context validation, priority rules from the spec, and deterministic result rendering. Include verified lesson metadata only when a supplied learning policy has `status=PROVEN`.

- [ ] **Step 4: Run focused test and verify GREEN**

Run: `python -m unittest tests.test_hq_unified_archive_pre_action -v`
Expected: all pre-action tests PASS.

- [ ] **Step 5: Run existing learning/self-heal/optimizer tests**

Run: `python -m unittest tests.test_hq_unified_archive_learning tests.test_hq_unified_archive_self_heal tests.test_hq_unified_archive_optimizer -v`
Expected: all PASS, proving no regression in lesson provenance or optimizer behavior.

### Task 2: Existing CLI becomes the executable gate

**Files:**
- Modify: `scripts/hq_unified_archive.py`
- Modify: `tests/test_hq_unified_archive_pre_action.py`

**Interfaces:**
- Consumes: `pre-action --context-path <json> [--archive-root <root> --query <text> --limit N]`.
- Produces: canonical JSON decision on stdout; non-ALLOW remains a valid decision payload, not a parser crash.

- [ ] **Step 1: Write failing CLI test**

The test writes a context JSON fixture, runs `hq_unified_archive.py pre-action`, parses stdout, and asserts an exact blocked decision. A second fixture with `--archive-root` and a verified lesson corpus asserts that lesson IDs/policy prefix are surfaced.

- [ ] **Step 2: Run focused test and verify RED**

Run: `python -m unittest tests.test_hq_unified_archive_pre_action -v`
Expected: FAIL because the `pre-action` subcommand is absent.

- [ ] **Step 3: Implement minimal CLI wiring**

Add `pre-action` parser with required `--context-path` and optional learning arguments. If either `--archive-root` or `--query` is supplied without the other, fail closed with a stable `UnifiedArchiveError`. Otherwise call existing `build_learning_policy()` and `evaluate_pre_action()`.

- [ ] **Step 4: Run focused test and verify GREEN**

Run: `python -m unittest tests.test_hq_unified_archive_pre_action -v`
Expected: PASS.

### Task 3: Bootstrap consumption is mandatory, not advisory

**Files:**
- Modify: `AGENTS.md`
- Modify: `tests/test_hq_unified_archive_learning_workflow.py`

**Interfaces:**
- Consumes: existing Unified Archive path and accepted learning policy from PR #205.
- Produces: restart law requiring `pre-action` before substantive execution and forbidding execution when decision is not `ALLOW`.

- [ ] **Step 1: Write failing restart-map assertions**

Assert that `AGENTS.md` contains `pre-action`, `ZB_PRE_ACTION_DECISION_V1`, `ACTIVE_ATTEMPT_OWNS_PATH`, and an explicit law that non-ALLOW decisions stop the proposed action.

- [ ] **Step 2: Run workflow test and verify RED**

Run: `python -m unittest tests.test_hq_unified_archive_learning_workflow -v`
Expected: FAIL on missing pre-action bootstrap binding.

- [ ] **Step 3: Add minimal AGENTS binding**

Extend only the existing Unified Archive learning/bootstrap section. Require explicit structured context, invoke the existing script, treat `WAIT` as read-result-only, and state the native-tool platform boundary honestly.

- [ ] **Step 4: Run workflow test and verify GREEN**

Run: `python -m unittest tests.test_hq_unified_archive_learning_workflow -v`
Expected: PASS.

### Task 4: Fresh full verification

**Files:** none beyond prior tasks.

- [ ] **Step 1: Run full unit suite**

Run: `python -m unittest discover -s tests -v`
Expected: full suite PASS.

- [ ] **Step 2: Run repository validation used by PR #205**

Use the existing `hq-validate` workflow/commands with no new workflow. Expected: schema, scope guard, and control-tower integrity PASS.

- [ ] **Step 3: Replay acceptance matrix**

Require exact outputs for all five historical loop actions plus normal product action. Acceptance: historical loop prevention coverage = `5/5`; normal product action = `ALLOW`.

- [ ] **Step 4: Record exact HEAD and evidence in PR #205**

Post only exact commit/run/test evidence and the platform-boundary statement. Do not merge or activate production.
