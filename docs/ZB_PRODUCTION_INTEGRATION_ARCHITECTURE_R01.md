# ZORR BLATT — Production Integration Architecture R01

Status: **CANDIDATE / DOCS ONLY / NOT PRODUCTION AUTHORIZATION**  
Protected-base binding: `9da550e842c7b2e22418b38d299e83b38e264122`  
Source: approved Integration Architecture sections 1–7 following completed O0/B0/M0/C1/GRANI feasibility proofs.

This document promotes proven **contracts, boundaries, governance, provenance and rollout rules** into a production-integration architecture candidate. It does **not** promote throwaway proof implementations into production, does **not** authorize runtime bootstrap or implementation, does **not** mutate `hq/state`, does **not** create OWNER LOCK, and does **not** activate G2 or Voice-to-Shot.

---

## 1. Integration target: two-plane architecture

ZORR BLATT production integration is split into two distinct planes.

```text
ZORR BLATT SHARED HQ
= CONTROL / AUTHORITY / EVIDENCE PLANE

        │ approved contracts
        │ exact repo + revision + hash bindings
        ▼

ZB PRODUCTION RUNTIME
= EXECUTION PLANE
  ZB CORE
  Body Compiler
  Motion / Action
  Cinematography
  Babylon Runtime
  Grani Presentation
```

Shared HQ is not the production runtime. It records and verifies:

```text
AUTHORITIES
CONTRACT VERSIONS
DEPENDENCY PINS
EVIDENCE
REVIEW VERDICTS
RUNTIME REPOSITORY BINDINGS
RELEASE / ARTIFACT HASHES
GATES
```

The runtime executes approved contracts and returns immutable build/QC evidence.

Hard law:

```text
HQ CAN AUTHORIZE / VERIFY RUNTIME.
RUNTIME CANNOT REDEFINE HQ AUTHORITY.
```

Proof branches remain evidence only. Their throwaway implementation code is not production code.

---

## 2. Production dataflow and authority graph

Canonical production direction:

```text
REFERENCE EVIDENCE
        │
        ▼
CHARACTER_DNA                         ← AUTHORITATIVE
        │
        ├──────────────┐
        │              │
        ▼              ▼
REST_RIG          SURFACE CONTRACT     ← AUTHORITATIVE
        │              │
        └──────┬───────┘
               ▼
       ZB BODY COMPILER
               │
               ▼
      COMPILED BODY MESH              ← DERIVED
               │
               ▼
        RUNTIME BODY
               │
               ▼
     BODY TRUTH PACKET                ← CANONICAL RUNTIME TRUTH
               │
               │ + SPACE TRUTH
               │ + MOTION DNA
               ▼
       MOTION TRUTH                   ← CANONICAL
               │
               ▼
       ACTION TRUTH                   ← CANONICAL
               │
               ▼
         SHOT INTENT                  ← AUTHORED INTENT
               │
               ▼
        CAMERA TRUTH                  ← CANONICAL PHYSICAL CAMERA
               │
               ▼
    OPERATOR PERFORMANCE              ← DERIVED PERFORMANCE
               │
               ▼
      FRAME COMPOSITION               ← DERIVED
               │
               ▼
    VIEW PRESENTATION / GRANI         ← DERIVED PRESENTATION
               │
               ▼
        PERCEIVED FRAME               ← DERIVED OUTPUT
```

Primary authority law:

```text
AUTHORITY FLOWS DOWNSTREAM.
DERIVED DATA NEVER WRITES BACK INTO AUTHORITY.
```

Forbidden reverse promotions include:

```text
OxiHuman params        ✗→ CHARACTER_DNA
compiled mesh          ✗→ CHARACTER_DNA
donor skeleton         ✗→ REST_RIG
animation clip         ✗→ MOTION TRUTH
pose snapshot          ✗→ ACTION TRUTH
camera framing         ✗→ ACTION TRUTH
operator shake         ✗→ CAMERA TRUTH
GRANI perceived frame  ✗→ PHYSICAL CAMERA
rendered image         ✗→ BODY / MOTION / ACTION truth
```

### 2.1 Proof-contract promotions

Only conclusions proven by the completed feasibility stages are promoted.

