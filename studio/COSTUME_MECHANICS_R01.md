# COSTUME_MECHANICS_R01

STATUS = ACTIVE HIGH-INFORMATION COSTUME GATE
TRACKER = #248
BRANCH = `duncan/zorr-studio-r01`
UPSTREAM = `FULL_CHARACTER_MODEL_LOCK_R02 = PASS`
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

## FAILURE ROUTER

If a control fails:

`NAME FORCE POINT -> NAME BROKEN ATTACHMENT/FOLD -> REPAIR THAT REGION ONLY -> FRESH CHECK`

Do not regenerate the whole character or whole costume.

## OUTPUT CLASSIFICATION

Per region/control:

- `LOCKED_CANDIDATE`
- `PASS_CANDIDATE`
- `OPEN`
- `CONFLICT`

## TERMINAL GATE

`COSTUME_MECHANICS_R01 = PASS` only when all six required force classes have repeatable anime fold logic and no hidden redesign.

This gate may use existing references for analysis immediately. Any new visual generation/editing requires separate exact OWNER authorization.

## NEXT

After PASS:

`POSE_MECHANICS_VISUAL_R01 -> CAMERA_LAYOUT_VISUAL_R01`
