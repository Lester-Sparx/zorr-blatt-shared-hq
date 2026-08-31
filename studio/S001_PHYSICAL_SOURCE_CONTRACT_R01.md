# S001 PHYSICAL SOURCE CONTRACT R01

STATUS = `PREP_ONLY / SOURCES_NOT_BUILT / NO_BUILD_AUTHORITY`
TRACKER = `#250`
WORKSTREAM = `DUNCAN PRIME / WORKSTREAM B`

## PURPOSE

Define the exact physical source-package requirements for later S001 construction while upstream character/costume/pose/camera gates are still unresolved.

This file specifies required source families, registration, coverage, depth/occlusion metadata and QC evidence. It does not authorize creation of S001 physical assets.

## HARD BOUNDARIES

- Do not redesign character identity or costume.
- Do not infer hidden anatomy or hidden garment structure beyond accepted source authority.
- Do not build S001 physical assets before legal upstream handoff.
- Do not turn Babylon into scene master.
- Do not generate/edit images without exact OWNER authorization.
- Do not assign final shot dimensions, FPS, overscan or camera envelopes until S001 contract resolves them.

## REQUIRED PHYSICAL SOURCE FAMILIES

Minimum scene-source families are:

`BG / MID / FG / CHAR`

Not every shot must use every optional sublayer, but every actual source used by S001 must belong to a declared family and have a stable ID.

### BG — BACKGROUND

Purpose:
- far architecture / room / horizon / wall / large stable spatial field;
- establishes readable world geometry and distant value mass.

Required metadata:
- stable layer ID;
- source file/revision;
- native raster/vector bounds;
- alpha policy;
- registration origin;
- intended screen/depth role;
- whether camera-relative or world-relative;
- coverage bounds for all declared camera extrema;
- allowed intentional crop, if any.

Hard fails:
- uncovered source edge during legal camera envelope;
- world perspective contradicts the intended grounding without an authored impossible-system event;
- background detail density outranks character authority.

### MID — MIDGROUND

Purpose:
- architecture/furniture/props/planes that provide spatial separation between BG and CHAR/FG;
- may carry contact or occlusion relationships if explicitly declared.

Required metadata:
- stable layer ID;
- source/revision;
- depth rank;
- registration anchors;
- transform authority;
- occlusion policy relative to CHAR;
- coverage bounds;
- parallax tracking anchor.

Hard fails:
- accidental occlusion of protected identity/attention anchors;
- depth ordering changes silently between frames;
- contact relation drifts under camera move because of wrong parenting.

### FG — FOREGROUND

Purpose:
- intentional near-camera mass, frame intrusion, architecture, prop, graphic shape or atmospheric plane;
- may increase camera pressure and depth readability.

Required metadata:
- stable layer ID;
- source/revision;
- depth rank;
- entry/exit frames if animated relative to aperture;
- allowed overlap target(s);
- forbidden overlap target(s);
- parallax tracking anchor;
- coverage margin at camera extremes.

Hard fails:
- random foreground clutter;
- accidental face/eye/primary-silhouette occlusion;
- FG motion that implies a different depth order than declared;
- source edge exposure unless entry/exit is intentional and recorded.

### CHAR — CHARACTER PACKAGE

Purpose:
- exact accepted ZORR character sources needed for S001 after upstream mechanics/pose gates.

Source authority must remain traceable to accepted character/model/costume sheets and later approved pose/source package.

Required metadata:
- stable character package revision;
- exact source authority references;
- declared pose/key state;
- logical layer IDs and parent relationships;
- deform authority per layer;
- visible registration/QC anchors;
- ground/contact anchors used in S001;
- protected face/fashion/silhouette regions;
- source coverage bounds including any legal animation/deformation envelope.

Character-package rules:
- topology-changing head yaw requires approved drawing state/key switch, not face warp;
- hidden joints are not invented merely to fit camera staging;
- costume attachment invariants from the mechanics gate remain authoritative;
- camera/world integration may not silently repair character mechanics by changing costume/body design.

## SCENE ROOT / REGISTRATION CONTRACT

Every physical source package must declare one shot registration system.

Required fields:
- `SCENE_ROOT` identifier;
- reference frame;
- output coordinate mapping;
- world/scene origin in the chosen 2D/2.5D scene representation;
- stable registration anchor for each source family;
- CHAR root/ground relation;
- whether each family inherits camera/world transforms or owns independent animation.

No source may be hand-shifted between revisions without updating its registration record.

## SOURCE BOUNDS

For each source layer `L`, record source-space visible bounds:

`B_L = [x_min, x_max] x [y_min, y_max]`

and, after transform at frame `f`, screen-space bounds:

`S_L(f)`.

For any layer required to fill the aperture, legal coverage requires:

`A_required(f) subseteq S_L(f)`

where `A_required(f)` is the output aperture plus declared overscan relevant to that layer.

Because S001 output and overscan are unresolved, exact numeric coverage cannot yet be calculated.

Current state:

`SOURCE_COVERAGE_NUMBERS = NOT_PROVEN`

## DEPTH ORDER CONTRACT

Every legal physical build must declare an ordered depth list, for example semantically:

`FG_NEAR -> CHAR -> MID -> BG_FAR`

but the actual S001 order must be explicitly resolved rather than copied from this example.

For each layer pair that may overlap, record:
- expected front/back relation;
- whether the relation may change;
- frames/conditions of any intentional change;
- protected overlap boundaries.

Unexpected z-order inversion = FAIL.

## PARALLAX ANCHORS

Every moving depth family used in parallax proof must expose at least one stable trackable anchor.

Required per tested family:
- anchor ID;
- source coordinate;
- screen coordinate at reference frame;
- screen coordinate at camera extremum;
- displacement vector and magnitude in px;
- expected relative displacement ordering based on declared depth.

No camera/parallax PASS from curve values alone.

## OCCLUSION METADATA

For each layer capable of covering CHAR, define:
- `OCCLUDER_ID`;
- permitted target region(s);
- forbidden target region(s);
- intentional overlap frame range;
- whether overlap is narrative/compositional or purely spatial;
- first failing frame if overlap exceeds the authored policy.

Protected targets may include, depending on actual framing:
- eye/brow authority region;
- face/jaw identity region;
- primary hand/prop punctuation;
- fashion silhouette anchor;
- ground/contact anchor.

The actual protected set is shot-specific and remains `NOT_PROVEN` until framing is resolved.

## CHARACTER / WORLD CONTACT

If S001 shows foot/floor, hand/object or body/furniture contact, record paired visible anchors.

For each pair:

`e_contact(f) = ||p_char(f) - p_world(f)||_2`

Units: output px.

Shot-specific tolerance must be set after output raster and intended motion are resolved.

Current state:

`CONTACT_TOLERANCE_PX = NOT_PROVEN`

## SOURCE SEPARATION REQUIREMENTS

The eventual OpenToonz source package must preserve independent control where the shot requires it.

At minimum distinguish:
- character package from environment;
- major scene depth families;
- any FG occluder that moves/parallaxes independently;
- any world element with a distinct contact/occlusion job;
- any character secondary-motion family authorized by the upstream source package.

Do not flatten layers merely for convenience if flattening destroys required parallax, occlusion, contact or QC traceability.

Conversely, do not split decorative micro-layers that have no production control purpose.

## FILE / REVISION MANIFEST — FUTURE REQUIRED SHAPE

When physical source creation becomes legal, the package must record at least:

| Field | Requirement |
|---|---|
| `PACKAGE_REV` | exact immutable/reviewable revision |
| `SHOT_CONTRACT_REV` | exact S001 contract binding |
| `CAMERA_LAYOUT_REV` | exact layout binding |
| `CHAR_PACKAGE_REV` | exact approved character/source binding |
| `LAYER_ID` | stable unique ID |
| `FAMILY` | BG/MID/FG/CHAR |
| `SOURCE_PATH` | exact path |
| `SOURCE_HASH_OR_BLOB` | exact durable identity when practical |
| `NATIVE_SIZE` | px or vector document bounds |
| `ALPHA_MODE` | explicit |
| `REGISTRATION_ANCHOR` | explicit |
| `DEPTH_RANK` | explicit |
| `TRANSFORM_AUTHORITY` | explicit |
| `COVERAGE_STATUS` | measured result |
| `OCCLUSION_POLICY` | explicit |
| `QC_ANCHOR_IDS` | explicit where applicable |

## PHYSICAL BUILD ENTRY GATE

`S001 PHYSICAL SHOT BASE` remains closed until all of the following are true:
- `COSTUME_MECHANICS_R01 = PASS`;
- required pose-mechanics gate = PASS;
- `CAMERA_LAYOUT_VISUAL_R01` legally opens and receives measured visual evidence;
- S001 aspect/output/FPS/framing/overscan/camera envelope are resolved;
- world/layout decisions are specific enough to define actual source extents;
- exact character package revision exists;
- MASTER / DUNCAN PRIME INTEGRATOR authorizes the downstream transition from fresh durable evidence.

Until then:

`PHYSICAL_SOURCE_REQUIREMENTS = PREPARED`
`PHYSICAL_SOURCES = NOT_BUILT`
`S001_PHYSICAL_BASE = BLOCKED_BY_UPSTREAM_GATES`

## NEXT

Persist Workstream B RESULT / EVIDENCE / OPEN / NEXT to issue #250 with exact commit bindings. No downstream PASS claim.