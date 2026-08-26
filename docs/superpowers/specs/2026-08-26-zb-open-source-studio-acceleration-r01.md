# ZORR BLATT — Open-Source Studio Acceleration R01

Status: **ARCHITECTURE STUDY CANDIDATE / STUDY ONLY / NO ADOPTION AUTHORIZATION**

Authority repository: `Lester-Sparx/zorr-blatt-shared-hq`

Study base commit: `85a101853b46b82b91b57739cac62b9933e0e355`

This study identifies open-source software and production-tested workflows that can shorten the path from the current ZORR BLATT architecture to a practical production studio without surrendering ZB authority to third-party tools.

This document does **not** adopt any dependency, create any external service, modify `hq/state`, create the production runtime, start P1 implementation, create OWNER LOCK, unlock G2 or Voice-to-Shot, or activate production. Every actual probe/adoption remains a separate future gate with exact version/revision/license/provenance bindings.

---

## 1. Governing engineering law — REUSE FIRST

ZORR BLATT must not rebuild generic technology that already exists in a suitable, maintainable, legally usable and integration-safe open-source form.

Hard law:

```text
REUSE OPEN SOURCE WHEN IT IS FIT-FOR-PURPOSE.

IF EXISTING CODE CAN SOLVE THE PROBLEM SAFELY AND CLEANLY,
WE DO NOT REBUILD IT FROM ZERO.

CUSTOM CODE IS RESERVED FOR:
ZB-SPECIFIC AUTHORITY,
ZB-SPECIFIC TRUTH,
ZB-SPECIFIC INTEGRATION,
OR GAPS THAT EXISTING TOOLS CANNOT SATISFY.
```

Decision sequence for generic engineering work:

```text
1. SEARCH EXISTING PRODUCTION-TESTED OPEN SOURCE.
2. VERIFY FIT / LICENSE / MAINTENANCE / INTEGRATION BOUNDARY.
3. ADOPT OR ADAPT IF SUITABLE.
4. RUN A NARROW PROBE IF FIT IS UNCERTAIN.
5. WRITE CUSTOM CODE ONLY IF A REAL GAP REMAINS.
```

The burden of proof is therefore reversed:

```text
GENERIC SUBSYSTEM
→ DEFAULT = REUSE / ADAPT
→ CUSTOM BUILD REQUIRES A DOCUMENTED GAP
```

This law accelerates delivery without weakening ZB authority because external tools remain replaceable and bounded.

---

## 2. Executive decision

ZORR BLATT should **not build a studio pipeline from scratch**.

The fastest safe strategy is:

```text
BUILD CUSTOM
= only the ZB-specific truth/authority/runtime layers

ADOPT / ADAPT OPEN SOURCE
= production tracking
  DCC authoring
  shot assembly
  asset publishing workflow
  editorial interchange
  render-farm management
  review/playback
  image/color infrastructure
  runtime asset optimization/validation
  optional motion-evidence acquisition
```

The strongest production reference is the Blender Studio pipeline: a Blender-centric, production-tested FOSS workflow built around Blender, Kitsu, Shot Builder/Asset Pipeline, centralized review, versioned production files and Flamenco rendering.

ZB must copy **workflow contracts and narrow components**, not blindly copy Blender Studio infrastructure assumptions such as SVN-only topology or a homogeneous workstation fleet.

---

## 3. Non-negotiable ZB authority boundary

Accepted ZB authority remains unchanged:

```text
REFERENCE EVIDENCE
→ CHARACTER_DNA
→ REST_RIG + SURFACE CONTRACT
→ BODY COMPILER
→ BODY_TRUTH
→ SPACE_TRUTH + MOTION DNA
→ MOTION_TRUTH
→ ACTION_TRUTH
→ SHOT_INTENT
→ CAMERA_TRUTH
→ OPERATOR_PERFORMANCE
→ FRAME COMPOSITION
→ GRANI / PRESENTATION
→ PERCEIVED_FRAME
```

Hard laws:

```text
AUTHORITY FLOWS DOWNSTREAM.
DERIVED DATA NEVER WRITES BACK INTO AUTHORITY.

SHARED HQ = CONTROL / AUTHORITY / EVIDENCE PLANE.
ZB RUNTIME = EXECUTION PLANE.

EXTERNAL STUDIO TOOL ≠ ZB AUTHORITY.
EXTERNAL EVENT ≠ GOVERNANCE VERDICT.
EXTERNAL PUBLISH ≠ RUNTIME APPROVAL.
```

Therefore:

- Kitsu task status is production-operations state, not ZB governance acceptance.
- Blender object/rig state is authoring data, not `CHARACTER_DNA` or `REST_RIG` authority.
- a Blender/Kitsu “Published” asset is a studio publish, not automatically canonical ZB runtime truth.
- mocap/keypoints are evidence inputs, not `MOTION_TRUTH`.
- OTIO is editorial interchange, not `ACTION_TRUTH` or `CAMERA_TRUTH`.
- glTF/GLB is delivery/runtime representation, not body authority.
- render output/review approval does not write back into Body/Motion/Action/Camera truth.

---

## 4. Evaluation vocabulary

Every candidate is classified as one of:

```text
ADOPT
= use substantially as provided behind a controlled external boundary

ADAPT
= reuse workflow/component but create a thin ZB integration adapter

PROBE
= run a narrow throwaway feasibility/integration proof before adoption

WATCH
= technically relevant, but not yet justified by scale/complexity

DEFER
= useful later; explicitly excluded from Studio v1 path

REJECT-AS-BACKBONE
= may contain useful ideas/components, but must not become ZB's central pipeline authority
```

No classification is itself adoption authorization.

---

## 5. Target studio topology

Recommended long-term topology:

```text
                         ZORR BLATT SHARED HQ
                  CONTROL / AUTHORITY / EVIDENCE
                    CHECKPOINT / HANDOFF / SIGNAL
                                │
                                │ explicit adapters/events
                                ▼
                     COMMS / STUDIO ORCHESTRATION
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
      PRODUCTION OPS       AUTHORING DCC       ZB RUNTIME
        Kitsu/Zou             Blender           Rust/WASM
              │                 │                 │
              │          Shot/Asset tools         │
              │                 │                 │
              └──────────┬──────┴──────┬──────────┘
                         ▼             ▼
                      EDITORIAL      DELIVERY
                        OTIO       glTF/GLB tools
                         │             │
                         ▼             ▼
                     RENDER/REVIEW / PRESENTATION
                   Flamenco · OCIO/OIIO · review tools
```

Boundary rule:

```text
STUDIO OPERATIONS MAY ROUTE WORK.
STUDIO OPERATIONS MAY NOT AUTHORIZE ZB TRUTH.
```

---

## 6. Candidate matrix

