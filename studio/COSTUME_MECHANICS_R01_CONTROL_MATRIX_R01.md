# COSTUME_MECHANICS_R01 — CONTROL MATRIX R01

STATUS = MECHANICS SPEC CLOSED / VISUAL REPEATABILITY WITNESS OPEN
TRACKER = #248
WORKSTREAM = #249 / WORKSTREAM A
BRANCH = `duncan/zorr-studio-r01`
UPSTREAM = `FULL_CHARACTER_MODEL_LOCK_R02 = PASS`
IMAGE_GENERATION = NO
IMAGE_EDITING = NO

## RESULT

The six required costume-force classes now have one explicit production law:

`POSE DRIVER -> BODY FORCE -> INVARIANT ATTACHMENTS -> 2–5 MEANINGFUL FOLD SHAPES -> CALM REGIONS -> FAILURE ROUTE`

This closes the **mechanics-definition** portion of `COSTUME_MECHANICS_R01` without changing character identity, costume design, body construction, hand construction or shot/camera scope.

It does **not** close the terminal visual gate. No new dynamic costume visual has been generated or edited under this workstream.

## EVIDENCE / AUTHORITY

Fresh upstream evidence already accepted on the active branch:

- `studio/FULL_CHARACTER_MODEL_LOCK_R02.md` = PASS;
- `studio/FULL_CHARACTER_MODEL_LOCK_R02_AUDIT_R01.md` = fresh cross-sheet audit;
- pack SHA256 = `a83b7de56d260908837f31153edfd85322cec566e3a0c37ad205db391ddf05e5`;
- `BODY_CONSTRUCTION_R01.png` SHA256 = `08b86bc13a1fb001a9251717ccee3867c9b6573b44cfe7a96bba8fbaf26bb018`;
- `HANDS_CANON_R03.png` SHA256 = `608ecfb9ec482a3a5605044c6b7b64681e90df735281c6741aecbf20e4f3c1ff`;
- `HAND_EXPRESSION_R01.png` SHA256 = `6ea891870a2c5db8597b411af5885ff4be89a85c851a2154fca95b87323b11c5`;
- accepted suit turnaround = standing silhouette / attachment support;
- accepted costume/accessory source = cuff, watch, belt, buttons, lapel, shoe and hardware facts.

The upstream audit already classifies `COSTUME ATTACHMENT POINTS = LOCKED_CANDIDATE` and names the established attachment family:

`shoulder seam / collar-lapel root / cuff / waist-belt / jacket hem / trouser waist / knee / ankle / watch / buttons`.

No hidden attachment point is introduced below.

## GLOBAL DEFORMATION LAW

For every control:

1. The body-under-costume authority moves first.
2. Garment anchors follow the body; they do not float independently.
3. Tension lines point away from the force/anchor pair.
4. Compression folds accumulate on the closing side of a joint.
5. The opposite side remains a larger, quieter tension plane.
6. A large garment region carries `2–5` meaningful fold shapes, not a noise field.
7. Ivory remains predominantly calm; black/ivory hierarchy must survive before internal fold lines are read.
8. Hardware is attached geometry, not decoration that drifts frame to frame.
9. No control may alter jacket cut, lapel family, trouser family, shoe family, body proportions or hand model.

## CONTROL 01 — ARM_RAISE

**Pose driver**

`humerus elevation at shoulder`

**Primary force path**

`upper arm rise -> shoulder seam displacement -> armpit closure/stretch -> upper side-chest pull`

**Invariant attachments**

- shoulder seam remains seated on the shoulder block;
- collar and lapel root remain attached to neck/chest structure;
- sleeve cap remains attached to armhole;
- jacket front/button family does not translate with the raised arm as one rubber sheet.

**Legal fold field**

- 1–2 armpit compression wedges on the closing side;
- 1–2 directional tension lines from sleeve/armhole toward chest or back plane;
- optional single secondary break where the jacket side plane changes direction.

