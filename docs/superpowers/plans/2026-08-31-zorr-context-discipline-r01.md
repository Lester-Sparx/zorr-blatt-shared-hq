# ZORR Context Discipline R01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce project-controlled context cost in long-running ZORR chats while preserving exact decision fidelity, OWNER authority, current HEAD/task bindings, verified lessons, contradiction handling, and recoverable RAW evidence.

**Architecture:** Extend the already-proven Unified Archive / verified-learning path instead of creating a second memory system. Add one narrow context-discipline module that projects unsuperseded current state, assembles a minimum evidence-complete JIT packet, creates derived handoffs, and renders delta-only OWNER output; integrate that packet into the existing pre-action gate and prove the behavior with long-chat negative/transfer fixtures plus byte-count benchmarks.

**Tech Stack:** Python standard library, existing `scripts/hq_unified_archive.py`, SQLite FTS5 already used by Unified Archive, existing `scripts/hq_pre_action.py`, `unittest`, existing GitHub/CI validation.

**Spec:** `docs/superpowers/specs/2026-08-31-zorr-context-discipline-r01-design.md`

## Global Constraints

- `CHAT = ACTIVE DELTA`.
- `CURRENT STATE = COMPACT UNSUPERSEDED VERIFIED PROJECTION`.
- `ARCHIVE = EXISTING FULL DURABLE HISTORY`.
- `RESTORE = MINIMUM EVIDENCE-COMPLETE JIT PACKET`.
- GitHub remains authority; chat and derived WARM state never become authority.
- Existing Permanent Archive V1 RAW history must remain immutable.
- Reuse order: existing ZORR -> native/standard -> mature OSS -> minimal glue.
- No second archive, vector DB, memory daemon/service, new model, or transcript summarizer authority.
- No universal fixed token limit or TOP-K acceptance law.
- Compaction may remove items from active restore but may not erase evidence/history.
- Old unsuperseded OWNER locks must survive compaction and be restored when relevant.
- Contradictory exclusive current facts fail closed with `DURABLE_CONTEXT_NOT_PROVEN`.
- `MERGE = NO` unless separately authorized.
- `CANON_CHANGE = NO`.
- Implementation MUST branch from the freshest legal base that already contains Unified Archive V1. At plan-writing time that is `duncan/sandbox` HEAD `28bca057b06eadff8759aa895d744d46266006a0` / PR #205; fresh-read it at execution time and stop rather than duplicating the subsystem if this has changed.
- The design PR #240 is documentation authority for this feature; implementation must not mutate #240 into a code PR.

---

## File Structure

**Create**
- `scripts/hq_context_discipline.py` — context classification, supersession projection, JIT packet assembly, handoff construction, owner-delta rendering, and benchmark CLI. It must call Unified Archive APIs rather than read/write a new archive format.
- `tests/test_hq_context_discipline_r01.py` — T1-T10 behavioral/negative/transfer acceptance suite.

**Modify**
- `scripts/hq_pre_action.py` — optional fail-closed consumption of a context packet before substantive action; preserve existing learning-policy behavior.
- `tests/test_hq_unified_archive_pre_action.py` — context-packet integration regressions.
- `AGENTS.md` — only after behavioral tests pass, document delta-only output, JIT restore, handoff, and derived-state precedence. Do not rewrite existing root/authority laws.

**Reuse without semantic replacement**
- `scripts/hq_unified_archive.py` — existing RAW-bound records, FTS5 `search_records`, `build_restore_packet`, verified lessons, optimized learning policy.
- Permanent Archive V1 workflow and RAW branch.

---

### Task 1: Establish the context-fact model and fail-closed supersession projection

**Files:**
- Create: `scripts/hq_context_discipline.py`
- Test: `tests/test_hq_context_discipline_r01.py`

**Interfaces:**
- Consumes: plain dictionaries representing project-controlled context facts.
- Produces:
  - `ContextDisciplineError(RuntimeError)`
  - `normalize_fact(fact: dict[str, Any]) -> dict[str, Any]`
  - `project_current_state(facts: list[dict[str, Any]], *, scope_tags: set[str] | None = None) -> dict[str, Any]`
  - packet schema constants `ZB_CONTEXT_FACT_V1`, `ZB_CONTEXT_CURRENT_STATE_V1`.

