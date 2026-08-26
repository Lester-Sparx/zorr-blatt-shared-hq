# ZORR BLATT — Accelerated Delivery Model R01

Status: **DESIGN SPEC CANDIDATE / GOVERNANCE + DELIVERY MODEL ONLY / NO IMPLEMENTATION AUTHORIZATION**

Shared HQ base binding: `ebe249122e4bb8f361f6efba97b511575d72b309`

This specification records the approved **Controlled Parallel Lanes** delivery model for ZORR BLATT. Its purpose is to shorten time to visible, testable production progress without weakening the accepted P1–P6 authority graph, role separation, evidence requirements, checkpoint laws, or protected gates.

This document changes **scheduling, feedback cadence, proof strategy and routing discipline**. It does **not** itself:

```text
merge Checkpoint Phase A
publish Checkpoint Phase B CURRENT
start or complete P1 Runtime Bootstrap
start P1 Implementation
start V0 Visual Sandbox
start Studio-S probes
assign SALVADOR work
adopt external dependencies
mutate hq/state/**
create OWNER LOCK
activate production
unlock G2
unlock Voice-to-Shot
```

Every such action remains separately governed.

---

## 1. Executive decision — Controlled Parallel Lanes

ZORR BLATT will no longer default to a fully linear engineering schedule in which all invisible infrastructure must be completed before any safe visual feedback appears.

The accepted delivery model is:

```text
CONTROLLED PARALLEL LANES
```

The governing structure is:

```text
                         ZORR BLATT SHARED HQ
                  CONTROL / AUTHORITY / EVIDENCE
                    CHECKPOINT / HANDOFF / SIGNAL
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
  CORE ENGINEERING       VISUAL TRUTH PREP      STUDIO-S REUSE
      P1 → P2 → ...       SALVADOR-SCOPED        probes/adapters
          │                     │                     │
          └──────────────┬──────┴────────────┬────────┘
                         │                   │
                         ▼                   ▼
                  V0 VISUAL SANDBOX      SPARX DASHBOARD
                    NON_CANONICAL          PROJECTION
                         │
                         ▼
                 EARLY VERTICAL SLICE
                    PROOF-ONLY
```

Hard law:

```text
PARALLEL SCHEDULING DOES NOT COLLAPSE GOVERNANCE GATES.
```

Parallel lanes may reduce waiting time. They may not transfer authority, skip evidence, auto-accept a candidate, or silently authorize another lane.

---

## 2. Existing authority graph remains unchanged

This model does not alter the accepted production truth direction:

```text
REFERENCE EVIDENCE
→ CHARACTER_DNA
→ CHARACTER-SPECIFIC REST_RIG + SURFACE CONTRACT
→ BODY COMPILER
→ BODY_TRUTH
→ SPACE_TRUTH + MOTION DNA
→ MOTION_TRUTH
→ ACTION_TRUTH
→ SHOT_INTENT
→ CAMERA_TRUTH
→ OPERATOR PERFORMANCE
→ FRAME COMPOSITION
→ VIEW PRESENTATION / GRANI
→ PERCEIVED FRAME
```

Existing laws remain binding:

```text
AUTHORITY FLOWS DOWNSTREAM.
DERIVED DATA NEVER SILENTLY WRITES UPSTREAM.

BUILD AUTHORITY
≠ QC AUTHORITY
≠ ARCHITECTURE AUTHORITY
≠ PRODUCTION ACTIVATION AUTHORITY.

NO STAGE AUTHORIZES THE NEXT GOVERNANCE STAGE IMPLICITLY.
```

Acceleration is therefore defined as:

```text
LESS IDLE WAITING
+ EARLIER SAFE FEEDBACK
+ MORE REUSE
+ FASTER ROUTING

NOT

LESS GOVERNANCE
+ WEAKER TRUTH BOUNDARIES
+ IMPERSONATED ACTORS
+ AUTOMATIC APPROVAL
```

---

## 3. Governing delivery laws

### 3.1 Earliest Visible Proof law

Every major engineering phase must expose the earliest safe human-inspectable result that can reveal wrong direction without pretending that the result is canonical truth.

Hard law:

```text
EVERY MAJOR ENGINEERING PHASE
MUST PRODUCE THE EARLIEST SAFE VISIBLE PROOF.
```

