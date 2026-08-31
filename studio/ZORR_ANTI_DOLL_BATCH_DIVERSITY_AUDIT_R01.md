# ZORR ANTI-DOLL BATCH DIVERSITY AUDIT R01

STATUS: DURABLE STUDIO QC SPEC
DATE: 2026-08-31
BRANCH: `duncan/zorr-studio-r01`
ACTIVE GATE: `OPENTOONZ CHARACTER LIFE SMOKE R01`
ARCHITECTURE EXPANSION: NO
IMAGE GENERATION / EDITING: NOT AUTHORIZED BY THIS SPEC

## 0. PURPOSE

Detect the failure mode where individual outputs look acceptable in isolation but the designer engine repeatedly collapses different characters, costumes or poses into one preferred production pattern.

Core law:

```text
INDIVIDUAL PASS DOES NOT OVERRIDE GROUP-LEVEL MANNEQUIN DRIFT.
```

And:

```text
DIVERSITY MUST BE PRESERVED — NOT INVENTED.
```

The target is not random novelty. The target is preservation of real source-specific differences while keeping one coherent ZORR visual language.

## 1. THREE DISTINCT LOOP CLASSES

### A. BODY MANNEQUIN NORMALIZATION

Candidate failure when different characters converge toward one recurring:

- neck;
- shoulder width/shape;
- chest volume;
- pelvis structure;
- limb proportion;
- head/body ratio;
- body mass;
- default stance;
- torso rhythm.

Hard review question:

```text
DO THESE CHARACTERS STILL HAVE THEIR SOURCE-SPECIFIC BODY CONSTRUCTION,
OR ARE THEY ONE BASE MANNEQUIN WITH DIFFERENT HEADS/CLOTHES?
```

### B. FACIAL MANNEQUIN DRIFT

Candidate failure when different characters converge toward one recurring:

- cranial silhouette;
- jaw family;
- eye spacing/layout;
- brow/cheek structure;
- nose/mouth placement relationship;
- age read;
- facial skeleton rhythm.

Do not maximize facial difference artificially. Preserve differences supported by character truth.

### C. GARMENT MANNEQUIN DRIFT

Candidate failure when different costumes converge toward one recurring:

- sleeve width/length;
- collar construction;
- shoulder drop;
- jacket length;
- hem rhythm;
- trouser width;
- boot proportion;
- layering pattern;
- garment asymmetry;
- fold rhythm.

Hard review question:

```text
ARE DIFFERENT COSTUMES BEING FORCED THROUGH ONE PRODUCTION TEMPLATE?
```

## 2. BATCH GATES

Use the existing staged audit pattern:

```text
3 CHARACTERS  -> FIRST BATCH DIVERSITY CHECK
10 CHARACTERS -> SECOND BATCH DIVERSITY CHECK
THEREAFTER    -> PERIODIC ARCHIVE AUDIT
```

These counts are project workflow checkpoints, not aesthetic thresholds.

## 3. REQUIRED COMPARISON VECTOR

For each character record, where source evidence exists:

```text
character_id
source_id
head_body_ratio
neck_shape
shoulder_axis_and_width
chest_mass
pelvis_mass
limb_character
body_mass_category
facial_skeleton_family
silhouette_signature
sleeve_width_length
collar_family
jacket_length
trouser_width
boot_height_mass
garment_asymmetry
garment_rhythm
pose_family
negative_space_signature
```

Values may be numeric, categorical, mask-based or `UNKNOWN` depending on actual evidence.

Never fill unknown fields from genre convention.

## 4. WITHIN-CHARACTER VS CROSS-CHARACTER LOOP

Two independent failures must be kept separate.

### WITHIN_CHARACTER_PATTERN_LOOP

Same character repeatedly receives nearly the same:

- support side;
- dominant diagonal;
- torso/pelvis relation;
- head tilt family;
- arm silhouette;
- negative-space topology.

### CROSS_CHARACTER_MANNEQUIN_DRIFT

Different characters collapse toward the same:

- body construction;
- facial skeleton;
- garment architecture;
- pose grammar.

A system may pass one and fail the other.

## 5. MEASUREMENT PRINCIPLE

Do not create one `DIVERSITY_SCORE`.

Use a vector of comparisons:

```text
BODY_VARIATION
FACE_VARIATION
GARMENT_VARIATION
POSE_VARIATION
SILHOUETTE_VARIATION
NEGATIVE_SPACE_VARIATION
IDENTITY_PRESERVATION
SOURCE_TRUTH_PRESERVATION
```

High variation is not automatically good.

Desired relationship:

```text
PRESERVE PROVEN SOURCE DIFFERENCES
+ ALLOW INTENTIONAL POSE / ACTING VARIATION
- GENERIC MANNEQUIN CONVERGENCE
- RANDOM FAKE DIVERSITY
```

## 6. CAUSAL ROUTING

If a repeated pattern is detected, classify first cause before repair.

Possible first causes:

```text
SOURCE PACK TOO WEAK
REFERENCE SELECTION BIAS
POSE TEMPLATE BIAS
DRAWING TEMPLATE BIAS
RIG TEMPLATE BIAS
GARMENT SIMPLIFICATION BIAS
QC BLIND SPOT
TRAINING DATA COLLAPSE
UNKNOWN
```

Do not fix body convergence by adding costume noise.
Do not fix facial convergence by changing color.
Do not fix garment convergence by stronger pose warp.
Do not fix pose repetition by random anatomy distortion.

## 7. REPAIR ORDER

```text
1. CONFIRM SOURCE-SPECIFIC DIFFERENCE EXISTS.
2. LOCALIZE WHERE PIPELINE ERASED IT.
3. CHANGE ONLY THAT LAYER / TRAINING RULE.
4. RE-MEASURE THE LOST DIFFERENCE.
5. CHECK IDENTITY + STYLE COHESION COLLATERAL.
6. TEST ON AN UNSEEN CHARACTER.
```

If the source itself does not establish a difference:

`DIFFERENCE = UNKNOWN`

Do not invent diversity just to satisfy the audit.

## 8. HARD REVIEW FLAGS

Use these exact machine/handoff labels when evidence supports them:

```text
MANNEQUIN_NORMALIZATION_CANDIDATE
FACIAL_MANNEQUIN_DRIFT_CANDIDATE
GARMENT_MANNEQUIN_DRIFT_CANDIDATE
POSE_PATTERN_LOOP_CANDIDATE
SOURCE_DIFFERENCE_ERASED
FAKE_DIVERSITY_CANDIDATE
CAUSE_UNKNOWN
```

Final artistic FAIL/PASS remains evidence/calibration dependent except where a source-locked invariant is directly violated.

## 9. TRAINING DATA LAW

A rejected or mannequin-normalized candidate must not silently become a positive training example.

Positive examples should demonstrate:

```text
SAME ZORR LANGUAGE
+ DISTINCT CHARACTER CONSTRUCTION
+ DISTINCT GARMENT CONSTRUCTION
+ INTENT-SPECIFIC POSE
+ IDENTITY PRESERVED
```

Negative examples should be tagged by actual failure class rather than merely `BAD`.

Suggested negative labels:

```text
NEG_BODY_MANNEQUIN
NEG_FACE_MANNEQUIN
NEG_GARMENT_MANNEQUIN
NEG_POSE_LOOP
NEG_DECORATIVE_NOISE
NEG_IDENTITY_DRIFT
```

## 10. TRANSFER TEST

A batch correction is not proven on the characters used to discover it.

Required:

```text
DISCOVERY BATCH
-> CAUSAL REPAIR
-> HOLDOUT / UNSEEN CHARACTER
-> SAME COMPARISON VECTOR
-> PROMOTE / NARROW / REJECT LESSON
```

If the repair improves diversity but damages identity or source truth, it fails.

## 11. RELATION TO ANTI-DOLL MATRIX

Use together with:

`studio/ZORR_ANTI_DOLL_MEASUREMENT_MATRIX_R01.md`

The matrix diagnoses a character/shot through pose, weight, acting, secondary, value, hatching and controlled violation.

This batch audit adds the missing population-level question:

```text
IS THE DESIGN ENGINE REPEATING ITS FAVORITE SOLUTION ACROSS THE CAST?
```

## 12. TERMINAL BOUNDARY

This file is a QC/training specification only.

It does NOT:

- authorize generation/editing;
- declare current cast PASS/FAIL without actual comparison evidence;
- invent diversity thresholds;
- replace character truth;
- change the active OpenToonz production gate;
- require a new software framework.