A valid fact shape is:

```python
{
    "schema": "ZB_CONTEXT_FACT_V1",
    "fact_id": "head-b",
    "class": "E2",
    "key": "ACTIVE_HEAD",
    "value": "bbbb",
    "exclusive": True,
    "verified": True,
    "authority": "GITHUB",
    "created_at": "2026-08-31T16:00:00Z",
    "scope_tags": ["LESTER", "SECURITY_R02"],
    "source_refs": ["github:pr:237"],
    "supersedes": ["head-a"],
}
```

E0 facts are never projected. E1 facts may remain while current. E2 facts may project when relevant. E3 facts project only as refs/pointers, not full raw payload. Exclusive keys may expose at most one unsuperseded current value.

- [ ] **Step 1: Write RED tests for ephemeral exclusion, supersession, OWNER-lock retention, and contradiction**

```python
from scripts.hq_context_discipline import ContextDisciplineError, project_current_state


def test_e0_never_enters_current_projection():
    state = project_current_state([
        {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": "progress-1",
            "class": "E0",
            "key": "PROGRESS",
            "value": "checking",
            "exclusive": False,
            "verified": False,
            "authority": "CHAT",
            "created_at": "2026-08-31T15:00:00Z",
            "scope_tags": ["LESTER"],
            "source_refs": [],
            "supersedes": [],
        }
    ])
    assert state["facts"] == []


def test_new_head_supersedes_old_head():
    facts = [
        fact("head-a", "E2", "ACTIVE_HEAD", "aaaa", exclusive=True, verified=True),
        fact("head-b", "E2", "ACTIVE_HEAD", "bbbb", exclusive=True, verified=True, supersedes=["head-a"]),
    ]
    state = project_current_state(facts)
    assert [(x["key"], x["value"]) for x in state["facts"]] == [("ACTIVE_HEAD", "bbbb")]


def test_old_unsuperseded_owner_lock_survives():
    facts = [
        fact("owner-lock-1", "E2", "OWNER_LOCK", "NO_OWNER_RELAY", exclusive=False, verified=True,
             authority="OWNER", created_at="2026-01-01T00:00:00Z"),
        fact("noise", "E0", "PROGRESS", "still checking", exclusive=False, verified=False),
    ]
    state = project_current_state(facts)
    assert any(x["fact_id"] == "owner-lock-1" for x in state["facts"])


def test_conflicting_unsuperseded_exclusive_values_fail_closed():
    facts = [
        fact("head-a", "E2", "ACTIVE_HEAD", "aaaa", exclusive=True, verified=True),
        fact("head-b", "E2", "ACTIVE_HEAD", "bbbb", exclusive=True, verified=True),
    ]
    with pytest.raises(ContextDisciplineError, match="DURABLE_CONTEXT_NOT_PROVEN:CONFLICT:ACTIVE_HEAD"):
        project_current_state(facts)
```

Use a local `fact(...)` helper in the test file to keep fixtures readable; do not add a production fixture builder.

- [ ] **Step 2: Run focused RED tests**

Run:

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

Expected: import failure because `scripts/hq_context_discipline.py` does not exist.

- [ ] **Step 3: Implement the minimal fact validator and supersession projection**

Start with:

```python
from __future__ import annotations

from collections import defaultdict
from typing import Any

FACT_SCHEMA = "ZB_CONTEXT_FACT_V1"
CURRENT_STATE_SCHEMA = "ZB_CONTEXT_CURRENT_STATE_V1"
CLASSES = {"E0", "E1", "E2", "E3"}


class ContextDisciplineError(RuntimeError):
    pass


def normalize_fact(fact: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fact, dict) or fact.get("schema") != FACT_SCHEMA:
        raise ContextDisciplineError("CONTEXT_FACT_INVALID")
    required = {
        "fact_id", "class", "key", "value", "exclusive", "verified",
        "authority", "created_at", "scope_tags", "source_refs", "supersedes",
    }
    missing = sorted(required - set(fact))
    if missing:
        raise ContextDisciplineError("CONTEXT_FACT_MISSING:" + ",".join(missing))
    if fact["class"] not in CLASSES:
        raise ContextDisciplineError("CONTEXT_FACT_CLASS_INVALID")
    if type(fact["exclusive"]) is not bool or type(fact["verified"]) is not bool:
        raise ContextDisciplineError("CONTEXT_FACT_BOOLEAN_INVALID")
    if not isinstance(fact["scope_tags"], list) or not all(isinstance(x, str) for x in fact["scope_tags"]):
        raise ContextDisciplineError("CONTEXT_FACT_SCOPE_INVALID")
    if not isinstance(fact["source_refs"], list) or not all(isinstance(x, str) for x in fact["source_refs"]):
        raise ContextDisciplineError("CONTEXT_FACT_SOURCE_INVALID")
    if not isinstance(fact["supersedes"], list) or not all(isinstance(x, str) for x in fact["supersedes"]):
        raise ContextDisciplineError("CONTEXT_FACT_SUPERSEDES_INVALID")
    return dict(fact)
```

`project_current_state` must:
1. validate all facts;
2. remove E0;
3. apply optional scope intersection while always retaining `authority == "OWNER"` facts whose key is relevant to the caller-provided scope;
4. remove any fact whose `fact_id` is named by another retained fact's `supersedes`;
5. group remaining exclusive facts by key and raise on more than one distinct value;
6. sort deterministically by `(key, created_at, fact_id)`;
7. return `{"schema": CURRENT_STATE_SCHEMA, "facts": [...]}`.

Do not infer supersession from recency alone. A newer timestamp is not authorization to silently supersede an older OWNER/canon/authority fact.

- [ ] **Step 4: Run focused tests GREEN**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

Expected: Task 1 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/hq_context_discipline.py tests/test_hq_context_discipline_r01.py
git commit -m "feat: add fail-closed context state projection"
```

---

### Task 2: Build the minimum evidence-complete JIT restore packet on top of Unified Archive

**Files:**
- Modify: `scripts/hq_context_discipline.py`
- Modify: `tests/test_hq_context_discipline_r01.py`

**Interfaces:**
- Consumes existing `scripts.hq_unified_archive.build_restore_packet` and `build_learning_policy`.
- Produces:
  - `build_context_packet(archive_root: Path, *, mandatory_anchors: list[dict[str, Any]], current_state: dict[str, Any], jit_queries: list[dict[str, str]]) -> dict[str, Any]`
  - schema `ZB_CONTEXT_PACKET_V1`.

Each JIT query is explicit and decision-facet keyed:

```python
{"facet": "STALE_HEAD_LESSON", "query": "stale head evidence substitution"}
```

There is no global TOP-K law. For each required facet, search begins narrow and expands deterministically only when no evidence is returned; missing required facets make the packet `NOT_PROVEN` rather than causing transcript flooding.

- [ ] **Step 1: Write RED tests for unrelated-history exclusion, required-facet retrieval, and missing-facet fail-closed**

```python
def test_jit_packet_excludes_unrelated_history(tmp_path):
    archive_root = build_archive_with_records(
        tmp_path,
        relevant="LYNCH screen geography continuity",
        unrelated="SHERIFF OCI digest pinning",
    )
    packet = build_context_packet(
        archive_root,
        mandatory_anchors=[anchor("CURRENT_TASK", "scene-17")],
        current_state=current_state_for("LYNCH"),
        jit_queries=[{"facet": "DIRECTING_LESSON", "query": "screen geography continuity"}],
    )
    text = json.dumps(packet, ensure_ascii=False)
    assert "screen geography" in text
    assert "OCI digest" not in text


def test_missing_required_jit_facet_is_not_proven(tmp_path):
    packet = build_context_packet(
        empty_archive(tmp_path),
        mandatory_anchors=[anchor("CURRENT_TASK", "scene-17")],
        current_state=current_state_for("LYNCH"),
        jit_queries=[{"facet": "DIRECTING_LESSON", "query": "screen geography continuity"}],
    )
    assert packet["status"] == "NOT_PROVEN"
    assert packet["missing_facets"] == ["DIRECTING_LESSON"]