For a phase whose natural output is spatial/visual, the visible proof should become an actual geometry/frame/image as early as safely possible. For a foundation-only phase such as P1, this law **must not create renderer or presentation scope**: its earliest visible proof may instead be a minimal human-inspectable deterministic contract/hash/evidence result produced by the existing phase scope.

Therefore:

```text
VISIBLE PROOF MUST REVEAL THE PHASE'S REAL OUTPUT.
VISIBLE PROOF MUST NOT INVENT A NEW SUBSYSTEM JUST TO BE VISUAL.
```

A visible proof must be explicitly classified as one of:

```text
CANONICAL OUTPUT
DERIVED OUTPUT
NON_CANONICAL_PREVIEW
DISPOSABLE_PROOF
```

unless the governing phase contract already provides an equivalent authority classification.

Hard boundary:

```text
VISIBLE ≠ APPROVED
VISIBLE ≠ CANONICAL
VISIBLE ≠ PHASE COMPLETE
```

The purpose is feedback latency reduction, not truth promotion.

### 3.2 REUSE-FIRST law

The accepted engineering law remains:

```text
REUSE OPEN SOURCE WHEN IT IS FIT-FOR-PURPOSE.
DO NOT REBUILD GENERIC WORK WITHOUT A DOCUMENTED GAP.
```

Before generic implementation:

```text
SEARCH EXISTING PRODUCTION-TESTED OPEN SOURCE
→ VERIFY FIT / LICENSE / MAINTENANCE / BOUNDARY
→ ADOPT or ADAPT
→ PROBE if uncertain
→ CUSTOM BUILD only when a documented real gap remains
```

Acceleration therefore prefers integration over reinvention.

### 3.3 Kill-Criterion law

Every spike, sandbox, disposable proof or adoption probe must define stop conditions before implementation begins.

Required pre-probe fields:

```text
QUESTION
PASS_CRITERIA
KILL_CRITERIA
SCOPE_BOX
TIME_OR_WORK_BOX
REUSE_ALLOWED
PROMOTION_ALLOWED
DISCARD_REQUIRED
OUTPUT_EVIDENCE
```

Hard law:

```text
KILL CRITERION REACHED
→ STOP THE PROOF
→ RECORD RESULT
→ DO NOT POLISH THE DEAD END
```

The scope/time box is a planning boundary, not a substitute for correctness or a promise of wall-clock completion.

---

## 4. Lane A — Project Memory / Routing Foundation

The first acceleration dependency is project-memory closure because parallel work is unsafe if every new session depends on chat memory.

Target sequence:

```text
CHECKPOINT PHASE A
→ stable Project Index / Roadmap / Agent Roles
→ exact Phase A merge M1

CHECKPOINT PHASE B
→ first CURRENT.json + CURRENT.md
→ stateBasisCommit = exact M1
→ previousCheckpointId = null
→ publication commit M2 derived from Git
```

Core law remains:

```text
NO CHAT IS PROJECT MEMORY.
SHARED HQ CHECKPOINT IS PROJECT MEMORY.
```

Phase B creates the minimum reliable substrate for:

```text
role-aware RESUME
automated work routing
SPARX dashboard projection
persistent SIGNAL_2 / SIGNAL_3 state
actor handoff continuity
```

No acceleration feature may invent current state from chat to compensate for a missing or stale checkpoint.

---

## 5. Automated handoff routing

The target routing chain is:

```text
LESTER
  candidate + artifact + evidence
        ↓
DUNCAN
  independent QC queue
        ↓
DJANGO
  architecture review queue when QC_PASS exists
        ↓
NEXT LEGAL TRANSITION
```

The user/SPARX should not be required to manually copy status text between agents when Shared HQ already contains sufficient exact bindings.

### 5.1 Routing is not verdict creation

Hard laws:

```text
AUTO ROUTING ≠ AUTO QC_PASS
AUTO ROUTING ≠ AUTO ACCEPTED
AUTO ROUTING ≠ AUTO RUNTIME_APPROVED
AUTO ROUTING ≠ OWNER DECISION
```

An orchestrator may:

```text
read CURRENT
read relevant handoff/evidence
identify next authorized actor
prepare a task/resume context
surface blockers/signals
record routing metadata where separately authorized
```

An orchestrator may not:

```text
forge an actor identity
submit a role-specific verdict as another actor
invent missing evidence
clear owner action without verification
activate production
create OWNER LOCK
```

### 5.2 Authenticated identity remains mandatory

```text
ROLE CONTEXT ≠ AUTHENTICATED ACTOR IDENTITY
```