**Calm regions**

lower torso, opposite lapel plane and unaffected jacket front remain large and quiet.

**Failure**

`shoulder seam floats / lapel root detaches / whole jacket wrinkles / sleeve becomes balloon-rubber`.

**Classification**

`MECHANICS_RULE = LOCKED_CANDIDATE`
`VISUAL_REPEATABILITY = OPEN`

## CONTROL 02 — ELBOW_90

**Pose driver**

`elbow flexion toward ~90 degrees`

**Primary force path**

`forearm closes -> inner sleeve compresses -> outer sleeve stretches -> cuff rotates with distal forearm`

**Invariant attachments**

- sleeve remains attached at upper arm and cuff;
- cuff stays orthogonal to the local wrist/forearm orientation rather than screen-horizontal;
- watch stays on the established wrist side and does not slide onto the hand;
- hand scale/model remains governed by `HANDS_CANON_R03`.

**Legal fold field**

- 2–3 compressed sleeve folds at inner elbow;
- 1–2 long outer-elbow tension shapes;
- cuff edge may overlap/compress locally but must not redesign.

**Calm regions**

upper sleeve away from elbow and jacket body stay mostly planar.

**Failure**

`watch drift / cuff drift / sleeve accordion noise / forearm length change / hand redesign`.

**Classification**

`MECHANICS_RULE = LOCKED_CANDIDATE`
`VISUAL_REPEATABILITY = OPEN`

## CONTROL 03 — TORSO_TWIST

**Pose driver**

`ribcage yaw relative to pelvis`

**Primary force path**

`ribcage rotation -> one front plane shortens -> opposite plane stretches -> waist/lapel relationship shears`

**Invariant attachments**

- collar/lapel root stays attached to chest/neck;
- jacket waist stays related to pelvis/waist authority rather than rotating fully with shoulders;
- button family preserves spacing logic on the garment plane;
- belt remains pelvis/waist-attached.

**Legal fold field**

- 1–2 diagonal tension folds across the stretched side;
- 1–2 compression breaks on the shortened waist side;
- optional single hem displacement fold where torso rotation meets pelvis stability.

**Calm regions**

lapel faces remain broad graphic shapes; no spiral wrinkle field.

**Failure**

`lapel shears off chest / buttons become screen-fixed / jacket rotates as rubber tube / waist anchor drifts`.

**Classification**

`MECHANICS_RULE = LOCKED_CANDIDATE`
`VISUAL_REPEATABILITY = OPEN`

## CONTROL 04 — SEATED_COMPRESSION

**Pose driver**

`hip flexion + pelvis support/contact`

**Primary force path**

`pelvis flexes -> front waist closes -> jacket hem is displaced upward/outward -> trouser waist/crotch compresses`

**Invariant attachments**

- jacket waist remains tied to torso/waist structure;
- belt/trouser waist remain pelvis-attached;
- jacket hem may lift/overlap but does not shorten permanently;
- crotch construction follows body authority and is not redrawn as a new trouser cut.

**Legal fold field**

- 1–2 waist compression folds;
- 1–2 jacket-hem displacement shapes;
- 1–2 trouser/crotch compression shapes only where hip closure requires them.

**Calm regions**

upper chest/lapels and most thigh plane stay broad and controlled.

**Failure**

`jacket becomes shorter design / belt floats / crotch redraw / seated pose covered in realistic micro-wrinkles`.

**Classification**

`MECHANICS_RULE = LOCKED_CANDIDATE`
`VISUAL_REPEATABILITY = OPEN`

## CONTROL 05 — KNEE_BEND

**Pose driver**

`knee flexion`

**Primary force path**

`knee closes -> back/inside trouser region compresses -> front/outer region tensions over knee volume`

**Invariant attachments**

- trouser leg remains one large graphic tube between hip and ankle;
- knee location follows body construction;
- trouser seam/cut family does not migrate;
- ankle relation remains consistent with shoe placement.

