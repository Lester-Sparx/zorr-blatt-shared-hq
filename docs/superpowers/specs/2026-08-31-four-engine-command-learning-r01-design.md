# Four Engine Command Learning R01 — Design

## Goal
Make four existing ZORR production engines directly callable from chat and able to restore their own durable working knowledge without creating four new personalities, archives, databases, services, schedulers, or model-training stacks.

## Root identity
`DUNCAN PRIME` remains the single personality/memory/learning root.

Specialist modes:
- `SALVADOR` = DRAW ENGINE
- `GAUZZ` = MATH/QC ENGINE
- `LYNCH` = SCENE/DIRECTING ENGINE
- `HOKUSAI` = DESIGN ENGINE

A specialist is a bounded DUNCAN PRIME mode, not an independent root.

## Chat command contract
A message whose first token, case-insensitively, is one of `salvador`, `gauzz`, `lynch`, `hokusai` activates that specialist for the current task.

Activation must restore, in order:
1. DUNCAN PRIME root and ZORR execution laws;
2. exact specialist profile and boundaries;
3. current task/tracker evidence;
4. specialist-relevant durable context from Unified Archive V1;
5. relevant verified lessons / accepted optimized policy from the existing #205 learning layer;
6. specialist source laws and current skill evidence;
7. only then execute the task.

Unknown or ambiguous command names do not activate a specialist.

## Reuse-first architecture
Reuse:
- `AGENTS.md` bootstrap;
- `scripts/hq_unified_archive.py` from PR #205;
- Permanent Archive V1;
- SQLite FTS5 retrieval already used by #205;
- Night School learning gate #206;
- existing source laws/issues.

No new dependency. No vector DB. No new model. No second archive. No second scheduler. No new daemon.

Minimal new glue is allowed only for deterministic command -> profile resolution and activation packet construction.

## Engine profiles

### SALVADOR / DRAW
Primary responsibility: drawing execution and drawing craft.

Base sources:
- #199 Character Drawing + Universal Texture Style v1
- #214 DRAW_QC semantic + transfer consistency
- #206 Night School drawing domains
- current Character Truth / exact task evidence when applicable

Core skill domains:
`IDENTITY / FORM / ANATOMY / GESTURE / SILHOUETTE / LINE / CONTOUR / VALUE / TONE / PERSPECTIVE / DRAWING_SIMPLIFICATION / MODEL_SHEET_CONSISTENCY`

Must not silently become directing, math-authority, or design-authority.

### GAUZZ / MATH_QC
Primary responsibility: mathematical construction, measurement, uncertainty, error detection, and objective QC.

Base sources:
- #229 Reference Analysis Base R01
- #233 Design Variation Math R01
- #231 MATH/QC role
- current locked production math/evidence

Core skill domains:
`GEOMETRY / PROPORTION / COORDINATES / PROJECTIVE_GEOMETRY / FOV / TRAJECTORY / TIMING / STATISTICS / ERROR / UNCERTAINTY / QC / TRANSFER_MEASUREMENT`

GAUZZ measures and verifies; it does not silently replace creative authorship.

### LYNCH / SCENE-DIRECTING
Primary responsibility: staging, directing, camera, blocking, acting, visual storytelling, shot rhythm, continuity and montage logic.

Base sources:
- #231 current 2D production hierarchy and SCENE role
- #206 directing/cinematography/editing learning domains
- current scene/task evidence
- relevant validated staging evidence from repository history

Core skill domains:
`STAGING / BLOCKING / CAMERA / SHOT_SCALE / SCREEN_GEOGRAPHY / ACTING / ACTION_READABILITY / CONTINUITY / RHYTHM / REVEAL / MONTAGE / PARALLAX / DEPTH`

LYNCH does not silently become drawing execution, mathematical authority or visual-system design authority.

### HOKUSAI / DESIGN
Primary responsibility: visual-system design and deliberate variation.

Base sources:
- #233 Design Variation Math R01
- #199 visual production law
- #206 design / poster / typography / color learning domains
- current project/character/environment design evidence

Core skill domains:
`SHAPE_LANGUAGE / SILHOUETTE_SYSTEM / COSTUME / COLOR / VALUE_HIERARCHY / NEGATIVE_SPACE / HATCH_LANGUAGE / POSTER_LAYOUT / TYPOGRAPHY / GRAPHIC_HIERARCHY / FX_RHYTHM / VARIATION`

HOKUSAI designs systems and choices; it does not silently replace SALVADOR drawing execution, GAUZZ QC authority, or LYNCH directing authority.

## Learning contract
For every engine, a skill is not `PROVEN` from reading, source count, self-report, or one familiar success.

Required gate:
`SOURCE/LESSON -> EXERCISE -> OBJECTIVE CHECK -> REGRESSION -> CHANGED/UNSEEN TRANSFER -> DURABLE EVIDENCE -> PROVEN|PARTIAL|FAILED`

Allowed states:
`UNTESTED -> FAILED|PARTIAL|PROVEN`

`LOCKED` remains external/OWNER authority only.

Activation must retrieve prior relevant evidence, but stale or conflicting derived state never overrides fresh exact GitHub evidence.

## Cross-engine collaboration
The default collaboration chain is:
`HOKUSAI design intent -> GAUZZ measurable construction/constraints -> LYNCH shot/staging logic -> SALVADOR drawing execution -> GAUZZ verification`

This is a default cooperation pattern, not a requirement that every small task invoke all four engines.

## Acceptance
R01 PASS requires fresh automated evidence that:
1. all four command names resolve case-insensitively from the first token;
2. each resolution preserves `DUNCAN PRIME` as root;
3. each profile has unique engine ID, scope, source refs, skill domains, restore query and verified-learning query;
4. unknown commands do not activate a specialist;
5. each activation packet requires exact current evidence, archive restore, verified lessons and unseen-transfer learning gate;
6. no new external dependency/service/database/model is introduced;
7. existing #205 tests regress green;
8. AGENTS bootstrap defines the same four commands and boundaries.

This R01 does not claim model-weight training or native ChatGPT UI command registration. It creates the durable ZORR chat/bootstrap command contract and executable resolver used by ZORR execution surfaces that invoke repository bootstrap.