If a transition requires `Django-Sparx-ZB`, `Sparx-Owner-ZB`, or another exact actor identity and that authenticated actor is unavailable:

```text
ROUTE / WAIT / SIGNAL
```

not:

```text
IMPERSONATE / SUBSTITUTE / AUTO-APPROVE
```

### 5.3 User involvement threshold

SPARX becomes a required participant only when a real manual or owner action is necessary, not as a routine courier.

When direct SPARX action is genuinely required and tools cannot perform it, render exactly:

```text
🚨 SPARX — ОТ ТЕБЯ НУЖНО ДЕЙСТВИЕ!!!
```

A `SIGNAL_3` manual action still requires gate-holder verification before CLEAR under Signal Protocol R01.

---

## 6. Lane B — Core Engineering remains narrow

### 6.1 P1 remains deliberately small

Acceleration does not expand P1.

P1 Runtime Contract Foundation remains limited to the accepted contract work:

```text
versioned schemas
canonical serialization
SHA-256 hashing
authority/writeback policy
UNRESOLVED safety
source bindings
provenance
stale derivation behavior
dependency direction
negative tests
determinism tests
immutable evidence
```

Forbidden P1 scope expansion includes:

```text
body renderer
full Character DNA production model
full REST_RIG implementation
motion solver
camera solver
Babylon production runtime
Grani effects
studio operations platform
V0 sandbox code inside production runtime
```

Hard acceleration law:

```text
TINY P1 FINISHES FASTER THAN EXPANDED P1.
DO NOT TURN P1 INTO THE WHOLE ENGINE.
```

### 6.2 P1 Runtime Bootstrap remains distinct

```text
P1 RUNTIME BOOTSTRAP START
≠ P1 IMPLEMENTATION START
```

Bootstrap creates only the minimal Rust-first execution-plane foundation allowed by its accepted design/spec.

P1 implementation still requires its own separate explicit transition.

---

## 7. P2 becomes visual-first without weakening Body Truth

The first meaningful P2 milestone should minimize time from authority input to a visible body representation.

Target milestone:

```text
CHARACTER MEASUREMENTS / APPROVED INPUT
→ ZB BODY SOLVE
→ WHITE PROXY
→ VISIBLE FRAME
```

Name:

```text
P2 WHITE PROXY VISUAL MILESTONE
```

The purpose is early anthropometric/shape feedback.

### 7.1 White proxy authority boundary

The proxy is a derived visualization of exact bound inputs and solver output. The render/frame is not itself Body Truth authority.

```text
CHARACTER_DNA / BODY INPUT AUTHORITY
→ SOLVER
→ DERIVED PROXY GEOMETRY
→ VISUALIZATION
```

Forbidden reverse promotion:

```text
“looks right” render
✗→ CHARACTER_DNA mutation

white proxy mesh
✗→ unreviewed REST_RIG authority

artist correction in downstream viewer
✗→ silent Body Truth rewrite
```

Corrections discovered visually must return through the appropriate authored/authority workflow, not by downstream writeback.

### 7.2 P2 success is larger than the first visual

The white proxy milestone is an early phase milestone, not P2 completion.

```text
WHITE PROXY VISIBLE
≠ P2 COMPLETE
≠ P2 QC_PASS
≠ P2 ARCHITECTURE ACCEPTED
```

P2 final completion requirements remain separately designed and authorized.

---

## 8. Lane C — Visual Truth Preparation

Visual/canon preparation should not wait idly for engineering phases when it can proceed independently inside approved visual rules.

Target SALVADOR-scoped preparation may include, when separately assigned:

```text
approved character reference inventory
body reference evidence
head / face / hair reference evidence
costume evidence
weapon / carry-side evidence
silhouette-critical features
identity/canon constraints
exact source bindings
known unresolved visual evidence
```

The output is **reference/canon evidence preparation**, not automatic engineering authority.

Hard boundary:

```text
SALVADOR VISUAL AUTHORITY
≠ CHARACTER_DNA ENGINEERING AUTHORITY
≠ REST_RIG AUTHORITY
≠ QC AUTHORITY
≠ DJANGO ARCHITECTURE AUTHORITY
```

Engineering may consume exact approved visual evidence through separately defined adapters/contracts.

Visual preparation must preserve the project's locked canon/reference laws and must not invent missing design details.

This specification does not itself assign a SALVADOR task. A concrete task/handoff must be separately created under the role system.

---