| Candidate | R01 decision | Earliest useful stage | Studio role | ZB authority rule |
|---|---|---|---|---|
| Blender | ADOPT as primary DCC | Studio authoring foundation | modeling/rigging/layout/animation/lighting/render authoring | never canonical authority by itself |
| Blender Studio Pipeline concepts | ADAPT | Studio foundation | project layout, shot/asset/review workflow | workflow only |
| Kitsu + Zou | ADOPT CANDIDATE after PROBE | Studio operations foundation | projects/assets/shots/tasks/reviews/statuses | operations state only |
| Blender Kitsu / Shot Builder | PROBE → ADAPT | shot production / P4-adjacent | automatic shot files/casting/editorial refs/hooks | consumes ZB-safe bindings; no truth promotion |
| Blender Asset Pipeline | PROBE → ADAPT | asset authoring / P2-adjacent | multi-artist asset task layers/publishing | published asset ≠ canonical runtime truth |
| Git LFS | PROBE first | production binary storage | Git-centric large file versioning | storage/versioning only |
| Apache Subversion | ALTERNATE PROBE | if Git LFS becomes operationally weak | large binary production version control | storage/versioning only |
| Flamenco | ADOPT LATER | render operations | Blender render-farm manager/workers | renders are derived outputs |
| OpenTimelineIO | ADOPT LATER | editorial / P4-adjacent | editorial interchange | edit does not mutate Action/Camera truth |
| OpenColorIO | ADOPT LATER | render/review | color management / ACES-capable config | presentation/color only |
| OpenImageIO | ADOPT LATER | render/image pipeline | image I/O/cache/processing infrastructure | image data downstream |
| glTF Transform | ADOPT at P5 boundary | P5 Babylon delivery | GLB/glTF optimization | derived delivery only |
| Khronos glTF Validator | ADOPT at P5 boundary | P5 Babylon delivery | standards validation/report | validation only |
| OxiHuman | existing PROBE/ADAPT candidate | P2 | body donor/backend | never `CHARACTER_DNA`/`REST_RIG` authority |
| FreeMoCap | PROBE | P3 | markerless motion evidence | evidence only |
| MMPose | PROBE | P3 | keypoint/pose evidence | evidence only |
| xSTUDIO or OpenRV | WATCH/PROBE ONE | review scale-up | professional playback/dailies | review UI only |
| OpenAssetIO | WATCH → PROBE | multi-tool/asset scale-up | asset identity integration bridge | does not define ZB asset authority |
| Rez | WATCH → PROBE | multi-workstation deployment | reproducible DCC environments | workstation/package environment only |
| OpenUSD | DEFER | multi-DCC / large scene scale | scene composition/interchange | not REST_RIG or ZB truth |
| MaterialX | DEFER | multi-DCC lookdev scale | material/look interchange | surface presentation transport only |
| OpenCue | DEFER | farm outgrows Flamenco | large-scale render scheduling | derived render operations |
| AYON | REJECT-AS-BACKBONE | — | broad pipeline framework | would duplicate ZB/Kitsu orchestration center |
| Prism Pipeline | REJECT-AS-BACKBONE | — | broad pipeline framework | same duplication risk |

---

## 7. Blender Studio Pipeline — strongest workflow donor

### 7.1 Why it matters

Blender Studio documents its current pipeline as production-tested and entirely based on Free/Open Source software. Its design targets a small production unit, roughly 10–20 people, with editorial-centric planning, centralized review/approval, version-controlled production files and Blender as the primary content-creation application.

This scale is close to the kind of lean studio ZB should optimize for before considering enterprise-scale infrastructure.

### 7.2 What to reuse

Reuse/adapt these workflow ideas:

```text
PROJECT TEMPLATE
ASSET CREATION / TASK LAYERS
ASSET CASTING TO SHOTS
SHOT BUILDER
EDITORIAL REFERENCE IN SHOTS
TASK-SPECIFIC SHOT FILES
PLAYBLAST / PREVIEW
CENTRAL REVIEW
RENDER FARM
APPROVED FRAMES → EDIT
```

### 7.3 What not to copy blindly

Blender Studio currently describes infrastructure assumptions including shared storage, SVN, Kitsu and Flamenco, and similarly configured workstations.

ZB should not make these assumptions authoritative. In particular:

```text
Shared HQ stays GitHub/Git governance.
Runtime stays separate Rust-first repository.
Production binary storage gets its own decision/probe.
OS/workstation topology stays replaceable.
```

### 7.4 Decision

```text
BLENDER STUDIO PIPELINE
→ ADAPT WORKFLOW
→ PROBE SPECIFIC ADD-ONS
→ DO NOT ADOPT AS A MONOLITHIC AUTHORITY SYSTEM
```

Primary references:
- Blender Studio tools and pipeline documentation.
- Blender Studio design principles and technical/artist guides.

---

## 8. Kitsu + Zou — recommended production-operations plane

Kitsu is a collaboration/production-tracking system for animation/VFX and supports assets, shots, tasks, statuses, reviews, scheduling and production workflows. Self-hosted Kitsu uses Zou as its API/database layer and exposes API-oriented integration paths.

### 8.1 ZB role

Recommended division:

```text
SHARED HQ
= governance / authority / evidence / checkpoint

KITSU
= production entities / tasks / assignments / statuses / previews / reviews

ZB RUNTIME
= canonical computation / runtime truth execution
```

### 8.2 Orchestrator boundary

Future bridge:

```text
Kitsu/Zou event or API state
→ COMMS ORCHESTRATOR observes
→ creates/updates work routing or handoff candidate
→ authorized ZB actor performs required governance action
```

Forbidden:

```text
Kitsu status APPROVED
✗→ automatic QC_PASS
✗→ automatic Django ACCEPTED
✗→ automatic RUNTIME_APPROVED
✗→ OWNER activation
```

### 8.3 Deployment decision

Do not fork/vendor Kitsu/Zou code into ZB Runtime. Keep it an external service with API/event boundary. Before adoption, run a separate probe that proves:

```text
create project
create asset + shot
assign workflow
upload/review preview
read exact entity/task state by API
receive/observe change event
map external entity IDs into ZB source bindings
prove no automatic governance writeback
```

### 8.4 Decision

```text
KITSU/ZOU
→ ADOPT CANDIDATE
→ FIRST REQUIRE A SEPARATE STUDIO-OPS PROBE
```

---

## 9. Blender Kitsu / Shot Builder — highest direct acceleration

Shot Builder already automates a large amount of scene plumbing:

```text
read shot metadata from Kitsu
create shot file by task type
automatically name scenes
create task output collections
link output collections across task types
load editorial reference
load/cast assets
execute project-specific hooks
```

That means ZB should **not** build a generic shot-file generator from zero unless a probe proves Shot Builder cannot be adapted safely.

### ZB adapter target

A thin ZB hook/adapter should eventually be responsible for injecting only approved downstream bindings, for example:

```text
shot identity
asset identities
frame range / fps
SHOT_INTENT reference
CAMERA_TRUTH reference where appropriate
runtime/evidence bindings
```

The hook must not infer missing canonical values from Blender state.

Decision:

```text
BLENDER KITSU / SHOT BUILDER
→ PROBE EARLY IN STUDIO-OPS TRACK
→ ADAPT IF BOUNDARY TESTS PASS
```

---

## 10. Blender Asset Pipeline — useful authoring/publish layer

The Blender Studio Asset Pipeline supports simultaneous work on an asset through configurable task layers and ownership, then merges contributions into a published asset.

For ZB, this can accelerate:

```text
modeling
rig authoring
shading
asset assembly
artist ownership
published Blender asset creation
```

But terminology must remain explicit:

```text
BLENDER PUBLISHED ASSET
≠ CHARACTER_DNA
≠ REST_RIG authority
≠ BODY_TRUTH
≠ RUNTIME_APPROVED artifact
```

A ZB validation/publish adapter would later prove that a Blender-side asset corresponds to exact upstream ZB bindings.

Decision:

```text
BLENDER ASSET PIPELINE
→ PROBE / ADAPT
```

---

## 11. Production binary versioning — Git LFS first, SVN as fallback probe

Blender Studio recommends version control for production `.blend` files and documents SVN or Git LFS as practical options.

ZB should **not** put large production assets into Shared HQ.

Recommended study direction:

```text
SHARED HQ
= small governance/evidence records

RUNTIME REPO
= source code + compact test fixtures

PRODUCTION ASSET STORE / REPO
= separate future binding
```

Because the existing ZB engineering/governance workflow is GitHub-centric, the first storage probe should test Git LFS with representative `.blend`, image, audio and preview sizes.

PASS criteria should include:

```text
clone/fetch performance acceptable
artist checkout/publish workflow acceptable
large-file quota/cost understood
exact object identities recoverable
offline/local recovery documented
CI does not accidentally pull whole media history
```

If Git LFS fails operationally, evaluate SVN, which Blender Studio uses because it is robust for large binary production files.

Decision:

```text
GIT LFS → FIRST PROBE
SVN     → ALTERNATE PROBE IF NEEDED
```

---

## 12. Flamenco — do not build a render scheduler

Flamenco is Blender's cross-platform render-farm management system. Blender Studio uses it to distribute jobs across multiple machines/workstations and requires shared storage accessible by workers.

For a small/medium Blender-centric ZB studio, this eliminates the need to build:

```text
render queue
worker discovery/task execution
job state UI
basic distributed frame scheduling
```

