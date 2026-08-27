# BABYLON DIRECTING v1 — Design Specification

Date: 2026-08-27  
Status: OWNER-APPROVED DESIGN / SPEC REVIEW PENDING  
Issue: #69  
Base main: `cf68c4882f84d8d0cce07f05ccc15345b913ddca`

## 1. Purpose

BABYLON DIRECTING v1 is a deterministic 3D blocking and camera-staging subsystem for ZORR BLATT.

Its job is not to create final animation, final character geometry, final lighting, or final art. Its job is to turn explicit directing data into a stable, inspectable Babylon scene that can communicate:

- where actors are;
- how far apart they are;
- which way they face;
- what their readable blocking pose is;
- how simple blocking motion evolves over time;
- where the camera is;
- what the camera sees;
- how a simple camera move evolves over time;
- which frame should be captured for downstream visual production.

The system must produce repeatable staging suitable for use as a reference source for SALVADOR.

## 2. Master Flow

```text
DIRECTING INTENT
→ STRUCTURED SCENE DOCUMENT
→ BABYLON SCENE COMPILER
→ PROXY BLOCKING
→ CAMERA / SHOT EVALUATION
→ SCRUB / REPLAY
→ FRAME CAPTURE
→ DOWNSTREAM SALVADOR REFERENCE
```

Future language adapter, explicitly outside v1:

```text
LYNCH TEXT
→ DIRECTING PARSER / ADAPTER
→ STRUCTURED SCENE DOCUMENT
```

The structured scene document is the stable boundary. Babylon must never depend directly on natural-language interpretation.

## 3. v1 Scope

### Included

- ground/stage reference;
- simple disposable humanoid proxies;
- stable actor ids;
- world-space actor placement;
- actor scale/height for blocking only;
- actor facing/orientation;
- minimal named-joint pose controls;
- simple root motion;
- simple joint motion;
- deterministic timeline playback and scrubbing;
- one or more explicitly defined cameras;
- explicit camera target/framing data;
- simple camera keyframes;
- shot markers and capture time;
- deterministic still-frame capture;
- inspectable scene state;
- validation of malformed or unsupported scene documents;
- independent QC fixtures.

### Explicitly excluded

- free-text or NLP scene generation;
- automatic LYNCH command parsing;
- final animation systems;
- motion-capture ingestion;
- physics-driven combat;
- procedural combat choreography;
- production character meshes;
- body compiler dependency;
- production rig dependency;
- textures or material authoring;
- final lighting pipeline;
- audio or music;
- camera shake automation;
- cinematic auto-director logic;
- automatic SALVADOR submission;
- Character Truth or canon mutation;
- paid services or remote inference.

## 4. Architecture Boundaries

The subsystem is split into four conceptual units.

### 4.1 Scene Contract

Owns the versioned structured scene document and validation rules.

It does not know Babylon internals.

Responsibilities:

- schema/version validation;
- actor/camera/shot id uniqueness;
- numeric sanity checks;
- required-field validation;
- supported pose-joint validation;
- supported motion-channel validation;
- capture-time validation;
- deterministic ordering rules.

### 4.2 Babylon Scene Compiler

Consumes a valid scene document and builds Babylon runtime objects.

Responsibilities:

- create stage/ground;
- create proxy actors;
- create minimal proxy joint hierarchy;
- apply initial transforms and poses;
- create cameras;
- create animation tracks;
- establish deterministic runtime state;
- expose an inspectable mapping from contract ids to runtime objects.

It must not modify source scene data.

### 4.3 Timeline / Shot Evaluator

Owns deterministic time evaluation.

Responsibilities:

- set exact time;
- scrub forward/backward;
- replay from zero;
- evaluate actor root motion;
- evaluate joint motion;
- evaluate camera motion;
- select current shot/camera;
- expose settled scene state for capture.

Playback is blocking-level and deterministic. Real-time frame-rate variation must not change evaluated transforms at a requested timestamp.

### 4.4 Frame Capture Adapter

Captures a selected camera at an explicit scene time.

Responsibilities:

- select camera by stable id;
- seek exact time;
- render after state evaluation;
- export one still image;
- record capture metadata sufficient to reproduce the frame.

The capture adapter does not submit to SALVADOR in v1.

## 5. Scene Document Contract

Recommended top-level shape:

```json
{
  "schemaVersion": "babylon-directing-v1",
  "sceneId": "scene-001",
  "stage": {},
  "actors": [],
  "cameras": [],
  "shots": [],
  "capture": {}
}
```

### 5.1 Stage

Required fields:

- width;
- depth;
- groundY;
- unit.

v1 unit is meters.

No stage geometry may imply production architecture truth. The stage is a spatial measuring surface only.

### 5.2 Actor

Each actor requires:

- `id` — stable unique string;
- `proxyType` — v1 supports `humanoid-basic`;
- `heightM` — blocking height only;
- `position` — x/y/z;
- `rotationYDeg` or equivalent deterministic facing representation;
- `pose` — named joint controls.

Optional:

- root motion keyframes;
- joint motion keyframes;
- display label for debug UI only.