## 9. Lane D — V0 Early Babylon Visual Sandbox

The approved early Babylon harness is explicitly disposable.

Canonical classification:

```text
V0 VISUAL SANDBOX
= DISPOSABLE_PROOF
= NON_CANONICAL
= NO DIRECT CODE PROMOTION TO P5
```

### 9.1 Purpose

V0 exists to answer visual/integration questions early:

```text
Can a simple proxy be displayed reliably?
Can simple transforms/motion be observed?
Can a simple camera frame the proxy?
Can the browser/runtime surface produce a useful frame quickly?
Can obvious scale/orientation/handedness/integration errors be seen early?
```

It is not a substitute for P2/P3/P4/P5.

### 9.2 Minimum V0 path

```text
WHITE / SIMPLE PROXY
→ SIMPLE TEST TRANSFORM OR MOTION
→ SIMPLE TEST CAMERA
→ BABYLON SANDBOX
→ FRAME / SCREENSHOT / DIAGNOSTIC
```

Inputs may be synthetic or explicitly noncanonical test data as defined by the V0 probe spec.

### 9.3 Forbidden truth claims

```text
V0 BODY ≠ BODY_TRUTH
V0 MOTION ≠ MOTION_TRUTH
V0 ACTION ≠ ACTION_TRUTH
V0 CAMERA ≠ CAMERA_TRUTH
V0 FRAME ≠ PRODUCTION PRESENTATION APPROVAL
```

### 9.4 No direct code promotion

Hard law:

```text
NO DIRECT SOURCE-CODE PROMOTION V0 → P5.
```

Allowed promotion from V0 is limited to reviewed knowledge artifacts such as:

```text
measured feasibility result
integration lesson
failure mode
API observation
test vector
contract requirement
performance measurement
validated boundary decision
```

Production P5 implementation must be created/adapted under the P5 architecture and dependency/provenance rules rather than copying V0 proof code by default.

### 9.5 Kill criteria required

Before V0 implementation, its probe spec must define concrete kill conditions, including at least:

```text
failure to render the minimum proxy path under the selected pinned toolchain
architecture contamination requiring upstream truth writeback
unexpected dependency/license boundary that makes the chosen topology unsuitable
scope growth beyond the agreed disposable visual question
```

Exact tool/version pins belong to the future V0 probe, not this delivery-model spec.

---

## 10. Early Vertical Slice

The project should prove one narrow path across multiple conceptual stages earlier than final production maturity.

Target proof:

```text
CHARACTER MEASUREMENTS
→ BODY PROXY
→ SIMPLE MOTION
→ SIMPLE CAMERA
→ BABYLON
→ FRAME
```

This is called:

```text
EARLY VERTICAL SLICE
```

### 10.1 Vertical slice is proof-only

The slice tests connectivity, boundary assumptions and feedback latency.

It does not imply maturity of any phase:

```text
VERTICAL SLICE PASS
≠ P2 COMPLETE
≠ P3 COMPLETE
≠ P4 COMPLETE
≠ P5 APPROVED
≠ PRODUCTION ACTIVATED
```

### 10.2 Authority tagging

Every stage in the vertical slice must carry explicit provenance/classification. If a phase has not yet produced canonical production truth, the slice must mark that portion as test/noncanonical rather than silently pretending it is authoritative.

Example pattern:

```text
MEASUREMENTS          = exact approved/test binding
BODY PROXY            = derived or noncanonical according to source maturity
SIMPLE MOTION         = synthetic/noncanonical unless backed by accepted Motion Truth
SIMPLE CAMERA         = synthetic/noncanonical unless backed by accepted Camera Truth
FRAME                 = proof output
```

### 10.3 No back-promotion

A visually successful slice cannot be used to back-promote downstream guesses into upstream truth.

```text
FRAME QUALITY
✗→ BODY AUTHORITY
✗→ MOTION AUTHORITY
✗→ ACTION AUTHORITY
✗→ CAMERA AUTHORITY
```

---

## 11. Lane E — Studio-S open-source acceleration

The accepted Open-Source Studio Acceleration R01 study remains the primary reuse guide.

Candidate classes include:

```text
ADOPT
ADAPT
PROBE
WATCH
DEFER
REJECT-AS-BACKBONE
```

Target generic systems may include separately gated probes/adoptions for:

```text
Kitsu / Zou
Blender Studio workflow concepts
Blender Kitsu / Shot Builder
Blender Asset Pipeline
Git LFS / SVN
Flamenco
OpenTimelineIO
OpenColorIO / OpenImageIO
glTF Transform
Khronos glTF Validator
FreeMoCap / MMPose evidence sources
other mature open-source tooling when justified
```

Hard separation:

```text
STUDIO-S* DOES NOT AUTHORIZE P*.
P* DOES NOT SILENTLY AUTHORIZE STUDIO-S*.
```

External tools remain operations, authoring, evidence, interchange, validation or presentation infrastructure according to their assigned boundary. They do not become ZB truth authority merely by being adopted.

---

## 12. SPARX Dashboard

The user-facing project dashboard is a **projection**, not a second state database.

Target human view:

```text
NOW
DONE
BLOCKED
NEXT
OWNER REQUIRED
ETA TO NEXT VISUAL
```

### 12.1 Source of truth

Dashboard data must derive from canonical project-memory/evidence sources such as:

```text
CURRENT.json
relevant handoffs
signal state
exact evidence/review bindings
stable Roadmap / Project Index where appropriate
```

Hard law:

```text
DASHBOARD ≠ SOURCE OF TRUTH.
```

No manual dashboard field may override canonical CURRENT/handoff/evidence state.

### 12.2 Field semantics

`NOW`
: current coarse phase and active legal work from checkpoint state.

`DONE`
: latest materially completed/accepted milestones with exact bindings where relevant.

`BLOCKED`
: active blocker summary derived from checkpoint/signal state.

`NEXT`
: next legal transitions, not wish-list tasks.

`OWNER REQUIRED`
: explicit owner/manual action requirement; must distinguish ordinary SPARX manual action from authenticated `Sparx-Owner-ZB` action.

`ETA TO NEXT VISUAL`
: planning projection only. It must never be treated as a governance deadline, canonical project fact or guaranteed completion time. If evidence is insufficient, display `UNRESOLVED` rather than invent precision.

### 12.3 Dashboard does not create transitions

```text
DASHBOARD DISPLAY
✗→ QC_PASS
✗→ ACCEPTED
✗→ ACTIVATED
✗→ OWNER LOCK
```

---

## 13. Parallel-lane concurrency rules

Parallel work is allowed only when lanes do not require unauthorized assumptions from each other.

### 13.1 Allowed parallelism

Examples of potentially safe parallelism after relevant separate gates:

```text
P1 contract work
|| visual reference preparation
|| V0 synthetic/noncanonical sandbox probe
|| Studio-S0 external tooling probes
```

provided none claims unfinished P1/P2/P3/P4 data as canonical production truth.

### 13.2 Dependency rule

If one lane depends on an output from another lane that is not yet accepted:

```text
USE TEST/NONCANONICAL INPUT
OR WAIT
```

Never:

```text
ASSUME FUTURE CONTRACT
PROMOTE DRAFT TO TRUTH
SILENTLY FREEZE AN UNREVIEWED INTERFACE
```

### 13.3 Merge conflict is not authority resolution

Technical branch mergeability does not resolve semantic authority conflicts. If two parallel lanes define incompatible assumptions about a canonical interface, the appropriate architecture/contract gate resolves the conflict before production promotion.

---

## 14. Scheduling sequence

The accepted accelerated ordering is:

```text
1. MERGE CHECKPOINT PHASE A

2. CHECKPOINT PHASE B
   → publish first CURRENT.json / CURRENT.md

3. ENABLE RECOVERABLE RESUME / DASHBOARD FOUNDATION
   → based on checkpoint/handoff/signal truth

4. RESUME TINY P1 RUNTIME BOOTSTRAP
   → under existing bootstrap authorization only

5. SEPARATE P1 IMPLEMENTATION GATE
   → no implicit start

6. AFTER THAT GATE, SAFE PARALLEL WORK MAY RUN UNDER ITS OWN AUTHORIZATIONS:
   - P1 implementation
   - SALVADOR visual truth/reference preparation
   - V0 disposable visual sandbox probe
   - Studio-S0 open-source operations probes

7. P2
   → early WHITE PROXY VISUAL MILESTONE

8. EARLY VERTICAL SLICE
   → proof-only path to Babylon frame

9. P3 / P4 / P5 / P6
   → continue under existing independent design/build/evidence/QC/architecture gates
```

This sequence does not authorize items 1–9 merely by listing them.

---

## 15. Project-memory implications

