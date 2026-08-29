# Unified Archive Restore V1 — Design

Status: DUNCAN SANDBOX CANDIDATE
Date: 2026-08-29

## Goal
Make the existing Permanent Archive V1 usable as one durable memory source for restarted/new ZORR BLATT agents, without replacing immutable RAW history or adding an always-on service.

## Locks
- `zb-archive-v1` and `hq/archive-v1/raw` remain authoritative and immutable.
- SHERIFF policy/runtime is untouched.
- No merge or production activation in this sandbox task.
- Open-code reuse first; no proprietary service and no external Python package.

## Reuse choice
Use Python standard-library `sqlite3` with SQLite FTS5 as the searchable derived layer. The FTS index is rebuildable and non-authoritative; durable derived outputs stay UTF-8 JSON.

## Derived layout
`hq/archive-v1/derived/unified-v1/records/<prefix>/<raw_sha256>.json` stores one deterministic searchable record per archived RAW event.

Schema `ZB_UNIFIED_ARCHIVE_RECORD_V1` fields: `schema`, `raw_sha256`, `event_name`, `action`, `repository`, `actor`, `subject_kind`, `subject_number`, `subject_title`, `body_text`, `search_text`, `source_url`, `attachment_urls`.

`hq/archive-v1/derived/unified-v1/CURRENT_CONTEXT.json` is the single known broad restore entrypoint. Schema `ZB_UNIFIED_CURRENT_CONTEXT_V1`; it contains a bounded deterministic set of newest records with exact RAW SHA-256 pointers. It never outranks RAW evidence or exact current task/PR/tracker evidence.

## CLI
Create `scripts/hq_unified_archive.py` with commands/functions to:
1. derive a normalized record from one GitHub event;
2. write it idempotently by RAW SHA-256;
3. rebuild `CURRENT_CONTEXT.json` deterministically;
4. build an in-memory SQLite FTS5 index from record files;
5. search and return evidence-bound matches;
6. fail closed if FTS5 is unavailable or derived bytes collide.

## Workflow
Extend `.github/workflows/zb-permanent-archive-v1.yml` after RAW ingestion to run the unified derived ingest, then keep existing full archive verification and Git-native append behavior.

## Bootstrap
Update `AGENTS.md` so broad project/history restoration reads `zb-archive-v1:hq/archive-v1/derived/unified-v1/CURRENT_CONTEXT.json` before falling back to chat/session memory. Exact task evidence still has priority.

## Attachment policy
V1 extracts attachment URLs from archived body/Markdown as durable evidence metadata. It does not claim binary mirroring yet.

## Acceptance
TDD must prove: deterministic record derivation, idempotence, FTS5 retrieval, deterministic CURRENT_CONTEXT, RAW SHA binding, attachment URL extraction, existing archive tests green, full unittest suite green, `scripts/hq_validate.py` green, and fresh exact-HEAD GitHub read-back.

`UNIFIED_ARCHIVE_RESTORE_V1 = PASS` means the sandbox candidate satisfies all acceptance checks. It does not mean merged or production-active.
