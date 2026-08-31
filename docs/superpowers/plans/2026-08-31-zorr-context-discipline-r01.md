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
- The design PR #240 is documentation authority for this feature; implementation must use a separate isolated branch/PR.

---

## File Structure

**Create**
- `scripts/hq_context_discipline.py` — context classification, supersession projection, JIT packet assembly, handoff construction, OWNER delta rendering, benchmark CLI.
- `tests/test_hq_context_discipline_r01.py` — T1-T10 behavioral/negative/transfer acceptance suite.

**Modify**
- `scripts/hq_pre_action.py` — optional fail-closed consumption of a context packet before substantive action; preserve existing learning-policy behavior.
- `tests/test_hq_unified_archive_pre_action.py` — context-packet integration regressions.
- `AGENTS.md` — only after behavioral proof, add the compact restart/output contract; do not rewrite existing root/authority laws.

**Reuse unchanged as authority/data layer**
- `scripts/hq_unified_archive.py` — RAW-bound records, FTS5 `search_records`, `build_restore_packet`, verified lessons, optimized learning policy.
- Permanent Archive V1 workflow and RAW branch.

---

### Task 1: Context fact model and fail-closed supersession projection

**Files:**
- Create: `scripts/hq_context_discipline.py`
- Create: `tests/test_hq_context_discipline_r01.py`

**Interfaces:**
- `ContextDisciplineError(RuntimeError)`
- `normalize_fact(fact: dict[str, Any]) -> dict[str, Any]`
- `project_current_state(facts: list[dict[str, Any]], *, scope_tags: set[str] | None = None) -> dict[str, Any]`
- schemas `ZB_CONTEXT_FACT_V1` and `ZB_CONTEXT_CURRENT_STATE_V1`.

A context fact is exactly:

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

- [ ] **Step 1: Write the shared test helper and RED tests**

Start `tests/test_hq_context_discipline_r01.py` with:

```python
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest


class ContextDisciplineR01Tests(unittest.TestCase):
    @staticmethod
    def fact(
        fact_id: str,
        class_: str,
        key: str,
        value: str,
        *,
        exclusive: bool,
        verified: bool,
        authority: str = "GITHUB",
        created_at: str = "2026-08-31T16:00:00Z",
        scope_tags: list[str] | None = None,
        source_refs: list[str] | None = None,
        supersedes: list[str] | None = None,
    ) -> dict[str, object]:
        return {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": fact_id,
            "class": class_,
            "key": key,
            "value": value,
            "exclusive": exclusive,
            "verified": verified,
            "authority": authority,
            "created_at": created_at,
            "scope_tags": list(scope_tags or ["LESTER"]),
            "source_refs": list(source_refs or []),
            "supersedes": list(supersedes or []),
        }

    def test_e0_never_enters_current_projection(self) -> None:
        from scripts.hq_context_discipline import project_current_state
        state = project_current_state([
            self.fact("progress-1", "E0", "PROGRESS", "checking", exclusive=False, verified=False)
        ])
        self.assertEqual(state["facts"], [])

    def test_new_head_supersedes_old_head(self) -> None:
        from scripts.hq_context_discipline import project_current_state
        facts = [
            self.fact("head-a", "E2", "ACTIVE_HEAD", "aaaa", exclusive=True, verified=True),
            self.fact("head-b", "E2", "ACTIVE_HEAD", "bbbb", exclusive=True, verified=True,
                      supersedes=["head-a"]),
        ]
        state = project_current_state(facts)
        self.assertEqual([(x["key"], x["value"]) for x in state["facts"]], [("ACTIVE_HEAD", "bbbb")])

    def test_old_unsuperseded_owner_lock_survives(self) -> None:
        from scripts.hq_context_discipline import project_current_state
        facts = [
            self.fact("owner-lock-1", "E2", "OWNER_LOCK", "NO_OWNER_RELAY",
                      exclusive=False, verified=True, authority="OWNER",
                      created_at="2026-01-01T00:00:00Z"),
            self.fact("noise", "E0", "PROGRESS", "still checking", exclusive=False, verified=False),
        ]
        state = project_current_state(facts)
        self.assertTrue(any(x["fact_id"] == "owner-lock-1" for x in state["facts"]))

    def test_conflicting_unsuperseded_exclusive_values_fail_closed(self) -> None:
        from scripts.hq_context_discipline import ContextDisciplineError, project_current_state
        facts = [
            self.fact("head-a", "E2", "ACTIVE_HEAD", "aaaa", exclusive=True, verified=True),
            self.fact("head-b", "E2", "ACTIVE_HEAD", "bbbb", exclusive=True, verified=True),
        ]
        with self.assertRaisesRegex(ContextDisciplineError,
                                    "DURABLE_CONTEXT_NOT_PROVEN:CONFLICT:ACTIVE_HEAD"):
            project_current_state(facts)
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

Expected: import failure because `scripts/hq_context_discipline.py` does not exist.

- [ ] **Step 3: Implement minimal validation/projection**

Start `scripts/hq_context_discipline.py` with:

```python
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

