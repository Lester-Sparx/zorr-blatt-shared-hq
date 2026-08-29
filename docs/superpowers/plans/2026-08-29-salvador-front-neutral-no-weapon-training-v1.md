# ZORR BLATT — SALVADOR FRONT-NEUTRAL / NO-WEAPON TRAINING PLAN V1

STATUS = PLAN_READY
MODEL_TRAINING_STATUS = NOT_RUN
PRODUCTION_PROMOTION = NOT_AUTHORIZED
CURRENT_MAIN_AT_PLAN = d805242a8ba6e2b169c1216acd3df86b8f9ddd84
RELATES = #198 Tier 1 silhouette identity gate; #199 Character Drawing + Universal Texture Style v1; #201 Visual Taboo #1

## 0. PRODUCT GOAL

Teach SALVADOR to take ZORR source/reference art and produce a production character reference with:

1. the same character identity;
2. the same body/build truth;
3. the same hair/costume/asymmetry truth;
4. a fixed readable front-neutral presentation;
5. no weapon or prop attached to the character;
6. weapon exported as a separate asset when a weapon exists in source/canon;
7. ZORR global character drawing law applied;
8. no redesign.

The source images remain SOURCE MATERIAL until an output is separately approved.

## 1. NON-NEGOTIABLE LAW

COMMON FRONT PRESENTATION != COMMON BODY.

The fixed pose standardizes orientation and readability only.
It must never standardize:
- head/body ratio;
- shoulder width;
- pelvis width;
- limb lengths;
- hand/foot size;
- breast/chest form;
- muscularity/softness;
- alien/altered anatomy;
- silhouette-defining costume mass;
- identity-critical asymmetry.

WEAPON != CHARACTER DETAIL.
Weapon is a separate asset class.

STYLE != IDENTITY.
Global style law comes from #199.
Identity geometry comes from the Character Truth / selected source evidence.

## 1A. VISUAL TABOO #1 — NO EXTERNAL AESTHETIC BINDINGS

AUTHORITATIVE DURABLE RECORD = Shared HQ issue #201.

SALVADOR and every ZORR visual task must be defined only by internal ZORR-approved visual anchors, measurable ZORR laws, Character Truth and geometry/pose constraints.

FORBIDDEN:
- `anime style`, `manga style` or equivalent external genre/style labels as production instructions;
- `like X`, `in the style of Y`, artist/studio/franchise/character comparisons;
- external images as style targets or aesthetic templates;
- external character/image identity used to shape ZORR face/body/costume/silhouette;
- internet image search for aesthetic imitation.

ALLOWED EXTERNAL RESEARCH:
`OPEN CODE -> MATH -> ALGORITHMS -> DOCUMENTATION -> QC`

Source images supplied for a ZORR character remain `SOURCE / IDENTITY EVIDENCE`; they do not become external style authority by implication.

Any prohibited external aesthetic binding is fail-closed:
`VISUAL_TABOO_1_VIOLATION = FAIL`

## 2. CURRENT SALVADOR BASELINE — DO NOT MISREPRESENT

At current main, SALVADOR is not yet this system.

Existing task contract accepts only:
TASK_KIND = PRODUCTION_IMAGE_EDIT

Existing ComfyUI workflow is disposable smoke:
LoadImage -> ImageInvert -> SaveImage

Existing backend accepts one prompt token and one reference token and returns one PNG.

Therefore V1 must be developed on an isolated experimental branch/workflow and may not replace the existing baseline until fresh QC passes.

## 3. REUSE-FIRST STACK

Use, in this order:

A. Existing ZORR agent-controller + ComfyUI backend/transport.
B. ComfyUI built-in mask/inpaint/conditioning primitives.
C. ControlNet for pose control; optional depth/segmentation only when they improve a measured failure.
D. IP-Adapter / IP-Adapter Plus for image-reference identity conditioning.
E. Optional FaceID path for human-like Tier 1 characters only if it demonstrably improves identity.
F. Optional Grounding DINO + SAM2 only for proposing object/body/weapon masks; proposed masks are never canon authority.
G. LoRA only after a curated approved target dataset exists.
H. DreamBooth/full-model personalization only as a last-resort subject-specific fallback.

Do not train a new large diffusion model from scratch.
Do not train a custom pose detector.
Do not use source-pose detection as the target pose.
The target pose is generated from the canonical presentation spec.

Pin exact versions / commits / model hashes for every external dependency before any production promotion.

## 4. NEW EXPERIMENTAL TASK

Proposed isolated task kind:

TASK_KIND = CHARACTER_FRONT_NORMALIZE

It is experimental only until QC promotion.

### Required inputs