```

Also add a test proving E3 content appears only as source/hash/url refs in the packet, not duplicated raw bytes.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

Expected: missing `build_context_packet`.

- [ ] **Step 3: Implement adaptive facet retrieval using existing archive APIs**

Use imports:

```python
try:
    from scripts.hq_unified_archive import build_learning_policy, build_restore_packet
except ModuleNotFoundError:
    from hq_unified_archive import build_learning_policy, build_restore_packet
```

Implementation rule:

```python
def _retrieve_facet(archive_root: Path, query: str) -> dict[str, Any] | None:
    for limit in (1, 2, 4, 8, 16):
        packet = build_restore_packet(archive_root, query, limit=limit)
        if packet.get("status") == "PROVEN" and packet.get("results"):
            return packet
    return None
```

The sequence above is an implementation search expansion, not a quality threshold. Acceptance must never depend on “TOP-16 is enough”; if a known required fact cannot be found, return `NOT_PROVEN`. If execution-time inspection shows the existing API can expose record count/exhaustion more directly, prefer that native exhaustion signal and remove the bounded sequence.

The context packet must include:
- mandatory anchors unchanged;
- the already-projected current state;
- one result set per requested facet;
- task-specific verified learning from `build_learning_policy` only when a lesson query is explicitly supplied;
- `source_refs` sufficient to expand to RAW later;
- `status`, `missing_facets`, and deterministic schema/version.

- [ ] **Step 4: GREEN + existing Unified Archive regression**

```bash
python -m unittest tests.test_hq_context_discipline_r01 tests.test_hq_unified_archive_v1 tests.test_hq_unified_archive_learning tests.test_hq_unified_archive_optimizer -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/hq_context_discipline.py tests/test_hq_context_discipline_r01.py
git commit -m "feat: add evidence-complete jit context packets"
```

---

### Task 3: Add delta-only OWNER-facing output without suppressing blockers or terminal evidence

**Files:**
- Modify: `scripts/hq_context_discipline.py`
- Modify: `tests/test_hq_context_discipline_r01.py`

**Interfaces:**
- Produces:
  - `diff_current_state(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]`
  - `render_owner_delta(delta: dict[str, Any], *, blocker: str | None, evidence: list[str], next_action: str | None) -> str`

- [ ] **Step 1: RED tests for no-delta and terminal evidence retention**

```python
def test_no_delta_does_not_repeat_settled_state():
    state = state_with("ACTIVE_HEAD", "bbbb")
    delta = diff_current_state(state, state)
    text = render_owner_delta(delta, blocker="WAITING_FOR_CI", evidence=[], next_action=None)
    assert text == "NO DELTA. BLOCKER = WAITING_FOR_CI"
    assert "bbbb" not in text


def test_terminal_delta_keeps_exact_evidence():
    previous = state_with("RESULT", "RUNNING")
    current = state_with("RESULT", "PASS")
    delta = diff_current_state(previous, current)
    text = render_owner_delta(
        delta,
        blocker=None,
        evidence=["run:33414957721", "head:556082d"],
        next_action="AUDIT_NEXT_GAP",
    )
    assert "DELTA:" in text
    assert "run:33414957721" in text
    assert "head:556082d" in text
    assert "NEXT: AUDIT_NEXT_GAP" in text
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

- [ ] **Step 3: Implement deterministic state diff + compact renderer**

The renderer must obey:
- no unchanged fact echo;
- `NO DELTA` when the current projection is semantically identical;
- evidence line omitted for routine non-terminal deltas when no evidence is required;
- terminal PASS/FAIL/BLOCKED evidence preserved exactly when supplied;
- never shorten/alter evidence IDs.

Return only these logical lines:

```text
DELTA: <changed key/value pairs>
EVIDENCE: <refs>        # only when non-empty
NEXT: <action>          # only when non-empty
```

or:

```text
NO DELTA. BLOCKER = <blocker>
```

