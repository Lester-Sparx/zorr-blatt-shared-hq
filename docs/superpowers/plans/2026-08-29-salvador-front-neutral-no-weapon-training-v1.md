# ZORR BLATT — SALVADOR FRONT-NEUTRAL / NO-WEAPON TRAINING PLAN V1

STATUS = PLAN_READY
MODEL_TRAINING_STATUS = NOT_RUN
PRODUCTION_PROMOTION = NOT_AUTHORIZED
PLAN_BASE_MAIN = d805242a8ba6e2b169c1216acd3df86b8f9ddd84
RELATES = #198 Tier 1 silhouette identity gate; #199 Character Drawing + Universal Texture Style v1

## Goal

Teach SALVADOR to take ZORR source/reference art and produce a production character reference with the same identity/body/hair/costume/asymmetry, a fixed readable front-neutral presentation, no weapon or prop attached to the character, a separately exported weapon when weapon truth exists, ZORR drawing law, and zero redesign.

`COMMON FRONT PRESENTATION != COMMON BODY`

`WEAPON != CHARACTER DETAIL`

`STYLE != IDENTITY`

## Current baseline truth

At this exact base SALVADOR is not yet this system:
- task contract allows only `PRODUCTION_IMAGE_EDIT`;
- current ComfyUI workflow is disposable `LoadImage -> ImageInvert -> SaveImage` smoke;
- current backend accepts one prompt token + one reference token and collects one PNG.

Therefore the normalizer must begin as an isolated experimental task/workflow and must not replace the current baseline until fresh QC passes.

## Reuse-first acceleration law

Use in this order:

`EXISTING ZORR -> COMFYUI NATIVE -> MATURE OSS -> MINIMAL GLUE -> LORA ONLY FOR PROVEN RESIDUAL GAP`

Preferred stack:
- existing ZORR agent-controller + ComfyUI transport;
- ComfyUI masks/inpaint/conditioning;
- ControlNet for deterministic fixed pose; depth/segmentation only for a measured failure;
- IP-Adapter/IP-Adapter Plus for image-reference identity;
- FaceID only where measured human-like identity tests prove benefit;
- Grounding DINO + SAM2 may propose body/weapon masks, but never self-approve canon masks;
- global ZORR Style LoRA only after approved target data exists;
- character-specific LoRA only after repeated identity failure;
- DreamBooth/full personalization last because of overfit risk.

No new large model from scratch. No custom pose detector. Pin exact dependency/model hashes before promotion.

## Experimental task

Proposed task kind: `CHARACTER_FRONT_NORMALIZE`.

Required inputs: character id, source images + SHA-256, Character Truth/source-evidence manifest, #199 style law, #198 silhouette law, `ZORR_FRONT_NEUTRAL_V1`, `WEAPON_POLICY=SEPARATE`, exact model/workflow/dependency hashes and seed.

Required outputs:
- `character_front_no_weapon.png`
- `character_front_mask.png`
- `character_front_silhouette.png`
- `pose_control.png`
- `weapon_source_mask.png`
- `weapon_separate.png | NONE`
- `identity_reference_contact_sheet.png`
- `metadata.json`
- `qc_report.json`

## ZORR_FRONT_NEUTRAL_V1 — mathematical presentation law

Presentation only; anatomy remains character-specific.

Normalized image coordinates x/y in [0,1].

Framing:
- bbox horizontal center `0.500 +/- 0.005 W`;
- top margin `0.04–0.07 H`;
- bottom margin `0.03–0.06 H`;
- full head/hands/feet + silhouette-critical hair/costume visible.

Orientation:
- torso yaw `0 +/- 3 deg`, roll `0 +/- 2 deg`;
- pelvis yaw `0 +/- 3 deg`, roll `0 +/- 2 deg`;
- head yaw `0 +/- 3 deg`, roll `0 +/- 2 deg`;
- shoulder axis <= `2 deg` from horizontal;
- pelvis axis <= `2 deg` from horizontal.

