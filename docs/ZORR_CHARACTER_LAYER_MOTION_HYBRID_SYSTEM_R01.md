# ZORR — CHARACTER LAYER MOTION HYBRID SYSTEM R01

STATUS = STUDY / WORKING HANDOFF
DATE = 2026-08-31
RULE = RESULT > PROCESS
PRIMARY UNIT = px, s, px/s, px/s^2, radians

## 0. PURPOSE

This document extends:

- `ZORR_ENGINE_HANDOFF_CONTRACT`
- `ZORR_2D_LAYER_MOTION_MATH`

Goal: make a drawn character feel alive inside a layered/parallax shot without replacing strong key drawings with a cardboard puppet.

Hard laws inherited from the contracts:

1. Geometry first, motion second, style third.
2. Hidden/occluded art is not invented.
3. A layer with unknown deformation authority is not deformed.
4. Measurements start in pixels.
5. Motion quality is not declared PASS without rendered measurement/calibration.
6. Existing mature tools are preferred over a new deformation framework.

---

## 1. OSS-FIRST DECISION

### PRIMARY: OpenToonz Plastic Tool

Use for:

- raster or vector texture-column deformation;
- triangular mesh generation;
- skeleton-driven local deformation;
- head/torso micro-motion;
- hair groups;
- coat/lapel/cloth secondary movement;
- accessories;
- cutout-style character motion inside an OpenToonz Xsheet/Timeline.

Why selected:

- native to a mature open-source 2D animation package;
- Plastic creates a mesh from an existing texture-column;
- skeleton vertices expose Position, Angle Bounds, Rigidity and Stacking Order;
- the texture remains linked to the mesh and is deformed by it;
- works inside the same timeline/camera environment used for 2D animation.

Reference: OpenToonz Documentation, chapter `Create animations using Plastic tool`.

### SECONDARY: Blender Grease Pencil + Armature

Use when the shot needs:

- deeper 2.5D/3D-aware staging;
- a character rig that must interact with a true 3D camera;
- Grease Pencil strokes controlled by an armature;
- vertex-group-weighted deformation;
- one rig shared with 3D props/camera/light.

Blender's Grease Pencil Armature Modifier is an existing non-destructive skeletal deformation path. It should be preferred over custom deformation code when this shot class requires Blender staging.

Reference: Blender 4.5 LTS Manual, `Grease Pencil > Modifiers > Deform > Armature`.

### SIMPLE CUTOUT FALLBACK: Synfig

Synfig already supports cut-out animation from separate image parts, grouped layers and rotation layers.

Use only when the shot is truly cutout-like and does not require Plastic/mesh deformation complexity.

Reference: Synfig documentation, `Cut-out Animation`.

### DECISION

```text
RASTER / ANIME DRAWING + 2D SECONDARY MOTION
    -> OpenToonz Plastic

GREASE PENCIL / TRUE 2.5D / 3D CAMERA COUPLING
    -> Blender Armature

SIMPLE RIGID CUTOUT
    -> Synfig

CUSTOM DEFORMATION FRAMEWORK
    -> DENY unless a proven gap remains
```

---

## 2. THE CHARACTER IS NOT ONE LAYER

Do not animate an entire character PNG if live acting is required.

Preferred semantic graph only where supported by visible/source art:

```text
CHAR_ROOT
├─ TORSO
├─ HEAD
│  ├─ FACE
│  ├─ HAIR_FRONT
│  └─ HAIR_BACK
├─ ARM_L / ARM_R          [only if separable]
├─ HAND_L / HAND_R        [only if separable]
├─ CLOTH_PRIMARY
├─ CLOTH_SECONDARY
└─ ACCESSORIES
```

If a region cannot be separated reliably:

```text
layer_state = UNSPLIT
```

Never guess a hidden elbow, shoulder, hand edge, cloth continuation or back-face region.

---

## 3. MOTION AUTHORITY

Every character layer receives both source authority and deformation authority from the handoff contract.

Typical working mapping:

| Layer | Source authority | Deformation authority | Intended role |
|---|---|---|---|
| face line-art | LOCKED_REFERENCE | PIVOT_ONLY or tightly limited | identity preservation |
| torso | LOCKED_REFERENCE | AFFINE / mesh if explicitly allowed | primary breathing/body mass |
| head | LOCKED_REFERENCE | PIVOT_ONLY / limited affine | counter-motion |
| hair group | LOCKED_REFERENCE | AFFINE / mesh | secondary drag |
| earring/accessory | LOCKED_REFERENCE | PIVOT_ONLY | pendular follow-through |
| coat tail / loose lapel | LOCKED_REFERENCE | AFFINE / mesh | cloth lag |
| unknown occluded part | UNKNOWN | UNKNOWN | HOLD / do not animate |