ZB should keep render output classified as downstream derived evidence/output.

Decision:

```text
FLAMENCO
→ ADOPT LATER AS EXTERNAL RENDER OPERATIONS SERVICE
```

OpenCue should only be evaluated if real farm scale exceeds Flamenco's intended operating envelope.

---

## 13. OpenTimelineIO — standard editorial interchange

OpenTimelineIO is an API/interchange format for editorial cut information. It represents clips, timing, tracks, transitions, markers, metadata and external media references.

ZB should avoid inventing its own general-purpose edit timeline format.

Recommended boundary:

```text
SHOT OUTPUTS / PREVIEWS
→ OTIO editorial representation
→ Blender VSE / external editor adapters / review
```

OTIO remains editorial state. It does not become Action Truth or Camera Truth.

Decision:

```text
OTIO
→ ADOPT LATER FOR EDITORIAL INTERCHANGE
```

---

## 14. OpenColorIO + OpenImageIO — adopt when render/image pipeline begins

OpenColorIO is designed for motion-picture/VFX/animation color management and supports ACES-oriented workflows. OpenImageIO provides production-grade image I/O/cache/processing infrastructure.

Do not write custom equivalents.

Recommended later flow:

```text
render / EXR / textures
→ OpenImageIO-based processing where needed
→ OpenColorIO project color policy
→ review / comp / delivery
```

Decision:

```text
OCIO  → ADOPT LATER
OIIO  → ADOPT LATER
```

Exact versions/configuration are deferred to the render/presentation adoption gate.

---

## 15. glTF Transform + Khronos glTF Validator — P5 fast path

For Babylon delivery, ZB should use established glTF tooling rather than build generic optimizers/validators.

Target downstream chain:

```text
ZB DERIVED RUNTIME ASSET
→ GLB/glTF EXPORT
→ glTF Transform optimization
→ Khronos glTF Validator
→ immutable validation report
→ Babylon runtime consumption
```

Neither optimizer nor validator owns Body Truth.

Decision:

```text
glTF Transform          → ADOPT AT P5 DELIVERY BOUNDARY
Khronos glTF Validator  → ADOPT AT P5 VALIDATION BOUNDARY
```

Production adoption must pin exact package/revision and preserve pre/post hashes.

---

## 16. OxiHuman — keep existing narrow P2 role

O0 already proved OxiHuman's usefulness as a replaceable donor/backend candidate while preserving ZB authority.

No architecture change is required:

```text
CHARACTER_DNA
→ ZB anthropometry adapter/solver
→ OxiHuman donor/backend candidate
→ derived geometry
→ independent re-measurement/QC
```

Forbidden:

```text
OxiHuman parameters ✗→ CHARACTER_DNA authority
OxiHuman skeleton   ✗→ REST_RIG authority
```

Decision:

```text
OXIHUMAN
→ KEEP EXISTING PROBE/ADAPT STATUS FOR P2
```

Exact accepted O0 provenance remains recorded in the Integration Architecture.

---

## 17. FreeMoCap + MMPose — motion evidence, never motion truth

These tools can shorten motion acquisition/reconstruction work.

Potential evidence flow:

```text
video / multi-camera capture
→ FreeMoCap and/or MMPose observations
→ joints/keypoints/trajectories/confidence
→ ZB validation/kinematics/contact reasoning
→ MOTION_TRUTH candidate
```

Hard boundary:

```text
MOCAP OUTPUT ≠ MOTION_TRUTH
POSE KEYPOINTS ≠ MOTION_TRUTH
POSE IS NOT MOTION
```

The probe must measure whether they provide useful evidence for ZB mechanics such as support/contact trajectory and timing, rather than merely visually plausible pose sequences.

Decision:

```text
FreeMoCap → PROBE AS EXTERNAL MOTION EVIDENCE SOURCE
MMPose    → PROBE AS EXTERNAL KEYPOINT/POSE EVIDENCE SOURCE
```

Do not embed a copyleft external stack directly into the ZB Rust runtime; keep evidence acquisition behind a process/file/API boundary unless later license/technical review says otherwise.

