# S001 SHOT CONTRACT R02

STATUS = `PREPARED FIELDS / NOT_LOCKED / NO_PHYSICAL_BUILD_AUTHORITY`
ACTIVE_PRODUCT_STREAM = #251
PREP_ORIGIN = former #250 / reusable evidence

## PURPOSE
Define what must be known about S001 when S001 is actually selected as the first real production shot. This contract must not manufacture a shot merely because an identifier and technical fields exist.

State vocabulary:
- `RESOLVED` = explicitly proven/locked by current durable authority;
- `ASSUMPTION` = useful working premise, never silent authority;
- `NOT_PROVEN` = no valid value/decision exists yet.

## CURRENT CONTRACT MATRIX

| Contract field | State | Current value / authority |
|---|---|---|
| Shot ID | `RESOLVED` | `S001` identifier exists |
| Shot story beat / narrative intent | `NOT_PROVEN` | no exact durable S001 beat found in current studio contract |
| Character action / pose target | `NOT_PROVEN` | no exact real production pose/key drawing selected |
| Primary visual read | `NOT_PROVEN` | none |
| Emotional / psychological pressure | `NOT_PROVEN` | none |
| Character identity authority | `RESOLVED` | #245 `FULL_CHARACTER_MODEL_LOCK_R02 = PASS` |
| Costume mechanics | `SUPPORTING_QC` | #248 on-demand controls; apply only relevant force classes to real pose |
| Pose mechanics | `NOT_PROVEN` | must be proven on the selected real key drawing / scene-bound pose |
| Camera layout | `NOT_PROVEN` | PREP requirements exist in `CAMERA_LAYOUT_VISUAL_R01.md`; no real layout selected |
| Aspect ratio | `ASSUMPTION` | `9:16` S001-specific working assumption only |
| Output raster | `NOT_PROVEN` | none |
| FPS | `NOT_PROVEN` | none |
| Duration | `NOT_PROVEN` | none |
| Reference/layout frame | `NOT_PROVEN` | none |
| Framing / shot scale | `NOT_PROVEN` | none |
| Overscan | `NOT_PROVEN` | none |
| Camera translation envelope | `NOT_PROVEN` | none |
| Camera push/zoom envelope | `NOT_PROVEN` | none |
| Camera roll envelope | `NOT_PROVEN` | none |
| BG/MID/FG/CHAR depth order | `NOT_PROVEN` | source requirements prepared separately; shot-specific order absent |
| World direction | `ASSUMPTION` | `SEVERE LUXURY + GRAPHIC ARCHITECTURE + CONTROLLED UNEASE` as OWNER-taste evidence, not lock |
| Lighting field | `NOT_PROVEN` | none |
| Physical source package | `NOT_PROVEN` | requirements only |
| S001 physical shot base | `NOT_PROVEN` | no authority to build yet |

## FIRST REAL BLOCKER FOR S001

`S001_SHOT_INTENT / STORY_BEAT / ACTION_POSE = NOT_PROVEN`

Technical fields are downstream of that product decision. Do not fill the vacuum with:
- a synthetic W01 ARM_RAISE frame;
- Krita/source-binding proof;
- OpenToonz installation work;
- generic camera dynamics;
- default 48f/24fps/1920x1080 smoke values.

`SMOKE DEFAULT != S001 CONTRACT`

## WHEN S001 BECOMES THE ACTIVE REAL SHOT

First bind the exact product intent:
```text
SHOT_ID = S001
STORY_BEAT = <exact durable intent>
CHARACTER_ACTION = <exact action/pose>
PRIMARY_READ = <what must read first>
EMOTIONAL_PRESSURE = <shot job>
```

Then resolve the technical header:
```text
CONTRACT_REV = <exact revision>
ASPECT = <exact rational>
OUTPUT = <W_out>x<H_out> px
FPS = <exact>
DURATION_FRAMES = <exact>
DURATION_SECONDS = <derived>
REFERENCE_FRAME = <exact>
FRAMING = <declared>
OVERSCAN_L/R/T/B = <exact px>
CAMERA_TRANSLATION_MAX_X/Y = <exact px>
CAMERA_PUSH_MIN/MAX = <exact ratio>
CAMERA_ROLL_ABS_MAX = <exact degrees>
DEPTH_ORDER = <ordered layer families>
SOURCE_PACKAGE_REV = <exact revision>
```

Any field irrelevant to the chosen shot may be explicitly marked `N/A` with reason; do not invent a number merely to complete a template.

## QC BINDING

The real S001 key drawing / pose must be checked against:
- #245 identity/model authority;
- only the relevant #248 costume-force controls;
- pose/readability/silhouette requirements;
- camera/framing requirements once selected;
- source/depth/contact requirements once the shot enters physical build.

A failure routes to the smallest failed layer. It does not reopen the whole character pack or the retired orchestration topology.

## CURRENT TERMINAL STATEMENT

`S001_SHOT_CONTRACT_R02 = PREPARED / NOT_LOCKED`
`S001_SHOT_INTENT = NOT_PROVEN`
`S001_PHYSICAL_BUILD_AUTHORITY = NO`

No S001 PASS, camera PASS, world lock, or physical-shot readiness is claimed.