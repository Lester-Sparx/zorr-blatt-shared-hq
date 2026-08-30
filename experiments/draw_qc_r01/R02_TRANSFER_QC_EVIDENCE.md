# DUNCAN DRAW_QC — R02 TRANSFER QC EVIDENCE

STATUS = SANDBOX / PROVISIONAL / NON-CANON
SCOPE = VISUAL LANGUAGE + CHARACTER MODEL-SHEET QC ONLY
PRODUCTION_MUTATION = NO
CANON_MUTATION = NO

## Authority boundary

- Durable drawing law: issue #199.
- Visual taboo / no external aesthetic binding: issue #201.
- Open-code-first Night School authority: issue #206.
- Current OWNER instruction: D2 works only on visual language and characters; no Babylon/runtime work.

R01 absolute-anchor QC and R02 model-sheet transfer QC are intentionally separate domains.
R02 does **not** weaken or replace R01 thresholds.

## Open code path

Minimal glue only around the existing pinned OpenCV stack already used by this branch:

- NumPy `2.3.5`
- `opencv-python-headless==4.14.0.94`
- GitHub Actions checkout pinned by commit in `.github/workflows/zorr-draw-qc-r01.yml`

No custom framework was introduced.

## Semantic-region correction

Problem found during fresh audit:

`largest foreground component` mixed face/skin with Character Truth black masses (hair, shirt, accessories), producing false absolute failures for `deep_ink_coverage` and edge density.

Correction:

- keep legacy `analyze_image_bgr()` unchanged for whole-component R01 usage;
- add `analyze_region_bgr(image, region_mask)` for caller-supplied semantic regions;
- do not infer semantic identity from color inside the QC module;
- fail closed on empty or shape-mismatched masks.

Fresh semantic-region CI evidence:

- HEAD `29917478de99fd74a9ac5c6de9467f0bf57976bd`
- `zorr-draw-qc-r01` run `33319255481` = SUCCESS
- `hq-validate` run `33319255493` = SUCCESS
- `oss-security` run `33319255489` = SUCCESS

## Current C00 source identity

No source raster bytes are committed here.

Registered source hashes from the current D2 source pack:

- C00-A DETAIL/COSTUME/ACCESSORY = `94c185aea5755e569f8359fd29c6e0b8a1748e1613f2b59e7a3e280205dcbc8e`
- C00-B HEAD YAW = `7646fa2724fd4372eb9811635dbf71bb052151eaf2d4cdb999159124660a16d1`
- C00-C MASTER FRONT = `57fbec5d9c136a90c6ac262f8011665fa061dca427bf3fb2c3f110d1cb0a69ed`
- C00-D BODY TURNAROUND = `49f1c5fa9973f185c4ed7441325e2705d392449f6d59b4592ec6d81bc4b4da82`

## C00-B transfer study

OpenCV frontal-face detection found three usable front/3/4 regions in C00-B for a first cross-view consistency study. Profiles remain outside this R02 measurement subset.

Measured semantic-region values at normalized width 397 px:

| View | tone bands | strong edge density | deep ink coverage | line hierarchy ratio | high-frequency Laplacian variance |
|---|---:|---:|---:|---:|---:|
| left 3/4 | 8 | 0.2014669213 | 0.0586260937 | 2.6666666667 | 80.2548037129 |
| front | 8 | 0.2225570875 | 0.0708144839 | 2.9103737536 | 123.8768193954 |
| right 3/4 | 7 | 0.2035543656 | 0.0589116104 | 2.9291998545 | 69.0116770847 |

Observed cross-view dispersion:

- tone-band range = `1.0`
- edge-density CV = `0.0453568777`
- deep-ink CV = `0.0904618353`
- line-hierarchy CV = `0.0421699512`
- high-frequency CV = `0.2598974183`

## R02 provisional transfer envelope

The current implementation uses a narrow provisional margin above the observed C00-B three-view dispersion:

- minimum views = `3`
- tone-band range <= `1.0`
- edge-density CV <= `0.06`
- deep-ink CV <= `0.12`
- line-hierarchy CV <= `0.06`
- high-frequency CV <= `0.30`

This is a **consistency** gate only. It does not declare the absolute style correct by itself.

## Negative discrimination

A controlled one-view drift fixture changes one sample to:

- tone bands `11`
- strong-edge density `0.340`
- deep-ink coverage `0.120`
- line-hierarchy ratio `1.45`
- high-frequency variance `510`

Expected result:

- `TRANSFER_TONE_DRIFT_FAIL`
- `TRANSFER_EDGE_DRIFT_FAIL`
- `TRANSFER_INK_DRIFT_FAIL`
- `TRANSFER_LINE_DRIFT_FAIL`
- `TRANSFER_HIGH_FREQ_DRIFT_FAIL`

## Fresh R02 code evidence

Transfer implementation parent HEAD:

`822fd472d907514f4a1cc5c5fa0ce5d36ad71d12`

Fresh workflow evidence on that HEAD:

- `zorr-draw-qc-r01` run `33319347422`: tests step SUCCESS; workflow SUCCESS
- `hq-validate` run `33319347462`: SUCCESS
- `oss-security` run `33319347431`: security job SUCCESS

## R02 verdict

`SEMANTIC_REGION_QC = PASS`

`MODEL_SHEET_TRANSFER_QC = PASS`

`ABSOLUTE_R01_AND_TRANSFER_R02_DOMAIN_SEPARATION = PASS`

`PRODUCTION_STYLE_CANON = NOT CLAIMED`

`NEXT = R03 HEAD_GEOMETRY_CONSISTENCY`