- CHARACTER_ID
- SOURCE_IMAGES[] (1 or more)
- CHARACTER_TRUTH_MANIFEST or explicit source-evidence manifest
- STYLE_LAW = #199 / ZORR_CHARACTER_DRAWING_LAW_V1
- SILHOUETTE_LAW = #198
- VISUAL_TABOO_LAW = #201
- POSE_SPEC = ZORR_FRONT_NEUTRAL_V1
- WEAPON_POLICY = SEPARATE
- SEED / sampler settings recorded
- exact base-model/checkpoint hash recorded
- exact custom-node/model hashes recorded

### Required outputs

character_front_no_weapon.png
character_front_mask.png
character_front_silhouette.png
pose_control.png
weapon_source_mask.png
weapon_separate.png | NONE
identity_reference_contact_sheet.png
metadata.json
qc_report.json

Optional:
depth_control.png
segmentation_control.png
intermediate_preview.png

## 5. ZORR_FRONT_NEUTRAL_V1 — MATHEMATICAL PRESENTATION SPEC

This spec controls presentation, not anatomy.

Coordinate system:
- image x: 0 left -> 1 right
- image y: 0 top -> 1 bottom
- subject bounding box calculated after generation

Framing:
- subject bbox horizontal center: x = 0.500 +/- 0.005 image width
- top margin: 0.04–0.07 image height
- bottom margin: 0.03–0.06 image height
- full head, hands and feet must be visible
- no crop of silhouette-defining hair/costume

Orientation:
- torso yaw: 0 deg +/- 3 deg
- torso roll: 0 deg +/- 2 deg
- pelvis yaw: 0 deg +/- 3 deg
- pelvis roll: 0 deg +/- 2 deg
- head yaw: 0 deg +/- 3 deg
- head roll: 0 deg +/- 2 deg
- shoulder-axis angle from horizontal: <= 2 deg
- pelvis-axis angle from horizontal: <= 2 deg

Arms:
- relaxed, visible, not weapon-bearing
- shoulder abduction target: 8–12 deg where anatomy permits
- elbow flexion target: 0–8 deg
- wrists neutral
- hands readable and not hidden behind torso
- for ordinary humanoids, maintain a visible silhouette gap between arm/hand and torso/thigh where practical
- family/character anatomy may override numeric limb pose only through an explicit pose exception

Legs:
- neutral balanced stance
- ankle-center spacing target for ordinary humanoids:
  0.55–0.75 × shoulder-joint spacing
- foot yaw: 0–8 deg outward
- no combat lunge / crouch / contrapposto
- nonstandard anatomy requires family-specific override, not forced human normalization

Background:
- plain neutral white / near-white
- no environment
- no FX
- no text
- no weapon
- no decorative layout elements in the production image itself

## 6. SOURCE DECOMPOSITION

Each source case is decomposed into separate evidence channels:

IDENTITY:
- face/head
- hair
- body/build
- costume
- asymmetry
- markings

STRUCTURE:
- body mask
- silhouette
- optional depth/segmentation

WEAPON:
- weapon mask
- visible weapon geometry
- occlusion notes
- weapon canon reference if available

SOURCE drawings are evidence.
They are not automatically target truth.

For the first curated training set, body/weapon masks must be manually verified.
Automatic segmentation may propose masks but cannot self-approve them.

## 7. TWO-BRANCH TEACHER WORKFLOW

### BRANCH A — CHARACTER

SOURCE REFERENCES
-> identity conditioning (IP-Adapter class)
-> fixed ZORR_FRONT_NEUTRAL_V1 pose control (ControlNet)
-> body/weapon masks
-> masked reconstruction where weapon/hand overlap must be repaired
-> ZORR character drawing law conditioning
-> character_front_no_weapon.png
-> black silhouette export
-> QC

No weapon prompt is not sufficient.
Weapon removal is enforced by mask separation + negative/conditioning rules + QC.

### BRANCH B — WEAPON

SOURCE WEAPON EVIDENCE
-> weapon mask/crop
-> remove hand/body contamination
-> reconstruct only occluded sections when sufficient evidence exists
-> neutral isolated weapon presentation
-> weapon_separate.png

If source/canon does not prove a weapon:
weapon_separate = NONE

Never hallucinate a weapon merely because a character is expected to fight.

## 8. STYLE TEACHING STRATEGY

### Stage S0 — NO MODEL TRAINING

First prove the workflow using existing models.

Target:
source -> correct identity -> fixed front pose -> no weapon -> ZORR style

This stage identifies whether the real failure is:
- pose;
- identity;
- masking;
- hand reconstruction;
- costume drift;
- style;
- weapon leakage.

Do not train before this taxonomy exists.

### Stage S1 — CURATED TEACHER TARGETS

Build approved source/target pairs.