Ordinary-humanoid arm presentation:
- relaxed and visible, no weapon;
- shoulder abduction `8–12 deg` target;
- elbow flexion `0–8 deg` target;
- neutral wrists;
- hands readable, not hidden by torso.

Ordinary-humanoid leg presentation:
- balanced neutral stance;
- ankle spacing `0.55–0.75 x shoulder-joint spacing`;
- foot yaw `0–8 deg` outward;
- no lunge/crouch/contrapposto.

Nonstandard anatomy uses explicit family/character overrides; never force all characters onto one mannequin.

Background = plain white/near-white. No environment, FX, text, weapon or decorative layout in the production image.

## Two-branch teacher workflow

CHARACTER:
`source refs -> identity conditioning -> fixed-pose ControlNet -> verified body/weapon masks -> masked reconstruction -> ZORR style -> no-weapon front -> silhouette -> QC`

WEAPON:
`proven weapon evidence -> mask/crop -> remove body/hand contamination -> evidence-supported reconstruction -> isolated weapon asset`

If weapon is not proven: `weapon_separate = NONE`. Never hallucinate one.

## Curriculum

### S0 — no training

First prove the modular inference workflow. Classify the first failure as pose, face identity, body identity, hair, costume, asymmetry, silhouette, weapon leak, hand repair, weapon extraction or style. Do not train until the failure boundary is known.

### S1 — curated teacher targets

Pilot with 20 source cases including no-weapon, visible-weapon, hand-occlusion, difficult hair and asymmetry.

Do not train a global style LoRA until >=50 OWNER/DUNCAN-approved ZORR target images exist. Reserve >=20% as holdout. Include multiple poses/views when possible so LoRA learns drawing language rather than front pose. Failed candidates never enter training data.

### S2 — global ZORR Style LoRA

Train only on approved ZORR targets. Goal = #199 drawing discipline, not character identity. Promotion requires holdout style improvement with no identity/pose regression.

### S3 — character-specific adaptation

Default remains image-reference conditioning. Character-specific LoRA only after repeated holdout identity failure. DreamBooth/full personalization last.

## QC

Humanoid pose QC against a character-specific target skeleton, errors normalized by subject bbox height:
- mean joint error <= `0.015 Hsubject`;
- max required-joint error <= `0.035 Hsubject`;
- shoulder axis <= `2.5 deg`;
- pelvis axis <= `2.5 deg`;
- no cropped required joint.

Identity uses multiple independent checks: face/reference where applicable, full-body/reference embeddings, silhouette and independent visual QC. No arbitrary universal embedding threshold. Calibrate evaluator thresholds from approved same-character positives vs other-character negatives; if class separation is not demonstrated, automated identity = `NOT_PROVEN`.

After first approved front master, repeatability silhouette target IoU >= `0.90` plus identity-critical contour checks.

Character weapon gate: visible weapon = ZERO, no residual grip deformation. Open-vocabulary detection/segmentation may assist QC but cannot override visible evidence.

Style #199 gate at comparable model-sheet scale:
- roughly 4–6 dominant tone bands;
- strong-edge density roughly 8–14%;
- deepest face/skin ink sparse by default, usually <5% unless canon requires black regions;
- line hierarchy required;
- photo noise, pores, random micro-wrinkles and continuous glossy 3D shading = FAIL.

## GOLDEN_12 production gate

Holdout only:
- 3 clean humanoid/no weapon;
- 3 humanoid/visible weapon;
- 2 difficult weapon-hand occlusion;
- 2 strong silhouette/costume asymmetry;
- 1 female humanoid;
- 1 altered/alien humanoid compatible with humanoid pose schema.

Production promotion requires 12/12 PASS for pose, no-weapon output, identity, zero redesign, style and output contract. Weapon-separate PASS is required only where weapon truth exists.

## Failure taxonomy

