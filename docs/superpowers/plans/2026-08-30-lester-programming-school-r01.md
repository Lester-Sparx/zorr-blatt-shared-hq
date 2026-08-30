# LESTER Programming School R01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, fail-closed per-domain programming skill model and next-training-target selector so DUNCAN PRIME can teach LESTER from verified evidence without fabricating competence.

**Architecture:** Reuse existing ZORR learning/SHERIFF patterns and Python stdlib only. Add one focused module that validates evidence, derives a neutral-to-proven profile, and selects the next curriculum target; keep SHERIFF discipline separate and leave Permanent Archive/DUNCAN reducers unchanged.

**Tech Stack:** Python 3 stdlib, JSON, unittest, existing GitHub Actions/HQ validation.

**Spec:** `docs/superpowers/specs/2026-08-30-lester-programming-school-r01-design.md`

## Global Constraints

- Tracker = issue #216.
- Base main = `b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1`.
- Work only on branch `duncan/lester-programming-school-r01`.
- `main` must remain unchanged.
- No merge, production, canon, PRIME_CORE or SHERIFF runtime mutation.
- Reuse existing ZORR/stdlib; add no package dependency, service, scheduler, database, queue or generic agent framework.
- Skill states are exactly `UNTESTED / FAILED / PARTIAL / PROVEN` in R01.
- Discipline and technical competence remain separate.

---

### Task 1: TDD RED — module contract exists only after a failing test

**Files:**
- Create: `tests/test_lester_programming_school.py`
- Later create: `scripts/lester_programming_school.py`

**Interfaces:**
- Produces test contract for module existence before behavior is implemented.

- [ ] **Step 1: Write the first failing test**

```python
from __future__ import annotations

import importlib.util
import unittest


class LesterProgrammingSchoolModuleTests(unittest.TestCase):
    def test_module_exists(self) -> None:
        self.assertIsNotNone(importlib.util.find_spec("scripts.lester_programming_school"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run focused test on CI and verify RED**

Run through existing PR CI / unittest discovery.
Expected: assertion failure because `scripts.lester_programming_school` does not exist.

- [ ] **Step 3: Create the empty module only after RED is proven**

Create `scripts/lester_programming_school.py` with imports/constants only; no untested behavior.

- [ ] **Step 4: Verify module-exists test GREEN**

Expected: PASS.

---

### Task 2: Evidence validation and fail-closed integrity

**Files:**
- Modify: `tests/test_lester_programming_school.py`
- Modify: `scripts/lester_programming_school.py`

**Interfaces:**
- Produces: `validate_evidence(records: list[dict[str, object]]) -> list[dict[str, object]]`
- Produces exception: `LesterProgrammingSchoolError`.

- [ ] **Step 1: Add failing tests**

Tests must prove:

```python
# EXECUTION without exactHead fails closed.
# unknown domain fails closed.
# duplicate evidenceId with identical canonical content deduplicates.
# duplicate evidenceId with different content raises integrity error.
# STUDY may omit exactHead but must still have a durable sourceRef.
```

Use concrete evidence dictionaries with `agentId="LESTER"`, modes `STUDY/EXECUTION/TRANSFER`, and 40-hex commit strings.

- [ ] **Step 2: Verify RED**

Expected failures: missing validator/error behavior.

- [ ] **Step 3: Implement minimal validator**

In `scripts/lester_programming_school.py` define:

```python
SKILL_STATES = ("UNTESTED", "FAILED", "PARTIAL", "PROVEN")
MODES = {"STUDY", "EXECUTION", "TRANSFER"}
RESULTS = {"PASS", "FAIL"}
DOMAINS = (...exact 16-domain tuple from spec...)

class LesterProgrammingSchoolError(RuntimeError):
    pass


def validate_evidence(records: list[dict[str, object]]) -> list[dict[str, object]]:
    ...
