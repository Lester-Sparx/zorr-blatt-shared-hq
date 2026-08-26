# ZORR BLATT — SALVADOR v1 CANON REFERENCE EDIT Design

Status: **OWNER-APPROVED IN CHAT / WRITTEN SPEC REVIEW REQUIRED BEFORE IMPLEMENTATION PLAN**

Authority repository: `Lester-Sparx/zorr-blatt-shared-hq`

Design branch: `salvador/v1-canon-reference-edit-design`

Base commit: `cf68c4882f84d8d0cce07f05ccc15345b913ddca`

Owner approval phrase: `ОДОБРЯЮ SALVADOR V1 DESIGN` on 2026-08-26.

## 1. Purpose

SALVADOR v1 is the first real production image mode built on top of the merged zero-budget local Agent Controller v0.

The user supplies an existing drawn character reference. SALVADOR must redraw that same reference into the ZORR BLATT production canon while preserving the subject and geometry as strongly as practical.

Core law:

```text
REFERENCE -> CANON EDIT
NOT text-to-image from scratch.
NOT redesign.
NOT pose invention.
NOT multi-character staging.
CANON > prettier output.
```

The production goal is a reliable canonization pass, not a broad generative art system.

## 2. User-facing behavior

Conceptually the user action is:

```text
user gives one character reference image
-> SALVADOR applies ZORR BLATT canon drawing treatment
-> one canonized output image is produced
```

For v1 execution, the local controller continues using the existing fixed `LOCAL_INBOX` boundary. A chat attachment is not automatically copied onto the owner's Windows machine by the current architecture. The production task becomes executable when its reference exists in the canonical local inbox directory.

A later intake bridge may make "drop image and go" fully automatic. That bridge is outside v1 and must not be faked by browser-tab automation.

## 3. v1 scope

The only new production task kind is:

```text
AGENT = SALVADOR
TASK_KIND = CANON_REFERENCE_EDIT
REFERENCE = LOCAL_INBOX
BACKEND = COMFYUI_LOCAL
```

v1 accepts one existing drawn character reference and returns one canonized image.

Supported intent:

- redraw a sketch, concept, character reference, or existing illustration into ZORR BLATT production canon;
- preserve the same subject;
- preserve pose and composition;
- preserve silhouette and major construction;
- preserve key costume/weapon read where present;
- apply approved canon drawing treatment;
- obey any locked character truths supplied in the production direction.

## 4. Explicit non-scope

v1 does NOT include:

- text-to-image character creation from scratch;
- photographs of real people as production input;
- multi-character scenes;
- automatic pose changes;
- automatic turnaround generation;
- automatic sheet normalization;
- expression-sheet generation;
- garment redesign;
- environment paintover;
- texture/material pass;
- texture generation from LYNCH commands;
- final high-resolution polish/upscale pipeline;
- paid inference APIs;
- automatic chat-to-local-file transport.

Texture work is reserved for a later SALVADOR v2 `TEXTURE_PASS` design.

## 5. Input contract

Exactly one local reference image is accepted per task.

Accepted file extensions remain:

```text
.png
.jpg / .jpeg
.webp
```

The existing local safety law remains unchanged:

```text
D:\BLATT2\ZB_AGENT_INBOX\<TASK_ID>\
```

The controller constructs this path. GitHub issue text cannot provide an arbitrary filesystem path.

The task is rejected or held when:

- no valid reference exists;
- more than one candidate image exists;
- the file is empty/corrupt/unsupported;
- the task is not explicitly marked as a ZB agent task;
- task preparation/QC determines that the input is outside the single-character v1 scope.

## 6. Character-count law

v1 is single-character only.

The task preparer/JINGO must assign `CANON_REFERENCE_EDIT` only to a reference intended to contain one primary character. v1 does not require the local controller to invent a new semantic computer-vision classifier for counting people in pixels.

If task preparation, workflow preflight, or visual QC detects multiple primary characters, execution/acceptance must stop rather than guess which subject to canonize.

Stable production scope error:

```text
SALVADOR_MULTI_CHARACTER_UNSUPPORTED
```

False refusal is preferable to silently altering the wrong subject.

## 7. Geometry preservation law

Geometry preservation is the highest production priority after locked canon truth.

SALVADOR v1 should preserve, as applicable:

- identity/read of the character;
- head/body relationship;
- body proportions;
- pose;
- camera framing;
- composition;
- silhouette;
- limb placement;
- major costume shapes;
- weapon placement;
- major asymmetries;
- major color/value zones when relevant to the source.

