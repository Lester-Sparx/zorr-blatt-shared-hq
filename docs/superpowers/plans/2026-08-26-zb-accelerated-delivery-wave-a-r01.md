# ZB Accelerated Delivery Wave A R01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close recoverable project memory first, integrate the approved Accelerated Delivery Model into the three Checkpoint Phase A stable documents, publish the first canonical CURRENT checkpoint, and then create the first SPARX Dashboard projection without starting P1/V0/P2/Studio-S implementation.

**Architecture:** Wave A is deliberately infrastructure-only. It preserves the existing P1–P6 authority graph and uses the already-open Checkpoint Phase A PR as the stable-doc integration vehicle, then creates Phase B from the exact Phase A merge commit. Dashboard creation follows Phase B as a separate projection step so the initial checkpoint PR remains exactly the approved two CURRENT files.

**Tech Stack:** Markdown + JSON in `Lester-Sparx/zorr-blatt-shared-hq`; GitHub branches/PRs; existing `hq-validate` workflow.

**Spec:** `docs/superpowers/specs/2026-08-26-zb-accelerated-delivery-model-r01.md`

**Related Specs:**
- `docs/superpowers/specs/2026-08-26-zb-checkpoint-system-r01.md`
- `docs/superpowers/specs/2026-08-26-zb-signal-protocol-r01.md`
- `docs/superpowers/specs/2026-08-26-zb-open-source-studio-acceleration-r01.md`
- `docs/ZB_PRODUCTION_INTEGRATION_ARCHITECTURE_R01.md`

## Global Constraints

- Preserve `NO CHAT IS PROJECT MEMORY`.
- Preserve Shared HQ as CONTROL / AUTHORITY / EVIDENCE plane and runtime as separate EXECUTION plane.
- Preserve `ROLE CONTEXT ≠ AUTHENTICATED ACTOR IDENTITY` and no impersonation.
- Preserve REUSE-FIRST: generic work defaults to ADOPT / ADAPT / PROBE; custom generic work requires a documented gap.
- Preserve `AUTO ROUTING ≠ AUTO QC_PASS ≠ AUTO ACCEPTED ≠ OWNER DECISION`.
- Preserve `P1 RUNTIME BOOTSTRAP START ≠ P1 IMPLEMENTATION START`.
- P1 remains PAUSED until checkpoint integration is complete; P1 IMPLEMENTATION remains NOT AUTHORIZED.
- V0 is design-only in this wave: `DISPOSABLE_PROOF / NON_CANONICAL / NO DIRECT SOURCE-CODE PROMOTION TO P5`.
- Do not start V0, Studio-S probes, SALVADOR assignments, P1 implementation, P2, G2, Voice-to-Shot, OWNER LOCK, or production activation in Wave A.
- Do not mutate `hq/state/**`.
- Every branch/PR must bind to exact SHAs and pass `hq-validate` before merge.
- Do not treat GitHub `merge_commit_sha` on an unmerged PR as proof of merge; require `merged=true` / returned merge result.

---

### Task 1: Integrate Accelerated Delivery Model into Checkpoint Phase A PR #27

**Files:**
- Modify on branch `docs/zb-checkpoint-phase-a-r01`: `docs/ZB_PROJECT_INDEX.md`
- Modify on branch `docs/zb-checkpoint-phase-a-r01`: `docs/ZB_MASTER_ROADMAP.md`
- Modify on branch `docs/zb-checkpoint-phase-a-r01`: `docs/ZB_AGENT_ROLES.md`

**Interfaces:**
- Consumes: accepted Accelerated Delivery Model R01 now on protected `main`.
- Produces: the same three stable Phase A documents, updated to point to the new canonical delivery-model spec without becoming CURRENT state.

- [ ] **Step 1: Update Project Index with the canonical delivery-model pointer**

Add a stable navigation entry for:

```text
docs/superpowers/specs/2026-08-26-zb-accelerated-delivery-model-r01.md
```

Describe it only as the canonical scheduling/feedback/routing model. Record these laws by reference, without duplicating the full spec:

```text
CONTROLLED PARALLEL LANES
EARLIEST SAFE VISIBLE PROOF
V0 = DISPOSABLE / NON_CANONICAL
DASHBOARD = PROJECTION, NOT SOURCE OF TRUTH
```

Do not add a Dashboard file path yet because the Dashboard file does not exist until Task 4.

- [ ] **Step 2: Update Master Roadmap with coarse accelerated-delivery direction**

Add a coarse section that states:

```text
Checkpoint Phase A
→ Checkpoint Phase B
→ resume tiny P1 Bootstrap
→ separate P1 Implementation gate

Parallel only after project-memory closure and separate authorization:
- Visual Truth Preparation
- V0 disposable visual sandbox
- Studio-S reuse/probes

P2 first visible milestone:
CHARACTER INPUT → BODY SOLVE → WHITE PROXY → VISIBLE FRAME
```

Also record:

```text
PARALLEL SCHEDULING DOES NOT COLLAPSE GOVERNANCE GATES.
VERTICAL SLICE PASS ≠ P2/P3/P4/P5 COMPLETE.
```

Roadmap must remain coarse; do not add per-commit/current alert details.

- [ ] **Step 3: Update Agent Roles with routing boundaries**

Add stable role rules:

```text
SPARX SHOULD NOT BE A ROUTINE COURIER BETWEEN AGENTS.
AUTO ROUTING MAY TRANSFER CONTEXT, NOT VERDICTS.
PARALLEL WORK DOES NOT TRANSFER AUTHORITY.
```

Preserve exact role boundaries for LESTER → DUNCAN → DJANGO → OWNER and the exact manual action alarm rule.

- [ ] **Step 4: Verify Phase A scope remains exactly three files**

Compare PR #27 head to current `main` after Accelerated Delivery spec merge.

Expected changed paths:

```text
docs/ZB_PROJECT_INDEX.md
docs/ZB_MASTER_ROADMAP.md
docs/ZB_AGENT_ROLES.md
```

Expected forbidden paths: none.

Scan all three files for:

```text
TODO
TBD
FIXME
PLACEHOLDER
```

Expected: zero unresolved markers.

- [ ] **Step 5: Re-run PR #27 CI on the new exact head**

Expected:

```text
hq-validate = success
PR mergeable = true
merged = false
```

- [ ] **Step 6: Merge PR #27 using its exact final head SHA**

Record returned merge SHA as:

```text
M1 = exact Checkpoint Phase A merge commit
```

Do not create Phase B until M1 is known.

---

### Task 2: Publish Checkpoint Phase B Initial CURRENT

**Files:**
- Create: `checkpoints/ZB_CHECKPOINT_CURRENT.json`
- Create: `checkpoints/ZB_CHECKPOINT_CURRENT.md`

**Interfaces:**
- Consumes: exact Phase A merge `M1`, Checkpoint R01 schema, Signal R01 extensions, current exact repository/evidence state.
- Produces: first recoverable canonical project state; `previousCheckpointId=null`.

- [ ] **Step 1: Create an isolated Phase B branch from exact M1**

Branch name:

```text
checkpoint/zb-initial-current-r01
```

Base must equal exact `M1`, not a branch-name assumption.

- [ ] **Step 2: Read exact current evidence before generating state**

Verify at minimum:

```text
Phase A merge M1 exists on main
Accelerated Delivery Model spec is merged
Signal Protocol spec is merged
Open-Source Studio Acceleration spec is merged
Production Integration Architecture R01 is merged
P1 Runtime Bootstrap target repo status
P1 Implementation authorization status
OWNER LOCK status
G2 status
Voice-to-Shot status
```

Do not reconstruct any unknown value from chat.

- [ ] **Step 3: Build canonical `ZB_CHECKPOINT_V1` JSON**

Required base shape:

```json
{
  "schemaId": "ZB_CHECKPOINT_V1",
  "schemaVersion": 1,
  "checkpointId": "2026-08-26-R01",
  "createdAt": "<exact UTC timestamp>",
  "createdBy": "Duncan-Sparx-ZB",
  "previousCheckpointId": null,
  "project": "ZORR BLATT",
  "sharedHq": {
    "repository": "Lester-Sparx/zorr-blatt-shared-hq",
    "stateBasisCommit": "<M1>"
  },
  "currentPhase": {
    "id": "P1_RUNTIME_BOOTSTRAP",
    "status": "PAUSED"
  },
  "globalStatus": {},
  "activeWork": {},
  "latestAcceptedDecisions": [],
  "openBlockers": [],
  "latestHandoffs": [],
  "nextTransitions": [],
  "ownerActionRequired": {
    "required": false,
    "action": null
  },
  "locks": {},
  "unresolved": [],
  "activeAlert": null,
  "checkpointReason": {
    "kind": "COMPLETE",
    "source": "CHECKPOINT_SYSTEM_PHASE_B_INITIAL_PUBLICATION",
    "signal": {
      "level": "SIGNAL_1",
      "code": "MILESTONE_CHECKPOINT_PUBLISHED"
    },
    "evidence": []
  }
}
```