**O0**
```text
DNA measurements
→ derived solver parameters
→ generated geometry
→ independent re-measurement
→ residual/error
```
OxiHuman remains a narrow, replaceable backend/donor candidate and never becomes ZB authority.

**B0**
```text
COMPILED BODY MESH
→ export/runtime representation
→ Babylon
```
Babylon may consume derived body output but does not become Body Truth authority.

**M0**
```text
BODY TRUTH + SPACE TRUTH + MOTION TRUTH = ACTION TRUTH
POSE IS NOT MOTION.
MOTION DNA MUST NOT MUTATE BODY DNA.
```

**C1**
```text
ACTION TRUTH
→ SHOT INTENT
→ CAMERA TRUTH
→ OPERATOR PERFORMANCE
```
Camera/operator/diagnostics remain downstream of Action Truth. Diagnostics are read-only.

**GRANI**
```text
PHYSICAL CAMERA
→ PRESENTATION / GRANI
→ PERCEIVED FRAME
```
Perceived Frame may intentionally disagree with Physical Camera, but canonical Physical Camera remains recoverable and presentation cannot write upstream.

### 2.2 Runtime packet classes

Initial versioned packet family:

```text
BODY_TRUTH_V1
SPACE_TRUTH_V1
MOTION_TRUTH_V1
ACTION_TRUTH_V1
SHOT_INTENT_V1
CAMERA_TRUTH_V1
OPERATOR_PERFORMANCE_V1
PRESENTATION_INTENT_V1
PERCEIVED_FRAME_META_V1
```

Shared foundational types:

```text
SOURCE_BINDING_V1
PROVENANCE_V1
UNRESOLVED_VALUE_V1
CANONICAL_HASH_V1
CONTRACT_HEADER_V1
```

Minimum packet header:

```text
schemaId
schemaVersion
authorityClass
writebackPolicy
producer
producerVersion
sourceBindings[]
createdFrom[]
canonicalHash
unresolvedFields[]
contractBundleSha256
```

Authority classes:

```text
AUTHORITATIVE
CANONICAL_RUNTIME
AUTHORED_INTENT
DERIVED
PRESENTATION_ONLY
```

Writeback policies:

```text
IMMUTABLE
DERIVE_ONLY
AUTHOR_EDITABLE
PRESENTATION_ONLY
```

### 2.3 UNRESOLVED law

```text
UNRESOLVED
≠ DEFAULT
≠ ESTIMATE
≠ PREVIEW
≠ TRUTH
```

Preview metadata may exist:

```text
status: UNRESOLVED
previewValue: optional
plausibleRange: optional
sourceEvidence: optional
```

But authority-critical production output with unresolved values must either:

```text
BLOCK
```

or be explicitly classified:

```text
NON_CANONICAL_PREVIEW
```

No implicit promotion is permitted.

---

## 3. ZB Production Runtime boundary

The production runtime is a separate execution-plane codebase/repository. The exact repository name/location is intentionally unresolved until runtime bootstrap.

Logical module direction:

```text
zb-runtime/
├─ core/
│  ├─ authority-contracts/
│  ├─ anthropometry/
│  ├─ body-compiler/
│  ├─ surface-contract/
│  ├─ kinematics/
│  └─ geometry-qc/
├─ motion/
│  ├─ motion-dna/
│  ├─ motion-truth/
│  └─ action-truth/
├─ cinematography/
│  ├─ shot-intent/
│  ├─ camera-truth/
│  ├─ operator-performance/
│  └─ diagnostics/
├─ presentation/
│  ├─ babylon-adapter/
│  ├─ grani/
│  └─ perceived-frame/
├─ contracts/
├─ tests/
└─ provenance/
```

These are logical boundaries and do not require immediate decomposition into many packages.

### 3.1 ZB CORE

ZB CORE owns canonical computation/validation such as:

```text
CHARACTER_DNA validation
REST_RIG contracts
anthropometry solving
body compilation
surface anchors
measurement / remeasurement
geometry QC

BODY TRUTH
SPACE TRUTH
MOTION TRUTH
ACTION TRUTH

canonical serialization / hashing
authority / writeback validation
```

Runtime adapters consume immutable/versioned packets from ZB CORE. They do not define upstream authority.

### 3.2 ZB CORE WASM

Architecture direction remains:

```text
ZB AUTHORITY
→ ZB CORE
→ ZB CORE WASM
→ CANONICAL / DERIVED PACKETS
→ BABYLON
→ PRESENTATION
```

WASM is an execution/transport form of core logic, not a new authority layer.

### 3.3 Babylon boundary

Babylon may:

```text
load derived mesh
skin mesh
evaluate runtime transforms
render scene
execute physical camera
provide frame timing
produce presentation buffers
```

Babylon may not:

```text
invent Character DNA
rewrite REST_RIG authority
promote morph/body parameters to truth
define Motion Truth from an animation clip
rewrite Action Truth because realization missed contact
rewrite Camera Truth because framing looked bad
write presentation distortion back into physical camera
```

### 3.4 Motion / Action boundary

`MOTION DNA` and `MOTION TRUTH` are separate.

Motion DNA describes character execution biases. Motion Truth describes a concrete time-dependent transfer of mass/support/momentum/contacts.

```text
BODY TRUTH
+ SPACE TRUTH
+ MOTION TRUTH
= ACTION TRUTH
```

Animation remains one realization of Action Truth, not Action Truth itself.

### 3.5 Cinematography boundary

```text
ACTION_TRUTH_V1
→ SHOT_INTENT_V1
→ CAMERA_TRUTH_V1
→ OPERATOR_PERFORMANCE_V1
```

Physical camera remains distinct from operator performance. Operator behavior must not silently become canonical physical camera truth.

### 3.6 Grani boundary

```text
CAMERA TRUTH
→ OPERATOR PERFORMANCE
→ FRAME COMPOSITION
→ VIEW PRESENTATION
→ GRANI
→ PERCEIVED FRAME
```

Presentation may intentionally distort perceived reality, but must leave canonical Body/Motion/Action/Camera truth accessible and unmodified.

---

## 4. Repository, release and provenance architecture

Runtime approval is based on immutable bindings, not branch names.

```text
runtimeRepo
runtimeCommit
runtimeRelease
runtimeArtifact
artifactSha256
contractVersion
contractBundleSha256
evidenceReport
evidenceReportSha256
dependencyManifestSha256
reviewVerdict
```

Hard law:

```text
BRANCH NAME IS NEVER AUTHORITY.
ONLY EXACT COMMIT + EXACT ARTIFACT / CONTRACT / EVIDENCE HASHES ARE AUTHORITATIVE BINDINGS.
```

### 4.1 Build is not approval

```text
RUNTIME COMMIT
→ CI BUILD
→ ARTIFACT
→ SELF TEST / QC REPORT
→ SUBMIT EVIDENCE TO HQ
→ INDEPENDENT REVIEW
→ HQ APPROVAL RECORD
```

Runtime CI may produce evidence. It may not declare itself approved.

### 4.2 Build evidence pack

Required candidate format:

```text
ZB_RUNTIME_EVIDENCE_V1
```

Minimum content:

```text
runtimeRepo
runtimeCommit
sourceTreeSha
contractVersions
contractBundleSha256

toolchain pins
dependency manifest hash

testResults
contractTests
authorityBoundaryTests
determinismTests

buildArtifacts[]
artifactSha256[]

knownLimitations[]
unresolvedFields[]

producerIdentity
createdAt
```

The report itself receives an immutable `evidenceReportSha256`.

### 4.3 Release binding

```text
RELEASE_BINDING_V1

releaseName
runtimeCommit
artifactSha256
evidenceReportSha256
contractBundleSha256
```

A release candidate is the exact combination of code, binaries, contracts and evidence.

### 4.4 Contract bundle

P1 must produce:

```text
ZB_CONTRACT_BUNDLE_V1
```

containing all schemas, authority/writeback enums, canonical serialization rules, hash rules, UNRESOLVED rules, source-binding rules, provenance rules and dependency-direction rules.

Compatibility requires both:

```text
schemaVersion match
+
contractBundleSha256 match
```

### 4.5 Dependency provenance

Production candidates prohibit floating dependencies:

```text
NO FLOATING DEPENDENCIES
```

Disallowed as production proof bindings:

```text
latest
*
main
master
HEAD
unbounded compatible ranges
```

Each external dependency must record exact version/revision, repository/source, license, selected packages/files and hashes.

