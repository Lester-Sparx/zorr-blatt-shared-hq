# ZORR CHARACTER LAYER SPLIT R01

Status: PROVISIONAL TRAINING MAP
Target: `OPENTOONZ CHARACTER LIFE SMOKE R01`

## Source authority

Use only the existing ZORR source pack:
- MASTER FRONT
- BODY TURNAROUND
- HEAD YAW
- DETAIL / COSTUME / ACCESSORY

This map describes visible production masses. It does NOT infer hidden anatomy under the suit.

Authority terms:
- `LOCKED_REFERENCE`
- `PIVOT_ONLY`
- `AFFINE`
- `MESH_DEFORM_ALLOWED`
- `UNKNOWN`

## First-smoke principle

The first life smoke is NOT a full puppet build.

Only build the minimum hierarchy needed to prove:
- breathing / torso life;
- head micro-acting;
- one secondary element;
- parallax;
- clean render.

Limbs hidden by tailored clothing are not granted invented joints simply because a human normally has them.

## Layer plan

| Layer ID | Visible source | Parent | Source authority | Deform authority | Pivot / attachment | R01 use |
|---|---|---|---|---|---|---|
| `CHAR_ROOT` | full figure | scene peg | LOCKED_REFERENCE | PIVOT_ONLY | ground/root transform | scene placement only |
| `TORSO_JACKET` | front torso | CHAR_ROOT | LOCKED_REFERENCE | MESH_DEFORM_ALLOWED | torso center / visible neck-belt axis | low-amplitude breathing only |
| `LAPEL_L` | front/detail | TORSO_JACKET | LOCKED_REFERENCE | AFFINE | attachment along jacket chest seam | follow torso; preserve lapel geometry |
| `LAPEL_R` | front/detail | TORSO_JACKET | LOCKED_REFERENCE | AFFINE | attachment along jacket chest seam | follow torso; preserve lapel geometry |
| `SHIRT_OPENING` | front/detail | TORSO_JACKET | LOCKED_REFERENCE | AFFINE | sternum opening region | minimal follow only |
| `CHAIN` | front/detail | TORSO_JACKET | LOCKED_REFERENCE | AFFINE | visible neck/chest attachment | secondary candidate after earring test |
| `NECK_VISIBLE` | front/head/detail | TORSO_JACKET | LOCKED_REFERENCE | AFFINE | base at visible collar/neck junction | tiny counter-motion only |
| `HEAD_FRONT_CORE` | master/head yaw front | NECK_VISIBLE | LOCKED_REFERENCE | PIVOT_ONLY | visible neck/head junction | identity protected; no yaw deformation |
| `FACE_CORE` | master/head yaw | HEAD_FRONT_CORE | LOCKED_REFERENCE | RIGID | n/a | no Plastic deformation in R01 |
| `HAIR_REAR_MASS` | head yaw | HEAD_FRONT_CORE | LOCKED_REFERENCE | AFFINE | scalp/root region visible in source | later secondary test |
| `HAIR_FRONT_CLUSTERS` | head yaw | HEAD_FRONT_CORE | LOCKED_REFERENCE | AFFINE | forehead/scalp root region | later secondary test; cluster motion, not strand noise |
| `EARRING_L` | head/detail | HEAD_FRONT_CORE | LOCKED_REFERENCE | PIVOT_ONLY | visible ear attachment | preferred first secondary test |
| `EARRING_R` | head/detail | HEAD_FRONT_CORE | LOCKED_REFERENCE | PIVOT_ONLY | visible ear attachment | preferred first secondary test |
| `BUTTONS_JACKET` | front/detail | TORSO_JACKET | LOCKED_REFERENCE | RIGID | inherited | preserve spacing; no rubber deformation |
| `BELT_BUCKLE` | front/detail | CHAR_ROOT | LOCKED_REFERENCE | RIGID | visible belt center | QC anchor; no deformation |
| `WATCH_BODY` | detail/front | WRIST_VISIBLE | LOCKED_REFERENCE | RIGID | visible wrist attachment | preserve shape |
| `ARM_L_VISIBLE` | front/turnaround | TORSO_JACKET | LOCKED_REFERENCE | UNKNOWN | elbow under sleeve not proven | freeze in first smoke |
| `ARM_R_VISIBLE` | front/turnaround | TORSO_JACKET | LOCKED_REFERENCE | UNKNOWN | elbow under sleeve not proven | freeze in first smoke |
| `WRIST_L_VISIBLE` | front/detail | ARM_L_VISIBLE | LOCKED_REFERENCE | PIVOT_ONLY | cuff/wrist boundary visible | freeze initially |
| `WRIST_R_VISIBLE` | front/detail | ARM_R_VISIBLE | LOCKED_REFERENCE | PIVOT_ONLY | cuff/wrist boundary visible | freeze initially |
| `HAND_L` | front | WRIST_L_VISIBLE | LOCKED_REFERENCE | PIVOT_ONLY | visible wrist boundary | no hand redesign; drawing-switch candidate later |
| `HAND_R` | front | WRIST_R_VISIBLE | LOCKED_REFERENCE | PIVOT_ONLY | visible wrist boundary | no hand redesign; drawing-switch candidate later |
| `TROUSER_MASS` | front/turnaround | CHAR_ROOT | LOCKED_REFERENCE | UNKNOWN | hidden pelvis/knee anatomy not proven | freeze in first smoke |
| `LEG_L_VISIBLE` | front/turnaround | TROUSER_MASS | LOCKED_REFERENCE | UNKNOWN | knee under trouser not proven | freeze in first smoke |
| `LEG_R_VISIBLE` | front/turnaround | TROUSER_MASS | LOCKED_REFERENCE | UNKNOWN | knee under trouser not proven | freeze in first smoke |
| `SHOE_L` | front/detail | LEG_L_VISIBLE | LOCKED_REFERENCE | RIGID | visible ankle/shoe junction | ground-contact QC anchor |
| `SHOE_R` | front/detail | LEG_R_VISIBLE | LOCKED_REFERENCE | RIGID | visible ankle/shoe junction | ground-contact QC anchor |

