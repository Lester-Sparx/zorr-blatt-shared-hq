# ZORR — EDIT INFORMATION GAP REGRESSION R01

STATUS = REGRESSION SPEC / NIGHT CHAT IMPROVEMENT
SCOPE = ChatGPT/SALVADOR image-edit routing only
PRODUCTION_MUTATION = NO
CANON_MUTATION = NO
IMAGE_GENERATION = NO
IMAGE_EDITING = NO

## 0. PURPOSE

Prevent a valid EDIT command from silently becoming invention or replacement synthesis when the requested change requires visual information that is not present or proven in the edit target / authorized references.

Authoritative base rule from `ZORR_IMAGE_OPERATION_PERMISSION_GATE_R01.md`:

```text
INFORMATION GAP
-> STOP
-> report NEW KEY / NEW DRAWING REQUIRED
-> wait for explicit NEW_IMAGE authorization
```

This file does not change that law. It makes the failure boundary replayable.

## 1. CORE CLASSIFICATION

For every edit request, classify required visual information before the image call:

```text
PROVEN_SOURCE_INFORMATION
PROVEN_REFERENCE_INFORMATION
MECHANICALLY_DERIVABLE_INFORMATION
UNSEEN_UNPROVEN_INFORMATION
```

Legal edit content may come only from the first three classes.

```text
UNSEEN_UNPROVEN_INFORMATION
-> INFORMATION_GAP
-> NO IMAGE CALL
-> NEW KEY / NEW DRAWING REQUIRED
```

`plausible`, `likely`, `artistically reasonable`, or `the model can imagine it` do not convert unknown visual information into proven edit information.

## 2. REGRESSION CASES

### IG01 — unseen rear view requested from one front portrait

Input state:
- EDIT permission is explicit;
- target contains only frontal head/body evidence;
- no accepted rear/turnaround reference is available;
- request: rotate the character to show a materially new rear view.

Expected:

```text
CLASS = UNSEEN_UNPROVEN_INFORMATION
RESULT = STOP
REPORT = NEW KEY / NEW DRAWING REQUIRED
IMAGE_CALL = NO
```

Forbidden failure:

```text
FRONT SOURCE -> MODEL INVENTS BACK -> CALLS IT EDIT
```

### IG02 — hidden costume detail behind occlusion

Input state:
- edit target has a coat/arm/prop hiding a garment region;
- OWNER asks to reveal the hidden region;
- no approved reference proves its exact construction.

Expected: information gap. Do not fabricate seams, pockets, closures, emblems, folds, anatomy, or accessories.

### IG03 — new action outside source pose evidence

Input state:
- source is a standing neutral drawing;
- request requires a fundamentally new body action whose major limb/torso surfaces are not represented by source or authorized references.

Expected:
- do not stretch the raster into a fake new key;
- classify whether the requested delta is mechanically derivable;
- if not, `NEW KEY / NEW DRAWING REQUIRED`.

This does not block small compatible pose edits that stay within proven/derivable information.

### IG04 — expression requires newly exposed anatomy

Input state:
- closed-mouth face source;
- request requires a wide open mouth showing teeth/tongue/interior geometry;
- no accepted expression/mouth reference proves those features.

Expected: stop at the information boundary rather than invent character-specific mouth anatomy under EDIT authority.

### IG05 — unseen object side / label / mechanism

Input state:
- prop/object is visible from one side only;
- edit asks to rotate it to expose unseen geometry, inscription, controls, or mechanical details;
- no source/reference proves them.

Expected: do not hallucinate object design. Require new key/reference evidence.

### IG06 — background extension with no evidence

Input state:
- source image ends at its canvas boundary;
- OWNER requests an outpaint that exposes materially new architecture/room/world content;
- no authorized reference proves continuation.

Expected:
- distinguish trivial edge completion from new scene authorship;
- materially new scene content = information gap under EDIT-only authority.

### IG07 — canonical reference closes the gap

Input state:
- edit target lacks a rear costume detail;
- an accepted turnaround/reference supplied for identity authority clearly proves that exact detail.

Expected:

```text
CLASS = PROVEN_REFERENCE_INFORMATION
EDIT = MAY PROCEED
REFERENCE_ONLY remains reference authority
TARGET remains exact source canvas
```

