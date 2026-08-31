# S001 SHOT CONTRACT R01

STATUS = `PREP_ONLY / NOT_LOCKED / NO_PHYSICAL_BUILD_AUTHORITY`
TRACKER = `#250`
WORKSTREAM = `DUNCAN PRIME / WORKSTREAM B`

## PURPOSE

Define the exact S001 contract fields that must be resolved before physical BG/MID/FG/CHAR assets or a shot base are built.

This document distinguishes:
- `RESOLVED` = explicitly proven/locked by current durable authority;
- `ASSUMPTION` = currently useful working premise that must not be promoted silently;
- `NOT_PROVEN` = no valid value exists yet.

## CURRENT CONTRACT MATRIX

| Contract field | State | Current value / authority | Promotion requirement |
|---|---|---|---|
| Shot ID | `RESOLVED` | `S001` | immutable identifier unless OWNER/master explicitly supersedes |
| Production hierarchy | `RESOLVED` | 2D-first / OpenToonz-primary | current studio law |
| Babylon role | `RESOLVED` | optional spatial evidence only if real geometry blocker exists | blocker evidence required before use on critical path |
| Character identity authority | `RESOLVED` | `FULL_CHARACTER_MODEL_LOCK_R02 = PASS` | preserve accepted model |
| Costume mechanics | `NOT_PROVEN` | active gate `#248`; terminal PASS absent | six bounded visual witnesses + fresh matrix check + legal promotion |
| Pose mechanics | `NOT_PROVEN` | downstream of costume mechanics | legal gate opening + visual proof |
| Camera layout | `NOT_PROVEN` | prep requirements only in `CAMERA_LAYOUT_VISUAL_R01.md` | legal gate opening + rendered/measured witnesses |
| Aspect ratio | `ASSUMPTION` | `9:16` is S001-specific only | explicit S001 lock before physical shot build |
| Output raster | `NOT_PROVEN` | none | exact `W_out x H_out` px |
| FPS | `NOT_PROVEN` | none | exact fps |
| Duration | `NOT_PROVEN` | none | exact frames + seconds |
| Reference/layout frame | `NOT_PROVEN` | none | exact frame number |
| Framing / shot scale | `NOT_PROVEN` | none | declared primary read + protected anchors/crop policy |
| Overscan | `NOT_PROVEN` | none | exact px per side + normalized fractions |
| Max camera translation | `NOT_PROVEN` | none | exact px envelope derived from legal layout |
| Max push/zoom | `NOT_PROVEN` | none | exact scale-ratio envelope derived from legal layout |
| Max roll | `NOT_PROVEN` | none | exact degree envelope derived from legal layout |
| BG/MID/FG/CHAR depth order | `NOT_PROVEN` | source contract prepared separately; shot-specific order not yet locked | legal layout decision |
| World direction | `ASSUMPTION` | `SEVERE LUXURY + GRAPHIC ARCHITECTURE + CONTROLLED UNEASE` from OWNER-taste evidence | successful ZORR-specific application + master/OWNER promotion |
| World impossible-system event | `NOT_PROVEN` | optional concept only | shot intent must require exactly one authored spatial violation |
| Lighting field | `NOT_PROVEN` | one-strong-field principle is provisional direction | legal design/color/material gate |
| Physical source package | `NOT_PROVEN` | requirements only | exact files/layers + source coverage proof |
| S001 physical shot base | `NOT_PROVEN` | blocked | upstream gates + resolved shot contract + source package |

## NON-SUBSTITUTION LAW

The deferred character-life smoke values:
- 48 frames;
- 24 fps;
- 1920x1080;

are experiment values only unless a later exact S001 authority explicitly adopts them.

Therefore:

`SMOKE DEFAULT != S001 CONTRACT`

## REQUIRED S001 HEADER BEFORE PHYSICAL BUILD

The first legal physical-build revision must include a complete header in this exact semantic form:

```text
SHOT_ID = S001
CONTRACT_REV = <exact revision>
ASPECT = <exact rational>
OUTPUT = <W_out>x<H_out> px
FPS = <exact>
DURATION_FRAMES = <exact>
DURATION_SECONDS = <derived exact or stated rational/decimal>
REFERENCE_FRAME = <exact>
FRAMING = <declared>
OVERSCAN_L/R/T/B = <exact px>
CAMERA_TRANSLATION_MAX_X/Y = <exact px>
CAMERA_PUSH_MIN/MAX = <exact ratio>
CAMERA_ROLL_ABS_MAX = <exact degrees>
DEPTH_ORDER = <ordered layer families>
SOURCE_PACKAGE_REV = <exact revision>
UPSTREAM_GATE_BINDINGS = <exact gate states/revisions>
```

Any missing required field keeps physical S001 build closed unless the field is explicitly proven irrelevant for the chosen shot.

## FRAMING DECISION RECORD

When pose mechanics legally hands off to camera, record:
- intended primary read;
- intended emotional/psychological pressure;
- character crop policy;
- face/eye protection policy;
- fashion/silhouette protection policy;
- foreground intrusion policy;
- negative-space job;
- camera-height job;
- whether the camera moves or is static;
- if moving, what information/pressure/depth change the move creates.

No `dynamic camera` language is accepted without the measurable envelope in the camera contract.

## WORLD DECISION RECORD

A future S001 world lock must state which of these are actually used:
- readable real space;
- large quiet dark/ivory material masses;
- sparse metal/glass/reflective accents;
- one strong light field;
- checker/grid/perspective evidence where useful;
- one optional impossible system.

If an impossible system exists, it must be exactly named, for example:
- floor perspective bends;
- corridor width/vanishing logic becomes impossible;
- reflection disagrees with real space;
- one repeated symbol invades perspective;
- scale relation changes once deliberately.

Multiple unrelated surreal systems in one shot require explicit master justification; otherwise treat as uncontrolled decorative noise.

## FORMAT DERIVATIONS

Once aspect and output are resolved, verify:

`W_out / H_out = declared aspect ratio`

within exact integer-raster equivalence or an explicitly documented pixel-aspect rule.

Once fps and frame duration are resolved:

`duration_seconds = duration_frames / fps`

Record both values. Do not eyeball timing from playback alone.

## CHANGE CONTROL

After physical source production begins, changes to any of the following are contract-breaking unless explicitly revalidated:
- aspect ratio;
- output raster;
- overscan;
- reference framing;
- camera movement envelope;
- depth order;
- source registration rules.

A contract-breaking change requires source-coverage and layout re-check. Old evidence does not automatically survive the change.

## TERMINAL STATE

Current state:

`S001_SHOT_CONTRACT_R01 = PREPARED_FIELDS / NOT_LOCKED`

This is not:
- S001 PASS;
- camera PASS;
- world canon lock;
- source-package readiness;
- physical-shot authorization.

## NEXT

Bind this matrix to the physical BG/MID/FG/CHAR source requirements, then record the Workstream B checkpoint in issue #250. Do not assign unresolved values.