---

## 18. Review — Kitsu/Blender first, xSTUDIO or OpenRV only when needed

Studio v1 should avoid installing overlapping review systems prematurely.

First line:

```text
Kitsu review/comments/statuses
+
Blender Kitsu Render Review
```

If production later requires stronger professional playback, frame comparison, high-end color-managed review or custom review integration, evaluate **one** of:

```text
xSTUDIO
OpenRV
```

Do not deploy both without a demonstrated gap.

Decision:

```text
xSTUDIO / OpenRV
→ WATCH
→ PROBE ONE ONLY IF BUILT-IN REVIEW IS INSUFFICIENT
```

---

## 19. OpenAssetIO — likely valuable after asset/tool scale increases

OpenAssetIO standardizes interaction between DCC/pipeline hosts and asset-management systems through entity references, resolution and publishing APIs. It is not itself a database, asset manager, pipeline framework or storage system.

This fits ZB conceptually because it can replace fragile raw-path coupling:

```text
entity identity
→ resolve current location/version/traits
→ tool consumes resolved data
```

However, introducing it before ZB has enough assets/tools would create unnecessary abstraction.

Decision:

```text
OPENASSETIO
→ WATCH NOW
→ PROBE WHEN MULTI-DCC / ASSET-SCALE PAIN APPEARS
```

---

## 20. Rez — workstation reproducibility candidate

As the studio gains multiple artists/machines and multiple Blender/tool versions, reproducible DCC environments become operationally important.

Rez can be evaluated for:

```text
Blender build selection
Python/plugin environment
pipeline tool versions
platform variants
reproducible workstation launches
```

It should not become a P1 runtime dependency; Rust runtime dependency/toolchain locking remains independent.

Decision:

```text
REZ
→ WATCH / PROBE DURING MULTI-WORKSTATION HARDENING
```

---

## 21. OpenUSD + MaterialX — deliberately defer

OpenUSD provides powerful scene composition/interchange; MaterialX provides portable material/look definitions. Both become attractive when ZB becomes multi-DCC or scene/look complexity demands them.

They are **not** necessary to prove P1–P5 foundations and can substantially increase pipeline complexity.

Important boundaries:

```text
USD scene graph ≠ ZB authority graph
USD skeleton/scene data ≠ REST_RIG authority
MaterialX material network ≠ canonical CHARACTER_DNA/BODY truth
```

Decision:

```text
OPENUSD   → DEFER FOR STUDIO v1
MATERIALX → DEFER FOR STUDIO v1
```

Re-evaluate when there is a concrete multi-DCC/interchange requirement.

---

## 22. OpenCue — defer until Flamenco is objectively insufficient

OpenCue targets large production render management and derives from Sony Pictures Imageworks infrastructure.

For early ZB Studio it would add deployment/operations complexity without demonstrated need.

Decision:

```text
OPEN CUE
→ DEFER
→ EVALUATE ONLY AFTER REAL FARM-SCALE EVIDENCE
```

---

## 23. AYON and Prism — do not create a second architecture center

AYON and Prism are broad pipeline frameworks with useful production features.

For a greenfield conventional studio, either could be a strong backbone candidate. ZB is no longer greenfield: it already has Shared HQ governance, immutable evidence/provenance laws, checkpoint/handoff rules and a separate Rust execution plane.

Making AYON or Prism the central production framework would risk creating two competing sources of pipeline semantics.

Decision:

```text
AYON  → REJECT-AS-BACKBONE FOR ZB STUDIO v1
PRISM → REJECT-AS-BACKBONE FOR ZB STUDIO v1
```

Individual ideas/integrations may still be studied later.

---

## 24. Recommended P1–P6 mapping

### P1 — Runtime Contract Foundation

Do **not** add studio systems as P1 runtime dependencies.

Allowed parallel architecture work only:

```text
Kitsu/Zou studio-ops probe design
Blender Shot Builder probe design
binary-storage probe design
```

P1 remains contracts/canonical hashing/authority/provenance/validation only.

### P2 — Body Compiler