**Legal fold field**

- 2–3 compression folds on closing side;
- 1–2 long tension breaks over/around knee front or outer plane.

**Calm regions**

mid-thigh and lower shin away from the joint stay mostly planar.

**Failure**

`accordion leg / knee migrates / trouser cut changes / anatomy volume disappears under folds`.

**Classification**

`MECHANICS_RULE = LOCKED_CANDIDATE`
`VISUAL_REPEATABILITY = OPEN`

## CONTROL 06 — STRIDE_ANKLE

**Pose driver**

`hip separation + planted/swing leg ankle angle`

**Primary force path**

`leg direction changes -> trouser tube follows hip/knee/ankle chain -> lower hem meets shoe/ankle -> break/compression resolves at contact`

**Invariant attachments**

- trouser waist remains pelvis-attached;
- knee remains on the body chain;
- trouser hem remains related to ankle/shoe, not screen position;
- shoe family is unchanged;
- no special feet redesign is introduced unless a real shot later proves a gap.

**Legal fold field**

- 1–2 directional folds along the leg motion/tension path;
- 1–3 trouser-break shapes near the planted ankle/shoe contact;
- swing leg may be cleaner than planted leg when no compression force exists.

**Calm regions**

upper leg planes remain large; stride does not imply all-over trouser wrinkling.

**Failure**

`shoe disconnect / ankle break floats / equal wrinkles on swing and planted legs / hidden shoe redesign`.

**Classification**

`MECHANICS_RULE = LOCKED_CANDIDATE`
`VISUAL_REPEATABILITY = OPEN`

## CROSS-CONTROL INVARIANTS

The following must match across all six witnesses when visual execution is authorized:

| Invariant | Required state |
|---|---|
| Character identity/body ratio | unchanged |
| Jacket cut/length family | unchanged; only pose deformation |
| Lapel root/family | unchanged |
| Button family | attached to garment plane; no drift |
| Belt/waist | pelvis/waist attached |
| Cuff | distal sleeve/wrist attached |
| Watch | same wrist side and local attachment |
| Trouser cut | unchanged |
| Knee/ankle chain | follows body construction |
| Shoe family | unchanged |
| Ivory/black hierarchy | preserved |
| Fold density | force-localized; `2–5` meaningful shapes per large active region |

## VISUAL WITNESS ACCEPTANCE TEST

For each of the six authorized visual witnesses, record:

`CONTROL_ID`
`POSE_DRIVER`
`ACTIVE_FORCE_POINTS`
`ATTACHMENT_INVARIANTS = PASS/FAIL`
`FOLD_DIRECTION = PASS/FAIL`
`CALM_REGION_PRESERVED = PASS/FAIL`
`IVORY_BLACK_HIERARCHY = PASS/FAIL`
`NO_REDЕSIGN = PASS/FAIL`
`VERDICT = PASS_CANDIDATE / OPEN / CONFLICT`

Terminal gate requires all six witnesses to satisfy all checks in one coherent character model.

## OPEN

`VISUAL_REPEATABILITY_WITNESS = OPEN`

Reason: current #248 authority explicitly states that no image generation/editing is authorized by the tracker. Existing accepted sources establish model identity, standing costume facts and attachment anchors, but do not constitute a fresh six-pose deformation witness under this gate.

Therefore:

`COSTUME_MECHANICS_R01 != PASS`

No terminal PASS is claimed.

## NEXT

Next legal step for WORKSTREAM A:

`OBTAIN EXACT OWNER AUTHORITY FOR THE SIX COSTUME-MECHANICS VISUAL WITNESSES`

Then execute only the six bounded controls above, evaluate them against this matrix, persist fresh evidence, and close #248 only if all six pass.

After real `COSTUME_MECHANICS_R01 = PASS`:

`POSE_MECHANICS_VISUAL_R01` becomes the next workstream gate.