Pilot:
- 20 source cases for workflow evaluation
- include clean no-weapon, weapon-present, occluded-hand, asymmetrical-costume and difficult-hair cases

Style-LoRA dataset gate:
- do not train global style LoRA until >= 50 OWNER/DUNCAN-approved ZORR character targets exist
- reserve >=20% as holdout and never train on them
- include more than one pose/view where available so the LoRA learns drawing language, not "front pose"

No failed candidate may enter the target dataset.

### Stage S2 — GLOBAL ZORR STYLE LoRA

Goal:
learn #199 drawing discipline, not character identity.

Training images:
only approved ZORR production targets.

Captions/tags describe only internal measurable ZORR properties, for example:
- clean graphic ZORR production drawing
- controlled line hierarchy
- compact tone bands
- low microdetail
- character-specific attributes separately

External genre, artist, studio, franchise, named-style, or external-image imitation labels are forbidden by #201.

Do not mix source art with target art as if they share the same style.

Acceptance:
style improves without reducing identity/pose scores on holdout.

### Stage S3 — CHARACTER-SPECIFIC ADAPTATION (ONLY IF NEEDED)

Default:
IP-Adapter/reference conditioning using the character's own approved/source evidence only.

Escalate to character-specific LoRA only when:
- repeated identity failure is proven across the holdout;
- style and pose already pass;
- adequate approved reference views exist.

DreamBooth/full personalization is last resort because of overfit risk.

## 9. QC METRICS

### 9.1 Pose

For humanoids, run a pose estimator on the output for QC only.
Compare output joints to the character-specific canonical target skeleton.

Normalize errors by subject bbox height.

Initial acceptance target:
- mean joint error <= 0.015 subject height
- max required-joint error <= 0.035 subject height
- shoulders horizontal <= 2.5 deg
- pelvis horizontal <= 2.5 deg
- no cropped required joint

If pose estimator is unreliable for a nonhuman body:
POSE_AUTOMATION = NOT_PROVEN
and use family-specific landmark QC.

### 9.2 Identity

Use multiple independent checks:
- face/reference similarity for human-like faces when applicable;
- full-body/reference embedding similarity;
- silhouette comparison;
- manual DUNCAN visual identity QC.

Do not hard-code an arbitrary universal embedding threshold.

Calibrate threshold per evaluator using:
- positive set = approved same-character pairs
- negative set = other-character pairs

A numeric identity threshold is valid only if:
worst_positive > best_negative + declared margin.

Otherwise automated identity score = NOT_PROVEN.

### 9.3 Silhouette

After a character receives an approved front master:
- black-fill silhouette becomes the SILHOUETTE_TRUTH reference
- subsequent redraws compare mask IoU / contour distance against it

Starting repeatability target:
- silhouette IoU >= 0.90 for equivalent front presentation
- identity-critical contour regions receive separate manual checks

Before first master approval, silhouette requires OWNER/DUNCAN visual gate.

### 9.4 Weapon absence

Character output:
- visible weapon pixels/shape = ZERO
- no scabbard/weapon attachment unless explicitly part of character canon for this no-weapon task (default: remove)
- hands must not retain weapon-grip deformation

Automated QC may use open-vocabulary detection (e.g. Grounding DINO) plus segmentation, but detector thresholds must be calibrated on a ZORR positive/negative gold set.
Automated "no weapon" never overrides visible human QC evidence.

### 9.5 Weapon separate

If weapon is proven:
- no body/hand contamination
- complete visible silhouette
- original design preserved
- occluded geometry reconstructed only when supported by weapon truth/evidence
- otherwise mark unresolved section, do not invent it

### 9.6 Style law (#199 + #201)

At comparable model-sheet scale:
- dominant large-region palette roughly 4–6 tone bands
- strong-edge density target roughly 8–14%
- deep ink sparse by default, usually <5% of face/skin area unless canon requires black regions
- line hierarchy required
- no pores/photo noise/random micro-wrinkles
- no continuous glossy 3D shading
- identity geometry drift = FAIL
- any external aesthetic binding = `VISUAL_TABOO_1_VIOLATION = FAIL`

## 10. GOLDEN VALIDATION SET

Create GOLDEN_12 before promotion:

- 3 clean humanoid / no weapon
- 3 humanoid / visible weapon
- 2 difficult weapon-hand occlusion
- 2 strong silhouette / costume asymmetry
- 1 female humanoid
- 1 altered / alien humanoid compatible with humanoid pose schema

Every item is holdout.

Promotion requires 12/12 PASS on:
- pose
- no-weapon character output
- identity
- no redesign
- style
- visual-taboo compliance
- output contract

Weapon-separate PASS is required only for items with proven weapon source/canon.