- [ ] **Step 4: GREEN**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/hq_context_discipline.py tests/test_hq_context_discipline_r01.py
git commit -m "feat: add delta-only owner output"
```

---

### Task 4: Add derived handoff packets and cold-start validation

**Files:**
- Modify: `scripts/hq_context_discipline.py`
- Modify: `tests/test_hq_context_discipline_r01.py`

**Interfaces:**
- Produces:
  - `build_handoff(*, role_or_engine: str, current_goal: str, task_or_correlation: str, authoritative_main: str, current_state: dict[str, Any], open_gaps: list[str], lesson_refs: list[str], next_action: str, source_refs: list[str]) -> dict[str, Any]`
  - `validate_handoff(handoff: dict[str, Any]) -> dict[str, Any]`
  - schema `ZB_CONTEXT_HANDOFF_V1`.

The handoff is derived state only. It must carry source refs and explicitly set `authority = "DERIVED"`.

- [ ] **Step 1: RED tests for cold-start and stale handoff rejection**

```python
def test_handoff_contains_minimum_resume_state():
    handoff = build_handoff(
        role_or_engine="LESTER",
        current_goal="harden chat reasoning",
        task_or_correlation="#235",
        authoritative_main="b18ca6b",
        current_state=state_with("ACTIVE_HEAD", "556082d"),
        open_gaps=["ASSIGN_VS_EXECUTION"],
        lesson_refs=["verdict:SV1-LOOP-001"],
        next_action="REPRODUCE_NEXT_NEGATIVE",
        source_refs=["github:issue:235", "github:pr:237"],
    )
    assert handoff["authority"] == "DERIVED"
    assert handoff["next_action"] == "REPRODUCE_NEXT_NEGATIVE"
    assert handoff["source_refs"] == ["github:issue:235", "github:pr:237"]


def test_handoff_cannot_override_fresher_authority():
    handoff = build_handoff(... authoritative_main="old-main" ...)
    with pytest.raises(ContextDisciplineError, match="HANDOFF_STALE"):
        validate_handoff(handoff, fresh_authoritative_main="new-main")
```

Use `unittest` equivalents in the actual test file; snippets are behavioral targets.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

- [ ] **Step 3: Implement handoff builder/validator**

Required fields exactly mirror the spec:

```python
HANDOFF_FIELDS = {
    "role_or_engine",
    "current_goal",
    "task_or_correlation",
    "authoritative_main",
    "active_base",
    "active_head",
    "verified_current_state",
    "current_blocker_or_none",
    "open_gaps",
    "relevant_verified_lesson_refs",
    "next_action",
    "source_refs",
    "supersedes",
}
```

Do not persist chat transcript or chain-of-thought. Do not accept handoff authority over a fresh GitHub main/PR/workflow read.

- [ ] **Step 4: GREEN**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/hq_context_discipline.py tests/test_hq_context_discipline_r01.py
git commit -m "feat: add derived context handoffs"
```

---

### Task 5: Enforce context validity at the existing pre-action boundary

**Files:**
- Modify: `scripts/hq_pre_action.py`
- Modify: `tests/test_hq_unified_archive_pre_action.py`

**Interfaces:**
- Existing `evaluate_pre_action(context, *, learning_policy=None)` remains backward-compatible.
- Add optional keyword-only argument `context_packet: dict[str, Any] | None = None`.
- `_decision(...)` adds a compact `context` view only when a packet is provided.

- [ ] **Step 1: RED negative tests**

Add:

```python
def test_substantive_action_blocks_on_not_proven_context_packet(self):
    packet = {
        "schema": "ZB_CONTEXT_PACKET_V1",
        "status": "NOT_PROVEN",
        "missing_facets": ["CURRENT_HEAD"],
    }
    result = self._decide(self._context(), context_packet=packet)
    self.assertEqual((result["decision"], result["reason"]),
                     ("BLOCK", "DURABLE_CONTEXT_NOT_PROVEN"))


def test_proven_context_packet_preserves_existing_pre_action_decision(self):
    packet = {
        "schema": "ZB_CONTEXT_PACKET_V1",
        "status": "PROVEN",
        "missing_facets": [],
    }
    result = self._decide(self._context(), context_packet=packet)
    self.assertEqual((result["decision"], result["reason"]),
                     ("ALLOW", "PRE_ACTION_GATE_PASS"))
```

