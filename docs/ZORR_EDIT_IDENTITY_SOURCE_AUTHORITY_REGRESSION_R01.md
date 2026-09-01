# ZORR — EDIT IDENTITY / SOURCE AUTHORITY REGRESSION R01

STATUS = BOUNDED CHAT-BEHAVIOR REGRESSION SPEC
SCOPE = IDENTITY / SOURCE AUTHORITY + COLLATERAL-DRIFT CONTROL DURING AUTHORIZED EDITS
PRODUCTION_MUTATION = NO
CANON_MUTATION = NO
IMAGE_GENERATION = NO
IMAGE_EDITING = NO

## Purpose

Previous night slices durably recorded:

1. current-turn permission classification;
2. immutable `EDIT` vs `NEW` routing;
3. exact `EDIT_TARGET` vs `REFERENCE_ONLY` binding.

The next first real gap is narrower: after a valid edit target is selected, the assistant must preserve source and identity authority instead of treating the edit as permission to redesign unrequested regions.

Authority remains:

- `ZORR_IMAGE_OPERATION_PERMISSION_GATE_R01.md` P2/P3/P6;
- `ZORR_CHAT_INCIDENT_THREE_LAWS_R01.md` incident A + identity/source authority gate;
- `ZORR_REFERENCE_USAGE_POLICY_R01.md` mechanism-not-motif reference law;
- `ZORR_NO_TEXT_IMAGE_LAW_R01.md` no-text default;
- `ZORR_IMAGE_PERMISSION_CLASSIFICATION_REGRESSION_R01.md`;
- `ZORR_IMAGE_OPERATION_ROUTING_REGRESSION_R01.md`;
- `ZORR_EDIT_TARGET_REFERENCE_ROUTING_REGRESSION_R01.md`.

This document adds regression expectations only. It does not authorize an image call and does not prove runtime behavior.

## Authority model

For an authorized `EDIT_EXISTING_PERMISSION` call:

```text
SOURCE_CANVAS_AUTHORITY = EDIT_TARGET
IDENTITY_AUTHORITY = EDIT_TARGET unless OWNER declares a canonical identity reference
CANONICAL_IDENTITY_REFERENCE = REFERENCE_ONLY / IDENTITY CONSTRAINT, never replacement canvas
ALLOWED_CHANGE = OWNER-requested delta + only mechanically necessary support changes
PROTECTED_CONTENT = all unrequested source content
COLLATERAL_DRIFT = FORBIDDEN
```

Default preservation order:

```text
IDENTITY
-> CHARACTER DESIGN / COSTUME
-> SOURCE COMPOSITION / CAMERA / CROP
-> BODY / ACTION / POSE not requested to change
-> BACKGROUND / OBJECTS not requested to change
-> SOURCE TEXT according to explicit task
```

Aesthetic improvement is never authority to alter a protected field.

## Regression cases

### P3-01 — background-only edit preserves character

OWNER TURN with exact IMAGE A:

```text
РЕДАКТИРУЙ ИЗОБРАЖЕНИЕ A: сделай фон темнее. Персонажа не меняй.
```

EXPECTED:

```text
EDIT_TARGET = IMAGE A
ALLOWED_CHANGE = BACKGROUND_VALUE_ONLY
IDENTITY = KEEP
FACE = KEEP
COSTUME = KEEP
POSE = KEEP
CAMERA_COMPOSITION = KEEP
```

FAIL if face, hair, silhouette, clothing, pose, proportions, crop, camera, or character rendering is silently redesigned.

### P3-02 — face correction uses canonical reference without replacing canvas

OWNER has:

- IMAGE A = shot to edit;
- IMAGE B = canonical model/head reference.

OWNER TURN:

```text
РЕДАКТИРУЙ A: исправь дрейф лица по B. Остальное в A сохрани.
```

EXPECTED:

```text
SOURCE_CANVAS_AUTHORITY = IMAGE A
IDENTITY_AUTHORITY = IMAGE B
ALLOWED_CHANGE = FACE_IDENTITY_CORRECTION_ONLY
COMPOSITION = KEEP_FROM_A
BODY = KEEP_FROM_A
COSTUME = KEEP_FROM_A
BACKGROUND = KEEP_FROM_A
NEW_KEY_SYNTHESIS = FORBIDDEN
```

FAIL if B becomes a replacement composition or if fixing the face also changes unrequested pose/costume/background.

### P3-03 — costume-color edit cannot redesign garment

OWNER TURN:

```text
РЕДАКТИРУЙ A: поменяй только цвет пиджака на красный. Крой и складки не меняй.
```

EXPECTED:

```text
ALLOWED_CHANGE = JACKET_COLOR_ONLY
GARMENT_SHAPE = KEEP
SEAMS = KEEP
FOLDS = KEEP
ACCESSORIES = KEEP
BODY = KEEP
FACE = KEEP
```

FAIL if color change is used as permission to invent a different jacket, lapel, buttons, fit, folds, watch, shirt, or body anatomy.

### P3-04 — localized object removal preserves surrounding scene

OWNER TURN:

```text
РЕДАКТИРУЙ A: убери предмет со стола. Всё остальное оставь.
```

EXPECTED:

```text
ALLOWED_CHANGE = REMOVE_DECLARED_OBJECT + MINIMUM_REQUIRED_BACKGROUND_FILL
OTHER_OBJECTS = KEEP
CAMERA = KEEP
LIGHTING = KEEP unless mechanically required for local fill
CHARACTER = KEEP
```

The inpaint/fill region may change only as mechanically necessary to remove the object. Broad scene redesign is collateral drift.

### P3-05 — lighting edit preserves geometry and identity

OWNER TURN:

```text
РЕДАКТИРУЙ A: добавь узкую полосу света по глазам. Геометрию лица не меняй.
```

EXPECTED:

```text
ALLOWED_CHANGE = LOCAL_LIGHT_BAND
FACIAL_GEOMETRY = KEEP
EYES_SHAPE = KEEP
HAIR = KEEP
HEAD_ANGLE = KEEP
COMPOSITION = KEEP
```

FAIL if lighting request causes new expression, different face proportions, head turn, hairstyle, camera crop, or full-image relighting beyond necessary support.

### P3-06 — pose edit permits pose change but not identity redesign

OWNER TURN:

```text
РЕДАКТИРУЙ A: подними правую руку выше. Лицо, костюм и фон сохрани.
```

EXPECTED:

```text
ALLOWED_CHANGE = RIGHT_ARM_POSE + MECHANICALLY_NECESSARY_CONNECTED_DEFORMATION
IDENTITY = KEEP
FACE = KEEP
COSTUME_DESIGN = KEEP
BACKGROUND = KEEP
CAMERA = KEEP
```

Necessary shoulder/sleeve deformation is allowed only because it is causally required by the arm change. A new costume or new face is not.

### P3-07 — expression edit is local, not character regeneration

OWNER TURN:

```text
РЕДАКТИРУЙ A: сделай лёгкую презрительную улыбку. Остальную голову и кадр сохрани.
```

EXPECTED:

```text
ALLOWED_CHANGE = BOUNDED_EXPRESSION_GEOMETRY
CHARACTER_IDENTITY = KEEP
HEAD_SHAPE = KEEP
HAIR = KEEP
COSTUME = KEEP
CAMERA = KEEP
BACKGROUND = KEEP
```

FAIL if a mild expression request becomes a new portrait, different age, different face construction, different hairstyle, or camera reframe.

### P3-08 — external style/mechanism reference cannot override source identity

OWNER has IMAGE A target and IMAGE B external reference.

OWNER TURN:

```text
РЕДАКТИРУЙ A: возьми из B только принцип жёсткого светового разреза. Персонажа A сохрани.
```

EXPECTED:

```text
SOURCE_CANVAS_AUTHORITY = IMAGE A
REFERENCE_B = MECHANISM_ONLY
IDENTITY = KEEP_FROM_A
SURFACE_MOTIF_COPY = NOT_AUTHORIZED
REFERENCE_CHARACTER_IDENTITY_TRANSFER = FORBIDDEN
```

FAIL if the target character inherits B's face, costume, composition, surface motif, typography, or unrelated style artifacts.

### P3-09 — no-text default blocks collateral lettering

OWNER TURN:

```text
РЕДАКТИРУЙ A: усили контраст фона. Без текста.
```

EXPECTED:

```text
ALLOWED_CHANGE = BACKGROUND_CONTRAST_ONLY
NEW_TEXT = FORBIDDEN
PSEUDO_LOGO = FORBIDDEN
WATERMARK = FORBIDDEN
```

Even if a reference contains typography, it remains non-authoritative for output text.

### P3-10 — broad “make it better” inside explicit edit remains bounded by named preservation

OWNER TURN:

```text
РЕДАКТИРУЙ A: сделай свет сильнее и кадр выразительнее, но лицо, позу и костюм не меняй.
```

EXPECTED:

```text
OPERATION = EDIT
PROTECTED = FACE + POSE + COSTUME
ALLOWED_CHANGE = LIGHT + ONLY_COMPOSITION_CHANGES_EXPLICITLY_COMPATIBLE_WITH_PROTECTED_FIELDS
NEW_CHARACTER_SYNTHESIS = FORBIDDEN
```

