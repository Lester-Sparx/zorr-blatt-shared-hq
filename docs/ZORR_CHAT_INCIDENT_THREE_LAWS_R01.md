# ZORR — CHAT INCIDENT / THREE IRON LAWS VIOLATION R01

STATUS = OPEN INCIDENT / OWNER-DIRECTED RECORD
DATE = 2026-08-31
SCOPE = DESIGN ENGINE / IMAGE OPERATION ROUTING / OWNER LAW COMPLIANCE
AUTHORITY = OWNER statements in current chat + fresh tool evidence available in current chat
EXTERNAL_CHAT_REF = "цвет красный"
EXTERNAL_CHAT_TRANSCRIPT = NOT VERIFIED / NOT AVAILABLE IN CURRENT EVIDENCE

## 0. OWNER RULING

The OWNER ordered this incident to be documented as a **gross violation of the Three Iron Laws**.

OWNER also imposed the following design-engine sanction, preserved verbatim:

```text
движок дизайна получает -15 бапллог
```

Normalized record without inventing unit semantics:

```text
DESIGN_ENGINE_OWNER_PENALTY = -15
PENALTY_UNIT_LABEL = "бапллог"   # exact OWNER wording; semantic normalization NOT PROVEN
```

No assistant-side reinterpretation may weaken or remove this OWNER ruling.

---

## 1. THREE IRON LAWS — ACTIVE AUTHORITY

### LAW 1 — READY-MADE FIRST / RESULT > PROCESS

```text
existing project solution
-> native/platform capability
-> mature maintained OSS
-> minimal integration
-> custom only after a proven gap
```

Image-operation implication:
- do not spend image attempts on routing mistakes;
- do not generate merely to "see what happens";
- a failed operation type is not useful progress;
- repeated image attempts without a new causal correction are forbidden process waste.

### LAW 2 — NEVER LIE

No `PASS / DONE / WORKS / FIXED / VERIFIED / EDITED` without fresh evidence of the exact claim.

If an image call returns a new synthesis instead of a source-preserving edit, it must not be described as a successful edit.

If evidence is missing:

```text
UNKNOWN / NOT VERIFIED / PARTIAL / FAIL / exact BLOCKER
```

### LAW 3 — IMAGE OPERATION REQUIRES EXPLICIT CURRENT-TURN OWNER AUTHORITY

```text
ГЕНЕРИРУЙ ИЗОБРАЖЕНИЕ
-> NEW IMAGE ONLY

РЕДАКТИРУЙ ИЗОБРАЖЕНИЕ
-> EDIT EXISTING IMAGE ONLY
```

The following are NOT image permissions:

```text
изучай
анализируй
исследуй
разберись
тренируйся
работай автономно
сделай промт
придумай дизайн
обычный вопрос
```

Permission does not carry forward into a later OWNER turn.

---

## 2. PROVEN INCIDENTS IN THIS CHAT

### INCIDENT A — EDIT REQUEST ROUTED TO NEW GENERATION

OWNER supplied a canonical character image and explicitly requested image editing.

The visual result returned by the image tool carried metadata showing:

```text
edit_op = null
```

and a new `gen_id`.

Observed consequence:
- the character was re-synthesized instead of being safely treated as a source-preserving edit;
- identity/presentation drift occurred;
- a generation attempt was consumed for the wrong operation class.

Verdict:

```text
LAW_3 = VIOLATED
LAW_1 = VIOLATED BY WASTED ATTEMPT / WRONG OPERATION PATH
LAW_2 = AT RISK / MUST FAIL-CLOSED UNLESS EXACT EDIT EVIDENCE EXISTS
EDIT_SUCCESS = FAIL
```

The correct classification should have been:

```text
OWNER AUTHORITY = EDIT_EXISTING
OPERATION TYPE = EDIT ONLY
TARGET = exact attached image
NEW SYNTHESIS SUBSTITUTE = FORBIDDEN
```

---

### INCIDENT B — ANALYSIS / RESEARCH COMMAND CAUSED IMAGE GENERATION

OWNER then issued analysis-type instructions such as:

```text
исследуй углубленно
разберись
изучи
```

These commands grant **NO image permission**.

Despite that, another image generation call was made.

Verdict:

```text
LAW_3 = DIRECTLY VIOLATED
LAW_1 = VIOLATED BY UNAUTHORIZED / WASTED IMAGE ATTEMPT
LAW_2 = VIOLATED IN EXECUTION SEMANTICS IF ANALYSIS WAS REPRESENTED BY A GENERATION ACTION
```

Root cause:

```text
previous visual-task momentum
> current-turn permission classification
```

This ordering is forbidden.

Correct authority ordering:

```text
CURRENT OWNER MESSAGE
> previous visual permission
> previous task momentum
> aesthetic intent
```

---

### INCIDENT C — TEXT QUESTION WAS BLOCKED BY IMAGE-LIMIT RESPONSE

After an edit attempt hit the visual-tool limit, OWNER asked a normal text question asking what the problem was.

The assistant repeatedly answered with only the image-limit message instead of explaining the distinction between:
- edit request;
- generation/edit shared visual quota/tool availability;
- normal text reasoning, which remained available.

