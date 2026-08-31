# OPENTOONZ TRAINING CURRICULUM R01

Status: ACTIVE TRAINING
Branch: `duncan/zorr-studio-r01`

## Goal

Train ZORR as a repeatable 2D anime production system on the existing ZORR character source pack before attempting full scene production.

Final evidence target: `OPENTOONZ CHARACTER LIFE SMOKE R01` — 48 frames, 1920x1080, 24 fps.

## Source pack

Use the existing approved/provisional ZORR source family only:
- MASTER FRONT
- BODY TURNAROUND
- HEAD YAW
- DETAIL / COSTUME / ACCESSORY

Do not invent hidden anatomy. Do not redesign costume or identity during motion training.

## Core OpenToonz facts to exploit

OpenToonz Plastic works on a texture column and a generated mesh. The texture column may itself contain more than one drawing. Plastic skeleton vertices expose Position, Angle Bounds, Rigidity and Stacking Order. Stage Schematic / pegbars / camera provide the scene hierarchy and 2.5D depth/parallax. Function Editor controls timing/interpolation.

Production consequence:

`KEY DRAWING -> limited Plastic deformation -> next KEY DRAWING`

not:

`ONE PNG -> extreme mesh deformation -> every pose`

## Character rig map R01

### RIGID / identity-protected
- face core
- eye geometry
- nose/jaw topology
- buttons
- belt buckle
- watch body
- shoe construction

Plastic deformation here is either forbidden or minimal.

### PRIMARY movable masses
- torso / ribcage mass
- pelvis mass
- neck support
- upper arms
- forearms
- thighs
- lower legs

Use low-amplitude movement in the first smoke. No extreme action pose.

### SECONDARY movable masses
- front hair clusters
- rear hair mass
- earrings
- jacket hem / lapel support where separable
- shirt opening / chain only if cleanly separable

Secondary must lag or settle relative to primary motion; it must not move independently at random.

## Head rule

Yaw is NOT a Plastic task.

Use the existing HEAD YAW drawings as distinct key drawings / angle states. Plastic may provide only micro-settle, tiny pitch/tilt and breathing-related motion inside one valid angle.

If an angle transition visibly changes face topology, switch drawing rather than stretch the current face.

## Training passes

### P01 — BREATH WITHOUT PNG SCALE

Question: can the character feel alive without scaling the whole drawing?

Freeze:
- camera
- head angle
- identity
- costume
- feet

Animate only:
- small ribcage rise/fall
- tiny shoulder response
- tiny neck counter-motion

Target: one calm 48-frame breathing cycle.

Fail if:
- head simply scales with torso
- jacket outline rubberizes
- face proportions drift
- feet float

### P02 — HEAD MICRO-ACTING

Keep P01 torso motion.

Add only:
- tiny head tilt / settle
- small neck counter-rotation

No yaw deformation. If yaw is required, use another key drawing from HEAD YAW.

### P03 — SECONDARY

Add one secondary system only.

Preferred first candidate: earrings because their attachment point is clear and their motion is easy to read.

Then test hair clusters separately.

Secondary law:
`parent action -> delay -> overshoot -> settle`

Do not animate all hair strands independently.

### P04 — 2.5D PARALLAX

Scene hierarchy:
- foreground
- character plane
- background
- camera

Use Stage Schematic / pegbars / Z-depth. Animate one restrained camera move and verify that foreground responds more strongly than background.

Do not use Babylon for this pass.

### P05 — DRAWING SWITCH

Use at least two real head drawings from HEAD YAW in one short shot.

Goal: prove that OpenToonz can combine key-drawing replacement with limited Plastic motion without identity popping.

Plastic should bridge life inside each drawing state, not manufacture the missing view.

### P06 — ACTION PREP

Only after P01-P05 survive fresh QC.

Create/use a genuine attack anticipation key drawing and a strike key drawing. Plastic may support overlap and settle between valid drawings, but may not create the extreme pose from neutral.

## QC training

Measure rendered output, not rig elegance.

Track at minimum:
- face anchor drift in pixels
- silhouette drift after removing intended rigid transform
- foot contact drift
- head/body proportion drift
- secondary lag timing in frames
- camera displacement and layer parallax in pixels
- accidental z-order changes

No arbitrary universal PASS threshold. Record measured deltas first and calibrate from approved shots.

## One-change law

Each training pass changes one main subsystem only.

`CONSTANTS + ONE VARIABLE -> RENDER -> QC -> PASS/FAIL`

On FAIL:
1. classify geometry / pivot / hierarchy / timing / z-order / camera / deformation;
2. isolate first broken layer;
3. fix only that layer or transform;
4. re-render;
5. re-measure.

Do not rebuild the rig or add another framework unless the lower layer is proven insufficient.

## Current blocker

This chat runtime does not currently contain an OpenToonz executable. That is an execution-environment blocker, not a reason to change the chosen production architecture. Training design and source preparation continue on this branch; actual 48-frame smoke begins as soon as OpenToonz is available in an executable environment.
