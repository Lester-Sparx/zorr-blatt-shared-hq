# SALVADOR SHADOW LEARNING R01 — Design

STATUS = DUNCAN 3 SANDBOX / DESIGN CANDIDATE
DATE = 2026-08-29
BRANCH = duncan3/salvador-shadow-learning-r01
IMPLEMENTATION = NOT STARTED
PRODUCTION_MUTATION = NO
CANON_MUTATION = NO
AUTO_PROMOTION = NO

## 1. Purpose

Create a preservation-first shadow-learning layer for SALVADOR that learns from every authorized visual run without changing the production run itself.

The shadow layer observes inputs, outputs, measured differences, QC outcomes, failure causes, and approved training evidence; it converts them into append-only learning events and a recoverable current training state.

Core flow:

`AUTHORIZED RUN -> OBSERVE -> MEASURE -> COMPARE -> DIAGNOSE -> ARCHIVE -> REDUCE STATE -> NEXT TRAINING TARGET`

Hard separation:

`SHADOW LEARNING != LIVE SELF-MODIFICATION`

The shadow layer MUST NOT modify production prompts, production model selection, workflow, denoise, dimensions, source assets, output assets, canon, QC verdicts, or owner locks.

## 2. Authority and inheritance

This design inherits and MUST remain subordinate to:

- ZORR BLATT Studio Constitution R02 (#76).
- SALVADOR Visual Truth & Production QC Charter R01 (#77).
- Existing training baseline/stress contracts (#93, #98).
- HQ Memory + Search vertical architecture (#144).

Authority rules:

`LEARNING CANDIDATE != PRODUCTION LAW`

`FAILED OUTPUT != DESIGN AUTHORITY`

`QC PASS != OWNER CANON`

`ASSISTANT INFERENCE != LOCKED TRUTH`

Any conflict with higher-authority truth is a fail-closed STOP for promotion, not permission to reinterpret the source.

## 3. Scope

### In scope

- Observe authorized SALVADOR runs and training runs.
- Register immutable source and result artifact references.
- Compute deterministic or explicitly versioned measurements.
- Record QC result, failure IDs, root-cause hypotheses, and learned-rule candidates.
- Maintain append-only learning history.
- Compute a current training snapshot from history.
- Restore SALVADOR learning context across sessions.
- Identify next training targets from unresolved or repeatedly failing skills.
- Support exact/lexical/hybrid retrieval through the HQ Memory/Search layer.

### Out of scope

- Autonomous production prompt rewriting.
- Autonomous model/workflow migration.
- Autonomous canon or OWNER LOCK changes.
- Auto-approval of generated art.
- Auto-promotion of rules to LOCKED.
- Replacing SALVADOR visual QC.
- Replacing OWNER validation.
- Replacing DUNCAN technical QC where a technical exact-head gate applies.
- Training on arbitrary internet images as project truth.
- One global opaque numeric "intelligence score".

## 4. Prime laws

1. `OBSERVE ALL AUTHORIZED RUNS` — every run inside the configured shadow scope produces a durable observation event, including FAIL.
2. `MUTATE NOTHING` — the observer has no write path into production execution state.
3. `MEASURE BEFORE INTERPRETING` — persist raw/derived measurements before model-authored diagnosis.
4. `ARCHIVE EVERY EVENT` — no useful success/failure exists only in chat.
5. `FAIL != ZERO LEARNING` — a failed result may still produce positive learning evidence.
6. `LEARNING CANDIDATE != PRODUCTION LAW` — learned-rule candidates require independent validation and authority promotion.
7. `HARD LOCK FAIL OVERRIDES AGGREGATE QUALITY` — no weighted average may rescue a broken identity/canon hard lock.
8. `RAW IS IMMUTABLE` — source bytes, result bytes, and historical QC records are never rewritten in place.
9. `STATE_NOW = REDUCE(EVENT_HISTORY)` — the current training snapshot must be reconstructible from append-only history.
10. `OPEN IS BETTER THAN INVENTED` — unknown values remain OPEN/UNTESTED.

## 5. Event model

The canonical learning unit is `SALVADOR_PROGRESS_EVENT_R01`.

Required fields:

```text
event_id
schema_version
subject_id = SALVADOR
task_id
run_id
run_kind
observed_at
source_refs[]
source_hashes[]
input_artifacts[]
output_artifacts[]
metric_set_version
measurements
qc_result
qc_evidence_refs[]
failure_ids[]
root_cause_hypotheses[]
learned_rule_candidates[]
skill_state_before
skill_state_after
progress_delta
next_target_candidates[]
provenance
supersedes_refs[]
derived_from_refs[]
```

Every event is append-only. Corrections create new events that supersede prior interpretations while preserving the original record.

## 6. Provenance

Every observation, metric, diagnosis, and rule candidate must retain provenance.

Minimum source types:

```text
OWNER_DIRECT
OWNER_CORRECTION
LOCKED_REFERENCE
APPROVED_REFERENCE
WORKING_REFERENCE
SOURCE_QUOTE
TEST_RESULT
QC_RESULT
MEASURED_DERIVATION
ASSISTANT_INFERENCE
ASSISTANT_GENERATED
```

Minimum provenance fields:

```text
source_id
source_type
source_location
source_hash
authority
created_at
extractor_or_metric_version
```

`ASSISTANT_INFERENCE` and `ASSISTANT_GENERATED` MUST NEVER silently promote to canon or LOCKED training law.

## 7. Mathematics and skill state

Do not collapse learning into one fake percentage.

Represent training state as a domain vector:

`K_t = {k_identity, k_proportion, k_silhouette, k_face, k_mask, k_costume, k_color, k_weapon, k_asymmetry, k_pose, k_framing, k_effects, k_qc_reliability, ...}`

After event `E_t`:

`K_(t+1) = UPDATE(K_t, E_t)`

Progress is a structured delta:

`DeltaK_t = K_(t+1) - K_t`

Allowed skill states:

```text
UNTESTED
FAILED
PARTIAL
PROVEN
LOCKED
```

`LOCKED` is authority-bearing and cannot be self-awarded by the learner.

A failure may improve knowledge without improving capability:

```text
RESULT = FAIL
ROOT_CAUSE = edit mask intersects higher-authority locked region
LEARNED_RULE_CANDIDATE = edit_mask INTERSECT higher_authority_lock MUST equal empty
CAPABILITY_DELTA = NONE_OR_NEGATIVE
KNOWLEDGE_DELTA = POSITIVE
```

## 8. Measurement model

Measurements are versioned and must be separable from interpretation.

Initial metric families:

```text
geometry
proportion
identity_landmarks
silhouette
color_zones
pose
handedness
weapon_geometry
asymmetry
framing_crop
material_zone_consistency
source_to_output_difference
```

Examples:

- `geometry_error`: normalized landmark displacement against authoritative reference.
- `proportion_error`: normalized ratio deviation for approved body/asset ratios.
- `silhouette_error`: contour/mask distance under a named method/version.
- `color_zone_error`: mismatch of major approved color regions, not raw pixel identity.
- `weapon_error`: length/orientation/hand-attachment deviation against weapon truth.
- `framing_error`: crop/coverage deviation against task framing requirements.

No metric family is allowed to redefine canon. Metrics compare against supplied authority.

## 9. QC interaction

Shadow learning consumes QC; it does not replace QC.

Required distinction:

```text
MEASUREMENT = what changed
DIAGNOSIS = likely why
QC = whether requirements passed
VALIDATION = whether result is right for the project/OWNER intent
```

Hard-lock rule:

`IF ANY REQUIRED HARD LOCK FAILS -> RESULT REMAINS FAIL`

A high aggregate similarity or aesthetic score cannot rescue:

- face drift;
- body drift;
- weapon/handedness drift;
- mask identity drift;
- silhouette drift;
- source-authority conflict;
- unauthorized redesign.

## 10. Rule lifecycle

Learned rules use a separate state machine:

`OBSERVED -> CANDIDATE -> RETESTED -> PROVEN -> LOCKED`

Failure/retirement states:

`REJECTED`
`SUPERSEDED`
`QUARANTINED`

Promotion gates:

- `OBSERVED -> CANDIDATE`: rule is explicitly tied to evidence and scope.
- `CANDIDATE -> RETESTED`: tested on a defined retest set not authored ad hoc by the learner during scoring.
- `RETESTED -> PROVEN`: independent evaluation shows the rule is useful without creating critical regressions.
- `PROVEN -> LOCKED`: explicit authorized promotion under Studio Constitution/OWNER/domain authority.

No automatic transition to `LOCKED`.

## 11. Archive and storage integration

Reuse HQ Memory + Search architecture from #144 rather than inventing a new database.

MVP storage:

```text
immutable RAW files
+
content-addressed artifact store
+
SQLite state/index database
+
SQLite FTS5
```

The learning system writes structured records compatible with the existing HQ objects:

```text
TRAINING_PROFILE
PROGRESS_EVENT
DECISION_RECORD
ARTIFACT_RECORD
SOURCE_RECORD
```

Binary art remains outside SQL blobs and is identified by content hash.

Artifact record minimum:

```text
artifact_id
path_or_object_ref
sha256
media_type
created_from
subject_ids[]
qc
status
authority
```

## 12. Current snapshot and recovery

The durable current training profile is a derived snapshot, never the only copy of truth.

`STATE_NOW = REDUCE(E_1, E_2, ... E_n)`

Required recovery call:

`LOAD_CONTEXT(subject="SALVADOR")`

It should return a compact packet:

```text
SUBJECT = SALVADOR
STATE_VERSION
LOCKED_SKILLS[]
PROVEN_CAPABILITIES[]
PARTIAL_SKILLS[]
FAILURE_MODES[]
ACTIVE_TRAINING_RULES[]
BEST_APPROVED_ARTIFACTS[]
OPEN_WEAKNESSES[]
LAST_PROGRESS_DELTA[]
NEXT_TARGETS[]
SOURCE_POINTERS[]
```

The packet MUST NOT dump raw chat history by default.

## 13. Status-aware search

Learning search inherits the HQ status model.

Default priority:

`CURRENT LOCKED > CURRENT PROVEN/APPROVED > CURRENT OPEN/PARTIAL > QUARANTINE > SUPERSEDED > REJECTED/DROP`

Search results must expose:

```text
text
subject
skill
status
authority
source
version
score
```

Old/superseded evidence remains searchable when explicitly requested but must not outrank current authoritative state by default.

## 14. Failure learning

Every meaningful failure should be archived with:

```text
failure_id
task_id
source_refs[]
failed_result_ref
exact_violation
root_cause
correct_repair
prevention_rule_candidate
skills_affected[]
retest_required
```

The system MUST distinguish:

- design authority (never inherited from failed output),
- diagnostic evidence (may be learned from failure),
- capability evidence (FAIL is not a capability PASS).

## 15. Shadow execution boundary

The shadow component must use a one-way observation boundary.

Preferred contract:

`PRODUCTION/TEST EVENT -> READ-ONLY OBSERVER ADAPTER -> SHADOW LEARNING PIPELINE`

The observer may read:

- task metadata;
- source/output artifact refs and hashes;
- approved measurement inputs;
- QC verdict/evidence.

The observer may write only to the training archive/HQ memory namespace.

Forbidden write targets:

- production controller task state;
- SALVADOR production config;
- model/workflow/prompt profile;
- source/result bytes;
- canon/OWNER LOCK;
- QC result;
- GitHub authoritative production events except a dedicated learning-record namespace approved later.

## 16. Error handling / fail closed

- Missing source -> event can record `OPEN`, but no authoritative diagnosis or rule promotion.
- Conflicting authority -> record `CONFLICT`, stop rule promotion.
- Missing measurement implementation -> record metric `UNAVAILABLE`, do not fabricate.
- Corrupt artifact/hash mismatch -> quarantine event/artifact reference and stop derived learning from it.
- Duplicate run event -> deduplicate by stable event/run/artifact identity; preserve exact duplicates as references, not repeated learning deltas.
- Changed metric implementation -> new `metric_set_version`; old values remain historical.
- Changed QC after learning event -> append a correction/supersession event and recompute snapshot.

## 17. Reuse law

Before implementing custom infrastructure, reuse existing components:

1. Existing HQ Memory/Search contracts from #144.
2. Pydantic for strict schemas and JSON Schema export.
3. SQLite for transactional local persistence.
4. SQLite FTS5 for lexical search.
5. Existing hashing/content-addressed artifact patterns.
6. pytest for deterministic scenario tests.
7. sqlite-vec only behind an interface and only after lexical MVP proves insufficient.
8. DuckDB only for later analytics/audit, not primary truth storage.

No new graph DB, vector server, search engine, or distributed service in R01.

## 18. MVP component boundaries

### A. `shadow_event_contracts`
Strict Pydantic schemas for progress events, measurements, rule lifecycle, and training snapshot.

### B. `shadow_observer`
Read-only adapter that converts authorized run/QC evidence into normalized event input.

### C. `shadow_measurements`
Versioned deterministic metric functions. No authority decisions.

### D. `shadow_reducer`
Reduces append-only events into the current SALVADOR training snapshot.

### E. `shadow_archive_adapter`
Persists events/artifact refs through the HQ Memory storage contract.

### F. `shadow_context_builder`
Builds `LOAD_CONTEXT(SALVADOR)` packets.

Each component must be independently testable and must not require production model execution for unit tests.

## 19. Vertical acceptance scenarios

### Scenario A — failure produces learning without production mutation

1. Record authorized run with source/result hashes.
2. QC = FAIL due to mask overlap with locked face region.
3. Shadow stores failure + candidate prevention rule.
4. Production config/profile remains byte-identical.
5. Context restore surfaces the failure and candidate rule.

Expected: PASS.

### Scenario B — success updates capability state

1. Skill `color_zone_preservation = PARTIAL`.
2. New authorized run passes QC with versioned color-zone metrics in tolerance.
3. Independent evidence supports promotion to `PROVEN`.
4. Snapshot rebuild returns `PROVEN` and source pointers.

Expected: PASS.

### Scenario C — owner correction supersedes old learning interpretation

1. Old event records interpretation X.
2. OWNER correction changes the authoritative fact to Y for a narrow domain.
3. New event supersedes X only in that domain.
4. Old history remains searchable.
5. Current context reports Y.

Expected: PASS.

### Scenario D — conflicting raw archive cannot change current authority

1. Add old contradictory RAW source.
2. Search finds it.
3. Status/authority ranking keeps current LOCKED truth above it.
4. Current SALVADOR context remains unchanged.

Expected: PASS.

### Scenario E — restart/rebuild

1. Persist several progress events.
2. Destroy/recreate derived snapshot/index state.
3. Rebuild from immutable event history.
4. `LOAD_CONTEXT(SALVADOR)` reproduces the same current skill states and source pointers.

Expected: PASS.

### Scenario F — hard lock beats aggregate quality

1. Candidate has strong silhouette/color/pose metrics.
2. Weapon is attached to the wrong anatomical hand against LOCKED truth.
3. QC = FAIL.
4. Shadow archives useful metric evidence but does not mark task capability PASS.

Expected: PASS.

## 20. Acceptance criteria

R01 is implementation-ready only when the design/plan preserves all of these requirements:

```text
SHADOW_READ_ONLY_TO_PRODUCTION = PASS
PRODUCTION_PROFILE_MUTATION = NO
CANON_MUTATION = NO
AUTO_PROMOTION = NO
APPEND_ONLY_EVENTS = PASS
RAW_IMMUTABLE = PASS
PROVENANCE = PASS
ARTIFACT_HASHING = PASS
VERSIONED_MEASUREMENTS = PASS
FAILURE_LEARNING = PASS
HARD_LOCK_OVERRIDE_BY_SCORE = IMPOSSIBLE
SKILL_VECTOR_STATE = PASS
RULE_LIFECYCLE = PASS
STATUS_AWARE_SEARCH = PASS
SNAPSHOT_REBUILD = PASS
CROSS_SESSION_CONTEXT_RESTORE = PASS
OWNER_CORRECTION_SUPERSESSION = PASS
OPEN_NOT_AUTOFILLED = PASS
REUSE_EXISTING_HQ_MEMORY = PASS
FRESH_TESTS = REQUIRED
INDEPENDENT_QC = REQUIRED BEFORE PRODUCTION INTEGRATION
```

## 21. Implementation sequencing after design approval

Implementation is intentionally split into a minimal vertical slice:

1. Strict event/training schemas.
2. SQLite append-only event persistence via HQ Memory contract.
3. Snapshot reducer.
4. Context restore.
5. One deterministic measurement family + versioning.
6. Failure-learning and rule lifecycle.
7. Status-aware lexical search integration.
8. Vertical tests A-F.
9. Fresh full verification.
10. DUNCAN independent technical QC if/when implementation is handed off under an exact-head gate.

Semantic/vector search and broad visual metric coverage are explicitly deferred until the vertical slice is proven.

## 22. Design verdict target

This design reaches DESIGN PASS only if all of the following are true:

- shadow path is one-way/read-only relative to production;
- learning is durable and reconstructible;
- failures can generate knowledge without becoming design truth;
- measured evidence is separated from model interpretation;
- no aggregate score can override hard-lock QC;
- rule promotion is authority-gated;
- current state is recoverable across sessions;
- existing HQ Memory/Search architecture is reused rather than duplicated;
- implementation remains a small vertical MVP rather than a new platform.

END.