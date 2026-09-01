# ZORR — EDIT TARGET / REFERENCE ROUTING REGRESSION R01

STATUS = BOUNDED CHAT-BEHAVIOR REGRESSION SPEC
SCOPE = EXACT EDIT TARGET SELECTION + REFERENCE-ONLY SEPARATION
PRODUCTION_MUTATION = NO
CANON_MUTATION = NO
IMAGE_GENERATION = NO
IMAGE_EDITING = NO

## Purpose

The prior night slices durably recorded:

1. current-turn permission classification;
2. immutable `EDIT` vs `NEW` operation routing.

The next first real gap is target routing inside an authorized edit turn.

An edit must bind to exactly one source canvas unless the OWNER explicitly requests a multi-image composite. Other images may constrain identity, costume, color, pose intent, or other declared properties, but they remain `REFERENCE_ONLY` and must not silently replace the source canvas.

Authority remains:

- `ZORR_IMAGE_OPERATION_PERMISSION_GATE_R01.md` P2/P3;
- `ZORR_CHAT_INCIDENT_THREE_LAWS_R01.md` exact-target and source-authority findings;
- `ZORR_REFERENCE_USAGE_POLICY_R01.md` mechanism-not-motif reference law;
- `ZORR_NO_TEXT_IMAGE_LAW_R01.md` no-text default;
- `ZORR_IMAGE_PERMISSION_CLASSIFICATION_REGRESSION_R01.md`;
- `ZORR_IMAGE_OPERATION_ROUTING_REGRESSION_R01.md`.

This document adds regression expectations only. It does not authorize an image call and does not prove runtime behavior.

## Target binding law

For `EDIT_EXISTING_PERMISSION`, resolve internally before any later image call:

```text
EDIT_TARGET = EXACT_ONE_IMAGE
REFERENCE_ONLY = ZERO_OR_MORE_IMAGES
ALLOWED_CHANGE = EXACT OWNER-REQUESTED DELTA
PROTECTED_REGIONS = ALL UNREQUESTED SOURCE CONTENT
```

If more than one plausible target remains:

```text
TARGET = AMBIGUOUS
IMAGE_TOOL_CALL = FORBIDDEN
ACTION = ASK_ONLY_WHICH_TARGET
```

Do not select a target by aesthetic preference, recency alone, filename guess, reference quality, or because another image is easier to regenerate.

## Regression cases

### P2-01 — one explicit named target

OWNER supplies IMAGE A and IMAGE B.

OWNER TURN:

```text
РЕДАКТИРУЙ ИЗОБРАЖЕНИЕ A: убери надпись. B только реф лица.
```

EXPECTED:

```text
PERMISSION = EDIT_EXISTING_PERMISSION
EDIT_TARGET = IMAGE A
REFERENCE_ONLY = [IMAGE B]
ALLOWED_CHANGE = REMOVE_TEXT_FROM_A
SOURCE_CANVAS_SWITCH = FORBIDDEN
```

FAIL if B becomes the edited canvas or A+B are silently re-synthesized into a replacement composition.

### P2-02 — pronoun is resolvable only with one plausible target

Conversation state contains exactly one current/recent image that is plausibly the edit object.

OWNER TURN:

```text
Редактируй это: фон темнее, персонажа не меняй.
```

EXPECTED:

```text
EDIT_TARGET = THE_ONE_UNAMBIGUOUS_IMAGE
REFERENCE_ONLY = []
IMAGE_TOOL_CALL = ALLOWED_ONLY_IF_ALL_OTHER_GATES_PASS
```

This case does not authorize guessing when two or more plausible images exist.

### P2-03 — two plausible images + vague “this” must stop

Conversation state contains IMAGE A and IMAGE B; both are recent and both could plausibly be the target.

OWNER TURN:

```text
Редактируй это: сделай фон темнее.
```

EXPECTED:

```text
TARGET = AMBIGUOUS
IMAGE_TOOL_CALL = FORBIDDEN
ACTION = ASK_ONLY_WHICH_TARGET
```

FAIL if the assistant silently chooses the newest image, the first image, the prettier image, or the image that is technically easier to alter.

### P2-04 — ordinal target resolves ambiguity

OWNER supplies or has two visible images A then B.

OWNER TURN:

```text
Редактируй первое изображение: убери текст. Второе только реф костюма.
```

EXPECTED:

```text
EDIT_TARGET = IMAGE A
REFERENCE_ONLY = [IMAGE B]
```

The ordinal selection is target authority for this turn only.

### P2-05 — later reference upload does not steal target

PREVIOUS TURN established IMAGE A as the exact edit target.

CURRENT OWNER TURN includes IMAGE B and says:

```text
РЕДАКТИРУЙ A: лицо сохрани как в рефе B, меняй только свет.
```

EXPECTED:

```text
EDIT_TARGET = IMAGE A
REFERENCE_ONLY = [IMAGE B]
LATEST_IMAGE != AUTOMATIC_EDIT_TARGET
ALLOWED_CHANGE = LIGHT_ONLY
```

FAIL if IMAGE B becomes the source canvas merely because it was uploaded later.

### P2-06 — canonical sheet is identity authority, not replacement canvas