FACT_SCHEMA = "ZB_CONTEXT_FACT_V1"
CURRENT_STATE_SCHEMA = "ZB_CONTEXT_CURRENT_STATE_V1"
CONTEXT_PACKET_SCHEMA = "ZB_CONTEXT_PACKET_V1"
HANDOFF_SCHEMA = "ZB_CONTEXT_HANDOFF_V1"
BENCHMARK_SCHEMA = "ZB_CONTEXT_BENCHMARK_V1"
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
    for field in ("scope_tags", "source_refs", "supersedes"):
        if not isinstance(fact[field], list) or not all(isinstance(x, str) for x in fact[field]):
            raise ContextDisciplineError("CONTEXT_FACT_LIST_INVALID:" + field)
    return dict(fact)
```

`project_current_state` must:
1. validate all facts;
2. remove E0;
3. apply scope intersection when supplied;
4. retain relevant unsuperseded OWNER authority even when old;
5. remove facts explicitly named by a retained fact's `supersedes`;
6. group remaining exclusive facts by key and raise if more than one distinct value remains;
7. sort deterministically by `(key, created_at, fact_id)`;
8. return `{"schema": CURRENT_STATE_SCHEMA, "facts": projected}`.

Do not infer supersession from recency alone.

- [ ] **Step 4: Run GREEN**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/hq_context_discipline.py tests/test_hq_context_discipline_r01.py
git commit -m "feat: add fail-closed context state projection"
```

---

### Task 2: Minimum evidence-complete JIT restore packet

**Files:**
- Modify: `scripts/hq_context_discipline.py`
- Modify: `tests/test_hq_context_discipline_r01.py`

**Interfaces:**
- Reuse `scripts.hq_unified_archive.derive_record`, `write_record`, `build_restore_packet`, `build_learning_policy`.
- Add `build_context_packet(archive_root: Path, *, mandatory_anchors: list[dict[str, Any]], current_state: dict[str, Any], jit_queries: list[dict[str, str]], lesson_query: str | None = None) -> dict[str, Any]`.

- [ ] **Step 1: Add archive fixture helpers with real existing APIs**

Add to the test class:

```python
    @staticmethod
    def archive_event(title: str, body: str, number: int) -> bytes:
        payload = {
            "action": "created",
            "issue": {
                "number": number,
                "title": title,
                "html_url": f"https://github.com/Lester-Sparx/zorr-blatt-shared-hq/issues/{number}",
            },
            "comment": {
                "body": body,
                "html_url": f"https://github.com/Lester-Sparx/zorr-blatt-shared-hq/issues/{number}#issuecomment-1",
                "created_at": "2026-08-31T16:00:00Z",
            },
        }
        return (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")

    @classmethod
    def write_archive_record(cls, archive_root: Path, *, title: str, body: str, number: int) -> str:
        import hashlib
        from scripts.hq_unified_archive import derive_record, write_record
        raw = cls.archive_event(title, body, number)
        digest = hashlib.sha256(raw).hexdigest()
        record = derive_record(
            raw,
            raw_sha256=digest,
            event_name="issue_comment",
            repository="Lester-Sparx/zorr-blatt-shared-hq",
            actor="Lester-Sparx",
        )
        write_record(record, archive_root)
        return digest
```

