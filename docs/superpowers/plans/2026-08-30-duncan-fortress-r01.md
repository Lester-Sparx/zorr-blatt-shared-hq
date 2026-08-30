# DUNCAN Fortress R01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make DUNCAN Night School learning fail-closed and deterministically rebuildable from Permanent Archive V1, using only existing ZORR code, Python standard library, Git, and mature FOSS security tools.

**Architecture:** Keep RAW GitHub events authoritative and immutable. Add one thin DUNCAN-derived event/reducer beside the existing SALVADOR archive reducer: an invalid Night School report remains preserved in RAW but cannot mutate derived DUNCAN knowledge. Produce a disposable/rebuildable `DUNCAN_CONTEXT_NEXT.json` from validated derived events. Add FOSS-only workflow static checks without introducing a service, database, daemon, vector store, proprietary SDK, or second archive.

**Tech Stack:** existing ZORR Python archive code; Python 3 standard library (PSF); Git; GitHub Actions; actionlint (MIT), zizmor (MIT), Gitleaks (MIT) only after exact upstream version/license/ref verification.

**Spec:** issue #206 + current `ZORR_EXECUTION_CONSTITUTION.md` and `AGENTS.md`.

## Global Constraints

- `EXISTING ZORR CODE -> NATIVE/STANDARD PLATFORM -> MATURE OPEN-SOURCE SOURCE CODE -> MINIMAL ZORR GLUE`.
- Added dependencies/components must have public source and an OSI-compatible/open-source license; no proprietary learning/memory/security components.
- RAW archive remains source of truth; derived DUNCAN state must be deletable and fully rebuildable from RAW/derived event evidence.
- Allowed learned skill states are exactly `UNTESTED`, `FAILED`, `PARTIAL`, `PROVEN`; `LOCKED` is never emitted by autonomous Night School.
- Invalid reports are archived as facts but are not training-eligible and do not change `DUNCAN_CONTEXT_NEXT`.
- PRIME_CORE, OWNER relationship, canon, production and authority remain immutable in this slice.
- No production activation or model-weight training.

---

### Task 1: RED — DUNCAN report validation and rebuild contract

**Files:**
- Create: `tests/test_duncan_night_archive.py`
- Later create: `scripts/duncan_night_archive.py`

**Interfaces:**
- Consumes an `issue_comment.created` GitHub event body containing `DUNCAN_NIGHT_REPORT_R01`.
- Produces a validated derived record under `derived/duncan-night-v1/events/<raw_sha256>.json` and rebuildable context at `derived/duncan-night-v1/DUNCAN_CONTEXT_NEXT.json`.

- [ ] Add tests proving a valid `PARTIAL` skill delta is accepted and updates context.
- [ ] Add a regression test proving `PARTIAL+` is rejected from learning while RAW preservation remains unaffected by this reducer.
- [ ] Add a test proving `PRIME_CORE_CHANGED != NO` rejects learning.
- [ ] Add a test proving context rebuilt from the same validated event set is byte-identical.
- [ ] Commit tests only and open a PR so existing `hq-validate` physically demonstrates RED because the module does not yet exist.

### Task 2: GREEN — minimal reducer using existing archive patterns

**Files:**
- Create: `scripts/duncan_night_archive.py`
- Modify only if needed: `tests/test_duncan_night_archive.py`

**Interfaces:**
- `archive_duncan_night_event(event_bytes: bytes, archive_root: Path, metadata: Mapping[str, str]) -> dict[str, str] | None`
- `rebuild_duncan_context(archive_root: Path) -> dict[str, object]`

- [ ] Reuse `_canonical_json` and `_write_once` from `scripts.hq_archive_ingest.py`.
- [ ] Parse only `issue_comment.created` and only bodies beginning `DUNCAN_NIGHT_REPORT_R01`.
- [ ] Require exact safety fields `PRIME_CORE_CHANGED = NO` and `PRODUCTION_MUTATION = NO`.
- [ ] Parse each `SKILL_DELTA` state and accept only exact allowed values; reject `PARTIAL+`, `LOCKED`, unknown states and malformed transitions from training eligibility.
- [ ] Write content-addressed derived event with provenance to RAW SHA-256.
- [ ] Rebuild current context deterministically from sorted validated events; current context contains validated skills, self-model deltas, owner-taste deltas, source event hashes/comment IDs and latest cycle ID, never RAW replacement text.
- [ ] Verify targeted tests and full unittest suite green on exact PR HEAD.

### Task 3: Wire reducer into Permanent Archive V1

**Files:**
- Modify: `.github/workflows/zb-permanent-archive-v1.yml`
- Modify: `scripts/hq_archive_verify.py`
- Modify: `tests/test_hq_archive_v1.py` if verifier coverage is needed.

- [ ] Add one deterministic `Derive DUNCAN Night School learning` step after RAW preservation using `python3 -m scripts.duncan_night_archive`.
- [ ] Extend archive verification to validate `DUNCAN_CONTEXT_NEXT.json` provenance and confirm it equals a fresh reducer rebuild; derived mismatch must fail closed.
- [ ] Keep existing SALVADOR derivation intact; do not create a second archive/workflow.
- [ ] Run full PR CI and require green exact HEAD.

### Task 4: FOSS-only supply-chain checks

**Files:**
- Create/modify: `.github/workflows/oss-security.yml`

- [ ] Fresh-verify upstream source, license and immutable release/ref for actionlint, zizmor and Gitleaks.
- [ ] Use immutable/pinned versions or release SHA checks; no mutable unverified installer path.
- [ ] Run actionlint against workflows, zizmor against GitHub Actions definitions and Gitleaks against repository content/history in bounded CI.
- [ ] Do not add proprietary scanners or SaaS-only gates.
- [ ] Require the workflow itself to pass on the PR HEAD before merge.

### Task 5: Final verification and durable evidence

- [ ] Fresh-read PR diff and exact HEAD; prove no unrelated production/canon changes.
- [ ] Fetch all PR workflow runs/jobs and require every required introduced check green.
- [ ] Merge only when exact-head CI and scope are green.
- [ ] Trigger/observe one fresh Night School report after merge and prove: RAW archived; validated derived event created; `DUNCAN_CONTEXT_NEXT.json` rebuilt; invalid status cannot promote knowledge.
- [ ] Fresh-read `main`, Constitution, merged files and archive evidence; record terminal result in issue #206.
- [ ] Separately record administrative blockers that cannot be changed by the connector: `zb-archive-v1` branch ruleset and `main` required-status ruleset. Never pretend code CI substitutes for repository-enforced rulesets.