### 4.6 Approval and activation are separate

```text
RUNTIME_APPROVED
≠ RUNTIME_ACTIVATED
```

`RUNTIME_APPROVED` records a technically and architecturally accepted exact candidate. Activation is a separate OWNER decision.

---

## 5. Governance and production integration state machine

Role separation:

```text
LESTER = builder / implementation
DUNCAN = independent QC / production lead
DJANGO = architecture authority
OWNER = production activation / OWNER LOCK authority
```

Hard law:

```text
BUILD AUTHORITY
≠ QC AUTHORITY
≠ ARCHITECTURE AUTHORITY
≠ PRODUCTION ACTIVATION AUTHORITY
```

Canonical governance sequence:

```text
INTEGRATION_ARCHITECTURE_DRAFT
        ↓
DJANGO / ARCHITECTURE_ACCEPTED
        ↓
P1_IMPLEMENTATION_CANDIDATE
        ↓
DUNCAN / QC_PASS
        ↓
DJANGO / RUNTIME_ARCHITECTURE_ACCEPTED
        ↓
RUNTIME_APPROVED
        ↓
OWNER DECISION
        ↓
RUNTIME_ACTIVATED
```

Architecture acceptance only authorizes creation of a P1 candidate. It does not authorize runtime approval, activation, OWNER LOCK, G2 or Voice-to-Shot.

### 5.1 Builder authority

Lester may assert only:

```text
BUILT
TESTED
ARTIFACT PRODUCED
EVIDENCE PRODUCED
```

Lester may not create QC, architecture, runtime-approval, activation or OWNER-lock verdicts.

### 5.2 Duncan QC authority

Duncan independently verifies exact SHA/hash bindings, contract tests, authority/writeback protection, UNRESOLVED behavior, provenance, negative tests and HQ/runtime separation.

Outcome:

```text
QC_PASS
```

or:

```text
QC_CHANGES_REQUIRED
```

QC_PASS does not activate runtime.

### 5.3 Django runtime architecture authority

After QC_PASS, Django reviews the exact implementation candidate against the accepted architecture contract.

Outcome:

```text
ACCEPTED
```

or:

```text
CHANGES_REQUIRED
```

The review must bind the exact runtime commit plus artifact/evidence/contract bundle hashes.

### 5.4 Runtime approval

Only the combination:

```text
BUILD CANDIDATE
+ QC_PASS
+ DJANGO ACCEPTED
```

permits an exact candidate to become `RUNTIME_APPROVED`.

### 5.5 OWNER activation and OWNER LOCK

Only `Sparx-Owner-ZB` may decide:

```text
RUNTIME_APPROVED
→ RUNTIME_ACTIVATED
```

or HOLD/rollback policy.

OWNER LOCK remains a separate optional action and is never implied by activation.

### 5.6 Rollback

Rollback changes the active immutable release binding to a previously approved immutable release. It is never a fuzzy pointer such as `latest-good`.

### 5.7 Forbidden governance transitions

Machine validation must reject, among others:

```text
LESTER → QC_PASS
LESTER → ARCHITECTURE_ACCEPTED
DUNCAN → ARCHITECTURE_ACCEPTED
DJANGO → OWNER_LOCK
DJANGO → RUNTIME_ACTIVATED
RUNTIME CI → RUNTIME_APPROVED
RUNTIME CI → HQ state mutation
QC_PASS → automatic activation
ARCHITECTURE_ACCEPTED → automatic activation
RUNTIME_APPROVED → automatic OWNER_LOCK
```

Authenticated GitHub identity must match the actor allowed for the transition. No actor impersonation is permitted.

---

## 6. P1 — Runtime Contract Foundation

P1 is the first production implementation wave.

P1 explicitly does **not** build a character renderer, body engine, animation system, Babylon scene or Grani effect stack.

Purpose:

```text
DOWNSTREAM MAY READ UPSTREAM.
DOWNSTREAM MAY DERIVE FROM UPSTREAM.
DOWNSTREAM MAY NOT SILENTLY MUTATE UPSTREAM.
```

### 6.1 Required P1 schemas and shared types

Required schemas:

```text
BODY_TRUTH_V1
SPACE_TRUTH_V1
MOTION_TRUTH_V1
ACTION_TRUTH_V1
SHOT_INTENT_V1
CAMERA_TRUTH_V1
OPERATOR_PERFORMANCE_V1
PRESENTATION_INTENT_V1
PERCEIVED_FRAME_META_V1
```

Required shared types:

```text
SOURCE_BINDING_V1
PROVENANCE_V1
UNRESOLVED_VALUE_V1
CANONICAL_HASH_V1
CONTRACT_HEADER_V1
```

### 6.2 Canonical serialization and hashing

P1 defines one deterministic canonical representation with stable:

```text
field ordering
array semantics
numeric representation
null / absent semantics
enum normalization
identifier normalization
```

Hash algorithm:

```text
SHA-256
```

Distinct digest classes must be maintained for packets, contract bundles, artifacts, dependency manifests and evidence reports.

### 6.3 Source bindings and stale derivation

Derived/canonical packets record upstream hashes through `createdFrom[]`.

Example:

```text
ACTION_TRUTH_V1
createdFrom:
  BODY_TRUTH:<sha>
  SPACE_TRUTH:<sha>
  MOTION_TRUTH:<sha>
```

If an upstream hash changes, downstream data becomes:

```text
STALE_DERIVATION
```

The runtime reports rebuild/review required. It must not silently regenerate authored downstream intent.

### 6.4 P1 provenance

Minimum candidate provenance:

```text
repo
commit
sourceTreeHash
toolchain pins
dependencyLockHash
contractBundleSha256
buildId
buildArtifactSha256
```

### 6.5 Dependency-direction enforcement

Architecture direction:

```text
authority
   ↓
body
   ↓
motion / action
   ↓
camera
   ↓
presentation
```

CI must reject prohibited upstream dependency/mutation paths.

### 6.6 Required negative tests

At minimum:

```text
presentation tries to modify CAMERA_TRUTH
→ FAIL

camera tries to modify ACTION_TRUTH
→ FAIL

motion tries to modify Body authority
→ FAIL

derived body params try to overwrite CHARACTER_DNA
→ FAIL

previewValue tries to become canonical without explicit promotion
→ FAIL

packet uses wrong contractBundleSha256
→ FAIL

sourceBinding references missing/invalid source
→ FAIL

derived packet references stale upstream
→ STALE / BLOCK

unknown authorityClass
→ FAIL
```

### 6.7 Determinism

Repeated execution with identical canonical input must produce identical canonical bytes/hashes under the supported reference toolchain.

### 6.8 Minimum P1 modules

Initial codebase only needs the logical equivalent of:

```text
contracts/
canonical/
authority/
provenance/
validation/
tests/
```

P1 excludes body mesh generation, Babylon rendering, animation playback, camera rendering and Grani effects.

### 6.9 Lester P1 deliverables

Minimum immutable candidate bundle:

```text
runtime repo
runtime commit
source tree hash

ZB_CONTRACT_BUNDLE_V1
contractBundleSha256

P1 runtime/library artifact
artifactSha256

dependency/provenance manifest
dependencyManifestSha256

automated tests
test report

ZB_RUNTIME_EVIDENCE_V1
evidenceReportSha256
```

### 6.10 P1 CI gates

All must pass:

```text
SCHEMA_VALIDATION
CANONICAL_SERIALIZATION
HASH_DETERMINISM
AUTHORITY_BOUNDARY
WRITEBACK_NEGATIVE_TESTS
UNRESOLVED_POLICY
SOURCE_BINDINGS
STALE_DERIVATION
DEPENDENCY_DIRECTION
PROVENANCE_COMPLETE
```

Any failed gate invalidates the P1 implementation candidate.

### 6.11 P1 PASS / FAIL

PASS requires proof that:

```text
VERSIONED CONTRACTS EXIST
CANONICAL HASHING IS DETERMINISTIC
PROVENANCE IS COMPLETE
UNRESOLVED IS SAFE
DEPENDENCY DIRECTION IS ENFORCED
DOWNSTREAM WRITEBACK IS BLOCKED
EVIDENCE IS IMMUTABLY BOUND
```

FAIL if any derived/presentation layer can mutate upstream authority, if UNRESOLVED silently promotes, hashes are non-deterministic, dependencies float, runtime can self-approve or runtime CI can mutate HQ governance state.