Also add one regression proving the existing learning view is unchanged when a context packet is supplied.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_hq_unified_archive_pre_action -v
```

Expected: `_decide`/`evaluate_pre_action` does not accept `context_packet` yet.

- [ ] **Step 3: Implement minimal integration**

Before existing action-specific checks:

```python
if context_packet is not None:
    if not isinstance(context_packet, dict) or context_packet.get("schema") != "ZB_CONTEXT_PACKET_V1":
        raise PreActionError("CONTEXT_PACKET_INVALID")
    if context_packet.get("status") != "PROVEN":
        return _decision(context, "BLOCK", "DURABLE_CONTEXT_NOT_PROVEN", learning_policy, context_packet)
```

Do not duplicate archive lookup inside `hq_pre_action.py`. Packet construction belongs to `hq_context_discipline.py`; pre-action only consumes the proven/not-proven result.

CLI integration:
- add optional `--context-packet-path`;
- parse JSON with the same fail-closed unreadable/invalid behavior;
- no new daemon/service.

- [ ] **Step 4: Run focused + regression tests**

```bash
python -m unittest tests.test_hq_unified_archive_pre_action tests.test_hq_context_discipline_r01 -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/hq_pre_action.py tests/test_hq_unified_archive_pre_action.py
git commit -m "feat: enforce proven context before substantive actions"
```

---

### Task 6: Implement the full T1-T10 behavioral acceptance suite and changed/unseen fixtures

**Files:**
- Modify: `tests/test_hq_context_discipline_r01.py`
- Modify: `scripts/hq_context_discipline.py` only if a test exposes a real missing behavior.

**Interfaces:**
- No new subsystem interfaces. This task proves the design behavior.

- [ ] **Step 1: Add T1 long-chat decision parity fixture**

Construct a deterministic history with at least:
- repeated progress E0 records;
- old/new HEAD pair with explicit supersession;
- one active blocker;
- one old still-valid OWNER lock;
- unrelated SALVADOR and SHERIFF records;
- one verified matching lesson;
- one unverified/open lesson analogue;
- RAW evidence pointers.

Define a small decision extractor used only by tests:

```python
def decision_signature(packet):
    return {
        "role": value(packet, "ROLE"),
        "task": value(packet, "CURRENT_TASK"),
        "head": value(packet, "ACTIVE_HEAD"),
        "blocker": value(packet, "CURRENT_BLOCKER"),
        "next": value(packet, "NEXT_ACTION"),
        "owner_lock": value(packet, "OWNER_LOCK"),
    }
```

Assert the compact packet produces the same signature as a carefully resolved full-history baseline.

- [ ] **Step 2: Add T2-T5 negatives**

Required tests:
- stale supersession rejection;
- contradictory exclusive current state -> `DURABLE_CONTEXT_NOT_PROVEN`;
- unrelated domain exclusion;
- old OWNER lock retained.

- [ ] **Step 3: Add T6 verified lesson transfer with an unseen case**

Use an old verified lesson about stale evidence, then query a changed task with a different task ID but the same error/domain signature. Assert the verified lesson is retrieved. Add an OPEN/unverified lesson fixture and assert it is absent.

- [ ] **Step 4: Add T7 evidence escalation**

Start with compact pointer-only evidence. Simulate a disputed terminal claim by making the test explicitly call the existing Unified Archive restore/raw expansion path. Assert the system expands the exact evidence ref rather than loading unrelated history.

- [ ] **Step 5: Add T8 no-delta repeated status case**

Run three identical projected states through `diff_current_state`. Assert the second and third owner outputs are `NO DELTA...` and do not contain repeated architecture/law text.

- [ ] **Step 6: Add T9 handoff cold-start case**

Use only:
- mandatory anchors;
- a derived handoff;
- JIT archive lookups.

Assert the fresh session recovers the same `decision_signature` without any copied transcript.

- [ ] **Step 7: Add T10 context reduction benchmark using UTF-8 bytes**

No tokenizer dependency is required in R01. Measure project-controlled serialized bytes:

```python
naive_bytes = len(json.dumps(full_history, sort_keys=True, ensure_ascii=False).encode("utf-8"))
packet_bytes = len(json.dumps(packet, sort_keys=True, ensure_ascii=False).encode("utf-8"))
ratio = naive_bytes / packet_bytes
self.assertGreater(naive_bytes, packet_bytes)
self.assertEqual(decision_signature(packet), decision_signature(full_baseline))
```

Do NOT hard-code a universal ratio such as `>= 5x`. The test requires a material reduction on this representative fixture (`packet_bytes < naive_bytes`) and separately proves decision parity/critical-fact recall/stale rejection. The exact measured ratio is reported as evidence, not as a global law.

- [ ] **Step 8: Run the full context suite twice for determinism**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
python -m unittest tests.test_hq_context_discipline_r01 -v
```

