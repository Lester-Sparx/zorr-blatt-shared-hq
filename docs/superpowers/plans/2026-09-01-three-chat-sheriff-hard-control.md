# ZORR Three-Chat SHERIFF Hard Control R01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce the approved universal SHERIFF law across CHAT A/B/C through one shared studio law, existing bootstrap/orchestration bindings, and fail-closed CI validation.

**Architecture:** Reuse the existing ZORR Constitution, SHERIFF infrastructure, three-chat orchestration, and `hq-validate`. Add no new workflow, daemon, archive, router, or framework. A stdlib validator checks durable contract invariants; unit tests drive RED→GREEN.

**Tech Stack:** Python 3 stdlib, `unittest`, Markdown durable contracts, existing GitHub Actions `hq-validate`.

**Spec:** `docs/superpowers/specs/2026-09-01-three-chat-sheriff-hard-control-design.md`

## Global Constraints

- GitHub remains the durable source of truth.
- Do not modify `main` directly.
- Do not merge as part of this work.
- Do not perform image generation/editing or production asset mutation.
- Do not create a second SHERIFF control plane or workflow.
- Use TDD: tests must fail on the candidate before implementation.
- Preserve CHAT A=#249, CHAT B=#250, CHAT C=#251 and the current active-gate model.

---

### Task 1: RED contract tests

**Files:**
- Create: `tests/test_three_chat_sheriff_law.py`

**Interfaces:**
- Consumes: repository files under `studio/`.
- Produces: CLI expectations for `scripts/validate_three_chat_sheriff.py [ROOT]`.

- [ ] **Step 1: Write failing tests**

Tests must assert that the real candidate repository validates, that a fixture with `CURRENT HEAD = <40 hex>` is rejected with `CURRENT_HEAD_LITERAL_FORBIDDEN`, and that a fixture with a broken CHAT C/#251 binding is rejected with `CHAT_C_TRACKER_BINDING_MISSING`.

- [ ] **Step 2: Run RED in PR CI**

Run: existing `hq-validate` on the test-only candidate.

Expected: `hq-schema` FAIL because `scripts/validate_three_chat_sheriff.py` and the shared law/wiring do not yet exist. Confirm failure is from this new test, not unrelated repository breakage.

---

### Task 2: Shared law + validator GREEN

**Files:**
- Create: `studio/ZORR_SHERIFF_THREE_CHAT_LAW_R01.md`
- Create: `scripts/validate_three_chat_sheriff.py`
- Modify: `studio/ZORR_MASTER_CHAT_BOOTSTRAP_R01.md`
- Modify: `studio/ZORR_THREE_CHAT_ORCHESTRATION_R01.md`
- Modify: `.github/workflows/hq-validate.yml`

**Interfaces:**
- Consumes: durable Markdown contracts.
- Produces: `validate_repository(root: Path) -> None` and CLI exit status 0/1.

- [ ] **Step 1: Add the approved shared law**

Persist the A/B/C role boundaries, evidence laws, PASS-type separation, anti-loop rule, fresh-state rule, conflict/promotion rules, and durable write/readback rule.

- [ ] **Step 2: Implement minimal validator**

Validator checks: shared law exists; bootstrap and orchestration reference it; A/B/C tracker bindings remain exact; required SHERIFF invariant tokens remain present; `CURRENT ... HEAD = <40hex>` is forbidden in the three durable contract files.

- [ ] **Step 3: Wire existing contracts**

Add shared-law fresh-read to master bootstrap and orchestration. Do not add static current SHA values.

- [ ] **Step 4: Wire existing CI**

Add `python3 scripts/validate_three_chat_sheriff.py` to `hq-schema` in `.github/workflows/hq-validate.yml` before the full unittest suite.

- [ ] **Step 5: Run GREEN**

Expected: exact candidate HEAD has `hq-validate` SUCCESS with all three jobs SUCCESS and all unittests green.

---

### Task 3: Fresh readback + durable result

**Files:**
- No production files beyond Task 2.

**Interfaces:**
- Consumes: exact PR HEAD and workflow run.
- Produces: evidence-bound RESULT / DELTA / EVIDENCE / NEXT checkpoint.

- [ ] **Step 1: Fresh-read exact PR HEAD**

Verify the five changed enforcement surfaces match the candidate.

- [ ] **Step 2: Verify workflow binding**

Confirm `hq-validate` run belongs to exact candidate HEAD and all jobs passed.

- [ ] **Step 3: Persist checkpoint**

Record test-first RED evidence, GREEN run ID, exact HEAD, changed files, and next legal gate. Do not claim merge/production activation.
