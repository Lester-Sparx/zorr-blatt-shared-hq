# HQ Durable Archive MVP R01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove a persistent, append-only, provenance-bound archive that survives session/process restart and can rebuild snapshot/search/context without losing source/history.

**Architecture:** A sibling `hq-memory` package owns archive persistence. Immutable RAW and immutable canonical JSON records are source truth; SQLite/FTS5 is disposable and rebuilt from records. Pydantic validates durable contracts. Existing controller code is untouched.

**Tech Stack:** Python 3.12+, Pydantic v2, stdlib sqlite3/FTS5, pathlib/hashlib/json, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-29-hq-memory-archive-mvp-r01-design.md`

## Global Constraints

- `NO_INFORMATION_LOSS = PASS` is the first hard gate.
- RAW and record history are immutable/append-only.
- SQLite is rebuildable derivative state, never sole truth.
- No semantic/vector layer in R01.
- No new agents.
- No changes under `agent-controller/src/zb_local_controller/`.
- No automatic canon/LOCK promotion.
- No merge before fresh CI + DUNCAN exact-head QC.

---

### Task 1: Package scaffold + vertical RED proof

**Files:**
- Create: `hq-memory/pyproject.toml`
- Create: `hq-memory/tests/test_vertical_archive.py`
- Create: `.github/workflows/hq-memory-test.yml`

**Interfaces:**
- Tests will import `zb_hq_memory.archive.ArchiveStore`, `zb_hq_memory.models.*`, `zb_hq_memory.context.build_context_packet`.
- No production package exists yet; first CI must fail for the intended missing-package reason.

- [ ] **Step 1: Add package/test dependency config**

`hq-memory/pyproject.toml` declares Python `>=3.12`, `pydantic>=2.8,<3`, and test extra `pytest>=8`.

- [ ] **Step 2: Add four acceptance tests**

`test_vertical_archive.py` must cover:
1. learned rule survives new `ArchiveStore` instance + index rebuild + context packet;
2. OWNER correction supersedes old record while both immutable files remain;
3. contradictory historical RAW/record remains searchable without replacing current LOCKED record;
4. unknown field is not invented/autofilled by context output.

- [ ] **Step 3: Add isolated CI workflow**

Run on pull request when `hq-memory/**` or this workflow changes:

```yaml
- uses: actions/setup-python@v5
  with: { python-version: '3.12' }
- run: python -m pip install -e './hq-memory[test]'
- run: python -m pytest hq-memory/tests -q
```

- [ ] **Step 4: Open draft PR and verify RED**

Expected: pytest collection/import failure because `zb_hq_memory` production package does not yet exist. Record run ID and failure reason in issue #144/PR.

---

### Task 2: Strict Pydantic durable contracts

**Files:**
- Create: `hq-memory/src/zb_hq_memory/__init__.py`
- Create: `hq-memory/src/zb_hq_memory/models.py`
- Create: `hq-memory/tests/test_models.py`

**Interfaces:**
- Produce `RecordStatus`, `SourceType`, `Provenance`, `EntityProfile`, `TrainingProfile`, `ProgressEvent`, `DecisionRecord`, `ArtifactRecord`, `SourceRecord`, and `parse_record(payload)`.
- Every model serializes deterministically using `model_dump(mode='json', exclude_none=True)` followed by canonical sorted JSON in the store.

- [ ] **Step 1: Write model validation tests**

Tests require UTC-aware timestamps, SHA-256 hex source hash, non-empty IDs/text, valid status/source type, and discriminator-based record parsing.

- [ ] **Step 2: Run focused tests and verify RED**

`python -m pytest hq-memory/tests/test_models.py -q`

Expected: missing models/imports.

- [ ] **Step 3: Implement minimal strict models**

Use Pydantic `BaseModel`, `ConfigDict(extra='forbid', frozen=True)`, `Field`, validators, and `Literal` record type discriminators. No ORM/custom validation framework.

- [ ] **Step 4: Run focused tests GREEN**

`python -m pytest hq-memory/tests/test_models.py -q`

---

### Task 3: Immutable RAW + append-only record store

**Files:**
- Create: `hq-memory/src/zb_hq_memory/archive.py`
- Create: `hq-memory/tests/test_archive_store.py`

**Interfaces:**

```python
class ArchiveStore:
    def __init__(self, root: Path): ...
    def ingest_raw(self, data: bytes) -> RawObject: ...
    def append_record(self, record: DurableRecord) -> Path: ...
    def iter_records(self) -> tuple[DurableRecord, ...]: ...
    def get_record(self, record_id: str) -> DurableRecord: ...
```

`RawObject` exposes `sha256`, `path`, `size`.

- [ ] **Step 1: Write RAW/history tests**

Require:
- content-addressed SHA-256 path;
- idempotent same bytes;
- collision detection if expected content-addressed path contains wrong bytes;
- same record ID + same canonical bytes idempotent;
- same record ID + changed bytes raises `RECORD_ID_COLLISION`;
- iteration revalidates every record rather than trusting filenames.

- [ ] **Step 2: Verify RED**

`python -m pytest hq-memory/tests/test_archive_store.py -q`

- [ ] **Step 3: Implement minimal store**

Use `hashlib.sha256`, `Path.mkdir`, exclusive `open('xb')` where possible, temporary sibling files + `os.replace` for atomic publication, canonical UTF-8 JSON, and explicit `ArchiveIntegrityError` codes.

- [ ] **Step 4: Verify GREEN**

`python -m pytest hq-memory/tests/test_archive_store.py -q`

---

### Task 4: Deterministic current snapshot + supersession

**Files:**
- Create: `hq-memory/src/zb_hq_memory/snapshot.py`
- Create: `hq-memory/tests/test_snapshot.py`

**Interfaces:**

```python
def build_current_snapshot(records: Iterable[DurableRecord]) -> CurrentSnapshot: ...
```

`CurrentSnapshot.records` contains effective non-superseded records; `history` remains available from ArchiveStore.

- [ ] **Step 1: Write supersession tests**

Require:
- OWNER correction references old `record_id` via `supersedes`;
- current returns new record;
- old file remains and can be loaded;
- missing superseded target fails closed;
- duplicate/conflicting supersession fails closed;
- status alone cannot silently delete history.

- [ ] **Step 2: Verify RED**

`python -m pytest hq-memory/tests/test_snapshot.py -q`

- [ ] **Step 3: Implement reduction**

Build ID map, validate edges, detect missing/duplicate supersession targets, mark old record logically superseded in projection only, preserve immutable stored record bytes.

- [ ] **Step 4: Verify GREEN**

`python -m pytest hq-memory/tests/test_snapshot.py -q`

---

### Task 5: Rebuildable SQLite FTS5 index + status-aware search

**Files:**
- Create: `hq-memory/src/zb_hq_memory/index.py`
- Create: `hq-memory/tests/test_search.py`

**Interfaces:**

```python
class SearchIndex:
    def __init__(self, db_path: Path): ...
    def rebuild(self, records: Iterable[DurableRecord]) -> None: ...
    def search(self, query: str, *, statuses: set[RecordStatus] | None = None) -> tuple[SearchHit, ...]: ...
```

- [ ] **Step 1: Write FTS/rebuild tests**

Require:
- SQLite DB can be deleted then rebuilt from immutable records;
- exact record/entity ID match wins;
- FTS5 phrase/prefix lexical search works;
- default status rank `LOCKED > OPEN > QUARANTINE > SUPERSEDED > DROP`;
- explicitly requesting historical status returns historical hit;
- contradictory historical record never becomes current merely because FTS score is high.

- [ ] **Step 2: Verify RED**

`python -m pytest hq-memory/tests/test_search.py -q`

- [ ] **Step 3: Implement SQLite/FTS5**

Use stdlib `sqlite3`; create normal metadata table plus FTS5 virtual table. `rebuild()` starts a transaction, clears derivative rows, and repopulates from validated records.

- [ ] **Step 4: Verify GREEN**

`python -m pytest hq-memory/tests/test_search.py -q`

---

### Task 6: Bounded cross-session context packet + final vertical proof

**Files:**
- Create: `hq-memory/src/zb_hq_memory/context.py`
- Create: `hq-memory/tests/test_context.py`
- Modify: `hq-memory/tests/test_vertical_archive.py`
- Create: `hq-memory/README.md`

**Interfaces:**

```python
def build_context_packet(store: ArchiveStore, entity_id: str) -> ContextPacket: ...
```

Packet contains current proven records, latest progress, known failures/open records, and provenance pointers. No field generation or LLM inference.

- [ ] **Step 1: Write context tests**

Require packet to survive a brand-new store/index object, exclude superseded current values by default, retain provenance pointers, include explicit OPEN items, and never create unknown fields.

- [ ] **Step 2: Verify RED**

`python -m pytest hq-memory/tests/test_context.py -q`

- [ ] **Step 3: Implement minimal context compiler**

Read durable records from store, build current snapshot, select matching entity records, order deterministically, return Pydantic packet.

- [ ] **Step 4: Full verification**

Run fresh on exact HEAD:

```bash
python -m pytest hq-memory/tests -q
python -m compileall -q hq-memory/src
```

Then require PR CI: `hq-memory-test = SUCCESS` plus existing `hq-validate`/scope checks unaffected.

- [ ] **Step 5: DUNCAN handoff**

Record exact HEAD, changed files, test count/output, compile result, `NO_INFORMATION_LOSS` vertical scenarios A-D, scope integrity, and request independent DUNCAN QC. Do not merge before DUNCAN PASS.
