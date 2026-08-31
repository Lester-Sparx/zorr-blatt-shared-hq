# CAMERA LAYOUT VISUAL R01

STATUS = `PREP_ONLY / GATE_NOT_OPEN / NO_PASS_AUTHORITY`
TRACKER = `#250`
WORKSTREAM = `DUNCAN PRIME / WORKSTREAM B`
BRANCH = `duncan/zorr-studio-r01`

## PURPOSE

Prepare the exact measurable contract that `CAMERA_LAYOUT_VISUAL_R01` must satisfy once the upstream route legally opens it.

This document is not a camera-layout PASS, not an S001 shot lock, and not authorization to build physical shot assets.

Current route authority remains:

`#245 FULL_CHARACTER_MODEL_LOCK_R02 = PASS`
`-> #248 COSTUME_MECHANICS_R01`
`-> POSE_MECHANICS_VISUAL_R01`
`-> CAMERA_LAYOUT_VISUAL_R01`

At this checkpoint `#248 COSTUME_MECHANICS_R01 != PASS`, so this file may define requirements only.

## AUTHORITY BOUNDARIES

Frozen:
- accepted character identity from `FULL_CHARACTER_MODEL_LOCK_R02`;
- accepted costume identity and attachment facts;
- 2D-first / OpenToonz-primary production hierarchy;
- Babylon is optional spatial evidence only if a real geometry blocker is proven;
- no image generation/editing is authorized by this spec;
- no camera decision may silently redesign character, costume, pose mechanics, line/color/material state, or world canon.

Provisional taste evidence only:
- `SEVERE LUXURY + GRAPHIC ARCHITECTURE + CONTROLLED UNEASE`;
- camera pressure through purposeful low/close framing, crop, foreground intrusion, negative space and strong directional geometry;
- `READABLE REAL SPACE + LARGE QUIET MATERIAL MASSES + ONE STRONG LIGHT FIELD + OPTIONAL ONE IMPOSSIBLE SYSTEM`.

These are candidate ZORR directions from OWNER-reference evidence. They are not production canon merely because they are listed here.

## CORE CAMERA LAW

`CAMERA MUST SERVE CHARACTER AUTHORITY, SHOT INTENT, DEPTH READABILITY AND MEASURABLE SOURCE COVERAGE.`

Not:

`CAMERA = DECORATIVE MOTION OR RANDOM DISTORTION.`

A camera/layout witness may use pressure, crop, foreground intrusion or asymmetry only when its dramatic job is stated and the character remains readable.

## COORDINATE SYSTEM

All quantitative review begins in output pixels.

Let:
- output raster = `W_out x H_out` px;
- screen origin = top-left `(0,0)`;
- `+x` = right;
- `+y` = down;
- screen point = `p = (x_px, y_px)`;
- normalized point = `p_n = (x_px / W_out, y_px / H_out)`;
- frame time = integer frame `f` unless a later contract explicitly requires subframe evaluation.

No numeric camera judgement is valid until `W_out`, `H_out` and frame rate are resolved for the shot.

## REQUIRED SHOT-FORMAT INPUTS

Before physical layout production or terminal camera PASS, the exact S001 shot contract must resolve:

| Field | Required representation | Current state |
|---|---|---|
| Aspect ratio | exact rational or exact integer raster relation | `9:16 = S001 ASSUMPTION ONLY` |
| Output resolution | `W_out x H_out` px | `NOT_PROVEN` |
| FPS | frames/second | `NOT_PROVEN` |
| Shot duration | frames and seconds | `NOT_PROVEN` |
| Reference frame | exact layout frame number | `NOT_PROVEN` |
| Framing state | declared shot scale / crop / protected anchors | `NOT_PROVEN` |
| Overscan | px per side and normalized fractions | `NOT_PROVEN` |
| Max camera translation | `dx_max`, `dy_max` in output px | `NOT_PROVEN` |
| Max push/zoom | dimensionless scale ratio relative to reference | `NOT_PROVEN` |
| Max camera roll | degrees | `NOT_PROVEN` |
| Depth order | declared ordered set of physical layer families | `NOT_PROVEN` |

The deferred 48f / 24fps / 1920x1080 character-life smoke values are experimental smoke values and do not silently resolve S001.

