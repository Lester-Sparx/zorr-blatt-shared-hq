# ZORR CONTEXT DISCIPLINE R01 — Design

STATUS = DESIGN_ONLY / OWNER_APPROVED_ARCHITECTURE
LOGICAL_AGENT = LESTER
BASE_MAIN = b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1
PRIMARY_TRACKER = #235
MERGE = NO
CANON_CHANGE = NO
ARCHIVE_REWRITE = NO
NEW_MEMORY_SYSTEM = NO
NEW_DAEMON = NO
NEW_SERVICE = NO

## 1. Purpose

Increase the useful lifetime and decision quality of ZORR working chats by reducing repeated context, preventing stale state from surviving beside fresh state, and moving durable truth out of chat into the existing GitHub/Archive authority path.

The target is not shorter prose for its own sake. The target is:

`LESS PROJECT-CONTROLLED CONTEXT -> SAME OR BETTER DECISION FIDELITY -> MORE HEADROOM FOR NEW REASONING`

Chat remains working memory. GitHub remains authority. Existing Permanent Archive V1 remains the historical archive. This design must not create a second archive, second memory authority, second agent layer, or second truth store.

## 2. Core model

ZORR context is divided into three logical temperatures without creating three physical authority systems.

### HOT — active chat state

Contains only information needed to make the next correct decision:

- current role / engine;
- current goal;
- exact current task/correlation binding;
- exact current candidate/base/HEAD when applicable;
- current verified state;
- current blocker or uncertainty;
- next legal action;
- only the recent unsuperseded deltas required to understand that action.

HOT is disposable working memory. It is never authority.

### WARM — compact derived current state

A rebuildable checkpoint derived from durable evidence. It contains the latest unsuperseded values needed to resume work without replaying the chat.

WARM must be reconstructible from GitHub/Archive evidence and must never override fresher exact tracker/PR/workflow evidence.

### COLD — existing durable history

Existing GitHub issues/PRs/workflows and Permanent Archive V1 RAW history remain the complete evidence/history layer.

COLD is not injected into a chat wholesale. It is retrieved just in time when a current decision needs it.

## 3. Information classes

Every project-controlled chat item belongs to one of four classes.

### E0 — EPHEMERAL

Examples:
- "checking" / progress chatter;
- tool-call narration;
- repeated status with no state change;
- dead hypothesis that produced no reusable lesson;
- temporary intermediate SHA already superseded by the final candidate;
- repeated explanation of settled law.

Retention:
- may remain in raw conversation history;
- MUST NOT enter WARM current state;
- MUST NOT be retrieved into a future chat by default;
- MUST NOT be converted into a verified lesson.

### E1 — ACTIVE DELTA

A new but not yet terminal working fact or hypothesis that changes the next action.

Examples:
- newly reproduced failure;
- newly isolated boundary;
- current candidate HEAD;
- current unresolved contradiction;
- current exact blocker.

Retention:
- present in HOT while active;
- may enter WARM while unresolved/current;
- automatically disappears from WARM when superseded/resolved unless historical reconstruction requests it.

### E2 — DURABLE VERIFIED EVENT

Examples:
- explicit OWNER directive/authority change;
- verified PASS/FAIL/BLOCKED terminal state;
- exact evidence-bound finding;
- accepted canon/lock;
- role/authority boundary;
- verified lesson/regression rule;
- durable handoff state.

Retention:
- persist through existing GitHub/Archive authority paths;
- may be represented compactly in WARM;
- retrieved JIT only when relevant, except mandatory boot/authority anchors.

### E3 — RAW EVIDENCE

Examples:
- workflow logs;
- immutable source comments;
- test artifacts;
- exact original event bytes;
- screenshots/hashes where evidence policy requires them.

Retention:
- keep under existing evidence/archive rules;
- HOT/WARM store only a pointer/hash/ref unless raw bytes are required for the current decision;
- never rewrite RAW history during compaction.

## 4. Delta-only communication law

After a state has been established, later agent messages report only materially new information.

A fact is repeated only when at least one of these is true:

1. the user explicitly asks for a recap/explanation;
2. the fact is required to disambiguate a dangerous/irreversible action;
3. the previous value has been superseded and the contrast matters;
4. a terminal PASS/BLOCKED claim requires the exact evidence inline.

Routine OWNER-facing output defaults to:

```text
DELTA: <what changed>
EVIDENCE: <exact proof only when needed>
NEXT: <one next legal action>
```

If nothing materially changed:

```text
NO DELTA. BLOCKER = <exact blocker>
```

Long explanations are opt-in or used only when omission would reduce decision quality.

## 5. Supersession law

Current state is key-based, not transcript-based.

For any state key K, at most one unsuperseded current value may be loaded into HOT/WARM.

Example:

```text
K = ACTIVE_HEAD
old = A
new = B
B.supersedes = A
current(K) = B
```

A is retained in durable history but excluded from normal restore.

