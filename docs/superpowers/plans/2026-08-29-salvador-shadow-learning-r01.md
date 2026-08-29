# SALVADOR SHADOW LEARNING R01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add a read-only SALVADOR shadow-learning vertical slice with versioned measurements, append-only progress evidence, reconstructible skill state, failure learning, and search.

**Architecture:** Reuse the already-built `hq-memory/archive-mvp-r01` implementation at exact `1cfde222ce9c688296c16676b9c1b3d143e5f481`. Do not build a second database, archive, reducer, context system, or search service. Extend only the existing generic contracts where SALVADOR needs structured fields, then add one thin `salvador_shadow.py` adapter/reducer and focused pytest scenarios.

**Tech Stack:** Existing Python 3.12 + Pydantic 2 + `ArchiveStore` + SQLite/FTS5 `SearchIndex` + pytest.

**Spec:** `docs/superpowers/specs/2026-08-29-salvador-shadow-learning-r01-design.md`

## Global Constraints

- `SHADOW LEARNING != LIVE SELF-MODIFICATION`.
- No writes to production controller/config/prompt/model/workflow/canon/QC/source/result bytes.
- RAW/history append-only and immutable.
- Skill states: `UNTESTED / FAILED / PARTIAL / PROVEN / LOCKED`; no fake global percentage.
- `LOCKED` never self-awarded.
- Hard-lock failure always remains FAIL regardless of aggregate metrics.
- Reuse existing HQ Memory archive/snapshot/search code; custom code is only glue.
- No merge to `main`, no production activation.

### Task 1 — RED vertical scenarios

Create `hq-memory/tests/test_salvador_shadow.py` first. Cover: FAIL can create learning while capability stays FAILED; PASS can advance PARTIAL→PROVEN only with independent evidence; LOCKED cannot be self-awarded; owner correction supersedes prior interpretation; hard-lock failure cannot be rescued by good aggregate metrics; snapshot rebuild/context restore is deterministic; records remain searchable through existing `SearchIndex`.

Run `python -m pytest hq-memory/tests/test_salvador_shadow.py -q` and require RED because SALVADOR adapter/API does not yet exist.

### Task 2 — Minimal reusable implementation

Modify `hq-memory/src/zb_hq_memory/models.py` only if needed for optional structured SALVADOR fields while keeping existing records backward-compatible. Add `hq-memory/src/zb_hq_memory/salvador_shadow.py` as a thin adapter around existing `ProgressEvent`, `ArchiveStore`, `build_current_snapshot`, and `SearchIndex`. Export the public API from `__init__.py`.

No new persistence engine, no new index, no second archive.

### Task 3 — GREEN + regression

Run the focused test until GREEN. Then run full `python -m pytest hq-memory/tests -q` and `python -m compileall -q hq-memory/src`. Open/update a draft PR against `hq-memory/archive-mvp-r01` and require GitHub Actions `hq-memory-test` PASS on the exact implementation HEAD.

### Task 4 — Fresh QC

Fresh-read exact PR HEAD, changed-file scope, CI run/jobs/logs, and diff. Confirm no production/config/canon/workflow mutation. Persist `DUNCAN3_IMPLEMENTATION_QC` with exact HEAD and evidence. Only then may `IMPLEMENTATION_PASS = YES` be claimed.