- [ ] **Step 2: Add RED JIT tests**

```python
    def test_jit_packet_excludes_unrelated_history(self) -> None:
        from scripts.hq_context_discipline import build_context_packet, project_current_state
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_archive_record(root, title="LYNCH lesson",
                                      body="screen geography continuity axis", number=701)
            self.write_archive_record(root, title="SHERIFF lesson",
                                      body="OCI digest pinning security", number=702)
            state = project_current_state([
                self.fact("role", "E2", "ROLE", "LYNCH", exclusive=True, verified=True,
                          scope_tags=["LYNCH"])
            ])
            packet = build_context_packet(
                root,
                mandatory_anchors=[{"key": "CURRENT_TASK", "value": "scene-17"}],
                current_state=state,
                jit_queries=[{"facet": "DIRECTING_LESSON", "query": "screen geography continuity"}],
            )
        text = json.dumps(packet, ensure_ascii=False)
        self.assertIn("screen geography", text)
        self.assertNotIn("OCI digest", text)

    def test_missing_required_jit_facet_is_not_proven(self) -> None:
        from scripts.hq_context_discipline import build_context_packet, project_current_state
        with tempfile.TemporaryDirectory() as tmp:
            packet = build_context_packet(
                Path(tmp),
                mandatory_anchors=[{"key": "CURRENT_TASK", "value": "scene-17"}],
                current_state=project_current_state([]),
                jit_queries=[{"facet": "DIRECTING_LESSON", "query": "screen geography continuity"}],
            )
        self.assertEqual(packet["status"], "NOT_PROVEN")
        self.assertEqual(packet["missing_facets"], ["DIRECTING_LESSON"])
```

Also add a test where an E3 fact's `value` contains a large raw string but the projected packet includes only its `source_refs`; raw body duplication is a failure.

- [ ] **Step 3: Run RED**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

- [ ] **Step 4: Implement JIT retrieval using Unified Archive only**

Import existing APIs:

```python
try:
    from scripts.hq_unified_archive import build_learning_policy, build_restore_packet
except ModuleNotFoundError:
    from hq_unified_archive import build_learning_policy, build_restore_packet
```

Use adaptive search expansion:

```python
def _retrieve_facet(archive_root: Path, query: str) -> dict[str, Any] | None:
    previous_count = -1
    limit = 1
    while True:
        packet = build_restore_packet(archive_root, query, limit=limit)
        results = packet.get("results") if isinstance(packet, dict) else None
        if isinstance(results, list) and results:
            return packet
        current_count = len(results) if isinstance(results, list) else 0
        if current_count == previous_count and limit > 1:
            return None
        previous_count = current_count
        limit *= 2
        if limit > 1024:
            return None
```

The numeric ceiling is a defensive loop bound, not an acceptance threshold. If execution-time inspection exposes exact archive exhaustion/record count, replace this with that exact exhaustion signal.

`build_context_packet` must include only:
- mandatory anchors;
- projected current facts;
- one result set per explicit required facet;
- verified learning from `build_learning_policy` only when `lesson_query` is supplied;
- source refs for later RAW escalation;
- `status` and `missing_facets`.

- [ ] **Step 5: GREEN + Unified Archive regressions**

```bash
python -m unittest tests.test_hq_context_discipline_r01 tests.test_hq_unified_archive_v1 tests.test_hq_unified_archive_learning tests.test_hq_unified_archive_optimizer -v
```

- [ ] **Step 6: Commit**

```bash
git add scripts/hq_context_discipline.py tests/test_hq_context_discipline_r01.py
git commit -m "feat: add evidence-complete jit context packets"
```

---

### Task 3: Delta-only OWNER output

**Files:**
- Modify: `scripts/hq_context_discipline.py`
- Modify: `tests/test_hq_context_discipline_r01.py`

**Interfaces:**
- `diff_current_state(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]`
- `render_owner_delta(delta: dict[str, Any], *, blocker: str | None, evidence: list[str], next_action: str | None) -> str`