Actor dimensions are disposable directing parameters. They are not Character DNA, Body Truth, or canon.

### 5.3 Minimal Named Joint Set

v1 should stay deliberately small:

- pelvis;
- spine;
- chest;
- neck;
- head;
- shoulderL / shoulderR;
- upperArmL / upperArmR;
- forearmL / forearmR;
- handL / handR;
- thighL / thighR;
- shinL / shinR;
- footL / footR.

Joint controls are local rotations. Optional translation is forbidden for child joints in v1 unless a later explicit gate adds it.

### 5.4 Motion Keyframes

Root keyframe fields:

- timeSec;
- position;
- rotationYDeg.

Joint keyframe fields:

- timeSec;
- joint;
- localRotationDeg.

Interpolation in v1 is deterministic linear interpolation for translation and deterministic shortest-path interpolation for rotations using the chosen runtime representation.

No easing library or procedural secondary motion is required for v1.

### 5.5 Camera

Each camera requires:

- `id`;
- position;
- target or explicit look-at point;
- vertical FOV in degrees;
- near/far clip values with safe defaults allowed by the compiler.

Optional camera motion keyframes:

- timeSec;
- position;
- target;
- FOV.

No automatic subject tracking. If the camera follows a subject, that behavior must be authored explicitly as keyframes or a later gated feature.

### 5.6 Shot

Each shot requires:

- `id`;
- `cameraId`;
- startSec;
- endSec.

Optional:

- label;
- preferredCaptureSec.

Shots do not own camera transforms. They reference cameras.

### 5.7 Capture

Capture requires:

- `shotId` or `cameraId`;
- `timeSec`;
- widthPx;
- heightPx;
- output filename/prefix.

Capture dimensions are reference-output dimensions, not SALVADOR runtime dimensions.

## 6. Determinism Law

For a fixed:

- scene document bytes after canonical parsing;
- Babylon/runtime version;
- viewport/capture dimensions;
- requested time;

then evaluated actor transforms, joint transforms, camera transform/FOV, selected shot, and still-frame staging must be reproducible.

Randomness is forbidden in v1 unless a field is explicitly added with a declared seed. No such random feature is required for the first implementation.

## 7. Proxy Geometry Law

The humanoid proxy must be simple enough to inspect and cheap enough to render instantly.

Preferred construction:

- capsule/cylinder/box primitives;
- visible head;
- torso;
- pelvis;
- upper/lower limbs;
- hands/feet as simplified forms;
- explicit left/right readability.

The proxy must communicate:

- silhouette;
- scale;
- facing;
- support leg / stance;
- arm direction;
- eyeline/head direction;
- distance and overlap.

It must not attempt likeness, anatomy approval, costume design, texture design, or production character identity.

## 8. Camera Law

Camera behavior follows ZB directing principles:

- camera interprets action; it does not automatically follow action;
- static camera is a valid and important choice;
- motion must have an authored reason and duration;
- every motion must have an explicit start and end state;
- no automatic shake;
- no hidden auto-framing after scene load;
- camera state at capture time must be inspectable.

The first proof requires at least one static shot and one simple authored camera or actor move.

## 9. Motion Law

v1 motion is blocking motion, not animation truth.

Supported intent examples:

- move root from A to B;
- rotate to face another actor;
- raise/lower an arm;
- lean torso;
- turn head;
- simple step-like root translation with basic leg pose change;
- simple camera push/pan authored by keyframes.

Unsupported in v1:

- foot locking solver;
- IK solver requirement;
- collision response;
- ragdoll;
- dynamics;
- procedural walk cycle;
- combat solver;
- physically correct momentum transfer.

The system may stage the idea of action without claiming final motion quality.

## 10. Validation and Failure Behavior

Invalid input must fail before scene compilation when possible.

Examples of hard failures:

- unsupported schema version;
- duplicate actor/camera/shot ids;
- missing referenced camera;
- invalid numeric values;
- negative duration;
- capture time outside valid timeline when policy requires bounded time;
- unsupported joint name;
- keyframes not strictly orderable by time after normalization;
- malformed vector/rotation data;
- unsupported proxy type.

No silent correction of semantic errors.

Safe normalization may include:

- deterministic key ordering internally;
- explicit defaults documented by schema;
- conversion from degrees into Babylon runtime rotation representation.

Every correction/default used must be inspectable in compiled metadata.

## 11. Inspectability

For debugging and QC, the runtime must expose or serialize a compact evaluated-state snapshot containing at least:

- sceneId;
- schemaVersion;
- evaluated time;
- actors: id, root position, root facing, named-joint rotations;
- active camera id, position, target, FOV;
- active shot id if any;
- capture settings;
- runtime/version metadata.

This snapshot is test evidence and must not be confused with canon authority.

## 12. First Proof Scene

The first accepted Babylon Directing v1 proof uses one deliberately small scene.

Required content:

- actor `A` and actor `B`;
- visibly different proxy heights or silhouette proportions for blocking readability;
- deliberate world-space spacing;
- distinct facing directions;
- distinct static poses;
- one static camera composition;
- one simple motion sequence, preferably either:
  - actor A advances/turns while actor B holds; or
  - camera performs a simple authored push while actors hold;