SALVADOR may simplify micro-detail and visual noise where that is part of the approved ZORR BLATT drawing treatment, but it must not use simplification as permission to redesign the character.

## 8. Canon precedence

Canonical precedence is:

```text
locked project canon
> locked character canon
> production direction
> source reference detail
> model aesthetic preference
```

A visually attractive result that violates locked canon is a failed result.

The production prompt must contain an immutable canon layer controlled by the repository plus a task-specific direction layer.

Task issue text must not be able to override immutable canon rules with instructions such as "ignore canon", "redesign", or equivalent.

## 9. Canon prompt architecture

SALVADOR v1 uses two prompt layers:

### 9.1 Immutable repository-owned canon prompt

A versioned production prompt asset defines the global behavior of `CANON_REFERENCE_EDIT`, including:

- preserve identity;
- preserve geometry;
- preserve pose/composition;
- no redesign;
- simplify only according to approved production drawing rules;
- locked canon outranks aesthetic preference;
- single-character production edit.

This asset is code-reviewed and versioned with the workflow.

### 9.2 Task-specific production direction

The durable task direction may add character-specific requirements derived from already approved canon, for example locked face/body truths or a narrowly requested drawing treatment.

The task direction may refine the edit but may not relax immutable v1 laws.

## 10. ComfyUI production workflow architecture

The production workflow is separate from the disposable Task 7 `ImageInvert` smoke workflow.

The smoke workflow remains proof infrastructure only and MUST NOT be treated as a production model.

Recommended v1 data flow:

```text
Load reference
-> normalize size/aspect without changing composition
-> encode/reference-condition the source
-> structural preservation conditioning when the approved local model path supports it
-> canon/style conditioning
-> low-to-moderate transformation image-to-image pass
-> decode
-> save one output
-> controller validates and persists canonical result
```

The workflow must favor structure preservation over large generative freedom.

The exact checkpoint/control model is an implementation-time local compatibility choice, not a hard-coded orchestration constant.

## 11. Recommended model strategy

v1 should use a free/local image-to-image model family that can run reliably on the owner's 4 GB NVIDIA GPU.

Recommended constraints:

- local inference only;
- batch size 1;
- one image output;
- conservative working resolution suitable for 4 GB VRAM;
- strong source-image conditioning;
- low-to-moderate denoise/transform strength;
- optional structural conditioning if it fits the VRAM budget;
- model/checkpoint name and path remain external configuration;
- no production model binary is committed to Shared HQ;
- model identity/version/checksum is recorded in local deployment metadata where practical.

### 11.1 Recommended first compatibility baseline

The first implementation spike should prefer a lightweight SD1.5-class local illustration/anime image-to-image path because it is materially more realistic on the 4 GB target than starting with a large modern checkpoint.

Baseline workflow behavior:

```text
reference image
-> VAE/image-to-image encoding
-> batch 1 sampler
-> conservative denoise, initially tuned inside approximately 0.25-0.45
-> same-aspect output at the bounded working size
```

If a single structural conditioning model such as line-art/canny ControlNet fits the 4 GB smoke reliably, it should be tested as the preferred geometry-preservation enhancement. If it does not fit reliably, v1 falls back to the conservative low-denoise image-to-image baseline rather than expanding scope or using a paid backend.

Exact checkpoint/control names are selected only after a local compatibility/preservation spike and are external deployment configuration.

A model is not approved merely because it runs. It must pass a disposable local preservation test before it may process production canon references.

## 12. Resolution policy

v1 prioritizes reliability and geometry preservation over maximum output resolution.

Recommended first production limits:

- preserve source aspect ratio;
- no crop unless explicitly required by a later mode;
- batch size 1;
- constrain the working image so the long side is at most 768 px for the first 4 GB VRAM implementation target;
- output at the workflow working size;
- high-resolution upscale is a separate later stage.

If the source is larger, normalization must be deterministic and must not distort aspect ratio.

## 13. Task contract extension

The existing strict machine-readable task format is retained:

```text
ZB_AGENT_TASK_V0
TASK_ID = ZB-SALVADOR-...
AGENT = SALVADOR
TASK_KIND = CANON_REFERENCE_EDIT
STATE = ASSIGNED
REFERENCE = LOCAL_INBOX

<production direction>
```

`CANON_REFERENCE_EDIT` is added to the explicit allowed task kinds.