- [ ] **Step 1: RED tests**

```python
    def test_no_delta_does_not_repeat_settled_state(self) -> None:
        from scripts.hq_context_discipline import diff_current_state, project_current_state, render_owner_delta
        state = project_current_state([
            self.fact("head-b", "E2", "ACTIVE_HEAD", "bbbb", exclusive=True, verified=True)
        ])
        delta = diff_current_state(state, state)
        text = render_owner_delta(delta, blocker="WAITING_FOR_CI", evidence=[], next_action=None)
        self.assertEqual(text, "NO DELTA. BLOCKER = WAITING_FOR_CI")
        self.assertNotIn("bbbb", text)

    def test_terminal_delta_keeps_exact_evidence(self) -> None:
        from scripts.hq_context_discipline import diff_current_state, project_current_state, render_owner_delta
        previous = project_current_state([
            self.fact("result-a", "E1", "RESULT", "RUNNING", exclusive=True, verified=True)
        ])
        current = project_current_state([
            self.fact("result-b", "E2", "RESULT", "PASS", exclusive=True, verified=True,
                      supersedes=["result-a"])
        ])
        text = render_owner_delta(
            diff_current_state(previous, current),
            blocker=None,
            evidence=["run:33414957721", "head:556082d"],
            next_action="AUDIT_NEXT_GAP",
        )
        self.assertIn("DELTA:", text)
        self.assertIn("run:33414957721", text)
        self.assertIn("head:556082d", text)
        self.assertIn("NEXT: AUDIT_NEXT_GAP", text)
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

- [ ] **Step 3: Implement deterministic diff/renderer**

Rules:
- unchanged facts are never echoed;
- identical projection -> `NO DELTA`;
- routine evidence line is omitted when empty;
- terminal evidence IDs are preserved byte-for-byte;
- output has at most `DELTA`, optional `EVIDENCE`, optional `NEXT`, or one `NO DELTA. BLOCKER = ...` line.

- [ ] **Step 4: GREEN and commit**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
git add scripts/hq_context_discipline.py tests/test_hq_context_discipline_r01.py
git commit -m "feat: add delta-only owner output"
```

---

### Task 4: Derived handoff and cold-start validation

**Files:**
- Modify: `scripts/hq_context_discipline.py`
- Modify: `tests/test_hq_context_discipline_r01.py`

**Interfaces:**
- `build_handoff(*, role_or_engine: str, current_goal: str, task_or_correlation: str, authoritative_main: str, active_base: str, active_head: str, current_state: dict[str, Any], current_blocker: str | None, open_gaps: list[str], lesson_refs: list[str], next_action: str, source_refs: list[str], supersedes: list[str]) -> dict[str, Any]`
- `validate_handoff(handoff: dict[str, Any], *, fresh_authoritative_main: str) -> dict[str, Any]`
- schema `ZB_CONTEXT_HANDOFF_V1`.

- [ ] **Step 1: RED tests**