`POSE_DRIFT`, `IDENTITY_FACE_DRIFT`, `IDENTITY_BODY_DRIFT`, `HAIR_DRIFT`, `COSTUME_DRIFT`, `ASYMMETRY_LOSS`, `SILHOUETTE_COLLAPSE`, `WEAPON_LEAK`, `HAND_REPAIR_FAIL`, `WEAPON_EXTRACTION_FAIL`, `STYLE_TOO_NOISY`, `STYLE_TOO_RENDERED`, `STYLE_TONE_COUNT_FAIL`, `BACKGROUND_CONTAMINATION`, `MODEL_OR_NODE_NONDETERMINISM`, `DEPENDENCY_MISMATCH`, `OUTPUT_CONTRACT_FAIL`.

Fix the first failing boundary. Never hide pose/identity failure with extra style/detail.

## Provenance

Every PASS run records source SHA-256 values, style-law anchor, SALVADOR HEAD, ComfyUI version, workflow hash, base checkpoint hash, ControlNet/IP-Adapter/custom-node hashes, input-mask hashes, sampler/steps/guidance/seed and output hashes.

No silent model download, substitution or unpinned node update in a PASS run.

## TDD implementation order

1. RED exact `CHARACTER_FRONT_NORMALIZE` contract.
2. RED multi-asset condition-bundle manifest while legacy one-reference path stays unchanged.
3. RED mandatory result pack/hashes.
4. RED deterministic pose-control generation.
5. RED `weapon=NONE` cannot emit a weapon artifact.
6. RED weapon-proven input requires separate weapon output state.
7. RED old `PRODUCTION_IMAGE_EDIT` smoke remains unchanged.
8. Minimal GREEN implementation.
9. Fresh tests.
10. Fresh physical ComfyUI GOLDEN smoke.
11. Independent DUNCAN QC.
12. Production promotion only after evidence.

Do not rewrite Controller; add only minimal bundle/workflow/result-pack glue.

## Research basis checked 2026-08-29

- ComfyUI official `ControlNetApplyAdvanced` documentation confirms image+ControlNet conditioning with controllable strength/start/end.
- ComfyUI official `VAEEncodeForInpaint` supports image+mask latent inpainting and mask growth.
- Tencent IP-Adapter is a lightweight image-prompt adapter designed to work with pretrained diffusion and controllable generation.
- Hugging Face Diffusers documents LoRA as the lightweight/faster adapter-training route and warns DreamBooth is hyperparameter-sensitive/easy to overfit.
- Grounding DINO provides open-set language-conditioned object detection.
- SAM2 provides promptable image/video segmentation.

## Durable private archive

`/ZORR/PERMANENT_ARCHIVE_V1/PRODUCTION_LAWS/SALVADOR/FRONT_NORMALIZE_V1/`

- `SALVADOR_FRONTPOSE_NOWEAPON_TRAINING_PLAN_V1.md` SHA-256 `68c5a7ccdd42b080e5ed8d349360bfda66dfe1d4ca7a04e237fad232382d3076`
- `SALVADOR_CHARACTER_FRONT_NORMALIZE_V1.schema.json` SHA-256 `eaa48f4cbe143776165c69fb6ea12ac721e6edbfaa0aa517e83cfed5918f1c8c`
- `SALVADOR_FRONT_NORMALIZE_QC_V1.json` SHA-256 `2e7d9dabd9f6d6e2f63d6a362ac47d6aad2d5a3b0d1be4b082aa6c9939291606`
- `MANIFEST.json` SHA-256 `79f266f497aa18d6d65f09cb0b540be5803eab84cf8eefe02439d5c73e07a265`

## Terminal state

`PLAN_PASS = YES`

`WORKFLOW_BASE_PASS = NOT_RUN`
`STYLE_LORA_PASS = NOT_RUN`
`SALVADOR_FRONT_NORMALIZER_PRODUCTION_PASS = NOT_RUN`

This document must never be cited as proof that model training or physical ComfyUI execution already passed.