### 6.12 Explicit P1 non-goals

P1 does not resolve or authorize:

```text
full Character DNA field design
real production Zorr measurements
full REST_RIG format
surface topology implementation
OxiHuman production adoption
Babylon production adoption
motion solver
animation generation
camera solver
Grani renderer
coordinate-system lock
G2
Voice-to-Shot
OWNER LOCK
production activation
```

---

## 7. Rollout and post-architecture sequence

After this architecture candidate is accepted, rollout remains explicitly staged.

### 7.1 Docs-only architecture candidate

This exact document is the architecture candidate.

Allowed scope:

```text
docs/ZB_PRODUCTION_INTEGRATION_ARCHITECTURE_R01.md
```

Forbidden scope in this architecture PR:

```text
hq/state/**
schemas/**
scripts/**
tests/**
runtime implementation
workflow enabling production
OWNER LOCK
G2
VOICE_TO_SHOT
```

### 7.2 Django architecture gate

Django must review:

```text
exact architecture head SHA
exact document hash/bytes
protected base SHA
```

against the entire Section 1–7 contract.

Architecture acceptance records architecture approval only.

### 7.3 Merge architecture docs only

After Django ACCEPTED, only the docs architecture PR may be merged.

That records the production-integration architecture but leaves runtime unbuilt/unapproved/inactive.

### 7.4 Runtime bootstrap

Only after architecture is recorded may a separate explicit transition authorize:

```text
P1 RUNTIME BOOTSTRAP START
```

Bootstrap resolves the exact execution-plane repository and creates only the minimal P1 foundation.

### 7.5 Lester P1 build

Separate transition:

```text
P1 IMPLEMENTATION START
```

Lester builds the exact P1 contract foundation and returns immutable candidate evidence.

### 7.6 Duncan QC

Separate transition:

```text
P1 QC START
```

Duncan independently validates the P1 candidate and may produce only QC_PASS or changes required.

### 7.7 Django implementation review

After QC_PASS, Django compares the actual P1 candidate against this accepted architecture contract.

Only Django ACCEPTED permits creation of an exact `RUNTIME_APPROVED` candidate record.

### 7.8 OWNER boundary

OWNER may HOLD or ACTIVATE an approved runtime binding. OWNER LOCK remains a separate optional authenticated action.

### 7.9 Later waves

After an approved P1 foundation, later engineering waves remain separately authorized:

```text
P2 — BODY COMPILER
P3 — MOTION / ACTION
P4 — CINEMATOGRAPHY
P5 — BABYLON RUNTIME
P6 — GRANI PRESENTATION
```

Each repeats:

```text
DESIGN / SCOPE
→ BUILD
→ EVIDENCE
→ DUNCAN QC
→ DJANGO ARCHITECTURE REVIEW
→ APPROVED CANDIDATE
```

No stage implicitly authorizes its successor.

G2 and Voice-to-Shot remain outside this architecture rollout and require independent future gates.

---

## 8. Proof provenance bindings

The following completed proofs inform this architecture. Their experimental code is not promoted into production.

### O0 — OxiHuman donor/body feasibility

- accepted O0 branch head: `b6729f21c83f79e655f84265d23773f28a8da9d4`
- exact donor repo: `cool-japan/oxihuman`
- version: `v0.2.1`
- revision: `603b446854c3d5a9ca478214e7b85008d54786b9`
- core pack: `assets/packs/oxihuman-core-v1.ohpk`
- core pack SHA-256: `09c4bb1f849fe5d2bc21db6dd8a8bf7c753ee58db185bc46ab4c6b8e0dc0f6f7`

Conclusion promoted: donor/backend feasibility and fit→remeasure loop only; donor parameters/skeleton do not become ZB authority.

### B0 — Babylon body compiler boundary

- proof head: `117395e3974f2ccf835f19749823d92bea263aef`
- exact Babylon packages: `@babylonjs/core@9.22.2`, `@babylonjs/loaders@9.22.2`
- GLB SHA-256: `626be02ae16ddf2bfd8760633761489a3c24f5b35d1e5b3f4a0c9a602cbffaf0`
- evidence artifact ZIP SHA-256: `6e2c4a0d6d3fb09aac87f54a2f942eb3b6335404856a1891ff2e2355184ebd81`