Once Checkpoint Phase B exists, the accelerated model should be represented in project memory through stable docs and current state rather than chat.

Potential checkpoint-visible facts include, when they become true:

```text
active lane assignments
active blockers
current legal transitions
V0 probe status
Studio-S probe status
next visual milestone
owner action requirements
```

Stable scheduling laws belong in durable docs/specs; transient task state belongs in CURRENT/handoffs.

Do not overload CURRENT with historical event logs. Archives/handoffs/Git preserve history.

---

## 16. Signal integration

Signal Protocol R01 remains unchanged.

Useful mappings include:

```text
SIGNAL_1
→ major material milestone such as accepted visible proof/checkpoint publication

SIGNAL_2
→ material blocker, failed probe, changes required, checkpoint conflict/stale state

SIGNAL_3
→ progress cannot continue without concrete SPARX/manual/owner action
```

A failed V0 probe may produce `SIGNAL_2` if it creates a material blocker, but a normal expected negative experiment does not need an alert unless project state is materially affected.

Signal spam remains forbidden.

---

## 17. Evidence discipline for fast work

Speed does not excuse weak evidence.

Every reusable result must bind enough provenance to answer:

```text
WHAT RAN?
ON WHICH EXACT SOURCE/REVISION?
WITH WHICH INPUTS?
WHAT OUTPUT WAS PRODUCED?
WHAT AUTHORITY CLASS DID IT HAVE?
WHAT WAS NOT CHANGED?
WHAT FAILED / WHAT PASSED?
CAN THE RESULT BE REPRODUCED?
```

Disposable proofs may have lighter artifacts than production candidates, but they must still preserve enough exact evidence to prevent repeated rediscovery.

---

## 18. Promotion discipline

The model distinguishes **knowledge promotion** from **code/data authority promotion**.

### 18.1 Knowledge may transfer

A disposable proof may inform later production work through:

```text
lessons learned
validated assumptions
failed assumptions
contract requirements
measured limits
test vectors
integration boundaries
pin/license observations
```

### 18.2 Production assets/code require their own gate

A proof artifact does not become production code/data simply because the experiment succeeded.

```text
PROOF PASS
≠ PRODUCTION PROMOTION
```

Where direct reuse is later considered for any proof other than V0, the governing adoption/implementation gate must explicitly permit it and verify provenance/license/tests.

For V0 specifically:

```text
DIRECT CODE PROMOTION IS PROHIBITED.
```

---

## 19. Role responsibilities under accelerated delivery

### LESTER

May implement authorized engineering/proof tasks, produce candidates/artifacts/evidence and hand them off.

Acceleration expectation:

```text
small testable increments
early proof output
no generic rewrite without documented gap
clear kill criteria for spikes
```

LESTER still cannot self-create QC/architecture/OWNER verdicts.

### DUNCAN

May independently QC exact candidates/evidence, coordinate legal next work, maintain delivery visibility and validate that parallel lanes remain inside boundaries.

Acceleration expectation:

```text
reduce idle routing delay
surface blockers early
protect authority boundaries
verify visible proof classification
```

DUNCAN cannot impersonate DJANGO or OWNER.

### DJANGO

Reviews architecture/implementation boundaries where required, including whether accelerated integration preserves accepted contracts.

Acceleration expectation:

```text
reject unnecessary framework invention
prefer narrow replaceable adapters
prevent proof code from silently becoming authority
```

DJANGO cannot replace independent QC or OWNER.

### SALVADOR

May prepare assigned visual/canon evidence/workflow outputs in parallel under visual/canon authority.

SALVADOR cannot promote visual preparation into engineering governance authority.

### SPARX / OWNER

Receives concise dashboard/manual-action requests rather than acting as routine handoff courier.

Authenticated OWNER transitions still require `Sparx-Owner-ZB` where specified.

---

## 20. Failure modes

The accelerated model must stop or raise the appropriate blocker if any of these occur:

### 20.1 Parallel authority contamination

```text
V0 data silently treated as Body/Motion/Camera Truth
Studio-S external status treated as QC/architecture verdict
SALVADOR visual output silently promoted into engineering authority
```

Result:

```text
BLOCK / CHANGES_REQUIRED
```

### 20.2 Interface guessing

A lane requires an unaccepted upstream interface and starts inventing it as if canonical.

Result:

```text
USE EXPLICIT TEST INTERFACE
OR WAIT FOR CONTRACT
```

### 20.3 Sandbox growth

