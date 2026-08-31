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

A specialist is a bounded DUNCAN PRIME mode, not an independent root. DUNCAN PRIME is not a fifth engine.

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

Minimal new glue is allowed only for deterministic command -> profile resolution and activation contract construction.

## Engine profiles

### SALVADOR / DRAW
Primary responsibility: drawing execution and drawing craft.
Base sources: #199, #214, #206, exact Character Truth/task evidence.
Core domains: identity, form, anatomy, gesture, silhouette, line, contour, value, tone, perspective, drawing simplification, model-sheet consistency.

### GAUZZ / MATH_QC
Primary responsibility: mathematical construction, measurement, uncertainty, error detection, objective QC.
Base sources: #229, #233, #231, current locked production math/evidence.
Core domains: geometry, proportion, coordinates, projective geometry, FOV, trajectory, timing, statistics, error, uncertainty, QC, transfer measurement.

### LYNCH / SCENE_DIRECTING
Primary responsibility: staging, directing, camera, blocking, acting, visual storytelling, shot rhythm, continuity and montage logic.
Base sources: #231, #206, current scene/task evidence, validated staging history.
Core domains: staging, blocking, camera, shot scale, screen geography, acting, action readability, continuity, rhythm, reveal, montage, parallax, depth.

### HOKUSAI / DESIGN
Primary responsibility: visual-system design and deliberate variation.
Base sources: #233, #199, #206, current project/character/environment design evidence.
Core domains: shape language, silhouette system, costume, color, value hierarchy, negative space, hatch language, poster layout, typography, graphic hierarchy, FX rhythm, variation.

## Learning contract
For every engine, a skill is not `PROVEN` from reading, source count, self-report, or one familiar success.

Required gate:
`SOURCE/LESSON -> EXERCISE -> OBJECTIVE CHECK -> REGRESSION -> CHANGED/UNSEEN TRANSFER -> DURABLE EVIDENCE -> PROVEN|PARTIAL|FAILED`

Allowed states: `UNTESTED -> FAILED|PARTIAL|PROVEN`. `LOCKED` remains external/OWNER authority only.

## Cross-engine collaboration
Default collaboration chain:
`HOKUSAI design intent -> GAUZZ measurable construction/constraints -> LYNCH shot/staging logic -> SALVADOR drawing execution -> GAUZZ verification`

This is a cooperation pattern, not a fifth engine and not a requirement that every small task invoke all four.

## Acceptance
R01 PASS requires fresh automated evidence that:
1. all four command names resolve case-insensitively from the first token;
2. each resolution preserves `DUNCAN PRIME` as root;
3. each profile has unique engine ID, scope, source refs, skill domains, restore query and verified-learning query;
4. unknown commands do not activate a specialist;
5. each activation contract requires exact current evidence, archive restore, verified lessons and unseen-transfer learning gate;
6. no new external dependency/service/database/model is introduced;
7. existing #205 tests regress green;
8. AGENTS bootstrap defines the same four commands and boundaries.

This R01 does not claim model-weight training or native ChatGPT UI command registration. It creates the durable ZORR chat/bootstrap command contract and executable resolver used by ZORR execution surfaces that invoke repository bootstrap.
