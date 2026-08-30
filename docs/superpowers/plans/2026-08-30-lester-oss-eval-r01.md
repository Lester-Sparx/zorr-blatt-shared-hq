# LESTER OSS Eval R01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove existing LESTER can feed objective Inspect AI evaluation evidence into the existing SHERIFF evidence contract with minimal ZORR glue.

**Architecture:** Keep LESTER, SHERIFF, Permanent Archive, and DUNCAN Fortress unchanged. Pin Inspect AI to one exact MIT-licensed Git commit, run one deterministic upstream smoke in GitHub Actions, then map only the upstream PASS evidence into the existing SHERIFF event schema.

**Tech Stack:** Existing ZORR Python/JSON/unittest/GitHub Actions + Inspect AI pinned Git source.

**Spec:** `docs/superpowers/specs/2026-08-30-lester-oss-eval-r01-design.md`

## Global Constraints

- Tracker = #216.
- Base main = `b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1`.
- Branch = `duncan/lester-oss-eval-r01`.
- Main remains unchanged; no merge in this task.
- No custom scorer, competence reducer, training framework, agent framework, scheduler, DB, queue, or archive.
- One PASS cannot become PROVEN; changed/unseen transfer remains mandatory.

---

### Task 1: Durable upstream contract

**Files:**
- Create: `config/training/LESTER_OSS_EVAL_R01.json`
- Create: `tests/test_lester_oss_eval_r01.py`

**Interfaces:**
- Produces exact upstream repo/ref/license plus promotion and SHERIFF boundary metadata.

- [ ] Add a failing unittest that requires the exact Inspect pin, `historicalBackfill=false`, `singlePassState=PARTIAL_ONLY`, `transferRequired=true`, and existing SHERIFF schema reference.
- [ ] Add the minimal JSON contract.
- [ ] Run the focused test and require PASS.

### Task 2: Real upstream smoke + minimal bridge

**Files:**
- Create: `scripts/lester_oss_eval_r01.py`
- Create: `.github/workflows/lester-oss-eval-r01.yml`
- Modify: `tests/test_lester_oss_eval_r01.py`

**Interfaces:**
- `build_sheriff_result_event(...) -> dict[str, object]`
- CLI runs a real Inspect task using `mockllm/model`, requires Inspect `CORRECT`, writes `sheriff-event.json`, and prints the event.

- [ ] Test the event builder with no Inspect dependency installed and require `PARTIAL_ONLY`, no historical backfill, transfer required, exact candidate/ref bindings.
- [ ] Implement the bridge with lazy Inspect imports and no local scoring algorithm.
- [ ] Add a PR workflow that installs Inspect AI from exact Git ref and `jsonschema==4.25.1`, runs the smoke, then validates `sheriff-event.json` against the existing SHERIFF schema.
- [ ] Run through GitHub PR CI and require both standard validation and dedicated Inspect smoke green.

### Task 3: Exact-head final verification

**Files:**
- Create: `docs/LESTER_OSS_EVAL_R01.md`

**Interfaces:**
- Operator record documents upstream source, evidence semantics, and the no-PROVEN-without-transfer rule.

- [ ] Fresh-read candidate HEAD and changed files.
- [ ] Fresh-read all workflow runs for exact candidate HEAD; require standard and dedicated jobs SUCCESS.
- [ ] Fresh-read current main; require it still equals base main.
- [ ] Fresh-read Constitution again.
- [ ] Persist #216 terminal evidence with exact HEAD/run IDs and `MERGED=NO`.