Expected: same results and deterministic packet serialization/order.

- [ ] **Step 9: Commit**

```bash
git add tests/test_hq_context_discipline_r01.py scripts/hq_context_discipline.py
git commit -m "test: prove context discipline behavioral acceptance"
```

---

### Task 7: Add a benchmark/report CLI without creating a new service

**Files:**
- Modify: `scripts/hq_context_discipline.py`
- Modify: `tests/test_hq_context_discipline_r01.py`

**Interfaces:**
- CLI modes:
  - `project`
  - `packet`
  - `handoff`
  - `delta`
  - `benchmark`
- Benchmark prints one JSON object using schema `ZB_CONTEXT_BENCHMARK_V1`.

- [ ] **Step 1: RED CLI benchmark test**

Use a temporary JSON fixture and subprocess call. Expected output:

```json
{
  "schema": "ZB_CONTEXT_BENCHMARK_V1",
  "naive_context_bytes": 12000,
  "compact_context_bytes": 2300,
  "compression_ratio": 5.2173913043,
  "decision_parity": true,
  "critical_fact_recall": true,
  "stale_fact_rejection": true
}
```

Numbers above are illustrative only; test exact values from its own deterministic fixture.

- [ ] **Step 2: Implement `argparse` CLI around the pure functions**

The CLI must not poll GitHub, open network connections, run as a daemon, or persist a second current-state database. It only transforms provided local evidence/archive inputs.

- [ ] **Step 3: GREEN**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

- [ ] **Step 4: Commit**

```bash
git add scripts/hq_context_discipline.py tests/test_hq_context_discipline_r01.py
git commit -m "feat: add context discipline benchmark cli"
```

---

### Task 8: Update agent restart/output law only after behavioral proof

**Files:**
- Modify: `AGENTS.md`
- Test: `tests/test_hq_context_discipline_r01.py`

**Interfaces:**
- Documentation contract only; no Constitution rewrite in R01.

- [ ] **Step 1: Add a RED documentation-contract test**

Read `AGENTS.md` and require exact concepts, not prose length:

```python
required = [
    "CHAT = ACTIVE DELTA",
    "CURRENT STATE = COMPACT UNSUPERSEDED VERIFIED PROJECTION",
    "RESTORE = MINIMUM EVIDENCE-COMPLETE JIT PACKET",
    "NO DELTA",
    "DURABLE_CONTEXT_NOT_PROVEN",
]
for text in required:
    self.assertIn(text, agents_text)
```

Also assert the existing precedence line `RAW ORIGINAL EVENT > VERIFIED GITHUB HISTORY` remains present.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

- [ ] **Step 3: Add one compact `Context Discipline R01` section to `AGENTS.md`**

Required content:

```text
CHAT = ACTIVE DELTA
CURRENT STATE = COMPACT UNSUPERSEDED VERIFIED PROJECTION
ARCHIVE = EXISTING FULL DURABLE HISTORY
RESTORE = MINIMUM EVIDENCE-COMPLETE JIT PACKET
```

And these laws:
- after established state, report only material deltas by default;
- if no state changed, use compact `NO DELTA` status rather than replaying settled context;
- do not load superseded facts into normal restore;
- do not drop still-valid OWNER authority because it is old;
- retrieve unrelated history only for an explicit dependency;
- derived handoff/current-state packets never override fresh exact GitHub evidence;
- contradiction/missing required evidence -> `DURABLE_CONTEXT_NOT_PROVEN`;
- terminal claims still carry exact evidence required by the Constitution.

Do not duplicate the whole spec in `AGENTS.md`.