The table is a working mapping, not a universal automatic assignment. Per-shot authority wins.

---

## 4. HYBRID MOTION LAW

The main ZORR production rule is:

```text
KEY DRAWING gives acting and identity.
RIG gives micro-motion between strong drawings.
SECONDARY MOTION gives material life.
PARALLAX gives depth.
NEW KEY DRAWING replaces the rig when pose meaning changes.
```

Do not force one drawing through an extreme pose change.

Use a new key drawing when any of these materially changes:

- silhouette meaning;
- head orientation beyond the credible visible source;
- hand/arm pose topology;
- strong facial expression geometry;
- occlusion order requiring unseen art;
- fashion silhouette;
- action line.

---

## 5. PRIMARY + SECONDARY MOTION

Inherited decomposition:

```math
x_i(t) = x_parent(t) + x_primary_i(t) + x_secondary_i(t)
```

Character hierarchy:

```text
PRIMARY
    torso/root action
    head authored counter-motion

SECONDARY
    hair lag
    cloth drag
    earring/accessory swing
    small overshoot / settle
```

Never give every layer the same curve.

That produces a rigid cardboard result even when many layers move.

---

## 6. BREATHING IS A MASS TRANSFER, NOT A SCALE EFFECT

For a quiet hold, torso breathing should be treated as a controlled motion of the chest/shoulder mass, not a global scale pulse.

Possible channels:

```text
TORSO translation Y
small torso rotation
small chest mesh deformation
shoulder change
HEAD counter-motion
cloth response
```

Avoid:

```text
CHAR_ROOT scale 1.00 -> 1.02 -> 1.00
```

as the only breathing mechanism. It expands the entire character uniformly and often reads as a camera/PNG effect.

---

## 7. COUNTER-MOTION

If torso moves, the head does not need to copy it exactly.

Example relationship:

```text
TORSO rises slightly
HEAD compensates slightly downward / opposite rotation
HAIR reacts after HEAD
EARRING reacts after HEAD with more freedom
```

The purpose is to create internal phase structure.

Do not invent universal delay constants. Measure/calibrate by shot.

---

## 8. FOLLOW-THROUGH

For hair, cloth and accessories, use the contract's damped target model when the tool/runtime supports an equivalent mature mechanism:

```math
q'' + 2*zeta*omega*q' + omega^2*q = omega^2*u(t)
```

where:

- `u(t)` is the parent/driver signal;
- `omega` controls response frequency;
- `zeta` controls damping.

Until calibrated:

```text
omega = UNKNOWN
zeta  = UNKNOWN
```

Do not create an "anime-perfect" global constant.

---

## 9. OPENToonz PLASTIC ROLE MAP

Recommended use of Plastic:

### Rigid-ish parts

Use sparse skeleton/control structure and high rigidity where appropriate:

- head mass;
- torso mass;
- forearm if source art is separable;
- shoe/rigid prop.

### Flexible parts

Use mesh deformation with attachment-root discipline:

- hair locks/groups;
- coat tails;
- loose lapels;
- sleeves where bending is visible and source-supported;
- scarves/accessory ribbons.

### Attachment law

```text
ROOT / SEAM = constrained
FREE TIP = allowed to lag
```

A hair tip should not move as an independent floating sprite.

---

## 10. PARALLAX + CHARACTER MOTION

The camera/parallax signal remains separate from character acting.

For camera screen displacement `C(t)`:

```math
delta_i(t) = -k_i C(t)
```

Then the character may have its own local motion inside the moving world.

Conceptually:

```text
SCREEN POSITION
=
CAMERA/PARALLAX COMPONENT
+
CHAR_ROOT COMPONENT
+
LOCAL BODY COMPONENT
+
SECONDARY COMPONENT
```

This prevents a false diagnosis where camera motion is mistaken for character acting.

---

## 11. TRAINING SHOT R01 — QUIET THREAT HOLD

This is a training example, NOT a universal quality threshold.

Delivery:

```text
fps = 24
length = 2.0 s
frames = 48
```

Background depth motion example:

```text
FAR_BG     total travel ~= 8 px
MID_BG     total travel ~= 18 px
CHAR_ROOT  total camera contribution ~= 3 px
FG         total travel ~= 36 px
```

Character acting example:

```text
TORSO
    one breath cycle
    vertical mass travel on the order of a few px
    very small rotation

HEAD
    smaller counter-motion
    phase differs from torso

HAIR_FRONT
    follows head with lag

EARRING
    larger angular freedom than hair root

LAPEL / CLOTH TIP
    small delayed response
```

These values are starting magnitudes for a controlled experiment only. Rendered measurement determines whether they are useful.

---

## 12. MOTION HIERARCHY TEST

A shot should be readable if secondary motion is disabled.

Test in this order:

```text
A. ROOT + CAMERA only
B. + TORSO primary
C. + HEAD counter-motion
D. + HAIR
E. + ACCESSORY / CLOTH
```

If `A -> B` does not improve acting, do not hide the problem under hair/FX.

If `D/E` dominate attention, reduce or redesign secondary motion.

---

## 13. WHAT TO MEASURE

Per contract, report actual values rather than magic aesthetic scores.

For animated layers:

```text
position_px
rotation_rad
scale
velocity_px_s
angular_velocity_rad_s
acceleration_px_s2
jerk_px_s3
z_order
```

For important anchors:

```text
head center
visible eyes
hand tip if visible
hair tip
coat tip
accessory tip
```

For the full rendered frame:

```text
motion-energy centroid
foreground silhouette area
foreground centroid
parallax contribution
camera contribution
```

Aesthetic quantities remain measurements until a ZORR reference set calibrates them.

---

## 14. SILHOUETTE / IDENTITY PROTECTION

For approved reference art:

- keep face identity geometry protected;
- measure unintended silhouette drift after inverse rigid transform;
- do not let mesh deformation change important facial contours merely because the rig allows it;
- preserve explicit line-scaling policy under layer scaling.

A mathematically smooth mesh deformation that damages the approved silhouette is FAIL.

---

## 15. WHEN TO STOP RIGGING AND REDRAW

Rigging has reached its useful limit when:

```text
required motion reveals OCCLUDED_UNKNOWN
OR
required pose changes semantic silhouette
OR
mesh distortion changes identity/fashion design
OR
z-order needs unseen source art
OR
joint/pivot cannot be measured from authorized art
```

Then:

```text
STOP RIG PATCHING
-> NEW KEY DRAWING / SOURCE ART REQUIRED
```

This is preferable to a third deformation patch on a fundamentally unsuitable drawing.

---

## 16. RESULT-FIRST DEBUG ORDER

When a character motion looks wrong:

```text
1. first broken layer
2. geometry / split
3. pivot
4. parent transform
5. primary timing
6. secondary timing
7. z-order / occlusion
8. deformation
9. camera/parallax contribution
10. pixel re-measure
```

Do not rebuild the rig when the first defect is one wrong pivot or one bad layer split.

---

## 17. TRAINING LADDER

### T01 — ROOT VS CAMERA

Character HOLD, layered parallax only.

Goal: understand screen motion vs camera motion.

### T02 — TORSO BREATH

Add one primary torso motion only.

Goal: make mass feel alive without global sprite scaling.

### T03 — HEAD COUNTER-MOTION

Add head compensation.

Goal: break rigid-body feel.

### T04 — HAIR / ACCESSORY FOLLOW-THROUGH

Add one hair group and one accessory.

Goal: learn hierarchy and phase delay.

### T05 — CLOTH RESPONSE

Add one cloth panel/coat tip.

Goal: material-specific secondary motion.

### T06 — HYBRID KEY CHANGE

At a meaningful pose/emotion transition, replace the current drawing with a new key drawing instead of forcing the old mesh.

Goal: prove the rig serves drawing, not the reverse.

---

## 18. CURRENT ZORR DECISION

```text
PRIMARY 2D CHARACTER MICRO-MOTION = OpenToonz Plastic
PRIMARY CAMERA/PARALLAX = existing 2D scene/timeline capability
2.5D / 3D-AWARE CHARACTER RIG = Blender Grease Pencil Armature
SIMPLE CUTOUT = Synfig
CUSTOM DEFORMATION ENGINE = NOT JUSTIFIED
```

No custom solver is required for the current training goal.

---

## 19. TERMINAL PRINCIPLE

```text
STRONG KEY DRAWING
+ CORRECT LAYER AUTHORITY
+ PARENT/CHILD HIERARCHY
+ PRIMARY MOTION
+ PHASED SECONDARY MOTION
+ CAMERA/PARALLAX
+ PIXEL QC
=
LIVE 2D CHARACTER SHOT
```

And:

```text
RIG = MOTION ECONOMY.
KEY DRAWING = ACTING AUTHORITY.
```