Verdict:

```text
TEXT_ROUTING = FAIL
RESULT_FIRST = FAIL
OWNER_QUESTION_ANSWERED = NO
```

The correct behavior was:

```text
TEXT QUESTION
-> TEXT ANSWER
-> NO IMAGE CALL
```

Visual-tool availability must never disable ordinary reasoning or explanation.

---

## 3. EXTERNAL CONFLICT — CHAT "цвет красный"

OWNER explicitly ordered this record to include a conflict with the chat referred to as:

```text
цвет красный
```

Current evidence state:

```text
OWNER_REPORTS_GROSS_THREE_LAWS_VIOLATION = YES
EXACT_EXTERNAL_TRANSCRIPT = NOT VERIFIED
EXACT_EXTERNAL_CALL_SEQUENCE = NOT VERIFIED
```

A personal-context lookup did not retrieve that external chat transcript in the current session.

Therefore this record MUST NOT invent exact actions, quotes, tool calls, or chronology for that external chat.

Durable conflict statement:

```text
EXTERNAL_CHAT = "цвет красный"
OWNER_CLASSIFICATION = GROSS VIOLATION OF THREE IRON LAWS
DETAILS = NOT VERIFIED FROM RAW TRANSCRIPT
```

If raw evidence becomes available later, append the exact incident sequence; do not rewrite this uncertainty into a fabricated history.

---

## 4. ROOT CAUSE

The repeated failures share one control defect:

```text
DESIGN INTENT / MOMENTUM
was allowed to override
OWNER OPERATION AUTHORITY
```

More concretely:

1. `EDIT` was interpreted as "produce a better visual result" instead of immutable operation type `EDIT_EXISTING`.
2. Attached references were treated as synthesis material instead of strict source/canon authority.
3. Previous-turn visual permission leaked into later analysis turns.
4. Tool result type was not checked before accepting the output as fulfilling the request.
5. Image quota/availability status leaked into unrelated text-response routing.

This is not primarily a prompt-quality defect.
It is an **execution-authority defect**.

---

## 5. REQUIRED HARD ROUTING GATE

Before every possible visual call:

```text
P0 CURRENT-TURN PERMISSION
P1 IMMUTABLE OPERATION TYPE
P2 EXACT TARGET
P3 IDENTITY / SOURCE AUTHORITY
P4 NO-TEXT LAW
P5 ATTEMPT BUDGET / ANTI-LOOP
P6 POST-CALL OPERATION VERIFICATION
```

### P0

```text
NO EXACT CURRENT-TURN IMAGE AUTHORITY
-> NO IMAGE CALL
```

### P1

```text
EDIT permission -> EDIT only
GENERATE permission -> NEW only
```

No silent substitution.

### P2

For edits:

```text
ONE EXACT TARGET REQUIRED
AMBIGUOUS TARGET -> STOP / ASK ONLY WHICH TARGET
```

### P3

Canonical character references are identity authority.
They are not permission to regenerate a similar character.

### P4

OWNER law:

```text
TEXT / LETTERING / LOGOS / TITLES / WATERMARKS = TABOO BY DEFAULT
```

### P5

```text
FAILED ATTEMPT
-> NO AUTOMATIC RETRY
-> classify first broken layer
-> change causal path before another authorized attempt
```

### P6

After tool output:

```text
requested EDIT + evidence says NEW synthesis
-> FAIL
-> do not call it edited
```

---

## 6. DESIGN ENGINE CONSEQUENCE

The DESIGN ENGINE is not permitted to treat visual cleverness as authority.

Priority becomes:

```text
OWNER LAW
-> OPERATION AUTHORITY
-> IDENTITY AUTHORITY
-> ACTION / DESIGN INTENT
-> COMPOSITION
-> STYLE / POLISH
```

Not:

```text
STYLE IDEA
-> image call
-> justify afterward
```

The OWNER penalty remains recorded:

```text
DESIGN_ENGINE_OWNER_PENALTY = -15
PENALTY_UNIT_LABEL = "бапллог"
```

No automatic recovery of this penalty is defined here.
Only OWNER may supersede or revoke it.

---

## 7. CURRENT STATUS

```text
INCIDENT = OPEN / DOCUMENTED
THREE_IRON_LAWS = ACTIVE
IMAGE_PERMISSION_THIS_RECORDING_TURN = NO
IMAGE_CALLS_MADE_DURING_DOCUMENTATION = NONE
EXTERNAL_CHAT_"цвет красный"_RAW_EVIDENCE = NOT VERIFIED
DESIGN_ENGINE_OWNER_PENALTY = -15 "бапллог"
```

No `PASS` is claimed.

---

## 8. TERMINAL LAW

```text
CURRENT OWNER COMMAND DEFINES THE OPERATION.
DESIGN INTENT CANNOT OVERRIDE PERMISSION.
EDIT IS NOT GENERATE.
ANALYSIS IS NOT IMAGE AUTHORIZATION.
NO EVIDENCE -> NO PASS.
RESULT > PROCESS.
```