Populate only exact verified facts. The initial CURRENT must explicitly capture at least these semantic states:

```text
integrationArchitecture = ACCEPTED
checkpointSystem = COMPLETE
signalProtocol = ACCEPTED
openSourceStudioAcceleration = ACCEPTED
acceleratedDeliveryModel = ACCEPTED
p1Bootstrap = PAUSED
p1Implementation = NOT_AUTHORIZED
p2BodyCompiler = NOT_AUTHORIZED
p3MotionAction = NOT_AUTHORIZED
p4Cinematography = NOT_AUTHORIZED
p5BabylonRuntime = NOT_AUTHORIZED
p6GraniPresentation = NOT_AUTHORIZED
g2 = NOT_AUTHORIZED
voiceToShot = NOT_AUTHORIZED
productionActivation = INACTIVE
ownerLock = INACTIVE
```

If the target runtime repository is still absent and current tooling cannot create it, represent that as an actionable blocker and synchronize Signal R01 invariants:

```text
openBlocker blocks P1_RUNTIME_BOOTSTRAP
ownerActionRequired.required = true
CURRENT.activeAlert.level = SIGNAL_3
CURRENT.activeAlert.class = OWNER_ACTION
CURRENT.activeAlert.code = OWNER_ACTION_REQUIRED
```

If exact evidence shows the repository exists before publication, do not create that blocker or alert.

- [ ] **Step 4: Generate `CURRENT.md` as a human projection of the JSON**

The Markdown must expose the same semantic state, including:

```text
Checkpoint ID
State basis commit
Current phase
Global status
Active work
Open blockers
Active alert
Next legal transitions
Owner action required
Locks
Unresolved
Checkpoint reason/evidence
```

JSON is canonical. Markdown must not add contradictory facts.

- [ ] **Step 5: Verify JSON/Markdown semantic equivalence**

Check every high-level status, blocker, alert, next transition and owner-action field in both representations.

Forbidden:

```text
JSON says PAUSED while MD says ACTIVE
JSON ownerActionRequired=true while MD says none
JSON activeAlert=SIGNAL_3 while MD omits the blocker
MD invents an ETA or task not in canonical sources
```

- [ ] **Step 6: Verify Phase B PR scope**

Expected diff from M1:

```text
2 files added
checkpoints/ZB_CHECKPOINT_CURRENT.json
checkpoints/ZB_CHECKPOINT_CURRENT.md
```

No archive is created because `previousCheckpointId=null`.

No handoff is required merely to publish the initial checkpoint unless a separate actor-transfer event is created.

- [ ] **Step 7: Open Phase B PR and run `hq-validate`**

Expected:

```text
hq-validate = success
mergeable = true
```

- [ ] **Step 8: Merge Phase B using the exact final head**

Record returned merge SHA as:

```text
M2 = checkpointPublicationCommit derived from Git history
```

Do not write `M2` back inside the checkpoint JSON; publication commit is derived from Git by Checkpoint R01 law.

---

### Task 3: Verify Recoverable Resume from Published CURRENT

**Files:**
- Read/verify only: `checkpoints/ZB_CHECKPOINT_CURRENT.json`
- Read/verify only: `docs/ZB_PROJECT_INDEX.md`
- Read/verify only: `docs/ZB_MASTER_ROADMAP.md`
- Read/verify only: `docs/ZB_AGENT_ROLES.md`

**Interfaces:**
- Consumes: Phase B publication on `main`.
- Produces: evidence that a fresh actor/session can restore project state without chat memory.

- [ ] **Step 1: Re-read CURRENT from protected main**

Verify:

```text
schemaId = ZB_CHECKPOINT_V1
previousCheckpointId = null
stateBasisCommit = M1
M1 is an ancestor of current main
CURRENT publication is M2 or later main ancestry
```

- [ ] **Step 2: Perform a DUNCAN resume dry-run**

Produce the standard resume fields from repository data only:

```text
role
checkpoint
phase
state basis
my task/status
latest handoff
blockers
active alert
next legal transition
owner action
```

Expected: no chat-memory dependency.

- [ ] **Step 3: Verify staleness/conflict rules**

Expected:

```text
stateBasisCommit ancestor of main = true
no uncheckpointed material transition after M2 = true at the moment of verification
```

If a material transition happened after M2, stop and publish a new checkpoint rather than pretending the initial CURRENT is current.

---