```python
    def test_handoff_contains_minimum_resume_state(self) -> None:
        from scripts.hq_context_discipline import build_handoff, project_current_state
        handoff = build_handoff(
            role_or_engine="LESTER",
            current_goal="harden chat reasoning",
            task_or_correlation="#235",
            authoritative_main="b18ca6b",
            active_base="b18ca6b",
            active_head="556082d",
            current_state=project_current_state([
                self.fact("head", "E2", "ACTIVE_HEAD", "556082d", exclusive=True, verified=True)
            ]),
            current_blocker=None,
            open_gaps=["ASSIGN_VS_EXECUTION"],
            lesson_refs=["verdict:SV1-LOOP-001"],
            next_action="REPRODUCE_NEXT_NEGATIVE",
            source_refs=["github:issue:235", "github:pr:237"],
            supersedes=[],
        )
        self.assertEqual(handoff["authority"], "DERIVED")
        self.assertEqual(handoff["next_action"], "REPRODUCE_NEXT_NEGATIVE")
        self.assertEqual(handoff["source_refs"], ["github:issue:235", "github:pr:237"])

    def test_handoff_cannot_override_fresher_authority(self) -> None:
        from scripts.hq_context_discipline import (
            ContextDisciplineError, build_handoff, project_current_state, validate_handoff,
        )
        handoff = build_handoff(
            role_or_engine="LESTER",
            current_goal="harden chat reasoning",
            task_or_correlation="#235",
            authoritative_main="old-main",
            active_base="old-main",
            active_head="candidate-head",
            current_state=project_current_state([]),
            current_blocker=None,
            open_gaps=[],
            lesson_refs=[],
            next_action="READ_FRESH_MAIN",
            source_refs=["github:issue:235"],
            supersedes=[],
        )
        with self.assertRaisesRegex(ContextDisciplineError, "HANDOFF_STALE"):
            validate_handoff(handoff, fresh_authoritative_main="new-main")
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

- [ ] **Step 3: Implement handoff builder/validator**

Required logical fields:

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

Always set `authority = "DERIVED"`. Never persist transcript or hidden reasoning. `validate_handoff` rejects a different fresh main and never treats the handoff as authority.

- [ ] **Step 4: GREEN and commit**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
git add scripts/hq_context_discipline.py tests/test_hq_context_discipline_r01.py
git commit -m "feat: add derived context handoffs"
```

---

### Task 5: Existing pre-action gate consumes context validity

**Files:**
- Modify: `scripts/hq_pre_action.py`
- Modify: `tests/test_hq_unified_archive_pre_action.py`

**Interfaces:**
- Change `evaluate_pre_action(context, *, learning_policy=None)` to `evaluate_pre_action(context, *, learning_policy=None, context_packet=None)`.
- Existing callers remain valid.

- [ ] **Step 1: Extend the test helper signature and add RED tests**

Change `_decide` to:

```python
    def _decide(
        self,
        context: dict[str, object],
        learning_policy: dict[str, object] | None = None,
        context_packet: dict[str, object] | None = None,
    ) -> dict[str, object]:
        gate = self._gate_module()
        return gate.evaluate_pre_action(
            context,
            learning_policy=learning_policy,
            context_packet=context_packet,
        )
```

Add:

```python
    def test_substantive_action_blocks_on_not_proven_context_packet(self) -> None:
        packet = {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "NOT_PROVEN",
            "missing_facets": ["CURRENT_HEAD"],
        }
        result = self._decide(self._context(), context_packet=packet)
        self.assertEqual((result["decision"], result["reason"]),
                         ("BLOCK", "DURABLE_CONTEXT_NOT_PROVEN"))

    def test_proven_context_packet_preserves_existing_pre_action_decision(self) -> None:
        packet = {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "missing_facets": [],
        }
        result = self._decide(self._context(), context_packet=packet)
        self.assertEqual((result["decision"], result["reason"]),
                         ("ALLOW", "PRE_ACTION_GATE_PASS"))
```

Add a third test combining a PROVEN context packet with the existing verified learning fixture; assert `result["learning"]` is unchanged.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_hq_unified_archive_pre_action -v
```

- [ ] **Step 3: Implement minimal packet validation**

Before existing action-specific checks:

```python
if context_packet is not None:
    if not isinstance(context_packet, dict) or context_packet.get("schema") != "ZB_CONTEXT_PACKET_V1":
        raise PreActionError("CONTEXT_PACKET_INVALID")
    if context_packet.get("status") != "PROVEN":
        return _decision(context, "BLOCK", "DURABLE_CONTEXT_NOT_PROVEN", learning_policy)