No arbitrary new key/value fields are required for v1.

This keeps the queue contract narrow and compatible with the existing parser/state machine.

## 14. State/evidence law

The already accepted controller evidence law is unchanged:

```text
ASSIGNED != RUNNING
```

For production SALVADOR:

```text
RUNNING
```

may be posted only after real ComfyUI submission returns a non-empty real `prompt_id`.

```text
RESULT_READY
```

may be posted only after a real output image and result metadata are persisted and validated locally.

Duplicate protection remains mandatory. Re-polling a completed durable task must not submit a second generation.

## 15. Production result metadata

`result.json` should continue to record existing evidence and should additionally record enough production provenance to reproduce/debug the result without publishing the image itself.

Recommended additions:

```text
taskKind = CANON_REFERENCE_EDIT
workflowVersion
canonPromptVersion
modelId or local model label
workingWidth
workingHeight
promptId
resultSha256
```

No secret token, private local credential, or model binary is written to GitHub.

## 16. Output validation

A successful v1 output must satisfy machine validation before `RESULT_READY`:

- exactly one supported output image collected;
- non-empty file;
- decodable image;
- expected image type;
- dimensions are non-zero and within configured production bounds;
- checksum written;
- result metadata written atomically.

Machine validation does not prove artistic/canon correctness.

The first production acceptance run additionally requires human/JINGO visual QC against the supplied reference and locked canon.

## 17. Stable production failure/event vocabulary

Recommended machine/backend durable events include:

```text
SALVADOR_REFERENCE_REQUIRED
SALVADOR_BACKEND_UNAVAILABLE
SALVADOR_MODEL_UNAVAILABLE
SALVADOR_RESULT_INVALID
SALVADOR_RESULT_READY
```

Recommended coordination/QC scope verdicts include:

```text
SALVADOR_UNSUPPORTED_INPUT
SALVADOR_MULTI_CHARACTER_UNSUPPORTED
SALVADOR_CANON_CONFLICT
```

The second group does not imply that v1 contains a new semantic pixel classifier. Those verdicts may come from task preparation, workflow preflight where mechanically knowable, or visual/canon QC.

Low-level backend errors may still exist internally, but user-facing durable state should remain stable and understandable.

## 18. Safety and filesystem boundary

All existing controller safety boundaries remain mandatory:

- no arbitrary issue-controlled filesystem path;
- no shell execution from issue text;
- fixed GitHub CLI argv;
- fixed local roots;
- one active SALVADOR GPU task at a time;
- terminal `FAILED` behavior remains explicit;
- restart/duplicate safety remains intact;
- no runtime writes to the source repository;
- no paid API key.

## 19. Production activation gate

Merging implementation code does not automatically activate production SALVADOR.

Production activation requires all of the following:

```text
1. implementation tests PASS
2. independent DUNCAN QC PASS
3. disposable local production-model preservation smoke PASS
4. real ComfyUI prompt_id evidence
5. real persisted output + SHA256
6. duplicate submission proof
7. JINGO visual/canon QC PASS on a non-sensitive production test reference
8. explicit OWNER production activation approval
```

Until all eight are satisfied:

```text
PRODUCTION_ACTIVATION = NO
```

## 20. First production acceptance target

The first acceptance target should use one non-sensitive drawn single-character reference selected specifically for testing.

Pass criteria:

- source character remains clearly the same subject;
- pose/composition remain materially unchanged;
- major geometry is preserved;
- no unsolicited redesign;
- output visibly moves toward approved ZORR BLATT production drawing treatment;
- no production canon lock is violated;
- durable state/evidence is correct;
- no duplicate submission occurs.

The first acceptance target is a gate, not a declaration that all future references will be perfect.

## 21. Future SALVADOR v2 — explicitly deferred

The next planned visual subsystem is:

```text
TEXTURE_PASS
```

It may accept texture/material references or instructions supplied through LYNCH directing flow.

It is deliberately deferred so v1 can first prove reliable reference-preserving canon redraw.

No v2 texture behavior should be smuggled into the v1 workflow.

## 22. Implementation ownership

After written-spec approval:

- JINGO creates the implementation plan and gates;
- LESTER implements production controller/workflow support by TDD;
- DUNCAN independently verifies source identity, tests, safety boundaries, and live evidence;
- SALVADOR is the logical production image role using the local ComfyUI backend;
- OWNER controls final production activation.

No implementation starts from this document until the owner approves the written spec.