This applies to:
- HEAD/base bindings;
- blockers;
- PR/workflow state;
- role assignments;
- skill verdicts;
- production/canon values when legitimately superseded;
- hypotheses/resolutions;
- current next action.

If two unsuperseded values of the same exclusive key remain contradictory, restore fails closed with `DURABLE_CONTEXT_NOT_PROVEN` for the affected decision.

## 6. Mathematical optimization objective

Let:

- `P` = candidate restore packet;
- `C(P)` = project-controlled token/context cost of P;
- `Q` = decision-required fact set for the next action;
- `w(q)` = criticality weight for fact q;
- `Coverage(P,Q)` = weighted fraction of required facts represented correctly in P;
- `A(P)` = authority errors: unsupported/stale/superseded facts presented as current;
- `X(P)` = unresolved contradictions admitted into current state;
- `R(P)` = semantic redundancy: repeated information that does not change the decision.

R01 does not optimize a beauty score. It solves a constrained minimization:

```text
minimize    C(P) + alpha*R(P)
subject to  Coverage(P,Q_critical) = 1
            A(P) = 0
            X(P) = 0
            exact authority/evidence bindings preserved
```

For non-critical optional background facts, retrieval may stop when additional context no longer changes the decision or closes a known uncertainty.

No universal fixed token count or fixed TOP-K is authoritative. The smallest evidence-complete packet wins.

## 7. JIT restore algorithm

### Phase A — mandatory anchors

Always restore only the mandatory anchors needed by current law:

1. current main HEAD + Constitution;
2. AGENTS/restart law;
3. exact role/engine identity and authority boundary;
4. exact current task/tracker/correlation;
5. fresh exact current PR/HEAD/workflow/runtime evidence required by that task.

### Phase B — current-state projection

Load only unsuperseded WARM facts whose tags/scope intersect the task.

Required exclusion filters:
- superseded;
- resolved and no longer decision-relevant;
- wrong role/engine unless cross-role dependency is explicit;
- wrong project capability/domain;
- unverified lesson;
- stale derived state conflicting with fresh exact evidence.

### Phase C — verified lessons

Derive a query signature from:

`ROLE/ENGINE + TASK + ERROR_SIGNATURE + DOMAIN + CURRENT_ACTION`

Reuse existing archive/search mechanisms. Prefer exact tags/IDs and existing deterministic retrieval such as SQLite FTS5 where already available; do not add a vector DB or second memory service merely for R01.

Retrieve incrementally until all known decision facets are covered. There is no fixed `TOP_K` law.

### Phase D — evidence expansion on demand

Fetch E3 RAW evidence only when:
- a claim is disputed;
- derived state is contradictory;
- a terminal gate requires raw proof;
- the current decision cannot be justified from verified pointers/metadata.

### Phase E — fail closed

If a required fact is missing, contradictory, stale, or cannot be tied to authority/evidence, return `DURABLE_CONTEXT_NOT_PROVEN` for that action rather than expanding the chat with guesses.

## 8. Checkpoint triggers

A durable/WARM checkpoint is event-driven, not transcript-length-driven.

Create/update compact current state when any of these changes materially:

- goal/task/correlation;
- role/engine/authority;
- base or candidate HEAD;
- current blocker;
- terminal PASS/FAIL/BLOCKED;
- OWNER directive/canon/lock;
- verified lesson/regression;
- contradiction resolution;
- next legal action after a major gate;
- intentional chat handoff;
- measured context pressure requires migration to a fresh chat.

Do NOT checkpoint merely because the agent emitted routine progress prose.

## 9. Handoff packet

When a chat should be retired, persist a compact derived handoff through the existing durable context path. Required logical fields:

```text
ROLE_OR_ENGINE
CURRENT_GOAL
TASK_OR_CORRELATION
AUTHORITATIVE_MAIN
ACTIVE_BASE
ACTIVE_HEAD
VERIFIED_CURRENT_STATE
CURRENT_BLOCKER_OR_NONE
OPEN_GAPS
RELEVANT_VERIFIED_LESSON_REFS
NEXT_EXACT_ACTION
SOURCE_EVIDENCE_REFS
SUPERSEDES
```

The handoff packet is derived state, not authority. A new chat must fresh-read exact GitHub evidence before terminal claims.

The old chat is not required after a successful handoff.

## 10. Archive discipline

### Preserve

Always preserve durably when applicable:
- explicit OWNER authority/canon/locks;
- verified role boundaries;
- exact PASS/FAIL/BLOCKED evidence;
- active candidate/base bindings;
- verified lessons and known failure signatures;
- safety/security rules;
- original RAW evidence/history under existing archive rules.

### Do not promote to durable knowledge

Do not promote:
- routine progress;
- assistant self-description;
- unverified speculation;
- repeated settled facts;
- verbose reasoning transcript;
- failed search paths with no durable lesson;
- summaries whose only source is chat memory.

### Compact, never erase authority

Compaction removes items from active restore, not from authoritative RAW history. Superseded evidence remains available for audit/history.

## 11. Context-cost accounting

R01 measures project-controlled context, not hidden model/system instructions.