```

CLI:
- add optional `--context-packet-path`;
- read it as JSON;
- invalid/unreadable packet fails closed;
- do not perform archive retrieval inside `hq_pre_action.py`.

- [ ] **Step 4: GREEN and commit**

```bash
python -m unittest tests.test_hq_unified_archive_pre_action tests.test_hq_context_discipline_r01 -v
git add scripts/hq_pre_action.py tests/test_hq_unified_archive_pre_action.py
git commit -m "feat: enforce proven context before substantive actions"
```

---

### Task 6: T1-T10 behavioral acceptance and changed/unseen transfer

**Files:**
- Modify: `tests/test_hq_context_discipline_r01.py`
- Modify: `scripts/hq_context_discipline.py` only when a RED case proves missing behavior.

**Interfaces:**
- No new subsystem interface.

- [ ] **Step 1: Add deterministic state lookup helper**

```python
    @staticmethod
    def state_value(state: dict[str, object], key: str) -> object | None:
        facts = state.get("facts")
        if not isinstance(facts, list):
            return None
        matches = [x.get("value") for x in facts if isinstance(x, dict) and x.get("key") == key]
        return matches[0] if len(matches) == 1 else None
```

- [ ] **Step 2: T1 long-chat decision parity**

Build a list containing:
- 40 repeated E0 progress facts;
- old/new HEAD with explicit supersession;
- one current blocker;
- one old OWNER lock;
- unrelated SALVADOR and SHERIFF current-history facts;
- exact source refs.

Resolve the authoritative baseline by manually selecting the expected current values in the test:

```python
expected = {
    "ROLE": "LESTER",
    "CURRENT_TASK": "#235",
    "ACTIVE_HEAD": "556082d",
    "CURRENT_BLOCKER": "ASSIGN_VS_EXECUTION_UNPROVEN",
    "NEXT_ACTION": "REPRODUCE_NEGATIVE",
    "OWNER_LOCK": "NO_OWNER_RELAY",
}
```

Assert `project_current_state` + the JIT packet exposes exactly these current decision values and does not include E0 chatter.

- [ ] **Step 3: T2-T5 negatives**

Add separate tests for:
- old HEAD excluded after explicit supersession;
- two unsuperseded exclusive HEADs -> `DURABLE_CONTEXT_NOT_PROVEN`;
- LYNCH task does not load SHERIFF/SALVADOR history without explicit dependency;
- old unsuperseded OWNER lock remains present.

- [ ] **Step 4: T6 verified lesson transfer on changed task**

Reuse the existing `sync_sheriff_lessons` fixture pattern from `tests/test_hq_unified_archive_optimizer.py`. Create one CLOSED verdict with `regressionTest` + `lessonRef` and error signature `STALE_EVIDENCE_SUBSTITUTION`. Query a different task ID with the same error/domain terms through `build_learning_policy`; assert the lesson is retrieved. Create a second OPEN verdict and assert it is absent.

- [ ] **Step 5: T7 exact evidence escalation**

Create two RAW-bound archive records. Put only the selected record's `raw_sha256` and `source_url` in the compact packet. When the terminal claim is disputed, call the existing exact archive lookup path for that ref and assert the unrelated record body never enters the expanded evidence set.

- [ ] **Step 6: T8 no-delta repeated status**

Render the same projection three times. First output may contain the initial delta. Second and third outputs must be `NO DELTA` and must not contain `ACTIVE_HEAD`, architecture prose, or repeated settled laws.

- [ ] **Step 7: T9 handoff cold-start**

Construct a handoff from a proven projection, discard the original fact list in the test, then resume using only mandatory anchors + validated handoff + one JIT query. Assert the same expected current role/task/head/blocker/next action is recovered without transcript input.

- [ ] **Step 8: T10 measured context reduction in UTF-8 bytes**

Use the same long fixture:

```python
naive_bytes = len(json.dumps(full_history, sort_keys=True, ensure_ascii=False).encode("utf-8"))
compact_bytes = len(json.dumps(compact_packet, sort_keys=True, ensure_ascii=False).encode("utf-8"))
self.assertLess(compact_bytes, naive_bytes)
self.assertEqual(self.state_value(compact_packet["current_state"], "ACTIVE_HEAD"), "556082d")
self.assertEqual(self.state_value(compact_packet["current_state"], "OWNER_LOCK"), "NO_OWNER_RELAY")
```

Do not encode a universal compression-ratio gate. The measured ratio is evidence; correctness gates stay separate.

- [ ] **Step 9: Run twice for determinism and commit**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
python -m unittest tests.test_hq_context_discipline_r01 -v
git add scripts/hq_context_discipline.py tests/test_hq_context_discipline_r01.py
git commit -m "test: prove context discipline behavioral acceptance"
```

