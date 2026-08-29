# HQ Durable Archive MVP R01 — Design

STATUS = OWNER APPROVED FOR CONTINUOUS IMPLEMENTATION
SOURCE = issue #144 + OWNER priority override comment 5460450234
BASE = a83621eba5a33feae85960bf95489e8bac8ed711

## Goal

Build a permanent accumulating project archive whose primary invariant is **no information loss across chat/session boundaries**.

`CHAT != MEMORY`

`RAW / ORIGINAL EVIDENCE > APPEND-ONLY HISTORY > CURRENT SNAPSHOT > INDEX > SUMMARY`

## Hard priority

`NO_INFORMATION_LOSS = PASS` is the first hard gate.

If search is fast but raw/history can be lost, MVP = FAIL.
If raw/history is preserved and search is basic, MVP may proceed.

## Architecture

Create a sibling Python package `hq-memory/` so archive semantics do not alter `zb_local_controller` or production automation behavior.

Use ready/open components only:
- Python 3.12+
- Pydantic v2 for strict data models + JSON Schema export
- stdlib `sqlite3` + SQLite FTS5 for rebuildable lexical index
- filesystem content-addressed RAW store using SHA-256
- immutable JSON records for append-only history
- pytest for behavioral proof

No custom database, no custom search engine, no vector server, no Qdrant/Tantivy/sqlite-vec in MVP.

## Source-of-truth layout

```text
hq-memory/runtime/
  raw/sha256/<first2>/<sha256>.bin
  records/<record_type>/<record_id>.json
  index/hq-memory.sqlite3        # rebuildable derivative; never sole truth
```

The runtime root is configurable; tests use temporary directories. Production repository content is not auto-written by tests.

## Durable records

Minimum Pydantic record kinds:
- `EntityProfile`
- `TrainingProfile`
- `ProgressEvent`
- `DecisionRecord`
- `ArtifactRecord`
- `SourceRecord`

Every durable record has:
- stable `record_id`
- `record_type`
- `entity_id` / subject binding when applicable
- `status`: `LOCKED | OPEN | QUARANTINE | DROP | SUPERSEDED`
- source/provenance object
- UTC `created_at`
- optional `supersedes`
- human-searchable `text`

Provenance minimum:
- `source_id`
- `source_type`: `OWNER_DIRECT | OWNER_CORRECTION | SOURCE_QUOTE | ASSISTANT_INFERENCE | ASSISTANT_GENERATED | TEST_RESULT | QC_RESULT`
- `source_location`
- `source_hash`
- `authority`
- `created_at`

## Persistence laws

### RAW
`ingest_raw(bytes)` computes SHA-256 and writes exactly one content-addressed file. Existing matching bytes are idempotent. Existing path with different bytes is a fatal collision.

### Append-only history
`append_record(record)` writes a canonical JSON record exactly once.
- same ID + same canonical bytes => idempotent
- same ID + changed bytes => `RECORD_ID_COLLISION`
- no in-place record mutation

### Supersession
A newer record may reference an older `record_id` through `supersedes`. The older record remains present forever. Current snapshot derives effective records; it never deletes history.

### Snapshot rebuild
`build_current_snapshot()` reads immutable records, validates them, applies supersession, and returns current effective records. Deleting the SQLite index must not destroy the ability to rebuild current state.

## Search

SQLite is a derivative index. `rebuild_index()` drops/recreates index data from immutable record files.

Search order for MVP:
1. exact record/entity ID
2. exact/alias-capable fields where present
3. FTS5 lexical search
4. status filter
5. deterministic ranking with `LOCKED` above `OPEN`, then `QUARANTINE`, `SUPERSEDED`, `DROP`

No semantic/vector layer in R01.

## Context packet

`build_context_packet(entity_id)` returns only a bounded current packet:
- current records
- latest progress events
- locked rules
- known failures
- open items
- source pointers

It must not return the entire chat/history dump.

## Fail closed

Any unreadable/invalid durable record, hash mismatch, changed body under an existing ID, or missing required provenance must raise an explicit archive error. Never acknowledge persistence when durable bytes are not proven.

## Vertical acceptance scenarios

A. Persist a learned rule, recreate the store/process, rebuild index, and recover it through context.

B. Persist `X = old`, then OWNER correction `X = new` with `supersedes`. Current = new, old remains readable as SUPERSEDED/history.

C. Preserve a contradictory old RAW source. Search can find its record; current LOCKED state does not silently change.

D. Query an entity with proven fields + OPEN items. Context/search returns only stored facts; it does not autofill unknown values.

## Scope locks

- No new agents.
- No modification of existing controller/SALVADOR semantics.
- No canon promotion by model inference.
- No automatic `CANDIDATE -> LOCKED`.
- No deletion/rewrite of historical truth.
- No semantic search until persistence/FTS vertical slice passes.
- No merge without fresh CI and independent DUNCAN QC exact HEAD.