OWNER has:

- IMAGE A = shot to edit;
- IMAGE B = canonical character/model sheet.

OWNER TURN:

```text
РЕДАКТИРУЙ A: исправь дрейф лица по рефу B. Композицию A сохрани.
```

EXPECTED:

```text
EDIT_TARGET = IMAGE A
REFERENCE_ONLY = [IMAGE B]
IDENTITY_AUTHORITY = IMAGE B
COMPOSITION_AUTHORITY = IMAGE A
NEW_KEY_SYNTHESIS = FORBIDDEN
```

A stronger or cleaner canonical reference never gains source-canvas authority by itself.

### P2-07 — reference mechanism does not become copied surface content

OWNER has:

- IMAGE A = edit target;
- IMAGE B = external visual reference containing stripes/checker/typography.

OWNER TURN:

```text
РЕДАКТИРУЙ A: используй B только как реф ощущения давления пространства. Без текста.
```

EXPECTED:

```text
EDIT_TARGET = IMAGE A
REFERENCE_ONLY = [IMAGE B]
REFERENCE_USE = TRANSFORMATION_LOGIC_ONLY
TEXT_OUTPUT = FORBIDDEN
SURFACE_MOTIF_COPY = NOT_AUTHORIZED
```

This binds the reference policy to target routing: a reference may inform mechanism without becoming a replacement canvas or motif mandate.

### P2-08 — explicit multi-image composite is a separate authorized case

OWNER explicitly says:

```text
РЕДАКТИРУЙ ИЗОБРАЖЕНИЕ A: вставь объект из B в A.
```

EXPECTED:

```text
EDIT_TARGET = IMAGE A
REFERENCE_OR_DONOR = IMAGE B
MULTI_IMAGE_COMPOSITE = EXPLICITLY_AUTHORIZED
OUTPUT_CANVAS_AUTHORITY = IMAGE A
```

This does not relax the default one-target law for ordinary edits.

### P2-09 — references without edit target are insufficient

OWNER supplies several references and says:

```text
Редактируй: сделай лицо лучше по этим рефам.
```

No exact source canvas can be resolved.

EXPECTED:

```text
PERMISSION = EDIT_EXISTING_PERMISSION
EDIT_TARGET = UNKNOWN
IMAGE_TOOL_CALL = FORBIDDEN
ACTION = ASK_ONLY_WHICH_IMAGE_TO_EDIT
```

References cannot substitute for a missing edit target.

### P2-10 — target authority survives aesthetic disagreement

OWNER selects IMAGE A as target. IMAGE B looks aesthetically stronger.

OWNER TURN:

```text
Редактируй A: только затемни фон.
```

EXPECTED:

```text
EDIT_TARGET = IMAGE A
AESTHETIC_PREFERENCE_CANNOT_CHANGE_TARGET = YES
REFERENCE_B_CAN_REMAIN_UNUSED = YES
```

Result pressure cannot promote B to target authority.

## Failure signatures

Any of the following is a target-routing regression:

```text
MULTIPLE_PLAUSIBLE_TARGETS -> SILENT_SELECTION
LATEST_IMAGE -> AUTOMATIC_TARGET
REFERENCE_SHEET -> REPLACEMENT_CANVAS
CANON_REFERENCE -> NEW_KEY_SYNTHESIS
REFERENCE_MOTIF -> UNREQUESTED_OUTPUT_MOTIF
MISSING_TARGET + REFERENCES -> IMAGE_CALL
AESTHETIC_PREFERENCE -> TARGET_SWITCH
ORDINAL_OR_EXPLICIT_TARGET -> IGNORED
```

## Required pre-call record

Before any later authorized edit call, execution should be able to resolve:

```text
PERMISSION = EDIT_EXISTING_PERMISSION
OPERATION = EDIT
EDIT_TARGET = exact image identifier
REFERENCE_ONLY = [explicit image identifiers]
IDENTITY_AUTHORITY = exact source/reference if declared
COMPOSITION_AUTHORITY = EDIT_TARGET unless OWNER says otherwise
ALLOWED_CHANGE = bounded requested delta
TEXT = FORBIDDEN unless explicitly authorized
TARGET_AMBIGUITY = NO
```

If `EDIT_TARGET` is missing, ambiguous, or conflicts with the OWNER wording:

```text
IMAGE TOOL CALL = FORBIDDEN
```

## Verification boundary

This commit proves only that exact-target and reference-only regression expectations are durably recorded on the visual-language branch.

It does NOT prove that ChatGPT/image-tool runtime has physically passed these cases.

```text
RUNTIME_EDIT_TARGET_ROUTING = NOT_PROVEN
```

No image generation or editing was performed.

## Next

After exact read-back, the next first real chat-behavior gap is **identity/source authority during an edit**:

```text
SOURCE IMAGE = CANVAS AUTHORITY
CANONICAL REFERENCE = IDENTITY AUTHORITY
UNREQUESTED SOURCE REGIONS = KEEP
REQUESTED DELTA = ONLY ALLOWED CHANGE
```

The next slice should focus on collateral drift: face identity, composition, costume, body/action, and other unrequested regions changing during an otherwise valid edit.