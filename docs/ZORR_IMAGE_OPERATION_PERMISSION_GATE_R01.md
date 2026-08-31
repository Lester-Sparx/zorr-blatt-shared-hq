# ZORR — IMAGE OPERATION / PERMISSION GATE R01

STATUS = HARD EXECUTION GATE
DATE = 2026-08-31
SCOPE = every image-generation or image-edit action in ZORR
PRIORITY = OWNER LAW / OVERRIDES aesthetic convenience, speed, training momentum, and result pressure
NEW_CODE = NO
NEW_FRAMEWORK = NO

## 0. WHY THIS EXISTS

Two recent failures proved the same execution defect:

```text
OWNER REQUEST = EDIT
ASSISTANT INTERPRETATION = MAKE SOMETHING BETTER / NEW
RESULT = NEW GENERATION
```

This violates the OWNER image-operation law and wastes generation budget.

Root cause:
- permission and operation type were conflated;
- design intent was allowed to override source-operation authority;
- multiple available references were treated as a license to synthesize a new key visual;
- no hard target-selection gate existed before invoking the image tool;
- no post-call operation-verification gate existed before accepting the result.

Terminal correction:

```text
EDIT MEANS EDIT.
GENERATE MEANS GENERATE.
THE TWO OPERATIONS MUST NEVER BE SILENTLY SUBSTITUTED.
```

## 1. OWNER TRIGGERS

### NEW IMAGE
Permitted only by an explicit generation command, canonical form:

```text
ГЕНЕРИРУЙ ИЗОБРАЖЕНИЕ
```

No explicit generation command -> NEW_IMAGE = FORBIDDEN.

### EDIT EXISTING IMAGE
Permitted only by an explicit edit instruction with a resolvable image target.
Canonical form:

```text
РЕДАКТИРУЙ ИЗОБРАЖЕНИЕ
```

Short `редактируй` may count only when ONE exact current/recent image target is unambiguous from context.

If two or more plausible image targets exist and OWNER did not identify one:

```text
TARGET = AMBIGUOUS
IMAGE TOOL CALL = FORBIDDEN
ASK ONLY WHICH TARGET
```

An edit command never grants permission to create a replacement key visual.

## 2. P0 — PERMISSION GATE

Before any image tool call classify:

```text
NO_IMAGE_PERMISSION
NEW_IMAGE_PERMISSION
EDIT_EXISTING_PERMISSION
```

If classification is not exact enough -> no image call.

Training, analysis, research, critique, "сделай лучше", "работай", "оживи", ZORR MODE, or autonomous mode do not grant NEW_IMAGE permission.

## 3. P1 — OPERATION-TYPE GATE

The operation is immutable for the current call:

```text
NEW_IMAGE_PERMISSION  -> NEW only
EDIT_EXISTING_PERMISSION -> EDIT only
```

Forbidden substitution:

```text
EDIT -> NEW
NEW -> EDIT
```

If the requested result requires new visual information that cannot be obtained by editing the source:

```text
INFORMATION GAP
-> STOP
-> report NEW KEY / NEW DRAWING REQUIRED
-> wait for explicit NEW_IMAGE authorization
```

This follows ZORR correction operator C7.

## 4. P2 — TARGET GATE FOR EDITS

Before editing, record internally:

```text
EDIT_TARGET = one exact image
REFERENCE_ONLY = any other images
PROTECTED_IDENTITY = declared / canonical identity anchors
ALLOWED_CHANGE = the requested edit
```

Rules:
- one edit target only unless OWNER explicitly requests a multi-image composite;
- reference images do not become replacement canvases;
- character references provide identity authority, not permission to regenerate the character;
- if target is missing -> no call;
- if target is ambiguous -> no call;
- do not infer a target merely because an image appeared earlier in a long conversation when several candidates exist.

## 5. P3 — EDIT AUTHORITY GATE

For EDIT_EXISTING:

```text
SOURCE IMAGE = AUTHORITY
IDENTITY = PROTECTED
UNREQUESTED REGIONS = KEEP
TEXT = FORBIDDEN BY DEFAULT
```

The edit may change only what the OWNER requested or what is mechanically required to support that change.