## CAMERA ENVELOPE VARIABLES

The layout gate must record the following variables instead of hiding them inside an animation curve:

### Translation

For a reference camera state at frame `f0`:

`dx(f) = x_cam(f) - x_cam(f0)`

`dy(f) = y_cam(f) - y_cam(f0)`

Record:

`dx_max = max_f |dx(f)|`

`dy_max = max_f |dy(f)|`

Units: output px after the declared scene-to-screen transform.

### Push / zoom

Let `s_cam(f)` be the scene-to-screen scale at frame `f` and `s_cam(f0)` the reference scale.

`push_ratio(f) = s_cam(f) / s_cam(f0)`

Record:

`push_ratio_max = max_f push_ratio(f)`

`push_ratio_min = min_f push_ratio(f)`

Do not describe a push as `small`, `medium` or `cinematic` without the numeric ratio once the shot is in measurable layout.

### Roll

`roll_deg(f)` = camera roll relative to the declared reference state.

Record:

`roll_abs_max = max_f |roll_deg(f)|`

Random Dutch-angle use with no dramatic job is a layout FAIL even if source coverage succeeds.

### Overscan

Record side-specific coverage margins:
- `O_L_px`
- `O_R_px`
- `O_T_px`
- `O_B_px`

And normalized forms:

`O_L_n = O_L_px / W_out`
`O_R_n = O_R_px / W_out`
`O_T_n = O_T_px / H_out`
`O_B_n = O_B_px / H_out`

No default overscan percentage is authorized here.

## CHARACTER PROTECTION ANCHORS

Layout review must track visible approved anchors, not hidden anatomy:
- top of head;
- eye midpoint;
- chin;
- neck base / collar junction;
- shoulder outer silhouette L/R;
- jacket button centers where visible;
- belt buckle center where visible;
- wrist/cuff boundaries where visible;
- shoe contact points when present in frame.

For each protected anchor used by the shot, record:
- reference screen coordinate in px;
- normalized coordinate;
- whether crop/occlusion is `FORBIDDEN`, `ALLOWED_IF_AUTHORED`, or `INTENTIONAL`;
- first frame where the state changes.

A deliberate hard crop or foreground occlusion can be valid only if it has a stated shot job. Accidental loss of face/identity/silhouette is FAIL.

## FRAMING CONTRACT

Every camera-layout candidate must state:

1. **Primary read** — what the eye should read first.
2. **Character read** — full silhouette, partial silhouette, face, hand/prop punctuation, or another explicitly declared target.
3. **Pressure mechanism** — camera height, crop, foreground intrusion, negative space, axis compression, scale, or none.
4. **Protected region** — the character/face/fashion region that must remain readable.
5. **Negative-space job** — what the empty area is doing compositionally.
6. **Depth job** — why the selected BG/MID/FG separation exists.
7. **Motion job** — if camera moves, what new information or pressure the move creates.

If the camera move changes none of composition, information, pressure, depth read or narrative emphasis, remove it from the critical path.

## WORLD / CHARACTER AUTHORITY ORDER

For the current ZORR direction:

`CHARACTER IDENTITY / FASHION SILHOUETTE > SHOT ATTENTION ANCHOR > WORLD DETAIL DENSITY.`

World geometry may pressure the character but may not become uncontrolled level-design clutter.

Preferred world construction candidate:

`READABLE REAL SPACE`
`+ LARGE QUIET MATERIAL MASSES`
`+ ONE STRONG LIGHT FIELD`
`+ OPTIONAL SINGLE IMPOSSIBLE SYSTEM`

Hard rejects:
- generic game-cinematic PBR logic as final authority;
- constant neon-city noise;
- every surface emissive;
- decorative props with no staging job;
- perspective distortion with no authored reason;
- impossible geometry that makes character grounding unreadable;
- background texture/detail that outranks the character face or fashion mass.

## PARALLAX MEASUREMENT CONTRACT

When a camera/parallax witness becomes legal, define one stable screen-space anchor per tested layer family.

For layer `L`:

`d_L = p_L(f1) - p_L(f0)`

`D_L = ||d_L||_2` in px.

The intended depth order must be declared before judging the result.

