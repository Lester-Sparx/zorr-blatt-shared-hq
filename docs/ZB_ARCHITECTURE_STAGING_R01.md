# ZORR BLATT — Architecture Staging R01

Status: **STAGING / DOCS ONLY**  
Source: GitHub issue #9 and its architecture delta inventory.  
Protected-base binding: `c5f9a039f75422dda5a2749548cba98b91460413`.

This document records architecture direction only. It does not change Control Tower runtime/state semantics, production data, ZB CORE, Babylon runtime, gates, review evidence, or OWNER LOCK state.

## Authority boundaries

```text
CHARACTER_DNA = anthropometric authority
CHARACTER-SPECIFIC REST_RIG = skeletal authority
BASE HUMAN / MORPH WEIGHTS / COMPILED BODY = derived
UNRESOLVED stays unresolved
coordinate policy stays OPEN
no OWNER LOCK
```

## Human body / compiler direction

```text
REFERENCE EVIDENCE
→ CHARACTER_DNA
→ CHARACTER-SPECIFIC REST_RIG
→ ZB ANTHROPOMETRY ADAPTER / SOLVER
→ HUMAN BODY TEMPLATE + AUTHORING SHAPE BASIS
→ COMPILED BODY MESH
→ RUNTIME SKIN + SMALL CORRECTIVE SET
→ CHARACTER SHELL
→ BABYLON / ZB PRESENTATION
```

The former primitive/capsule body remains deterministic debug/oracle geometry only, not the production-body direction.

Separate authoring fit from runtime deformation:

```text
AUTHORING SHAPE BASIS
→ solve / compile neutral body once
→ COMPILED BODY MESH
→ skeleton + small pose-corrective set at runtime
```

Morph/body parameters are derived and never become Character Truth.

## Anthropometry solver principle

```text
TARGET DNA MEASUREMENTS
→ solver
→ morph/body parameters
→ generated vertices
→ independent re-measure
→ residual/error
```

## OxiHuman donor/reference path

OxiHuman is a narrow, replaceable donor/backend candidate, not ZB authority.

Useful donor concepts:

```text
pinned CC0 body pack
+ sparse morph engine
+ measurement → fit → remeasure loop
+ WASM geometry bridge
+ provenance/hash discipline
```

Explicitly rejected as authority:

- donor body parameters as Character Truth;
- donor skeleton as skeletal truth;
- nearest-joint inverse-distance weights as production ZB skinning without independent evidence;
- the whole donor repository as a mandatory foundation before subset QC.

Pinned candidate recorded by issue #9:

```text
repo: cool-japan/oxihuman
tag: v0.2.1
commit: 603b446854c3d5a9ca478214e7b85008d54786b9
core pack: assets/packs/oxihuman-core-v1.ohpk
pack SHA-256: 09c4bb1f849fe5d2bc21db6dd8a8bf7c753ee58db185bc46ab4c6b8e0dc0f6f7
```

Any future production dependency/asset must pin exact repository, revision, license, selected files, hashes, and local derived hashes.

## Surface Contract

Introduce a semantic surface layer independent of raw vertex IDs. Prefer stable semantic/barycentric anchors over raw vertex identifiers.

Candidate anchors/regions:

```text
SCALP_FRONT / BACK
CLAVICLE_L/R
SHOULDER_SURFACE_L/R
STERNUM
WAIST_FRONT
HIP_SURFACE_L/R
WRIST_SURFACE_L/R
ANKLE_SURFACE_L/R
```

Expected future consumers include clothing, hair, markings, measurements, 2D↔3D calibration, and attachments.

## Unresolved data policy

Unknown values remain unknown. Optional hypothesis metadata may support preview without promoting estimates to truth:

```text
status: UNRESOLVED
plausibleRange: [min, max]
previewValue: ...
sourceEvidence: ...
```

`previewValue` is never Character Truth.

## Pose-corrective and topology direction

Do not assume skin weights alone preserve anatomy. A small runtime corrective set may later be evaluated. Candidate QC may compare LBS, DQS, LBS+DDM, LBS+PSD or other approaches. No production method is selected here.

Treat topology as a versioned interface:

```text
BODY_TOPOLOGY_VERSION
SURFACE_REGIONS_VERSION
SKIN_WEIGHTS_VERSION
```

Canonical/control topology remains authority for anchors and identity surface data. Subdivision and LOD geometry remain derived presentation geometry.

## Marking topology asset

Identity markings should be representable as semantic topology, not only a texture:

```text
MARKING TOPOLOGY ASSET
paths
junctions
branches
surface anchors
coverage regions
LOD rules
```

Rendering density may simplify; identity topology must not silently change.

## ZB Core WASM direction

```text
ZB AUTHORITY
→ ZB CORE WASM
   anthropometry
   measurements
   morph engine
   mesh compilation
   surface anchors
   kinematics math
   geometry QC
→ DERIVED TRUTH
→ BABYLON
→ PRESENTATION
```

Babylon remains scene/render/animation/camera/presentation runtime. This document does not authorize implementation or dependency adoption.

## Motion Truth / Action Truth

```text
BODY TRUTH
+ SPACE TRUTH
+ MOTION TRUTH
= ACTION TRUTH
```

Core laws:

```text
POSE IS NOT MOTION.
MOTION IS THE TRANSFER OF MASS, SUPPORT AND MOMENTUM THROUGH TIME.
ACTION IS NOT AN ANIMATION CLIP.
ANIMATION IS ONE REALIZATION OF ACTION TRUTH.
```

Candidate phases:

```text
PREPARE
LOAD
LAUNCH
AIR / TRANSFER
CONTACT
RECOVERY
```

## Character Motion DNA

Motion DNA is separate from body DNA and must never mutate body authority.

Hard rule:

```text
MOTION DNA MUST NOT MUTATE BODY DNA.
```

Candidate traits include posture, stride, COM height bias, load depth, rotation/counter-rotation bias, air compactness, landing softness, momentum retention, recovery style, head stability, reaction delay, weapon handling, support preference, stance width bias, torso/limb lead bias, flight extension, contact commitment, braking bias, and chain continuity.

## Landing as a mechanical event

```text
FIRST_CONTACT
→ LOAD_ACCEPTANCE
→ COM_DECELERATION
→ JOINT_COMPRESSION
→ TORSO_RESPONSE
→ SECONDARY_CONTACT
→ FOOT_SETTLE
→ STABILIZATION
```

Impact ends when mass has mechanically responded, not merely when an impact frame or FX appears.

## Cinematography Stack

```text
ACTION TRUTH
→ SHOT INTENT
→ CAMERA TRUTH
→ OPERATOR PERFORMANCE
→ FRAME COMPOSITION
→ VIEW PRESENTATION
→ FRAME
```

Camera truth and operator performance are separate layers.

Core laws:

```text
CAMERA DOES NOT FOLLOW ACTION. CAMERA INTERPRETS ACTION.
THE OPERATOR IS A PERFORMER.
CAMERA MOVEMENT MUST HAVE A REASON, A TARGET AND A SETTLE.
A GOOD FRAME CONTROLS ATTENTION BEFORE IT SHOWS EFFECTS.
BIG HIT ≠ AUTOMATIC CAMERA SHAKE.
```

Candidate camera move phases:

```text
HOLD
INITIATE
TRAVEL
REFRAME
SETTLE
```

## Attention, history, and continuity

Attention anchors may include FACE, EYE, HAND, WEAPON_TIP, CONTACT_POINT, DOOR, ENEMY, EXPLOSION, EMPTY_SPACE, or CUSTOM_SURFACE_ANCHOR. Support primary attention, secondary attention, and attention transfer without requiring camera motion.

Continuity data should be able to describe:

```text
ACTION_AXIS
SCREEN_DIRECTION
ENTRY / EXIT
SIGHTLINES
DEPTH_PLANES
CONTACT_POINTS
```

Axis crossing is diagnosable rather than universally forbidden; intentional and accidental crossings must be distinguishable.

## Cinematography assistant boundary

Tooling may diagnose conditions such as FACE_OCCLUDED, ACTION_AXIS_LOST, CONTACT_OUTSIDE_FRAME, HEADROOM_COLLISION, CAMERA_TOO_FAST_FOR_OPERATOR_PROFILE, SUBJECT_LEAVES_SAFE_FRAME, ATTENTION_ANCHOR_OCCLUDED, and UNINTENTIONAL_AXIS_CROSS.

Diagnostics must not silently rewrite authored shots.

## Camera / presentation boundary

Canonical physical camera state must remain recoverable even when downstream presentation intentionally disagrees with it:

```text
PHYSICAL CAMERA
≠ potentially PERCEIVED FRAME under presentation / Grani
```

Reality-disagreement effects belong downstream of canonical camera truth.

## Dependency and provenance policy

Preferred default license classes:

```text
CC0
MIT
BSD-2-Clause
BSD-3-Clause
Apache-2.0
MPL-2.0 with file-level review
```

High-review / non-default classes:

```text
GPL
AGPL
custom research-only licenses
non-commercial model licenses
```

Named candidate libraries or systems remain evaluation candidates only; naming them does not approve them as dependencies.

## Implementation sequencing

```text
0. Control Tower bootstrap/evidence/QC checkpoint — complete before this branch.
1. Docs-only integration PR from exact protected main.
2. Independent architecture boundary review.
3. OxiHuman/body donor proof O0 on an isolated experimental branch.
4. Babylon Parametric Human/body compiler proof B0 after donor/body boundaries are clear.
5. Motion Truth proof M0 after a real body/rig output exists.
6. Cinematography proof C1 after Action/Motion contracts are stable enough.
7. Presentation/Grani remains downstream of canonical truth layers.
```

Each proof must be isolated and reviewable. This staging document does not authorize any proof implementation by itself.

## Forbidden shortcuts

- no architecture implementation code in this docs PR;
- no Control Tower validator/state/evidence changes;
- no ZB CORE/runtime/production-data changes;
- no donor slider → DNA writeback;
- no donor skeleton authority;
- no promotion of `UNRESOLVED` values to truth;
- no early coordinate-system lock;
- no experimental body/motion/camera implementation directly on `main`;
- no G2 or Voice-to-Shot activation from this document;
- no OWNER LOCK from staging or architecture review.

## Review target

The architecture reviewer should determine whether these boundaries are internally coherent, sufficiently isolated for later proof branches, and compatible with the existing authority/persistence model.

A review acceptance records architecture approval only. It does not create OWNER LOCK and does not authorize unrelated runtime or production mutations.