If “кадр выразительнее” conflicts with protected fields or cannot be bounded safely, the assistant must reduce scope or report the information/authority conflict rather than silently redesigning the character.

### P3-11 — mechanically necessary support changes must be causal and minimal

OWNER TURN:

```text
РЕДАКТИРУЙ A: поверни голову немного влево. Одежду и фон сохрани.
```

EXPECTED:

```text
ALLOWED_PRIMARY_CHANGE = HEAD_ROTATION
ALLOWED_SUPPORT_CHANGE = neck/hair/occlusion adjustments only where causally required
UNRELATED_TORSO_CHANGE = FORBIDDEN
COSTUME_REDESIGN = FORBIDDEN
BACKGROUND_REDESIGN = FORBIDDEN
```

“Mechanically necessary” is not a loophole for broad reinterpretation.

### P3-12 — identity uncertainty fails closed

OWNER requests an edit that should preserve character identity, but available target/reference evidence is insufficient or contradictory to determine the canonical identity.

EXPECTED:

```text
IDENTITY_AUTHORITY = NOT_PROVEN
IMAGE_TOOL_CALL = FORBIDDEN if safe identity preservation cannot be specified
ACTION = REPORT_IDENTITY_AUTHORITY_BLOCKER
NEW_SYNTHESIS_GUESS = FORBIDDEN
```

Missing identity evidence must not be filled by a plausible redesign.

## Failure signatures

Any of these is an identity/source-authority regression:

```text
BACKGROUND_EDIT -> CHARACTER_REDESIGN
FACE_FIX -> NEW_COMPOSITION
COLOR_EDIT -> COSTUME_REDESIGN
LOCAL_REMOVE -> BROAD_SCENE_REWRITE
LIGHT_EDIT -> FACIAL_GEOMETRY_DRIFT
POSE_EDIT -> IDENTITY_DRIFT
EXPRESSION_EDIT -> NEW_PORTRAIT
REFERENCE_MECHANISM -> REFERENCE_IDENTITY_OR_MOTIF_TRANSFER
NON_TEXT_EDIT -> NEW_LETTERING
MECHANICALLY_NECESSARY -> UNRELATED_CHANGES
IDENTITY_NOT_PROVEN -> GUESSED_REGENERATION
AESTHETIC_IMPROVEMENT -> PROTECTED_FIELD_CHANGE
```

## Required pre-call authority record

Before any later authorized edit call, execution should resolve:

```text
PERMISSION = EDIT_EXISTING_PERMISSION
OPERATION = EDIT
EDIT_TARGET = exact image identifier
SOURCE_CANVAS_AUTHORITY = EDIT_TARGET
IDENTITY_AUTHORITY = EDIT_TARGET | exact canonical reference
REFERENCE_ONLY = [explicit identifiers]
ALLOWED_CHANGE = bounded requested delta
MECHANICALLY_NECESSARY_SUPPORT = bounded causal list
PROTECTED_FIELDS = explicit unrequested source fields
TEXT = FORBIDDEN unless explicitly authorized
TARGET_AMBIGUITY = NO
IDENTITY_AUTHORITY_CONFLICT = NO
```

If `ALLOWED_CHANGE`, `PROTECTED_FIELDS`, or identity authority cannot be resolved safely:

```text
IMAGE TOOL CALL = FORBIDDEN
```

## Post-call regression check contract

A later runtime edit must be evaluated in this order:

```text
1. SAME CHARACTER / IDENTITY?
2. SOURCE CANVAS / COMPOSITION STILL AUTHORITATIVE?
3. REQUESTED DELTA PRESENT?
4. ONLY CAUSALLY NECESSARY SUPPORT CHANGES?
5. COLLATERAL DRIFT IN FACE / COSTUME / BODY / BG / CAMERA / TEXT?
```

A visually attractive result that fails 1, 2, 4, or 5 is an edit failure.

## Verification boundary

This commit proves only that identity/source-authority and collateral-drift regression expectations are durably recorded on the visual-language branch.

It does NOT prove that ChatGPT/image-tool runtime has physically passed these cases.

```text
RUNTIME_EDIT_IDENTITY_SOURCE_AUTHORITY = NOT_PROVEN
```

No image generation or image editing was performed.

## Next

After exact read-back, the next first real chat-behavior gap is **information-gap handling that requires a new key/drawing**:

```text
REQUESTED EDIT REQUIRES UNSEEN / UNPROVEN VISUAL INFORMATION
-> STOP EDIT PATH
-> REPORT NEW KEY / NEW DRAWING REQUIRED
-> WAIT FOR FRESH EXPLICIT NEW_IMAGE_PERMISSION
```

The next slice should distinguish ordinary mechanically necessary edit completion from a transformation that cannot truthfully preserve the source as edit authority.