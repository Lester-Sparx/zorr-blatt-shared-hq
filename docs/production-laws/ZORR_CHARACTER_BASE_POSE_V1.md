# ZORR BLATT — CHARACTER BASE POSE V1

STATUS = ACTIVE CANDIDATE LAW ON PR #200
SCOPE = ALL CHARACTER FAMILIES / TIER 1 FIRST MASTER
BASE_MAIN = d805242a8ba6e2b169c1216acd3df86b8f9ddd84
RELATES = #198 Tier 1 silhouette identity gate; #199 Character Drawing + Universal Texture Style v1; PR #200 SALVADOR front normalization

## Core law

Every character begins from one canonical presentation state before turnaround, action poses, weapons, FX, or scene work:

`CHARACTER_TRUTH -> ATTENTION_BASE -> SILHOUETTE_LOCK -> TURNAROUND -> POSE/ANIMATION`

The base presentation is a strict front-facing attention stance (`СТОЙКА СМИРНО`) used as the zero coordinate for character construction, comparison, rigging, SALVADOR normalization and Babylon transfer.

`COMMON BASE POSE != COMMON BODY`

The pose standardizes presentation only. It MUST NOT standardize character anatomy, sex, body family, height, head/body ratio, shoulder/pelvis width, limb proportions, mass, alien anatomy, costume silhouette, hair mass, markings or identity-critical asymmetry.

## Ordinary humanoid attention presentation

- full body, front view;
- head, sternum and pelvis facing camera;
- spine visually vertical;
- shoulder and pelvis axes horizontal within the declared QC tolerance;
- both arms completely outside pockets and fully readable;
- upper arms descend naturally along the torso;
- elbows near extension, without combat tension;
- wrists neutral;
- hands fully visible beside the thighs, fingers relaxed and readable;
- legs straight and balanced;
- feet in a simple neutral stance, no lunge, crouch or contrapposto;
- no weapon in hands, on body, in scabbard, holster or attached as a prop for the base export;
- no FX, environment, text or decorative layout;
- plain white / near-white production background.

Character/family anatomy may require explicit pose-landmark overrides. Such overrides preserve the law's purpose: a maximally readable neutral zero pose, never forced human normalization.

## Weapon law

`CHARACTER_BASE = NO WEAPON`

`WEAPON_BASE = SEPARATE ASSET`

A weapon proven by source/canon is exported separately. A weapon not proven is `NONE`. Never hallucinate a weapon.

## Geometry/QC law

For ordinary humanoids at the first-master gate:

- subject bbox horizontal center: `0.500 +/- 0.005 W`;
- torso yaw: `0 +/- 3 deg`;
- torso roll: `0 +/- 2 deg`;
- pelvis yaw: `0 +/- 3 deg`;
- pelvis roll: `0 +/- 2 deg`;
- head yaw: `0 +/- 3 deg`;
- head roll: `0 +/- 2 deg`;
- shoulder axis: `<= 2.5 deg` from horizontal;
- pelvis axis: `<= 2.5 deg` from horizontal;
- mean required-joint error against the character-specific target skeleton: `<= 0.015 Hsubject`;
- max required-joint error: `<= 0.035 Hsubject`;
- all required head/hand/foot landmarks visible.

Do not invent universal shoulder width, ankle spacing or body proportions. Those belong to Character Truth / body-family truth, not the common pose law.

## Tier 1 gate

For Tier 1 characters, the attention-base image is not approved until:

1. identity/body/hair/costume/asymmetry = preserved;
2. no redesign = proven;
3. no weapon = proven;
4. black-fill silhouette is individually recognizable under #198;
5. drawing obeys #199;
6. the attention-pose math/QC passes.

After approval, the resulting black-fill silhouette becomes the front `SILHOUETTE_TRUTH` for equivalent front-base redraws.

## ZORR BLATT prototype application

The currently locked ZORR BLATT prototype remains identity/source authority. His current hands-in-pockets pose is NOT the universal base pose. The first production normalization task is to preserve his face, body/build, dreadlock mass, organic markings, black overshirt, white tank, wide gray trousers, belt, shoes and character-specific silhouette while moving only the limbs required to reach this attention-base presentation.

## Salvador rule

SALVADOR must not "invent a new character in a neutral pose". It must solve a constrained normalization problem:

`LOCK CHARACTER TRUTH + APPLY ATTENTION POSE + REMOVE/SEPARATE WEAPON + APPLY ZORR DRAWING LAW + QC`

The existing PR #200 `ZORR_FRONT_NEUTRAL_V1` wording is superseded by this stricter attention-base law wherever the two conflict.

END
