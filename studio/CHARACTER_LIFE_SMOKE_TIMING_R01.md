# ZORR CHARACTER LIFE SMOKE — TIMING R01

Status: EXPERIMENT, NOT CANON
Target: 48 frames / 24 fps / 1920x1080

## Purpose

Train timing one subsystem at a time. These frame values are test values for R01 only. They are not universal animation constants.

## Frozen constants

For P01:
- same MASTER FRONT identity;
- same front head state;
- same costume;
- same feet / ground contact;
- same camera;
- same background;
- no hand or leg animation;
- no parallax yet;
- no secondary motion yet.

Only the breathing system changes.

## P01 — breathing cycle

Experimental cycle:

| Frame | State | Intent |
|---:|---|---|
| 1 | neutral A | baseline |
| 13 | inhale apex | ribcage/shoulders at small positive excursion |
| 25 | neutral B | return through baseline |
| 37 | exhale apex | small negative/relaxed excursion |
| 48 | loop approach | return close to frame 1 without a visible snap |

### Motion ownership

`TORSO_JACKET`
- drives the primary breath.
- movement must be local deformation / small translation-rotation relationships, not whole-character uniform scale.

`LAPEL_L/R`
- follow torso hierarchy.
- preserve tailored construction.

`NECK_VISIBLE`
- tiny counter-response only.

`HEAD_FRONT_CORE`
- held for P01 except inherited root motion that is unavoidable from the neck hierarchy.

`SHOE_L/R`
- fixed ground-contact anchors.

### P01 test variants

Change one variable only:
- `P01-A`: very small torso excursion;
- `P01-B`: medium-small torso excursion;
- `P01-C`: upper safe excursion before jacket rubberization.

Do not assign a permanent amplitude before rendered comparison.

## P02 — head micro-acting

After best P01 breathing candidate is fixed:

Add one head-settle curve while keeping breathing unchanged.

Experimental key positions:
- F1 baseline;
- F17 small tilt/settle;
- F33 counter-settle;
- F48 loop approach.

Hard rule:
- no yaw topology manufacture;
- no face mesh distortion;
- if a visible yaw change is wanted, P05 drawing-switch is required.

## P03 — earring secondary

Use only one secondary family first: earrings.

Driver: `HEAD_FRONT_CORE` motion from P02.

Test lag as separate variants, not one assumed law:
- `P03-A`: short lag;
- `P03-B`: medium lag;
- `P03-C`: longer lag.

For each variant measure:
- delay in frames from head direction change to earring response;
- overshoot angle;
- settle duration;
- whether earring intersects face/neck silhouette.

Choose from rendered evidence. Do not promote a lag value to global character law from one shot.

## P04 — parallax

Freeze character animation from the best P01-P03 candidate.

Add only one camera move.

Layer families:
- foreground;
- character plane;
- background.

Required proof:
- camera displacement is measurable in px;
- foreground screen displacement is greater in magnitude than background for the authored depth arrangement;
- character identity and ground contact do not drift because of incorrect parenting.

No Babylon in P04.

## P05 — head drawing switch

Use real HEAD YAW source drawings.

First test should be a small information jump rather than profile-to-profile:
- front -> 3/4, or
- 3/4 -> front.

Do not Plastic-warp the front face into 3/4.

Before the switch:
- current drawing remains inside its Plastic mesh envelope.

After the switch:
- new drawing must also fit the intended mesh envelope, or receive a separate valid mesh/state.

Measure:
- eye midpoint screen jump;
- chin jump;
- head silhouette area jump;
- neck attachment jump;
- hair silhouette jump.

The goal is not zero change; the goal is an intentional drawing change without an accidental spatial pop.

## Review frames

For every training pass export/inspect at minimum:
- F1
- F13
- F25
- F37
- F48

For any detected failure add the exact first failing frame to the review set.

## PASS discipline

No pass from curve inspection alone.

Sequence:
`SET KEYS -> RENDER -> INSPECT -> MEASURE -> PASS/FAIL`

On FAIL identify the first dominant class:
- GEOMETRY
- PIVOT
- HIERARCHY
- TIMING
- Z_ORDER
- CAMERA
- DEFORMATION

Then change one subsystem only.