- one explicit capture time;
- one reproducible still image.

The proof should be visually boring but structurally obvious. It is a systems proof, not a beauty shot.

## 13. SALVADOR Boundary

BABYLON DIRECTING v1 outputs a visual reference and reproducibility metadata only.

It must not:

- create a SALVADOR task automatically;
- alter SALVADOR's production runtime profile;
- alter SALVADOR denoise/model/workflow/prompt versions;
- claim proxy geometry as character canon;
- imply that Babylon pose or body measurements override locked face/body canon.

A later integration gate may define:

```text
BABYLON CAPTURE
→ LOCAL INBOX / REFERENCE HANDOFF
→ SALVADOR CANON_REFERENCE_EDIT
```

That integration is not part of this implementation.

## 14. LYNCH Boundary

LYNCH owns directing intent, not Babylon implementation details.

Future adapter responsibilities may include translating commands such as:

```text
Zorr left foreground.
Enemy right midground.
Low camera.
Enemy holds.
Zorr advances one step.
Slow camera push.
```

into the structured scene contract.

Babylon itself must never parse prose in v1.

## 15. Technology Direction

The implementation should use Babylon.js in a minimal isolated proof application/module.

Requirements:

- local/free runtime;
- no backend service required for core staging;
- no paid API;
- deterministic scene loading from a checked-in fixture;
- automated contract/compiler tests where browser rendering is not required;
- browser-level smoke for scene construction, timeline evaluation, and frame capture;
- pinned dependency versions in the implementation branch/lockfile.

Exact Babylon.js/package versions are implementation-plan decisions and must be pinned before coding begins.

The existing experimental Babylon body-compiler branch is not authority for this subsystem. Directing v1 must stay independently replaceable and must not depend on experimental body geometry.

## 16. Testing Strategy

### Contract tests

Verify:

- valid scene accepted;
- malformed scene rejected;
- duplicate ids rejected;
- unknown joints rejected;
- invalid camera references rejected;
- capture references validated;
- deterministic defaults.

### Compiler tests

Verify:

- actor count and ids;
- proxy hierarchy exists;
- initial actor transforms match contract;
- named joint rotations match contract;
- camera transform/FOV matches contract;
- animations are created only when requested.

### Timeline tests

Verify exact evaluated transforms at selected timestamps, including replay after arbitrary scrubbing.

### Determinism regression

Load the same fixture twice and compare evaluated-state snapshots at fixed timestamps.

### Capture smoke

In a real Babylon/browser execution:

- load fixture;
- seek capture time;
- render;
- persist still frame;
- record dimensions and capture metadata;
- repeat from fresh reload and confirm composition/state consistency.

Pixel-perfect GPU output equality is not required unless later proven stable across the exact test environment. State determinism is the primary invariant; visual QC confirms framing equivalence.

## 17. Acceptance Criteria

BABYLON DIRECTING v1 is ready for independent DUNCAN QC only when all are true:

1. versioned scene contract exists;
2. one checked-in proof scene exists;
3. two proxies compile with stable ids and inspectable transforms;
4. static poses are visibly distinct and inspectable;
5. root and/or joint motion can be scrubbed and replayed deterministically;
6. at least one camera is explicit and stable;
7. at least one simple authored camera or actor movement works;
8. still-frame capture works at an explicit time;
9. evaluated-state snapshot is reproducible;
10. malformed contract tests pass;
11. no NLP, textures, production body dependency, paid service, physics requirement, audio integration, canon mutation, or SALVADOR auto-submit was added;
12. implementation remains isolated from SALVADOR production runtime;
13. full relevant automated test suite passes;
14. browser/disposable Babylon smoke passes;
15. DUNCAN independently reviews exact implementation HEAD before any production integration.

## 18. Production / Authority Rules

- Design approval is not implementation approval.
- Spec approval authorizes implementation planning only.
- Implementation PASS does not automatically authorize production integration.
- DUNCAN QC is required before integration.
- No OWNER LOCK is created by this subsystem.
- No Babylon proxy data writes back to Character Truth.
- No SALVADOR runtime profile changes are authorized.
- No merge occurs without the normal explicit gate.

## 19. Planned Delivery Sequence

```text
OWNER DESIGN APPROVAL
→ FORMAL SPEC
→ OWNER SPEC REVIEW
→ IMPLEMENTATION PLAN
→ LESTER TDD IMPLEMENTATION
→ DUNCAN INDEPENDENT QC
→ DISPOSABLE BABYLON LIVE SMOKE
→ JINGO/OWNER DIRECTING REVIEW
→ SEPARATE INTEGRATION GATE
```

## 20. Success Definition

The first useful result is not a cinematic animation.

Success is reached when ZORR BLATT can describe a small shot as structured directing data and reliably obtain the same readable 3D blocking, camera framing, simple movement, and capture frame again.

That gives LYNCH a future deterministic stage to command and gives SALVADOR a future stable visual reference source without contaminating character canon or art-production authority.