### Task 4: Create Initial SPARX Dashboard Projection

**Files:**
- Create: `docs/ZB_SPARX_DASHBOARD.md`
- Modify: `docs/ZB_PROJECT_INDEX.md`

**Interfaces:**
- Consumes: published canonical CURRENT on main plus stable Roadmap/Index/Agent Roles.
- Produces: human projection only; no authority/state mutation.

- [ ] **Step 1: Create dashboard branch from exact current main after Phase B**

The branch must start from a commit that already contains the published CURRENT.

- [ ] **Step 2: Create dashboard with exactly these primary fields**

```text
NOW
DONE
BLOCKED
NEXT
OWNER REQUIRED
ETA TO NEXT VISUAL
```

Derivation rules:

```text
NOW            ← CURRENT.currentPhase + activeWork
DONE           ← accepted/completed globalStatus + exact evidence bindings
BLOCKED        ← CURRENT.openBlockers + persistent activeAlert
NEXT           ← CURRENT.nextTransitions
OWNER REQUIRED ← CURRENT.ownerActionRequired + identity distinction
ETA TO NEXT VISUAL ← planning projection only; default UNRESOLVED if evidence is insufficient
```

Hard law in the file:

```text
DASHBOARD ≠ SOURCE OF TRUTH.
```

- [ ] **Step 3: Update Project Index only because a canonical dashboard path now exists**

Add:

```text
docs/ZB_SPARX_DASHBOARD.md
= user-facing projection of CURRENT/handoff/signal/evidence
```

Do not move current state into the index.

- [ ] **Step 4: Verify dashboard cannot override CURRENT**

The dashboard must contain no manual status that disagrees with CURRENT. If a value cannot be derived, write `UNRESOLVED`.

- [ ] **Step 5: Open PR and run `hq-validate`**

Expected diff:

```text
docs/ZB_SPARX_DASHBOARD.md added
docs/ZB_PROJECT_INDEX.md modified
```

After CI success and exact-head verification, merge.

---

### Task 5: Wave A Completion Gate

**Files:**
- Verify only.

**Interfaces:**
- Consumes: merged Tasks 1–4.
- Produces: a stable starting point for the next separately authorized acceleration plans.

- [ ] **Step 1: Verify project-memory closure**

Expected:

```text
Project Index exists
Master Roadmap exists
Agent Roles exists
CURRENT.json exists
CURRENT.md exists
SPARX Dashboard exists
resume from CURRENT succeeds
```

- [ ] **Step 2: Verify forbidden work is still not started**

Expected:

```text
P1 Implementation = NOT_AUTHORIZED
V0 implementation = NOT_STARTED / not authorized by this plan
Studio-S probes = not started by this plan
SALVADOR assignment = not created by this plan
P2 = NOT_AUTHORIZED
OWNER LOCK = absent/inactive
G2 = NOT_AUTHORIZED
Voice-to-Shot = NOT_AUTHORIZED
production activation = INACTIVE
hq/state unchanged
```

- [ ] **Step 3: Identify next legal work from CURRENT**

The expected technical path is to resume P1 Runtime Bootstrap under its existing gate after checkpoint closure. If the runtime repository is absent, the checkpoint/dashboard should surface the exact owner/manual action rather than routing around it.

V0, Studio-S0 and Visual Truth Preparation require their own narrow design/probe/assignment gates according to the Accelerated Delivery Model.

---

## Self-Review

- **Spec coverage:** Wave A implements project-memory closure, routing substrate and dashboard projection only. It intentionally leaves V0/P1 implementation/P2/Studio-S/Salvador work to later separate plans.
- **Checkpoint integrity:** Phase B uses exact M1 as `sharedHq.stateBasisCommit`, `previousCheckpointId=null`, and never self-records M2.
- **Signal integrity:** transient checkpoint publication uses `SIGNAL_1`; persistent runtime-repo blocker, if verified, uses synchronized `SIGNAL_3` + `ownerActionRequired=true`.
- **Scope integrity:** Phase A remains exactly three stable docs; Phase B remains exactly two CURRENT files; Dashboard is a separate PR.
- **Placeholder scan:** no TODO/TBD/FIXME/PLACEHOLDER implementation markers are intentionally left unresolved.
- **Authority integrity:** routing and dashboard are projections/coordination only; no actor gains QC/architecture/OWNER authority.

## Execution Selection

The user has already authorized autonomous inline continuation. Execute this plan with `superpowers:executing-plans`, preserving exact branch isolation and stopping only for a genuine governance/manual-action blocker.