## 11. FAILURE TAXONOMY

Every failure must be assigned exactly one primary first-failing boundary:

POSE_DRIFT
IDENTITY_FACE_DRIFT
IDENTITY_BODY_DRIFT
HAIR_DRIFT
COSTUME_DRIFT
ASYMMETRY_LOSS
SILHOUETTE_COLLAPSE
WEAPON_LEAK
HAND_REPAIR_FAIL
WEAPON_EXTRACTION_FAIL
STYLE_TOO_NOISY
STYLE_TOO_RENDERED
STYLE_TONE_COUNT_FAIL
VISUAL_TABOO_1_VIOLATION
BACKGROUND_CONTAMINATION
MODEL_OR_NODE_NONDETERMINISM
DEPENDENCY_MISMATCH
OUTPUT_CONTRACT_FAIL

Fix the first failing boundary.
Do not compensate for a pose failure with style training.
Do not compensate for identity failure by increasing detail/noise.

## 12. DETERMINISM / PROVENANCE

Every run records:
- source SHA-256 for every input
- style-law SHA / issue
- visual-taboo law issue #201
- exact checkpoint/model hashes
- IP-Adapter/ControlNet/custom-node hashes
- workflow SHA-256
- sampler
- steps
- CFG/guidance values
- seed
- input masks SHA-256
- output SHA-256
- SALVADOR code HEAD
- ComfyUI version

No silent model downloads.
No random model substitution.
No unpinned custom-node update in a PASS run.

## 13. IMPLEMENTATION ORDER — TDD

On an isolated branch:

1. RED — new task contract rejects/accepts exact CHARACTER_FRONT_NORMALIZE schema.
2. RED — condition-bundle manifest supports multiple named reference assets; current one-reference path stays unchanged.
3. RED — output contract requires all mandatory outputs/hashes.
4. RED — fixed pose-control generator is deterministic.
5. RED — weapon=NONE path cannot hallucinate a weapon artifact.
6. RED — source with weapon requires separate weapon mask/output state.
7. RED — visual-taboo validator rejects prohibited external aesthetic binding tokens/metadata.
8. RED — existing PRODUCTION_IMAGE_EDIT smoke remains unchanged.
9. GREEN — minimum implementation.
10. Fresh unit tests.
11. Fresh ComfyUI smoke on GOLDEN cases.
12. Independent DUNCAN QC.
13. Only then consider production promotion.

## 14. MINIMAL CODE-SHAPE

Do not rewrite Controller.

Prefer:
- add isolated task kind
- add a condition-bundle manifest resolver
- extend ComfyUI workflow token replacement to named bundle assets while preserving old one-reference path
- add separate workflow file:
  salvador-character-front-normalize-v1.json
- add visual-taboo validation at task/conditioning boundary
- add separate result pack collector/manifest
- keep current production-image-edit workflow frozen

## 15. RESEARCH BASIS / VERIFIED REUSE

External research is technical-only under #201.

Verified during plan creation:
- ComfyUI is a node-based local inference/workflow engine.
- ControlNet supports human pose, depth and segmentation controls.
- ControlNets can be composed.
- ComfyUI ControlNetApplyAdvanced exposes strength/start/end controls.
- ComfyUI Mask Editor provides native mask authoring/editing.
- VAEEncodeForInpaint accepts image + mask and mask growth.
- ConditioningSetProperties can restrict conditioning by mask bounds.
- IP-Adapter provides lightweight image-prompt conditioning and can combine with controllable generation.
- LoRA trains only a small adapter parameter set and is the preferred first model-training layer.
- DreamBooth can personalize from few images but is overfit-sensitive.
- Grounding DINO provides open-set language-conditioned object detection.
- SAM2 provides promptable segmentation and automatic mask generation.
- cubiq ComfyUI_IPAdapter_plus remains a useful reference implementation but is maintenance-only; if used, pin exact commit/version/model hashes.

None of these external projects is an aesthetic authority for ZORR.

## 16. PASS GATES

PLAN_PASS:
- exact current baseline inspected
- reuse stack researched
- input/output contract frozen
- pose spec frozen
- weapon separation law frozen
- visual taboo #1 frozen
- curriculum frozen
- QC metrics frozen
- TDD implementation order frozen
- archived with hashes
= PASS

WORKFLOW_BASE_PASS:
- NOT CLAIMED by this document
- requires fresh physical ComfyUI evidence

STYLE_LORA_PASS:
- NOT CLAIMED by this document
- requires trained weights + holdout evidence

SALVADOR_FRONT_NORMALIZER_PRODUCTION_PASS:
- NOT CLAIMED by this document
- requires GOLDEN_12 12/12 + independent QC + authorized promotion

END