```

Validation must canonicalize each record with `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)`, enforce fields/ranges, deduplicate byte-identical IDs, and raise `EVIDENCE_ID_CONFLICT` when duplicate IDs differ.

- [ ] **Step 4: Verify focused tests GREEN**

---

### Task 3: Per-domain and per-task-kind skill derivation

**Files:**
- Modify: `tests/test_lester_programming_school.py`
- Modify: `scripts/lester_programming_school.py`

**Interfaces:**
- Produces: `build_profile(records: list[dict[str, object]]) -> dict[str, object]`.

- [ ] **Step 1: Add failing behavior tests**

Required cases:

```python
build_profile([]) -> every domain UNTESTED
STUDY PASS only -> UNTESTED
unverified EXECUTION PASS -> UNTESTED
verified EXECUTION FAIL only -> FAILED
one verified EXECUTION PASS -> PARTIAL
two verified EXECUTION PASS, no TRANSFER -> PARTIAL
verified EXECUTION PASS + verified TRANSFER PASS -> PROVEN
```

Also create two task kinds in one domain and assert each task-kind state is derived independently.

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement minimal profile reducer**

Each bucket tracks:

```python
{
  "state": "UNTESTED|FAILED|PARTIAL|PROVEN",
  "studyEvents": int,
  "verifiedPasses": int,
  "verifiedFailures": int,
  "verifiedTransferPasses": int,
  "evidenceIds": [str, ...],
  "sourceRefs": [str, ...],
  "lastSequence": int | None,
  "taskKinds": {...}
}
```

State rule:

```python
if verified_passes == 0 and verified_failures == 0: UNTESTED
elif verified_passes == 0: FAILED
elif verified_passes >= 2 and verified_transfer_passes >= 1: PROVEN
else: PARTIAL
```

Only `verified is True` + mode `EXECUTION|TRANSFER` affects pass/fail counts. STUDY affects only `studyEvents`.

Top-level profile must include:

```python
{
  "schemaVersion": "LESTER_PROGRAMMING_PROFILE_V1",
  "agentId": "LESTER",
  "historicalBackfill": False,
  "disciplineSource": "hq/sheriff/SHERIFF_SCOREBOARD_V1.json",
  "disciplineAffectsCompetence": False,
  "domains": {...}
}
```

- [ ] **Step 4: Verify focused tests GREEN**

---

### Task 4: Deterministic DUNCAN curriculum target

**Files:**
- Modify: `tests/test_lester_programming_school.py`
- Modify: `scripts/lester_programming_school.py`

**Interfaces:**
- Produces: `choose_next_training_target(profile: dict[str, object], preferred_domains: list[str] | None = None) -> dict[str, str]`.

- [ ] **Step 1: Add failing tests**

Prove:

```python
FAILED beats UNTESTED for remediation.
UNTESTED beats PARTIAL.
PARTIAL returns recommendedMode=TRANSFER.
FAILED/UNTESTED return recommendedMode=EXECUTION.
preferred_domains controls tie order without overriding lower state.
all PROVEN returns a deterministic TRANSFER maintenance target.
```

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement selector**

State priority:

```python
{"FAILED": 0, "UNTESTED": 1, "PARTIAL": 2, "PROVEN": 3}
```

Tie-break: fewer verified execution/transfer attempts, then preferred/catalog order.

Return:

```python
{
  "domain": str,
  "state": str,
  "recommendedMode": "EXECUTION|TRANSFER",
  "reason": str,
}
```

- [ ] **Step 4: Verify focused tests GREEN**

---

### Task 5: Durable catalog, neutral bootstrap and operator contract

**Files:**
- Create: `hq/training/LESTER_PROGRAMMING_DOMAIN_CATALOG_V1.json`
- Create: `hq/training/LESTER_PROGRAMMING_PROFILE_V1.json`
- Create: `docs/LESTER_PROGRAMMING_SCHOOL_R01.md`
- Modify: `tests/test_lester_programming_school.py`

**Interfaces:**
- Static catalog/profile must match module output exactly.

- [ ] **Step 1: Add failing tests for static files**

Tests read repository files and assert:

```python
catalog schemaVersion == "LESTER_PROGRAMMING_DOMAIN_CATALOG_V1"
exactly 16 unique domains in spec order
bootstrap profile == build_profile([])
all bootstrap domains UNTESTED
historicalBackfill is False
no evidence IDs/source refs are present
```

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Create catalog/bootstrap/docs**

Catalog is curriculum metadata only; no competence claims.

Operator contract must state:

`REAL ZORR TASK -> EVIDENCE -> TEST/QC -> LESSON -> CHANGED/UNSEEN TRANSFER -> SKILL UPDATE`

and:

`READING != SKILL`, `ONE PASS != PROVEN`, `SHERIFF DISCIPLINE != PROGRAMMING COMPETENCE`.

- [ ] **Step 4: Verify focused tests GREEN**

---

### Task 6: CLI and final exact-head verification

**Files:**
- Modify: `scripts/lester_programming_school.py`
- Modify: `tests/test_lester_programming_school.py`

**Interfaces:**
- CLI: `python3 -m scripts.lester_programming_school --evidence <json-file>` prints deterministic profile + `nextTrainingTarget` JSON.

- [ ] **Step 1: Add failing CLI test using a temporary JSON evidence file**

Assert exit code 0 for valid evidence and stable JSON; invalid evidence must exit non-zero.

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement minimal argparse CLI**

No network, database or package dependency.

- [ ] **Step 4: Run focused tests**

Expected: all `test_lester_programming_school.py` tests PASS.

- [ ] **Step 5: Run full repository verification on exact candidate HEAD**

Require:

```text
python3 scripts/hq_validate.py = PASS
python3 -m unittest discover -s tests -v = PASS
relevant GitHub Actions = SUCCESS
```

- [ ] **Step 6: Fresh-read Constitution and changed files from exact candidate HEAD**

- [ ] **Step 7: Persist terminal evidence to issue #216**

Terminal record must include exact base/HEAD, changed files, CI run IDs, focused/full test counts, `MAIN_UNCHANGED=YES`, `MERGED=NO`, and next legal gate.