For every restore benchmark record:

```text
NAIVE_CONTEXT_UNITS = tokens/bytes of full-history or current existing restore approach
R01_CONTEXT_UNITS = tokens/bytes of compact packet
COMPRESSION_RATIO = NAIVE_CONTEXT_UNITS / R01_CONTEXT_UNITS
DECISION_PARITY = PASS|FAIL
CRITICAL_FACT_RECALL = PASS|FAIL
STALE_FACT_REJECTION = PASS|FAIL
```

The optimization is accepted only when context cost falls without losing critical facts or changing a correct decision.

No fixed compression ratio is a universal law. R01 must demonstrate material reduction on representative long-running ZORR fixtures and report the measured ratio rather than inventing success.

## 12. Behavioral acceptance suite

A green schema/unit test alone is insufficient. R01 requires behavioral negative tests.

### T1 — long-chat decision parity

Given a long historical fixture, compare:
- full-history baseline;
- compact HOT/WARM + JIT restore.

Required: same correct current role, exact HEAD/task binding, blocker, authority and next legal action.

### T2 — stale supersession rejection

History contains old HEAD A and fresh HEAD B.

Required: normal restore exposes B only as current; A remains retrievable only for history/audit.

### T3 — contradiction fail-closed

Two exclusive unsuperseded authority/current-state facts conflict.

Required: no guessed merge; affected action returns `DURABLE_CONTEXT_NOT_PROVEN`.

### T4 — unrelated-history exclusion

A LYNCH/directing task coexists with unrelated SHERIFF/SALVADOR history.

Required: unrelated history is not loaded unless a concrete dependency exists.

### T5 — OWNER authority retention

A very old but still-unsuperseded OWNER lock must survive aggressive compaction and be restored when relevant.

### T6 — verified lesson transfer

A lesson proven in an old chat is retrieved in a changed/unseen later task when its error/domain signature matches.

Unverified or OPEN lessons must not be promoted.

### T7 — evidence escalation

Compact metadata is insufficient for a disputed PASS.

Required: system fetches exact RAW/workflow evidence JIT rather than replaying the whole chat or guessing.

### T8 — no-delta response discipline

Repeated polling/status cycles with no state change must not repeatedly echo settled context.

### T9 — handoff cold-start

A fresh chat using only mandatory anchors + handoff + JIT must resume the correct next action without OWNER restating history.

### T10 — context reduction

Measure context units against baseline on representative long-running chat fixtures. PASS requires a material measured reduction with T1–T9 still green.

## 13. Role/engine retrieval boundaries

All agents use the same discipline, but retrieval is scoped.

- LESTER: execution/security/task evidence and verified engineering lessons.
- DUNCAN PRIME: root identity, project truth, learning, exact task evidence.
- SALVADOR: drawing-relevant laws/evidence/lessons plus explicit cross-engine dependencies.
- GAUZZ: math/QC evidence/locks/lessons plus the exact artifact under measurement.
- LYNCH: scene/directing state/lessons plus required geometry/design/drawing constraints.
- HOKUSAI: design state/lessons plus frozen canon/production constraints.

Cross-role retrieval is explicit dependency, not default context flooding.

## 14. Reuse-first implementation direction

This design authorizes no implementation yet.

When implementation is separately approved/planned, reuse in this order:

1. current Constitution/AGENTS restart law;
2. existing GitHub issues/PR/workflow evidence;
3. Permanent Archive V1 RAW history;
4. existing/reviewed Unified Archive/current-context/verified-learning mechanisms if they are on the chosen legal base;
5. standard-library/SQLite FTS5/native GitHub mechanisms;
6. mature maintained OSS only for a demonstrated missing capability;
7. minimal ZORR glue last.

Explicitly prohibited by R01 scope:
- second archive;
- vector DB introduced without measured need;
- new memory daemon/service;
- transcript summarizer as a new authority;
- model-weight training;
- destructive archive rewrite;
- automatic merge or canon mutation.

## 15. Success definition

`ZORR_CONTEXT_DISCIPLINE_R01 = PASS` only when fresh evidence shows all of the following on the exact candidate:

1. active state contains no known superseded exclusive facts;
2. mandatory authority/evidence bindings are preserved;
3. representative long-chat decisions match the correct full-evidence baseline;
4. unrelated context is excluded by default;
5. verified lessons transfer and unverified lessons do not;
6. handoff resumes work without OWNER restating recoverable history;
7. project-controlled context cost is materially lower and measured;
8. RAW evidence remains recoverable and unmodified;
9. no second archive/memory authority/service was created;
10. chat output follows delta-only behavior without suppressing material blockers/evidence.

## 16. Design invariant

The entire design reduces to:

```text
CHAT = ACTIVE DELTA
CURRENT STATE = COMPACT UNSUPERSEDED VERIFIED PROJECTION
ARCHIVE = EXISTING FULL DURABLE HISTORY
RESTORE = MINIMUM EVIDENCE-COMPLETE JIT PACKET
```

The optimization must never trade truth for brevity.
