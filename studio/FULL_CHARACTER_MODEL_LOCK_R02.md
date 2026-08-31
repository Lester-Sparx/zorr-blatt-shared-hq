# FULL_CHARACTER_MODEL_LOCK_R02

STATUS = PASS / MODEL CONSISTENCY GATE CLOSED
TRACKER = #245
BRANCH = `duncan/zorr-studio-r01`
CHARACTER_FOUNDATION = PASS_CANDIDATE BASE / MODEL CONSISTENCY PROVEN
CANON_LOCK = NO
IMAGE_GENERATION = NO
IMAGE_EDITING = NO
AUDIT = `studio/FULL_CHARACTER_MODEL_LOCK_R02_AUDIT_R01.md`

## PURPOSE

Prove that the existing accepted character reference sheets describe **one coherent ZORR character model**, not six individually good but mutually drifting sheets.

Hard equation:

`6 GOOD SHEETS != MODEL LOCK`

Required proof:

`SHEET_1 ... SHEET_6 -> ONE CHARACTER MODEL`

This gate does **not** reopen BODY / HAIR / HANDS research from zero.

## VERIFIED INPUT FOUNDATION

- `HEAD_PITCH_VOLUME_R01`
- `BODY_CONSTRUCTION_R01`
- `HAIR_TOPOLOGY_R01`
- `HANDS_CANON_R03`
- `HAND_EXPRESSION_R01`
- `FACE_ACTING_R01`

Pack physical integrity and exact hashes were freshly verified in `FULL_CHARACTER_MODEL_LOCK_R02_AUDIT_R01.md`.

Supplementary existing sources were used only to cross-check already-defined head-yaw, standing costume and accessory facts. No new character design was generated.

## CLOSED CROSS-SHEET RESULT

| Subsystem | Result |
|---|---|
| HEAD / FACE IDENTITY | `LOCKED_CANDIDATE` |
| HAIR TOPOLOGY | `LOCKED_CANDIDATE` for current camera envelope |
| BODY RATIOS | `LOCKED_CANDIDATE` |
| HAND MODEL | `LOCKED_CANDIDATE` |
| IDENTITY MARKERS / ASYMMETRY | `LOCKED_CANDIDATE` |
| COSTUME ATTACHMENT POINTS | `LOCKED_CANDIDATE` |
| COMMON SCALE REFERENCE | `LOCKED_CANDIDATE` |

No hard cross-sheet conflict requiring subsystem rebuild was found.

## MODEL AUTHORITY

- `HEAD_PITCH_VOLUME_R01` = pitch/volume authority
- accepted head-yaw source = yaw/profile support
- `HAIR_TOPOLOGY_R01` = hair mass/topology authority
- `BODY_CONSTRUCTION_R01` = body-under-costume authority
- accepted suit turnaround = standing costume silhouette/attachment support
- `HANDS_CANON_R03` = neutral hand model authority
- `HAND_EXPRESSION_R01` = acting/foreground hand authority bounded by canon
- `FACE_ACTING_R01` = expression authority bounded by head identity
- accepted costume/accessory source = hardware/watch/shoe/belt/lapel facts

If a future drawing conflicts with these references:

`IDENTIFY CONFLICT -> NAME AUTHORITY -> REPAIR ONLY THAT SUBSYSTEM -> FRESH CHECK`

No averaging and no full character regeneration.

## ALLOWED OPEN ITEMS

These remain open without invalidating the model consistency PASS:

- `TOP/CROWN EXTREME HIGH CAMERA` only if a real shot proves the existing evidence insufficient;
- `COSTUME_DEFORMATION / FOLD MECHANICS` — next gate;
- final `LINE / COLOR / SHADOW / MATERIAL` approval;
- separated `OPENTOONZ SOURCE PACKAGE`;
- specialized feet/shoe action mechanics only if demanded by a real shot.

## PASS MEANING

`FULL_CHARACTER_MODEL_LOCK_R02 = PASS` means **the current character reference system is sufficiently cross-sheet coherent to stop rebuilding the character foundation and move downstream**.

It does not mean:

- final all-production canon lock;
- OpenToonz rig/source-layer readiness;
- S001 shot readiness;
- final material/color/shadow approval.

## SEPARATE LOCK BOUNDARIES

`CHARACTER MODEL LOCK` answers:

> Who is this character, and what geometry/identity remains invariant?

`S001 / SHOT BASE LOCK` answers:

> How does the already-locked character enter one specific shot with BG/MID/FG/camera/depth?

Do not merge these gates.

## FORMAT / ASPECT LAW

`9:16` remains only an `S001-SPECIFIC ASSUMPTION` until separately confirmed.

It is not global ZORR production canon.

Before S001 physical build, resolve exact output resolution, aspect ratio, fps, camera field/framing, overscan and maximum camera move/push envelope.

## NEXT LEGAL GATE

`COSTUME_MECHANICS_R01`

Purpose:

prove how the already-defined ivory suit deforms at real force points while preserving the locked character silhouette and attachment points.

Then:

`POSE_MECHANICS_VISUAL_R01`
-> `CAMERA_LAYOUT_VISUAL_R01`
-> approved `LINE / COLOR / SHADOW / MATERIAL`
-> `GOLDEN KEYFRAME`
-> separated `OPENTOONZ SOURCE PACKAGE`
-> `S001 PHYSICAL SHOT BASE`
-> `OPENTOONZ CUT`

## CURRENT TERMINAL STATE

`CHARACTER_FOUNDATION = READY FOR DOWNSTREAM PRODUCTION USE`
`FULL_CHARACTER_MODEL_LOCK_R02 = PASS`
`CANON_LOCK = NO`
`GENERIC_BODY_HAIR_HANDS_RESEARCH = FROZEN`
`SHOT_STAGE_FOUNDATION = SPEC READY / PHYSICAL NOT PROVEN`
`S001_9_16 = ASSUMPTION / NOT GLOBAL CANON`
`NEXT = COSTUME_MECHANICS_R01`
