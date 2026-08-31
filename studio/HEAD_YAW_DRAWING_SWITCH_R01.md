# ZORR HEAD YAW DRAWING SWITCH R01

Status: TRAINING DESIGN
Gate: P05 after P01-P04 survive fresh render QC

## Question

Can the existing ZORR HEAD YAW drawings be used as discrete key-drawing states inside OpenToonz while Plastic supplies only local life/settle, without identity drift or a visible spatial pop?

## Source

Use the existing HEAD YAW source pack only.

First transition:
`FRONT -> 3/4`

Do not start with profile-to-profile. The first test should isolate a moderate topology change.

## OpenToonz mechanism

Plastic supports:
- a texture column containing one or more drawings;
- multiple skeletons on a mesh level;
- switching the active skeleton at a frame;
- a `Skeleton Id` animation channel in Function Editor.

Production use:
- `S_FRONT` = skeleton authored for FRONT drawing;
- `S_3Q` = skeleton authored for the selected 3/4 drawing.

The actual numeric Skeleton Id values are assigned by OpenToonz and are not canonized in advance.

## Hard law

Do NOT deform `S_FRONT` until the face becomes 3/4.

When visible topology changes:
`DRAWING STATE CHANGE + SKELETON STATE CHANGE`

Plastic then handles only:
- tiny settle;
- tiny pitch/tilt within the valid drawing;
- secondary response;
- local continuity.

## Mesh-envelope preflight

Before animating:
1. expose FRONT and selected 3/4 drawings in the intended texture column;
2. verify both drawings remain inside the mesh masking envelope used for the test;
3. do not translate/flip the source drawing underneath an already-bound mesh as a substitute for rigging;
4. if one drawing exceeds the safe mesh envelope, use a larger justified envelope or separate mesh/state rather than clipping/stretching the drawing.

## Controlled test variants

Keep constant:
- torso animation;
- camera;
- background;
- lighting/color;
- character screen position;
- costume;
- transition frame.

Change only switch treatment.

### P05-A — hard drawing/skeleton switch

Purpose: establish raw spatial mismatch.

No extra head settle around the switch.

Measure the immediate pixel jump.

### P05-B — registered drawing/skeleton switch

Register FRONT and 3/4 using visible anchors before exposure:
- neck attachment center;
- chin;
- eye midpoint;
- top of head / dominant hair envelope.

No face deformation to force a match.

Purpose: remove avoidable placement error while preserving real geometry change.

### P05-C — registered switch + local settle

Use the same registered drawings as B.

Add only a small post-switch head/neck settle using the correct skeleton for each drawing state.

Purpose: determine whether acting/timing can make the legitimate key-drawing change read as intentional motion rather than a pop.

## QC packet

At the switch frame record:
- `eye_midpoint_jump_px`
- `chin_jump_px`
- `neck_attachment_jump_px`
- `top_head_jump_px`
- `silhouette_area_delta_px2`
- `hair_envelope_delta_px`
- `screen_center_jump_px`

Also inspect:
- face topology preserved inside each drawing;
- neck does not detach from torso;
- earring attachment remains plausible;
- hair does not clip mesh boundary;
- z-order does not change accidentally;
- no mesh stretch is used to hide drawing mismatch.

## Interpretation

Zero pixel change is NOT the goal because FRONT and 3/4 are different legitimate drawings.

The goal is:
- remove accidental registration error;
- preserve identity;
- preserve neck attachment;
- make the topology change correspond to intentional head motion;
- prevent Plastic from becoming a redraw substitute.

## Fail routing

If P05 fails, classify first cause:
- `SOURCE_DRAWING_CONFLICT`
- `REGISTRATION`
- `MESH_ENVELOPE`
- `SKELETON_STATE`
- `PIVOT`
- `TIMING`
- `Z_ORDER`

Only fix the dominant cause.

Do not redesign the whole character and do not change animation software from one failed switch test.