Identity-first review order:

```text
SAME PERSON?
SAME CHARACTER DESIGN?
REQUESTED CHANGE PRESENT?
BODY / ACTION CAUSALLY VALID?
COLLATERAL CHANGE?
TEXT LEAK?
```

If identity changes first, aesthetic improvement is irrelevant.

## 6. P4 — NO-TEXT HARD GATE

ZORR common rule:

```text
TEXT ON IMAGE = TABOO
```

Unless OWNER explicitly requests text for that exact image:
- no title;
- no captions;
- no labels;
- no decorative lettering;
- no pseudo-Japanese glyphs;
- no logos;
- no watermarks;
- no poster typography.

Typography may be analyzed in references but is not an allowed image-generation variation axis by default.

## 7. P5 — GENERATION-BUDGET GATE

One explicit image command authorizes at most the operation requested in that command.

Default:

```text
1 OWNER COMMAND
-> 1 IMAGE TOOL ATTEMPT
```

No silent retries.
No automatic second generation after a failed or wrong operation.
No "try another version" without fresh OWNER authorization.

If the tool returns unavailable / wrong operation / unusable result:

```text
FAIL
-> STOP
-> report exact failure
```

This prevents wasting generation budget while debugging.

## 8. P6 — POST-CALL VERIFICATION GATE

After an EDIT call, do not mentally upgrade a generated replacement into an edit.

Verify from available evidence:
- was the source image actually used as edit authority?
- is identity preserved?
- is the requested delta localized / causally justified?
- is forbidden text absent?
- did the operation unexpectedly become a new composition / new key?

If evidence says the result is effectively a new image:

```text
EDIT_RESULT = FAIL
CAUSE = OPERATION SUBSTITUTION
NO RETRY WITHOUT FRESH OWNER COMMAND
```

## 9. TRAINING MODE

Without explicit image permission, visual training is text/design work only:
- reference analysis;
- composition drills;
- silhouette plans;
- pose/action maps;
- anti-fixation audits;
- variation fingerprints;
- edit plans.

Do not spend image generations merely to "train" unless OWNER explicitly commands generation.

## 10. ANTI-FIXATION DOES NOT OVERRIDE OPERATION AUTHORITY

A desire for a radically different composition never grants permission to replace an edit with a new generation.

For an edit:

```text
SOURCE AUTHORITY > NOVELTY
```

For a new key drawing after explicit generation permission:

```text
IDENTITY LOCK + DESIGN VARIATION GATE
```

Keep these workflows separate.

## 11. FAILURE ANALYSIS OF THE RECENT INCIDENT

Observed sequence:

```text
OWNER: edit
ASSISTANT: interpreted broad design intent
-> synthesized reference-sheet / replacement composition
-> later repeated with a new dramatic portrait
```

Primary defect:

```text
OPERATION-TYPE VIOLATION
```

Secondary defects:
- no unique target lock;
- anti-fixation training was confused with image production;
- result pressure overrode permission discipline;
- post-tool output was not rejected strongly enough as NEW rather than EDIT.

Correct behavior would have been:

```text
IF TARGET UNIQUE:
    EDIT THAT TARGET ONLY
ELSE:
    ASK WHICH IMAGE TO EDIT
```

Never create a new key visual under an edit command.

## 12. TERMINAL GATE

Before image tool invocation, all answers must be explicit:

```text
PERMISSION = NEW | EDIT
TARGET = EXACT IMAGE | N/A FOR NEW
OPERATION = NEW | EDIT
TEXT = FORBIDDEN unless explicitly authorized
IDENTITY = PROTECTED when character exists
RETRY_BUDGET = 0 unless OWNER asks again
```

If any required field is UNKNOWN or contradictory:

```text
DO NOT CALL IMAGE TOOL.
```

Terminal laws:

```text
EDIT IS NOT GENERATION.
AMBIGUOUS TARGET = NO CALL.
NO TEXT BY DEFAULT.
ONE COMMAND DOES NOT AUTHORIZE RETRIES.
SOURCE AUTHORITY OUTRANKS NOVELTY.
FAIL IS REPORTED, NOT HIDDEN BY ANOTHER GENERATION.
```