Conclusion promoted: derived compiled body can cross into Babylon runtime without transferring body authority.

### M0 — Motion Truth / Action Truth boundary

- proof head: `10b44d975b01b22735529eebad603fb8f08e708b`
- evidence report SHA-256: `5a18cf1b83093d50f6ed024621dc457a0a3b924b274ce2114418951bcdd2eb87`
- evidence artifact ZIP SHA-256: `7dbba4f61bdf426c525b8f8c6a530920eb762e142f641f08d9a24d0e02afb76d`

Conclusion promoted: pose is not motion; Motion Truth is time-dependent; Motion DNA cannot mutate Body DNA; Action Truth derives from Body + Space + Motion Truth.

### C1 — Cinematography interpretation boundary

- proof head: `85d22b30769afe88a6c8a88bccb37db791a55b45`
- evidence report SHA-256: `5b960db8a7ebf4ed3b82919feb51344eacb44e0b8f8d2db7a035e85bd72fe482`
- evidence artifact ZIP SHA-256: `e4731b6bee4da9ef16c98ea0cbff4ceb1f67276e0a5b0d621875d4c96010d9c8`

Conclusion promoted: the same immutable Action Truth permits distinct camera interpretations; Camera Truth, Operator Performance and diagnostics do not mutate Action Truth; diagnostics are read-only.

### GRANI — Presentation Truth boundary

- proof head: `fedb172f9a12f8bb29b34d019e31a81b6b972536`
- evidence report SHA-256: `5470be4572fa6a0a9af6647e48cbeefdaf03713896e28b9a7ce15815869f3658`
- evidence artifact ZIP SHA-256: `dd292fb37beb183a3772b3352bb0bda319f047680168d969eab5fcd086b4d5ad`

Conclusion promoted: downstream perceived frame may intentionally disagree with physical camera while canonical Body/Motion/Action/Physical Camera remain unchanged and recoverable.

---

## 9. Architecture review target

The architecture reviewer must determine whether this R01 contract:

1. preserves Shared HQ as control/authority/evidence plane and keeps runtime as a separate execution plane;
2. preserves the authority graph and all no-writeback laws;
3. keeps ZB CORE upstream of Babylon and presentation;
4. keeps Motion/Action, Camera and Grani boundaries consistent with accepted proof evidence;
5. provides immutable repository/release/provenance bindings;
6. prevents runtime self-approval;
7. preserves independent Lester/Duncan/Django/OWNER responsibilities;
8. limits P1 to contract foundation only;
9. keeps coordinate lock, OWNER LOCK, G2 and Voice-to-Shot unauthorized;
10. defines a safe staged rollout into P1 and later P2–P6 waves.

Allowed verdicts for the exact architecture candidate:

```text
ACCEPTED
CHANGES_REQUIRED
```

Acceptance records architecture approval only. It does not itself bootstrap the runtime repository, authorize P1 implementation, activate production, create OWNER LOCK, unlock G2, or unlock Voice-to-Shot.

---

## 10. Governing laws

```text
PROOF CODE IS NOT PRODUCTION CODE.

AUTHORITY FLOWS DOWNSTREAM.
DERIVED DATA NEVER SILENTLY WRITES UPSTREAM.

HQ CAN AUTHORIZE / VERIFY RUNTIME.
RUNTIME CANNOT REDEFINE HQ AUTHORITY.

A RUNTIME MAY PRODUCE EVIDENCE.
IT MAY NOT APPROVE ITSELF.

BUILD AUTHORITY
≠ QC AUTHORITY
≠ ARCHITECTURE AUTHORITY
≠ PRODUCTION ACTIVATION AUTHORITY.

NO STAGE AUTHORIZES THE NEXT GOVERNANCE STAGE IMPLICITLY.

UNRESOLVED STAYS UNRESOLVED UNTIL AN EXPLICIT AUTHORIZED PROMOTION.

PHYSICAL CAMERA REMAINS RECOVERABLE WHEN PRESENTATION / GRANI DISAGREES.

OWNER LOCK IS NEVER IMPLIED.
G2 IS NOT AUTHORIZED.
VOICE-TO-SHOT IS NOT AUTHORIZED.
```