```text
OxiHuman           → existing narrow donor/backend candidate
Blender            → authoring/inspection bridge only
Asset Pipeline     → optional asset-authoring probe
```

### P3 — Motion / Action

```text
FreeMoCap          → evidence probe
MMPose             → evidence probe
Blender animation  → realization/authoring, never truth
```

### P4 — Cinematography

```text
Shot Builder       → strong adapter candidate
Kitsu shot data    → production operations input
OTIO               → editorial interchange
Blender camera     → visualization/authoring consumer of CAMERA_TRUTH
```

### P5 — Babylon Runtime

```text
glTF Transform     → downstream optimization
Khronos Validator  → delivery validation
OpenAssetIO        → optional scale-driven probe
```

### P6 — Grani Presentation

```text
OCIO/OIIO          → render/image/color infrastructure as needed
review stack       → presentation review only
```

### Studio operations after/alongside technical waves

```text
Kitsu/Zou
Blender Kitsu
Asset Pipeline
Git LFS or SVN
Flamenco
OTIO
OCIO/OIIO
review tooling
```

Each introduction remains separately authorized.

---

## 25. Proposed independent Studio Operations track

To prevent studio plumbing from blocking or contaminating P1–P6, this study recommends a **parallel but governance-separated** track. These names are recommendations only and are not yet roadmap authorization.

```text
STUDIO-S0 — OPERATIONS FOUNDATION
  Kitsu/Zou probe
  production entity model mapping
  binary storage probe
  Blender project template probe

STUDIO-S1 — ASSET + SHOT FACTORY
  Blender Kitsu / Shot Builder
  Asset Pipeline
  ZB adapter hooks

STUDIO-S2 — EDIT / REVIEW / RENDER
  OTIO
  Flamenco
  Kitsu/Render Review
  OCIO/OIIO policy

STUDIO-S3 — WORKSTATION / ASSET SCALE
  Rez if needed
  OpenAssetIO if needed
  professional review tool if needed

STUDIO-S4 — SCALE HARDENING
  evaluate USD/MaterialX/OpenCue only from demonstrated production pain
```

Hard law:

```text
STUDIO-S* DOES NOT AUTHORIZE P*.
P* DOES NOT SILENTLY AUTHORIZE STUDIO-S*.
```

---

## 26. Fastest path to ZB Production Studio v1

Recommended sequence:

```text
1. Finish Checkpoint / Project Ledger Phase A and Phase B.
2. Resume and complete P1 Runtime Bootstrap under its existing gate.
3. Complete P1 Contract Foundation under separate P1 IMPLEMENTATION gate.
4. In parallel under a separate Studio-Ops authorization:
   - probe Kitsu/Zou
   - probe Blender Studio project/Shot Builder workflow
   - probe Git LFS with representative production binaries
5. P2: build ZB body authority/compiler; reuse OxiHuman only as backend candidate.
6. P3: build Motion/Action truth; probe mocap/keypoint tools only as evidence sources.
7. P4: connect Shot Intent/Camera Truth to Blender shot factory and OTIO editorial.
8. P5: connect validated derived GLB/glTF output to Babylon using established optimizer/validator tooling.
9. P6: Grani/presentation plus formal color/image/review pipeline.
10. Add Flamenco when render throughput requires distribution.
11. Harden multi-workstation tooling and asset identity only after real operational pressure appears.
```

The objective is not to install the maximum number of open-source packages. It is to remove generic engineering work while keeping the unique ZB authority stack small, testable and replaceable.

---

## 27. What ZB should still build itself

These remain core ZB intellectual/technical work:

```text
CHARACTER_DNA contracts and authority
character-specific REST_RIG authority
surface contract
anthropometry adapter/solver
body compiler / geometry QC
BODY_TRUTH
SPACE_TRUTH
MOTION_DNA
MOTION_TRUTH
ACTION_TRUTH
SHOT_INTENT
CAMERA_TRUTH
OPERATOR_PERFORMANCE boundary
GRANI / PERCEIVED FRAME boundary
authority/writeback enforcement
canonical serialization/hashing
source/provenance bindings
checkpoint/handoff/governance integration
ZB-specific canon validation
external-tool boundary adapters
```

