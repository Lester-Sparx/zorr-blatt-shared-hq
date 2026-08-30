# ZORR STUDIO MATHEMATICS

STATUS = OWNER-DIRECTED / RESEARCH
TRACKER = #222
BRANCH = research/zorr-studio-mathematics-r01
BASE_MAIN_AT_START = b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1
MAIN_MUTATION = NO
MERGE = NO unless OWNER explicitly authorizes a merge gate
CANON_LOCK = NO

## SHARED VISIBILITY / RESTORE ENTRYPOINT

This README is the **first visibility index for all future ZORR mathematics chats/agents** after the mandatory boot law.

Required restore sequence for mathematics work:

```text
CURRENT MAIN
-> ZORR_EXECUTION_CONSTITUTION.md
-> AGENTS.md
-> TRACKER #222 + latest comments
-> fresh-read exact HEAD of research/zorr-studio-mathematics-r01
-> THIS README
-> relevant master/research document + code
```

Do not restore mathematics from chat memory when GitHub contains a fresher result.

### Current high-priority perspective path

For perspective / camera / location / object-placement work, read in this order:

1. `MATHEMATICAL_WORLD_PERSPECTIVE_LEARNING_R01.md` — pixel-first learning, free-space separation, first real-frame homography/Jacobian lessons and truth boundaries.
2. `PERSPECTIVE_GEOMETRY_MASTER_R01.md` — projective-space master: homogeneous points/ideal VPs, camera matrix, vanishing geometry, homography, Jacobians, metric tensor, uncertainty, multi-plane direction, character projection and stylized-perspective residuals.
3. `code/zorr_perspective_master_r01.py` — executable research kernel; use mature OpenCV estimators instead of inventing duplicate RANSAC/PnP/calibration infrastructure.

Perspective research rule:

```text
PIXEL EVIDENCE
-> PROJECTIVE GEOMETRY
-> CAMERA / PLANE MODEL
-> WORLD-SPACE CONSTRAINTS
-> REPROJECT
-> NUMERICAL ERROR
-> STYLE RESIDUAL IF INTENTIONAL
-> RECORD
```

`PHYSICAL BASE != ART DIRECTION`.
A deliberate anime perspective break should be represented as an explicit, measurable residual from the physical/projective base rather than being confused with an accidental geometry error.

### Shared visibility contract

OWNER directive: mathematics learning must be visible and reusable by later chats.

Therefore every significant new mathematics slice should, where applicable:

```text
1. persist the research document/code on this branch;
2. update this README when the restore map or priority edge changes;
3. record the exact branch HEAD + file(s) + PASS/NOT-PROVEN boundaries in tracker #222;
4. never rely on chat-only terminal knowledge;
5. never mutate main, merge, or canon-lock unless separately authorized.
```

This visibility index is a discovery/restore map, **not a second source of truth**. Exact files, exact branch HEAD, tracker evidence and current `main` authority win over this summary if they ever disagree.

## Mission

DUNCAN PRIME maintains this branch as the mathematics research line for ZORR BLATT.

The purpose is not to accumulate mathematics as theory. The purpose is to measure where mathematics materially improves studio quality, consistency, directing, speed, throughput, reliability, cost efficiency and verification.

Primary question:

> Where can a mathematical model replace repeated guesswork, expose drift earlier, or allocate scarce studio resources better without taking artistic judgement away from directing?

## Operating law

`DEFINE -> MEASURE -> CALCULATE -> APPLY -> VERIFY -> RECORD`

Evidence labels:

- `STANDARD` = official technical/industry standard or primary specification.
- `SOURCE-DERIVED` = supported by current ZORR/DUNCAN durable source.
- `MEASURED` = measured on approved/current ZORR evidence with reproducible method.
- `DERIVED` = direct calculation from stated inputs.
- `PROJECT` = bounded ZORR operating convention, not an industry law.
- `UNKNOWN` = not yet supported; must not be invented.

## Research domains

### Image / shot mathematics
- canonical 16:9 pixel coordinate system;
- scale, transforms, sampling and resampling;
- character geometry, landmarks and silhouette;
- line width/density/noise;
- color science, palette topology and perceptual color QC;
- texture frequency, anisotropy, aliasing and temporal stability;
- camera projection, FOV, lens equivalence and framing;
- motion trajectories, timing, spacing, kinematics and impact.

### Studio-system mathematics
- dependency graphs and change-impact radius;
- critical-path and constrained scheduling;
- queues, WIP, cycle time, throughput and bottlenecks;
- shot/resource optimization;
- GPU/render/generation cost per approved output;
- retry/rework economics;
- false-pass / false-fail statistics and QC calibration;
- reliability, SLI/SLO and error-budget reasoning;
- uncertainty and Monte Carlo deadline/cost forecasting;
- information gain of references, tests and research;
- artist/tool/task allocation as a constrained optimization problem.

## Core studio objective

A useful top-level research objective is:

```math
StudioEfficiency = ApprovedNarrativeValue / (Time + Money + Compute + Rework)
```

This is a research abstraction, not a locked scalar KPI. It exists to force explicit tradeoffs. `ApprovedNarrativeValue`, cost terms and weights remain `UNKNOWN` until operational definitions are measured and validated.

A candidate optimization can be expressed as:

```math
x^* = argmax_x ExpectedApprovedValue(x)
```

subject to:

```text
QUALITY_GATES = satisfied
IDENTITY/STYLE_DRIFT = within measured tolerances
RESOURCE_CAPACITY = respected
DEPENDENCIES = respected
DEADLINE_RISK = declared
MAIN/CANON AUTHORITY = unchanged
```

## Base research program

1. `PIXEL_MATH` — frame geometry, scale, coordinates, transfer and QC units.
2. `COLOR_TEXTURE_MATH` — perceptual color, semantic palette, frequency-domain texture and sampling.
3. `PRODUCTION_GRAPH_MATH` — dependencies, critical path, impact radius.
4. `FLOW_MATH` — WIP, throughput, queues, bottlenecks and rework loops.
5. `QUALITY_STATISTICS` — measurement uncertainty, false pass/fail, threshold calibration.
6. `COST_COMPUTE_MATH` — cost per approved asset/shot/frame/minute and compute efficiency.
7. `RISK_FORECASTING` — probability distributions and Monte Carlo for dates/costs.
8. `INFORMATION_VALUE` — which study/reference/test removes the most uncertainty per unit cost.
9. `RESOURCE_OPTIMIZATION` — allocation of artists, review attention, render capacity and hero-shot budget.
10. `PERSPECTIVE_MASTER` — homogeneous projective geometry, camera calibration, multi-plane reconstruction, local perspective tensors, world-space placement, reprojection QC and controlled stylized-perspective residuals.

## PASS discipline

A research slice may be called `PASS` only when:

- formulas are dimensionally and numerically checked;
- external claims use fresh primary/official evidence when material;
- project-specific thresholds are measured, not invented;
- limitations and assumptions are explicit;
- reproducible verification exists where practical;
- no research result is silently promoted to canon or production authority.

Research `PASS` means the mathematical/research artifact passed its declared checks. It does **not** automatically mean a production threshold or studio policy is approved.

## Repository law

This branch is intentionally isolated from `main`.

- no silent merge;
- no canon mutation;
- no production-path replacement;
- no second scheduler/database/scoring framework just to host research;
- prefer existing ZORR code, standard/native mechanisms and mature OSS before custom glue;
- bounded measurement helpers are allowed only when they prove a concrete research need.

Tracker: #222.