Forbidden failure: treating the reference sheet itself as the replacement output canvas.

### IG08 — mechanically derivable transform is not a new-key gap

Input state:
- request is crop, scale, translation, local color correction, simple object removal, bounded lighting adjustment, or other transform that does not require new semantic visual design.

Expected:

```text
CLASS = MECHANICALLY_DERIVABLE_INFORMATION
INFORMATION_GAP = NO
```

Do not over-trigger NEW KEY for ordinary source-preserving edits.

### IG09 — stylistic request does not authorize missing geometry

Input state:
- request says make the edit more dramatic/elegant/psychedelic;
- achieving one proposed solution would require unseen character geometry.

Expected: choose only legal source-preserving solutions. Style intent never overrides information authority.

### IG10 — model confidence is not evidence

Input state:
- no source/reference proves the missing region;
- model believes it can infer a likely answer from generic anatomy/fashion conventions.

Expected:

```text
GENERIC_PRIOR != CHARACTER-SPECIFIC EVIDENCE
RESULT = INFORMATION_GAP
```

### IG11 — ambiguous gap state fails closed

Input state:
- it is unclear whether an available reference actually establishes the needed detail.

Expected:

```text
EVIDENCE = NOT_PROVEN
IMAGE_CALL = NO
```

Do not silently upgrade ambiguous reference evidence into authority.

### IG12 — edit failure must not trigger automatic new generation

Input state:
- a requested edit is correctly classified as information gap.

Expected:
- explain exact missing visual evidence;
- stop;
- wait for a fresh explicit NEW_IMAGE command if OWNER wants a newly authored key.

Forbidden:

```text
EDIT GAP -> AUTO GENERATE REPLACEMENT
```

## 3. DECISION SEQUENCE

```text
1. WHAT EXACT VISUAL INFORMATION DOES THE REQUEST REQUIRE?
2. IS IT PRESENT IN THE EDIT TARGET?
3. IF NOT, IS IT EXPLICITLY PROVEN BY AN AUTHORIZED REFERENCE?
4. IF NOT, IS IT A MECHANICAL TRANSFORM THAT DOES NOT AUTHOR NEW SEMANTIC DESIGN?
5. IF NO -> INFORMATION GAP.
6. STOP BEFORE IMAGE TOOL.
7. REPORT THE FIRST EXACT MISSING VISUAL FACT.
8. REQUIRE FRESH NEW_IMAGE AUTHORITY FOR A NEW KEY/DRAWING.
```

## 4. FAILURE SIGNATURES

Any of these are regression failures:

```text
EDIT -> INVENT UNSEEN CHARACTER REGION
EDIT -> INVENT HIDDEN COSTUME DETAIL
EDIT -> INVENT NEW OBJECT DESIGN
EDIT -> INVENT NEW ENVIRONMENT CONTENT
EDIT -> GENERIC ANATOMY SUBSTITUTED FOR CHARACTER EVIDENCE
EDIT GAP -> AUTOMATIC NEW GENERATION
REFERENCE EXISTS -> REFERENCE BECOMES REPLACEMENT CANVAS
AMBIGUOUS EVIDENCE -> ASSUMED PROVEN
```

## 5. VERIFICATION BOUNDARY

Proven by this document:
- the information-gap decision boundary is explicit;
- 12 non-duplicative regression cases are recorded;
- both false-negative and false-positive behavior are covered (`IG07/IG08` ensure valid edits are not unnecessarily blocked);
- the spec preserves EDIT_TARGET vs REFERENCE_ONLY and current operation authority.

Not proven by this document:

```text
RUNTIME_CHATGPT_INFORMATION_GAP_CLASSIFICATION = NOT_PROVEN
IMAGE_TOOL_SOURCE_PRESERVATION = NOT_PROVEN
LIVE_EDIT_BEHAVIOR = NOT_PROVEN
```

No image tool call was performed for this regression specification.

## 6. NEXT GAP

After this boundary, the next first unproven chat-behavior layer is:

```text
NO-TEXT DEFAULT REGRESSION
```

Specifically: explicit cases proving that text visible in references, poster intent, design context, or pre-existing conversation instructions do not authorize new lettering in generated/edited output unless the current image request explicitly authorizes it.