---

### Task 7: Benchmark/report CLI

**Files:**
- Modify: `scripts/hq_context_discipline.py`
- Modify: `tests/test_hq_context_discipline_r01.py`

**Interfaces:**
- CLI subcommand `benchmark`.
- JSON schema `ZB_CONTEXT_BENCHMARK_V1`.

- [ ] **Step 1: RED subprocess test**

Create a temporary input JSON containing `full_history` and `compact_packet` from the deterministic fixture, then invoke:

```bash
python scripts/hq_context_discipline.py benchmark --input-path fixture.json
```

Test the output structurally:

```python
self.assertEqual(result["schema"], "ZB_CONTEXT_BENCHMARK_V1")
self.assertGreater(result["naive_context_bytes"], result["compact_context_bytes"])
self.assertGreater(result["compression_ratio"], 1.0)
self.assertTrue(result["decision_parity"])
self.assertTrue(result["critical_fact_recall"])
self.assertTrue(result["stale_fact_rejection"])
```

- [ ] **Step 2: Implement argparse CLI around pure functions**

`benchmark` must:
1. read one local JSON input;
2. serialize `full_history` and `compact_packet` canonically;
3. compute byte counts and ratio;
4. consume explicit booleans `decision_parity`, `critical_fact_recall`, `stale_fact_rejection` produced by the test/benchmark harness;
5. print one deterministic JSON object.

No network, daemon, database, polling, or second archive.

- [ ] **Step 3: GREEN and commit**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
git add scripts/hq_context_discipline.py tests/test_hq_context_discipline_r01.py
git commit -m "feat: add context discipline benchmark cli"
```

---

### Task 8: Agent restart/output contract after behavioral proof

**Files:**
- Modify: `AGENTS.md`
- Modify: `tests/test_hq_context_discipline_r01.py`

**Interfaces:** documentation contract only; no Constitution rewrite in R01.

- [ ] **Step 1: RED documentation test**

```python
    def test_agents_declares_context_discipline_without_weakening_precedence(self) -> None:
        agents_text = (Path(__file__).resolve().parents[1] / "AGENTS.md").read_text(encoding="utf-8")
        for text in (
            "CHAT = ACTIVE DELTA",
            "CURRENT STATE = COMPACT UNSUPERSEDED VERIFIED PROJECTION",
            "ARCHIVE = EXISTING FULL DURABLE HISTORY",
            "RESTORE = MINIMUM EVIDENCE-COMPLETE JIT PACKET",
            "NO DELTA",
            "DURABLE_CONTEXT_NOT_PROVEN",
            "RAW ORIGINAL EVENT > VERIFIED GITHUB HISTORY",
        ):
            self.assertIn(text, agents_text)
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
```

- [ ] **Step 3: Add one compact section to `AGENTS.md`**

It must state exactly:

```text
CHAT = ACTIVE DELTA
CURRENT STATE = COMPACT UNSUPERSEDED VERIFIED PROJECTION
ARCHIVE = EXISTING FULL DURABLE HISTORY
RESTORE = MINIMUM EVIDENCE-COMPLETE JIT PACKET
```

And only these operational rules:
- after state is established, default to material deltas only;
- if nothing changed, compact `NO DELTA` replaces repeated recap;
- superseded facts are excluded from normal restore;
- old still-valid OWNER authority is never dropped due to age;
- unrelated history is JIT only on an explicit dependency;
- derived handoff/WARM state never overrides fresh exact GitHub evidence;
- contradiction/missing required evidence -> `DURABLE_CONTEXT_NOT_PROVEN`;
- terminal claims retain exact evidence required by the Constitution.

Do not paste the full design into `AGENTS.md`.

- [ ] **Step 4: GREEN + validator and commit**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
python scripts/hq_validate.py
git add AGENTS.md tests/test_hq_context_discipline_r01.py
git commit -m "docs: add context discipline restart law"
```

---

### Task 9: Full regression, exact-head CI, measured evidence, durable delta

**Files:** no new production files unless a fresh regression proves one is necessary.