- [ ] **Step 4: GREEN + AGENTS regression**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
python scripts/hq_validate.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add AGENTS.md tests/test_hq_context_discipline_r01.py
git commit -m "docs: add context discipline restart law"
```

---

### Task 9: Full regression, security/authority negative verification, and durable evidence

**Files:**
- No new production files unless a real regression is found.
- Update implementation PR body/comment and issue #235 only with exact results.

**Interfaces:**
- Produces candidate evidence only; no merge.

- [ ] **Step 1: Fresh-read execution base and ensure no duplicate subsystem was introduced**

Verify changed files contain no:
- second archive root;
- new DB/service/daemon;
- vector store;
- duplicated RAW history;
- Constitution authority weakening.

- [ ] **Step 2: Run focused suites**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
python -m unittest tests.test_hq_unified_archive_v1 -v
python -m unittest tests.test_hq_unified_archive_learning -v
python -m unittest tests.test_hq_unified_archive_optimizer -v
python -m unittest tests.test_hq_unified_archive_pre_action -v
```

- [ ] **Step 3: Run full repository tests and validator**

Use the repository's established full unittest command from current CI, then:

```bash
python scripts/hq_validate.py
```

Expected: all tests and validation PASS on exact candidate HEAD.

- [ ] **Step 4: Run CI on the isolated implementation PR**

Require fresh exact-head `hq-validate` success and any existing scope/control-tower/security checks triggered by the branch. Do not substitute old PR #205/#237 runs.

- [ ] **Step 5: Capture behavioral evidence**

Record:

```text
NAIVE_CONTEXT_BYTES = <measured>
R01_CONTEXT_BYTES = <measured>
COMPRESSION_RATIO = <measured>
DECISION_PARITY = PASS
CRITICAL_FACT_RECALL = PASS
STALE_FACT_REJECTION = PASS
CONTRADICTION_FAIL_CLOSED = PASS
OWNER_LOCK_RETENTION = PASS
VERIFIED_LESSON_TRANSFER = PASS
HANDOFF_COLD_START = PASS
NO_DELTA_DISCIPLINE = PASS
```

- [ ] **Step 6: Post one concise durable delta to issue #235**

Use:

```text
LESTER_CONTEXT_DISCIPLINE_DELTA
EXACT_HEAD = ...
PR = ...
BASE = ...
BEHAVIORAL_GATES = ...
CONTEXT_BYTES = naive -> compact
COMPRESSION_RATIO = ...
DECISION_PARITY = ...
RAW_ARCHIVE_MUTATION = NO
NEW_MEMORY_SYSTEM = NO
REGRESSIONS = NONE | exact list
RESULT = CANDIDATE_PASS_NOT_MERGED | FAIL
NEXT = independent review / exact blocker
```

- [ ] **Step 7: Fresh-read the posted delta and require exact match**

Do not claim `ZORR_CONTEXT_DISCIPLINE_R01 = PASS` merely because unit tests are green. The terminal claim requires fresh behavioral evidence from T1-T10 plus exact-head CI and durable readback.

- [ ] **Step 8: Do not merge**

Stop at a reviewable isolated candidate unless separately authorized.

---

## Plan Self-Review Result

- Spec coverage: all sections are covered by Tasks 1-9; T1-T10 are explicitly mapped in Task 6.
- Authority preservation: WARM/handoff remain derived; fresh GitHub evidence and existing RAW precedence remain superior.
- OWNER-lock preservation: explicit Task 1 and T6 tests.
- No fixed TOP-K/token law: packet retrieval is evidence-completeness driven; context benchmark uses measured bytes, not an invented global ratio.
- Reuse-first: implementation is required to start from the current Unified Archive base and call its restore/learning APIs.
- No parallel infrastructure: one narrow pure-Python glue module only; no service/daemon/vector DB/new archive.
- No placeholders: each implementation task has concrete files, functions, tests, commands, expected outcomes, and commit boundaries.
- Type/signature consistency: `project_current_state`, `build_context_packet`, `diff_current_state`, `render_owner_delta`, `build_handoff`, `validate_handoff`, and optional `context_packet` pre-action integration are stable across tasks.
