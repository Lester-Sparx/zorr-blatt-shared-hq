# COSTUME_MECHANICS_R01

STATUS = MECHANICS SPEC CLOSED / VISUAL REPEATABILITY WITNESS OPEN
TRACKER = #248
WORKSTREAM = #249 / WORKSTREAM A
BRANCH = `duncan/zorr-studio-r01`
UPSTREAM = `FULL_CHARACTER_MODEL_LOCK_R02 = PASS`
CONTROL_MATRIX = `studio/COSTUME_MECHANICS_R01_CONTROL_MATRIX_R01.md`
IMAGE_GENERATION = NO
IMAGE_EDITING = NO

## PURPOSE

Prove repeatable **anime suit deformation logic** for the existing ZORR character without redesigning the costume and without realistic cloth-simulation overkill.

Hard rule:

`ANIME GARMENT READABILITY > REALISTIC WRINKLE COUNT`

`SILHOUETTE + LARGE PLANES + FORCE FOLDS > MICRO FOLDS`

## FROZEN FACTS

Do not change:

- character identity/body proportions;
- ivory double-breasted suit;
- black open shirt/central black mass;
- lapel geometry family;
- belt/waist relation;
- cuff/watch relation;
- sparse gold/silver hardware;
- jacket length and standing silhouette;
- trouser cut and black shoe family.

## FOLD LAW

Folds are legal only when caused by force at:

`SHOULDER / ARMPIT / ELBOW / WAIST / CROTCH / KNEE / ANKLE`

Typical large garment region:

`2–5 MEANINGFUL FOLD SHAPES`

Ivory surfaces remain mostly calm.

No decorative hatching, equal-weight wrinkles, realistic cloth noise or random redesign.

## SIX REQUIRED CONTROLS

1. `ARM_RAISE` — shoulder seam + armpit tension; lapel stays attached to chest logic.
2. `ELBOW_90` — sleeve compression on inner elbow, tension on outer elbow, cuff/watch remain attached.
3. `TORSO_TWIST` — chest/lapel/waist relationship changes coherently; jacket does not become rubber.
4. `SEATED_COMPRESSION` — waist + jacket hem + trouser waist/crotch compression; silhouette remains elegant.
5. `KNEE_BEND` — front/back knee tension/compression; trouser leg remains one large graphic tube.
6. `STRIDE_ANKLE` — hip/leg direction + ankle/trouser break + shoe relation.

The exact force/anchor/fold/failure law for all six controls is now frozen as a `LOCKED_CANDIDATE` mechanics specification in:

`studio/COSTUME_MECHANICS_R01_CONTROL_MATRIX_R01.md`

## PASS CHECK

Each control must satisfy:

- attachment points remain invariant;
- fold direction follows the applied force;
- no extra fold field appears in calm regions;
- ivory mass remains readable before internal lines;
- black/ivory hierarchy survives;
- watch/cuff/belt/buttons do not drift;
- no anatomy redesign under the garment;
- no costume redesign between controls.

## FRESH RESULT

`MECHANICS_DEFINITION = LOCKED_CANDIDATE`

Fresh upstream evidence used:

- `FULL_CHARACTER_MODEL_LOCK_R02 = PASS`;
- fresh cross-sheet audit confirms `COSTUME ATTACHMENT POINTS = LOCKED_CANDIDATE`;
- accepted body construction remains body-under-costume authority;
- accepted suit turnaround remains standing silhouette/attachment authority;
- accepted costume/accessory source remains cuff/watch/belt/button/lapel/shoe authority;
- accepted hand sources remain hand/cuff/watch interaction authority.

No new identity, costume or attachment geometry was introduced.

`VISUAL_REPEATABILITY_WITNESS = OPEN`

Reason: the active tracker explicitly does not authorize image generation/editing. Existing accepted references establish identity, standing costume geometry and attachment anchors, but they do not constitute a fresh six-control deformation witness for this gate.

Therefore:

`COSTUME_MECHANICS_R01 != PASS`

No terminal PASS is claimed.

## FAILURE ROUTER

If a visual control later fails:

`NAME FORCE POINT -> NAME BROKEN ATTACHMENT/FOLD -> REPAIR THAT REGION ONLY -> FRESH CHECK`

Do not regenerate the whole character or whole costume.

## OUTPUT CLASSIFICATION

Per region/control:

- `LOCKED_CANDIDATE`
- `PASS_CANDIDATE`
- `OPEN`
- `CONFLICT`

## TERMINAL GATE

`COSTUME_MECHANICS_R01 = PASS` only when all six required force classes have fresh repeatable visual evidence, attachment invariants hold, anime fold law is preserved, and no hidden redesign appears.

## OPEN

Exact remaining blocker:

`SIX_COSTUME_MECHANICS_VISUAL_WITNESSES = NOT AUTHORIZED / NOT PRESENT`

This is a narrow blocker on terminal #248 closure only. It does not reopen generic BODY / HAIR / HANDS work.

## NEXT

Next legal step:

`OWNER AUTHORITY -> SIX BOUNDED COSTUME-MECHANICS VISUAL WITNESSES -> FRESH MATRIX CHECK -> PASS/FAIL`

Only after real PASS:

`POSE_MECHANICS_VISUAL_R01 -> CAMERA_LAYOUT_VISUAL_R01`