Everything generic around those layers should have a strong presumption in favor of reuse rather than reinvention.

---

## 28. What ZB should explicitly avoid building from scratch

Unless a future proof shows the existing ecosystem is inadequate, do not build custom replacements for:

```text
production task tracker
basic review/comment system
generic shot-file assembler
generic Blender asset publish workflow
render queue / small render-farm scheduler
general editorial interchange format
general color-management engine
general image I/O/cache library
generic glTF optimizer
generic glTF standards validator
large-scale professional review player
basic mocap acquisition stack
basic pose/keypoint detector
```

---

## 29. License and process boundary rule

The study contains tools with different open-source license models, including permissive and copyleft licenses.

R01 architectural policy:

```text
THIRD-PARTY LICENSE MUST BE VERIFIED AT ADOPTION GATE.
EXACT VERSION/REVISION MUST BE PINNED AT ADOPTION GATE.
SELECTED FILES/PACKAGES AND HASHES MUST BE RECORDED.
```

Where a tool has strong copyleft obligations, default integration topology is:

```text
separate process/service/tool
↕ API / CLI / file interchange / event interface
ZB codebase
```

This is an engineering boundary policy, not legal advice. Distribution/deployment obligations must receive a separate license review before production release.

---

## 30. Adoption test template

Every future adoption/probe should answer:

```text
CANDIDATE
EXACT REPOSITORY
EXACT VERSION/TAG/COMMIT
LICENSE
MAINTENANCE STATUS
WHY REUSE IS BETTER THAN CUSTOM BUILD
ZB BOUNDARY
INPUTS
OUTPUTS
AUTHORITY CLASS
WRITEBACK POLICY
PROVENANCE BINDING
FAILURE MODES
REPLACEMENT PLAN
TEST/PROBE RESULT
```

Custom implementation requires an explicit additional field:

```text
DOCUMENTED GAP:
Why no suitable existing open-source solution can satisfy this requirement safely.
```

---

## 31. Acceptance criteria for this architecture study

The study is acceptable if it:

1. establishes REUSE-FIRST as the default engineering policy for generic subsystems;
2. identifies the major generic studio subsystems ZB can avoid rebuilding;
3. maps external tools to the existing P1–P6 architecture without transferring authority;
4. distinguishes ADOPT/ADAPT/PROBE/WATCH/DEFER/REJECT choices;
5. preserves Shared HQ as control/authority/evidence plane;
6. preserves Rust-first ZB Runtime as execution plane;
7. keeps Kitsu/Blender/mocap/editorial/render/review systems downstream or external to canonical authority;
8. avoids introducing a second pipeline authority center;
9. defers unnecessary enterprise-scale complexity;
10. requires exact dependency/license/provenance review at every real adoption gate;
11. provides a faster staged path to ZB Production Studio v1;
12. requires a documented gap before generic custom development is allowed.

---

## 32. Governing laws

```text
NO CHAT IS PROJECT MEMORY.

REUSE OPEN SOURCE WHEN IT IS FIT-FOR-PURPOSE.
DO NOT REBUILD GENERIC WORK WITHOUT A DOCUMENTED GAP.

BUILD THE ZB-SPECIFIC CORE.
REUSE THE GENERIC STUDIO PLUMBING.

EXTERNAL TOOL ≠ ZB AUTHORITY.
EXTERNAL EVENT ≠ GOVERNANCE VERDICT.

AUTHORITY FLOWS DOWNSTREAM.
DERIVED DATA NEVER WRITES BACK INTO AUTHORITY.

STUDIO-S* ≠ P* AUTHORIZATION.

NO FLOATING PRODUCTION DEPENDENCIES.
EVERY ADOPTION GETS EXACT VERSION / REVISION / LICENSE / HASH BINDINGS.

P1 RUNTIME BOOTSTRAP / P1 IMPLEMENTATION REMAIN SEPARATE GOVERNANCE GATES.
OWNER LOCK REMAINS SEPARATE.
G2 REMAINS LOCKED.
VOICE-TO-SHOT REMAINS LOCKED.
```
