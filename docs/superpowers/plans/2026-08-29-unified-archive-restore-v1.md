# Unified Archive Restore V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use Superpowers TDD. This session executes inline because no subagent execution surface is available.

**Goal:** Add one deterministic open-source search/restore layer over Permanent Archive V1.

**Architecture:** Preserve immutable RAW GitHub events unchanged. Derive JSON records keyed by RAW SHA-256, rebuild a bounded `CURRENT_CONTEXT.json`, and use Python `sqlite3` + SQLite FTS5 ephemerally for retrieval.

**Tech Stack:** Python 3 standard library, SQLite FTS5, GitHub Actions, existing archive workflow.

**Spec:** `docs/superpowers/specs/2026-08-29-unified-archive-restore-v1-design.md`

## Global Constraints
- Work only on `duncan/sandbox`.
- Do not merge or activate production.
- Do not change SHERIFF runtime/policy.
- No external Python packages or new service.
- RAW archive remains authoritative and immutable.

### Task 1: RED contract tests
**Files:** Create `tests/test_hq_unified_archive_v1.py`.

Test real behavior for: deterministic record fields and attachment extraction; idempotent write; deterministic `CURRENT_CONTEXT.json`; SQLite FTS5 retrieval returning RAW-bound evidence.

Run through existing `hq-validate` PR workflow. Expected RED: import/module missing.

### Task 2: Minimal GREEN implementation
**Files:** Create `scripts/hq_unified_archive.py`.

Interfaces:
- `derive_record(event_bytes: bytes, *, raw_sha256: str, event_name: str, repository: str, actor: str) -> dict`
- `write_record(record: dict, archive_root: Path) -> Path`
- `rebuild_current_context(archive_root: Path, *, limit: int = 50) -> dict`
- `search_records(archive_root: Path, query: str, *, limit: int = 10) -> list[dict]`

Implement only behavior required by Task 1 using standard library and FTS5.

### Task 3: Archive workflow integration
**Files:** Modify `.github/workflows/zb-permanent-archive-v1.yml`.

After RAW ingest, invoke `hq_unified_archive.py ingest-event` with `$GITHUB_EVENT_PATH`, archive root, and GitHub event metadata. Rebuild `CURRENT_CONTEXT.json` in the same command. Existing verification and archive commit ordering remain intact.

### Task 4: Bootstrap integration
**Files:** Modify `AGENTS.md`.

Add `CURRENT_CONTEXT.json` as the single broad restore entrypoint while keeping exact current tracker/PR/workflow evidence above derived state.

### Task 5: Fresh verification
On exact candidate HEAD require:
- focused unified archive tests PASS;
- existing `test_hq_archive_v1.py` PASS;
- full unittest suite PASS in `hq-validate`;
- `scripts/hq_validate.py` PASS;
- fresh GitHub read-back of all changed files;
- no main/production mutation.

Only then report `UNIFIED_ARCHIVE_RESTORE_V1 = PASS`.