For a conventional lateral move where authored layer order is `FG -> CHAR/MID -> BG`, a valid witness normally requires nearer layers to show larger screen displacement magnitude than farther layers. The exact inequality must follow the declared arrangement rather than a universal hard-coded order.

At minimum record:
- `D_FG_px` if FG exists;
- `D_CHAR_px` or declared fixed-character screen policy;
- `D_MID_px` if MID exists;
- `D_BG_px`;
- displacement direction/sign;
- the first frame where expected order breaks, if any.

Curve inspection alone cannot prove parallax. Required sequence:

`SET CAMERA -> RENDER -> TRACK ANCHORS -> MEASURE PX -> PASS/FAIL`

## GROUND / PARENTING CHECK

Character placement must preserve intentional contact with the world.

For each visible shoe contact anchor `q_char(f)` and corresponding declared ground anchor `q_ground(f)`:

`e_ground(f) = ||q_char(f) - q_ground(f)||_2`

Record the maximum screen error in px and the exact tolerance selected for the shot.

`epsilon_ground_px = NOT_PROVEN` until the shot contract and render scale exist.

Do not invent a universal tolerance here.

Unexpected contact drift caused by wrong parenting is FAIL.

## SOURCE COVERAGE CHECK

Every layer that is intended to fill the camera aperture at a frame must cover the complete transformed output aperture plus declared overscan.

For each such layer and each camera extremum, record:
- transformed visible bounds;
- required aperture bounds;
- uncovered edge count / first uncovered pixel region if failure occurs.

Unexpected transparent edge, clipped texture, missing paint or source boundary exposure = FAIL.

Intentional entry/exit of an FG occluder is exempt only when declared as shot behavior.

## OCCLUSION CHECK

Every occluder must have:
- stable layer ID;
- declared depth rank;
- declared target region it may cover;
- declared frames where coverage is intentional.

Record character overlap area when useful:

`R_occ(f) = A(CHAR alpha intersect OCC alpha) / A(CHAR alpha)`

No universal acceptable ratio is authorized here. The shot must set a threshold only after the actual composition exists.

Hard law independent of ratio:

`ACCIDENTAL OCCLUSION OF THE PRIMARY IDENTITY / ATTENTION ANCHOR = FAIL.`

## LAYOUT WITNESS PACKAGE — FUTURE GATE REQUIREMENT

Once upstream gates legally open camera layout, the witness package must contain, at minimum:
- exact shot-contract revision;
- exact source-package revision;
- reference frame render;
- camera-extreme renders;
- overlay or table of protected anchor coordinates;
- camera translation / push / roll measurements;
- source-coverage evidence;
- parallax measurements when movement exists;
- occlusion/grounding notes;
- explicit failure-frame list if any.

No terminal PASS from prose alone.

## PASS / FAIL BOUNDARY

`CAMERA_LAYOUT_VISUAL_R01 = PASS` may be considered only after:
- upstream route legally opens this gate;
- shot format values required for measurement are resolved;
- real visual layout witnesses exist;
- rendered/measured evidence confirms source coverage and intended depth behavior;
- character identity/fashion read survives the layout;
- accidental crop/occlusion/ground drift are absent;
- the camera has an explicit dramatic/compositional job;
- MASTER / DUNCAN PRIME INTEGRATOR performs the legal promotion from fresh evidence.

Until then:

`CAMERA_LAYOUT_VISUAL_R01 = NOT_OPEN / PREP_ONLY`

## CURRENT OPEN ITEMS

- S001 aspect ratio is still only `9:16 ASSUMPTION`.
- `W_out x H_out = NOT_PROVEN`.
- `FPS = NOT_PROVEN`.
- shot duration = `NOT_PROVEN`.
- framing/protected crop policy = `NOT_PROVEN`.
- overscan = `NOT_PROVEN`.
- max translation/push/roll = `NOT_PROVEN`.
- physical BG/MID/FG/CHAR source package = not yet built or authorized.
- camera visual witnesses = not yet legal under current upstream gate state.

## NEXT LEGAL STEP FOR WORKSTREAM B

Prepare the S001 shot-contract matrix and the physical BG/MID/FG/CHAR source contract using the variables above, without assigning unresolved numeric values and without claiming downstream PASS.