V0 begins accumulating production responsibilities or long-lived implementation dependencies.

Result:

```text
KILL / ARCHIVE LESSONS / DO NOT PROMOTE CODE
```

### 20.4 Dashboard divergence

Dashboard disagrees with CURRENT/handoff/evidence.

Result:

```text
DASHBOARD IS WRONG
→ REGENERATE FROM CANONICAL SOURCES
```

Never mutate canonical state to match the dashboard.

### 20.5 Routing identity gap

Next actor identity is unavailable.

Result:

```text
WAIT / SIGNAL IF MATERIAL
```

Never impersonate.

---

## 21. Testing expectations for future implementation

This spec does not implement the model, but future implementation plans should include tests for at least:

```text
checkpoint-derived dashboard projection
no dashboard writeback
role-aware handoff routing
no verdict creation by router
identity-mismatch rejection
V0 classification as NON_CANONICAL / DISPOSABLE
V0 direct-promotion rejection
vertical-slice authority labels
parallel-lane dependency checks
kill-criterion presence for probes
REUSE-FIRST documented-gap requirement for generic custom build proposals
```

Implementation plans should prefer deterministic machine-checkable rules where practical.

---

## 22. Non-goals

R01 does not define or authorize:

```text
full orchestrator implementation
specific automation/webhook provider
specific dashboard UI framework
V0 source code
V0 Babylon version pin
production Babylon adoption
P2 full Character DNA schema
P2 final body compiler implementation
P3 motion solver
P4 camera solver
P5 production runtime
P6 Grani implementation
Kitsu/Blender/Flamenco deployment
asset storage adoption
coordinate-system lock
OWNER LOCK
G2
Voice-to-Shot
production activation
```

Each receives its own future design/probe/adoption/implementation gate.

---

## 23. Acceptance criteria

The delivery model is acceptable only if it simultaneously satisfies all of the following:

1. preserves the existing P1–P6 authority graph;
2. preserves role separation and authenticated identity requirements;
3. closes project memory before depending on automation;
4. keeps P1 deliberately small and prevents visible-proof scope creep in foundation-only phases;
5. requires the earliest safe visible/human-inspectable proof from major engineering phases;
6. makes P2 white-proxy visualization an early milestone rather than phase completion;
7. permits SALVADOR visual/canon preparation in parallel only under separate assignment and existing authority;
8. classifies V0 Babylon sandbox as disposable/noncanonical;
9. prohibits direct V0 source-code promotion to P5;
10. enables an early proof-only vertical slice without false phase completion claims;
11. keeps Studio-S reuse/adoption independent from P1–P6 authorization;
12. requires kill criteria before spikes/probes;
13. reduces SPARX courier work through handoff routing without automatic verdicts;
14. makes SPARX Dashboard a projection from canonical project memory, never a source of truth;
15. preserves REUSE-FIRST and documented-gap requirements;
16. makes unresolved planning/ETA data explicit rather than invented;
17. keeps OWNER LOCK, G2, Voice-to-Shot and activation separately gated.

---

## 24. Governing summary

```text
MOVE FASTER BY RUNNING SAFE WORK IN PARALLEL.
DO NOT MOVE FASTER BY WEAKENING AUTHORITY.

PROJECT MEMORY FIRST.
TINY P1.
EARLY VISIBLE PROOF WITHOUT SCOPE CREEP.
P2 WHITE PROXY EARLY.
V0 BABYLON = DISPOSABLE / NON_CANONICAL.
NO DIRECT V0 CODE PROMOTION TO P5.

ROUTE HANDOFFS AUTOMATICALLY WHERE POSSIBLE.
DO NOT AUTOMATE VERDICTS.

SPARX DASHBOARD = PROJECTION, NOT AUTHORITY.

EVERY PROBE HAS A PASS CRITERION AND A KILL CRITERION.

REUSE GENERIC OPEN SOURCE WHEN FIT-FOR-PURPOSE.
CUSTOM GENERIC CODE REQUIRES A DOCUMENTED GAP.

VISIBLE ≠ APPROVED.
PROOF PASS ≠ PRODUCTION PROMOTION.

STUDIO-S* DOES NOT AUTHORIZE P*.
P* DOES NOT SILENTLY AUTHORIZE STUDIO-S*.

OWNER LOCK REMAINS SEPARATE.
G2 REMAINS NOT AUTHORIZED.
VOICE-TO-SHOT REMAINS NOT AUTHORIZED.
```