- [ ] **Step 1: Re-read exact execution base before verification**

Verify the implementation branch still descends from the intended Unified Archive base and changed files introduce no second archive root, DB, service, daemon, vector store, duplicated RAW history, or Constitution weakening.

- [ ] **Step 2: Focused regression**

```bash
python -m unittest tests.test_hq_context_discipline_r01 -v
python -m unittest tests.test_hq_unified_archive_v1 -v
python -m unittest tests.test_hq_unified_archive_learning -v
python -m unittest tests.test_hq_unified_archive_optimizer -v
python -m unittest tests.test_hq_unified_archive_pre_action -v
```

- [ ] **Step 3: Full repository verification**

Run the exact unittest command used by current `hq-validate` workflow, then:

```bash
python scripts/hq_validate.py
```

All tests must pass on `git rev-parse HEAD`.

- [ ] **Step 4: Open an isolated draft implementation PR against the same legal base**

Do not use PR #240 as the code PR. No merge.

- [ ] **Step 5: Require fresh exact-head CI**

Require the current implementation PR's `hq-validate` and all normally triggered scope/control-tower/security jobs to succeed. Old PR #205/#237 runs do not prove this candidate.

- [ ] **Step 6: Run benchmark CLI and preserve its exact JSON output**

The durable evidence must include the CLI's actual values for:
- `naive_context_bytes`;
- `compact_context_bytes`;
- `compression_ratio`;
- `decision_parity`;
- `critical_fact_recall`;
- `stale_fact_rejection`.

- [ ] **Step 7: Require all behavioral gates before candidate PASS**

Explicitly record PASS/FAIL for:
- contradiction fail-closed;
- OWNER-lock retention;
- verified lesson transfer on changed/unseen case;
- evidence escalation;
- no-delta discipline;
- handoff cold-start;
- RAW archive unchanged;
- no second memory system.

- [ ] **Step 8: Post one concise exact delta to issue #235**

Do not use a prose template with guessed values. Generate the comment from the exact `git rev-parse HEAD`, implementation PR number, CI run IDs, benchmark JSON, and T1-T10 results from this verification run.

Required field names are fixed:

```text
LESTER_CONTEXT_DISCIPLINE_DELTA
EXACT_HEAD
PR
BASE
BEHAVIORAL_GATES
NAIVE_CONTEXT_BYTES
R01_CONTEXT_BYTES
COMPRESSION_RATIO
DECISION_PARITY
RAW_ARCHIVE_MUTATION
NEW_MEMORY_SYSTEM
REGRESSIONS
RESULT
NEXT
```

- [ ] **Step 9: Fresh-read the posted delta and require exact match**

A mismatch blocks terminal state.

- [ ] **Step 10: Stop without merge**

`ZORR_CONTEXT_DISCIPLINE_R01 = PASS` is allowed only if T1-T10 behavioral evidence, exact-head CI, measured reduction, and durable readback all pass. Otherwise report one exact failed gate or blocker.

---

## Plan Self-Review Result

- Spec coverage: Tasks 1-9 cover HOT/WARM/COLD, E0-E3, supersession, JIT restore, delta-only output, handoff, context accounting, T1-T10, role/authority preservation, reuse-first, and terminal evidence.
- Placeholder scan: no `TBD`, `TODO`, ellipsis code placeholders, unnamed handlers, or undefined production interfaces remain.
- Type consistency: `project_current_state`, `build_context_packet`, `diff_current_state`, `render_owner_delta`, `build_handoff`, `validate_handoff`, and optional `context_packet` pre-action integration keep one signature throughout.
- Authority preservation: WARM and handoff remain derived; fresh GitHub/RAW precedence stays superior.
- OWNER-lock preservation: explicit Task 1 and T6 tests.
- No fixed TOP-K/token acceptance law: retrieval is evidence-completeness driven; byte ratio is reported, not used as a universal quality score.
- Reuse-first: implementation is required to extend existing Unified Archive V1 and pre-action APIs.
- No parallel infrastructure: one pure-Python glue module; no service/daemon/vector DB/new archive.