## Head-angle states

Do not deform `HEAD_FRONT_CORE` into a 3/4 or profile view.

Use separate drawing states from HEAD YAW:
- `HEAD_YAW_M90`
- `HEAD_YAW_M45`
- `HEAD_YAW_0`
- `HEAD_YAW_P45`
- `HEAD_YAW_P90`

Each state preserves its own approved visible topology.

Plastic may animate micro-settle inside one state. A topology-changing yaw requires a drawing switch / new key drawing.

## Plastic mesh-envelope law

Once a texture column is bound to a Plastic mesh:
- deformation belongs to the mesh/skeleton;
- do not reposition the source drawing independently and expect the mesh mask to follow;
- any drawing variants intentionally exposed under the same mesh must remain inside that mesh's mask/envelope;
- if a variant exceeds the safe envelope, use a deliberately larger valid envelope or a separate mesh/state instead of stretching or clipping the drawing.

This rule is especially important for future head, hand and costume drawing switches.

## First-smoke hierarchy

Minimal hierarchy for P01-P04:

`SCENE_ROOT`
-> `CHAR_ROOT`
   -> `TORSO_JACKET`
      -> `LAPEL_L`
      -> `LAPEL_R`
      -> `SHIRT_OPENING`
      -> `NECK_VISIBLE`
         -> `HEAD_FRONT_CORE`
            -> `FACE_CORE`
            -> `HAIR_REAR_MASS`
            -> `HAIR_FRONT_CLUSTERS`
            -> `EARRING_L`
            -> `EARRING_R`
   -> frozen arm/hand columns
   -> frozen trouser/leg/shoe columns

Feet and lower body remain fixed while the first upper-body life test is calibrated.

## QC anchors for R01

Use visible source-derived anchors only:
- top of head;
- eye midpoint;
- chin;
- neck base / collar junction;
- shoulder outer silhouette L/R;
- jacket button centers;
- belt buckle center;
- wrist/cuff boundaries;
- shoe contact points.

Do not create hidden hip, knee or elbow coordinates until a dedicated construction source provides them.

## Exit condition

This map becomes `READY_FOR_SMOKE` only when every layer used in the smoke has:
- stable ID;
- parent;
- source authority;
- deform authority;
- visible/measured pivot or explicit UNKNOWN;
- defined QC anchors where identity/grounding can drift.
