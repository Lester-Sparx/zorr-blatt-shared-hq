# FULL_CHARACTER_MODEL_LOCK_R02

STATUS = ACTIVE MODEL CONSISTENCY GATE
TRACKER = #245
BRANCH = `duncan/zorr-studio-r01`
CHARACTER_FOUNDATION = PASS_CANDIDATE
CANON_LOCK = NO
IMAGE_GENERATION = NO
IMAGE_EDITING = NO

## PURPOSE

Prove that the existing accepted character reference sheets describe **one coherent ZORR character model**, not six individually good but mutually drifting sheets.

Hard equation:

`6 GOOD SHEETS != MODEL LOCK`

Required proof:

`SHEET_1 ... SHEET_6 -> ONE CHARACTER MODEL`

This gate does **not** reopen BODY / HAIR / HANDS research from zero.

## INPUT FOUNDATION

Current character foundation is treated as `PASS_CANDIDATE` for the purpose of this gate:

- `HEAD_PITCH_VOLUME_R01`
- `BODY_CONSTRUCTION_R01`
- `HAIR_TOPOLOGY_R01`
- `HANDS_CANON_R03`
- `HAND_EXPRESSION_R01`
- `FACE_ACTING_R01`

The pack remains a flattened reference pack, not an OpenToonz-ready separated source package.

## CROSS-SHEET CONSISTENCY CHECKS

### 1. HEAD / FACE IDENTITY

Across all head and acting sheets, verify one invariant model for:

- head width/height relationship;
- jaw angle and chin length;
- brow height and eye spacing;
- nose length/wedge;
- ear anchor;
- scar trajectory/anchor;
- hairline relationship to the face;
- neck-to-head relationship.

Extreme acting may deform expression but must not silently redesign identity.

### 2. HAIR TOPOLOGY

Verify that front / three-quarter / profile / rear / pitch views preserve:

- one base mass;
- crown volume;
- major cluster count/direction;
- hairline anchors;
- rear silhouette relationship to neck/head.

Known open gap:

`TOP/CROWN = OPEN ONLY IF A REAL CAMERA REQUIRES IT`.

Do not create a separate top sheet merely for completeness.

### 3. BODY RATIOS

Verify consistency between body and acting sheets for:

- head/body scale;
- shoulder width;
- neck thickness/length;
- torso length;
- waist/pelvis relation;
- arm length;
- leg length;
- hand scale;
- foot scale where visible.

No neutral-vs-acting redesign is allowed.

### 4. HAND MODEL

Verify one hand model across canonical and acting sheets:

- palm width/length;
- finger length hierarchy;
- thumb root;
- wrist thickness;
- hand-to-head/body scale;
- cuff/watch relation;
- foreground exaggeration is perspective, not model drift.

### 5. ASYMMETRY / IDENTITY MARKERS

Verify persistent asymmetries and markers:

- scar placement;
- earrings/accessories;
- hair asymmetry;
- costume asymmetry where intentional;
- watch/chain/hardware attachment logic.

### 6. COSTUME ATTACHMENT POINTS

Before `COSTUME_MECHANICS_R01`, verify stable attachment anchors:

- shoulder seam;
- collar/lapel root;
- armpit;
- elbow/cuff;
- waist/belt;
- jacket hem;
- trouser waist/crotch/knee/ankle;
- watch/chain/button positions.

This gate does not require full fold mechanics yet.

### 7. SCALE REFERENCE

All six sheets must be relatable to one common model scale.

Required result:

- one declared head/body proportion envelope;
- one hand scale envelope;
- one shoulder/head relationship;
- one reference for neutral standing height.

Do not invent missing numeric precision. If source evidence cannot support an exact number, record a bounded visual/measured range and mark it `OPEN`.

## RESULT CLASSIFICATION

Every checked item must be classified as exactly one of:

- `LOCKED_CANDIDATE` — internally consistent and ready for owner/QC lock;
- `PASS_CANDIDATE` — usable, but not yet sufficient for lock;
- `OPEN` — missing evidence;
- `CONFLICT` — two or more accepted sheets disagree.

No conflict may be hidden by averaging.

## CONFLICT REPAIR LAW

If a conflict is found:

`IDENTIFY FIRST CONFLICT -> NAME AUTHORITY SHEET -> REPAIR ONLY CONFLICTING SUBSYSTEM -> FRESH CROSS-CHECK`

Do not regenerate a full turnaround or reopen already-good BODY / HAIR / HANDS research.

After two materially identical failed repairs, stop that repair path and change strategy.

## PASS GATE

`FULL_CHARACTER_MODEL_LOCK_R02 = PASS` only when all of the following are true:

1. Head/face identity is cross-sheet coherent.
2. Hair topology is coherent for currently required camera envelope.
3. Body ratios are coherent.
4. Hand model is coherent.
5. Identity asymmetries/markers are coherent.
6. Costume attachment points are coherent.
7. A common scale reference exists.
8. All remaining gaps are explicitly listed as `OPEN` and do not block current production.
9. No hidden redesign exists between neutral and extreme acting.
10. Fresh evidence demonstrates the exact reviewed state.

`PASS` here means **character model consistency gate passed**. It does not by itself mean final production canon, rig ready, shot ready, or OpenToonz ready.

## SEPARATE LOCK BOUNDARIES

`CHARACTER MODEL LOCK` answers:

> Who is this character, and what geometry/identity remains invariant?

`S001 / SHOT BASE LOCK` answers:

> How does the already-locked character enter one specific shot with BG/MID/FG/camera/depth?

These must not be merged into one gate.

## FORMAT / ASPECT LAW

`9:16` is currently treated only as an `S001-SPECIFIC ASSUMPTION` until separately confirmed.

It is **not global ZORR production canon**.

Before physical S001 assets are built, the shot contract must resolve:

- output resolution;
- aspect ratio;
- fps;
- camera field/framing;
- overscan;
- maximum push/move envelope.

## DOWNSTREAM ROUTE

After this gate passes:

`FULL_CHARACTER_MODEL_LOCK_R02`
-> `COSTUME_MECHANICS_R01`
-> `TOP/CROWN CONTROL` only if a real camera proves the gap
-> `POSE_MECHANICS_VISUAL_R01`
-> `CAMERA_LAYOUT_VISUAL_R01`
-> approved `LINE / COLOR / SHADOW / MATERIAL` state
-> `GOLDEN KEYFRAME`
-> separated `OPENTOONZ SOURCE PACKAGE`
-> `S001 PHYSICAL SHOT BASE`
-> `OPENTOONZ CUT`

## STOP RULE

Until this gate is resolved:

- no new generic BODY study;
- no new generic HAIR study;
- no new generic HANDS study;
- no full-sheet regeneration for completeness;
- no S001 physical build that assumes unresolved character geometry;
- no image generation/editing unless OWNER separately gives the exact allowed command.

## CURRENT TERMINAL STATE

`CHARACTER_FOUNDATION = PASS_CANDIDATE`
`FULL_CHARACTER_MODEL_LOCK_R02 = ACTIVE / NOT YET PASS`
`SHOT_STAGE_FOUNDATION = SPEC READY / PHYSICAL NOT PROVEN`
`S001_9_16 = ASSUMPTION / NOT GLOBAL CANON`
`NEXT = perform cross-sheet consistency audit and produce explicit LOCKED_CANDIDATE / PASS_CANDIDATE / OPEN / CONFLICT matrix`
