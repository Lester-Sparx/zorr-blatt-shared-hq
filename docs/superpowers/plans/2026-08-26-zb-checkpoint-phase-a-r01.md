# ZB Checkpoint Phase A R01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the approved ZB Checkpoint / Project Ledger System R01 into three stable Shared HQ navigation/authority documents without creating any CURRENT checkpoint state yet.

**Architecture:** Phase A creates only stable project-memory infrastructure: a topology index, a coarse master roadmap, and a stable role/authority contract. Operational current state remains deferred to Phase B so the first `CURRENT.json/.md` can bind to the exact Phase A merge commit. Signal Protocol R01 and Open-Source Studio Acceleration R01 are referenced as accepted project laws/infrastructure, but Phase A does not adopt external dependencies or create operational alerts.

**Tech Stack:** Markdown in `Lester-Sparx/zorr-blatt-shared-hq`; GitHub branch/PR; existing `hq-validate` workflow.

**Specs:**
- `docs/superpowers/specs/2026-08-26-zb-checkpoint-system-r01.md`
- `docs/superpowers/specs/2026-08-26-zb-signal-protocol-r01.md`
- `docs/superpowers/specs/2026-08-26-zb-open-source-studio-acceleration-r01.md`
- `docs/ZB_PRODUCTION_INTEGRATION_ARCHITECTURE_R01.md`

## Global Constraints

- Phase A candidate changes exactly three stable docs: `docs/ZB_PROJECT_INDEX.md`, `docs/ZB_MASTER_ROADMAP.md`, `docs/ZB_AGENT_ROLES.md`.
- Do not create or modify `checkpoints/ZB_CHECKPOINT_CURRENT.json`, `checkpoints/ZB_CHECKPOINT_CURRENT.md`, checkpoint archives, or handoffs in Phase A.
- Do not modify `hq/state/**`, schemas, runtime repositories/code, production workflows, OWNER LOCK, G2, Voice-to-Shot, or production activation.
- Preserve Shared HQ as CONTROL / AUTHORITY / EVIDENCE plane and ZB Runtime as separate EXECUTION plane.
- Preserve role separation: LESTER build/evidence; DUNCAN QC; DJANGO architecture; OWNER activation/OWNER LOCK; SALVADOR visual/canon workflow only.
- Preserve `ROLE CONTEXT ≠ AUTHENTICATED ACTOR IDENTITY` and no impersonation.
- Preserve `NO CHAT IS PROJECT MEMORY`; Phase B CURRENT becomes recoverable project state after Phase A is merged.
- Preserve Signal Protocol semantics: `SIGNAL_1` transient; persistent `SIGNAL_2/3`; signal does not create governance verdicts.
- Preserve REUSE-FIRST: generic subsystems default to REUSE / ADAPT; custom generic development requires a documented gap.
- Roadmap status is informational/coarse and never itself authorizes the next stage.
- P1 Runtime Bootstrap remains PAUSED pending checkpoint integration; P1 IMPLEMENTATION remains NOT AUTHORIZED.

---

### Task 1: Create Project Index

**Files:**
- Create: `docs/ZB_PROJECT_INDEX.md`

**Interfaces:**
- Consumes: accepted architecture/checkpoint/signal/studio-acceleration docs already on `main`.
- Produces: stable map to canonical project documents and system locations; no operational current-state fields.

- [ ] **Step 1: Create the index with explicit semantic role**

The document must state:

```text
PROJECT INDEX = WHERE THINGS ARE
```

It must map, without duplicating full source contents:

```text
Shared HQ control/authority/evidence plane
ZB Runtime execution plane target
Production Integration Architecture R01
Checkpoint / Project Ledger System R01
Signal Protocol R01
Open-Source Studio Acceleration R01
Master Roadmap
Agent Roles
CURRENT checkpoint paths (future/Phase B until created)
checkpoint archive paths
handoff paths
proof provenance O0/B0/M0/C1/GRANI
P1 bootstrap design/spec
protected gates: OWNER LOCK, G2, Voice-to-Shot
visual/canon production guide pointers where currently available
```

The index must say that absence of a target file is explicit when Phase B has not created it; it must not fabricate links or state.

- [ ] **Step 2: Verify the index does not become a second source of truth**

Check that it points to canonical sources and does not restate detailed schemas, proof reports, packet definitions, or current operational status beyond stable topology.

- [ ] **Step 3: Commit through the Phase A branch**

Expected result: one new stable map file, no CURRENT/hq/state/runtime changes.

---

### Task 2: Create Master Roadmap

**Files:**
- Create: `docs/ZB_MASTER_ROADMAP.md`

**Interfaces:**
- Consumes: Integration Architecture rollout, Checkpoint R01, Signal R01, Studio Acceleration R01.
- Produces: coarse phase/path document; no authorization transitions.

- [ ] **Step 1: Define roadmap semantics**

The document must state:

```text
MASTER ROADMAP = WHERE THE PROJECT IS GOING
ROADMAP STATUS ≠ AUTHORIZATION
```

- [ ] **Step 2: Record the accepted coarse path**

At minimum:

```text
Checkpoint System Phase A — stable docs integration
Checkpoint System Phase B — initial CURRENT checkpoint publication
P1 Runtime Bootstrap — resume after checkpoint integration
P1 Runtime Contract Foundation — separate explicit implementation authorization
P2 Body Compiler
P3 Motion / Action
P4 Cinematography
P5 Babylon Runtime
P6 Grani Presentation
Studio-S operations track — separately authorized reuse/adoption/probes
G2 — separate future gate
Voice-to-Shot — separate future gate
OWNER activation / OWNER LOCK — separate owner decisions
```

The Studio-S track must preserve `STUDIO-S* DOES NOT AUTHORIZE P*` and `P* DOES NOT SILENTLY AUTHORIZE STUDIO-S*`.

- [ ] **Step 3: Encode REUSE-FIRST as an engineering direction, not dependency adoption**

Record that each generic subsystem first searches production-tested open source and uses ADOPT/ADAPT/PROBE before custom build; actual dependency adoption still requires an exact gate with version/revision/license/provenance.

- [ ] **Step 4: Verify no phase is marked authorized merely because it appears on the roadmap**

Expected result: roadmap communicates sequence and coarse current placement only.

---

### Task 3: Create Agent Roles

**Files:**
- Create: `docs/ZB_AGENT_ROLES.md`

**Interfaces:**
- Consumes: accepted governance/state-machine rules, Checkpoint handoff/resume rules, Signal actor-scoped clear rules.
- Produces: stable authority contract for SPARX/OWNER, DJANGO, DUNCAN, LESTER, SALVADOR.

- [ ] **Step 1: Define role semantics**

The document must state:

```text
AGENT ROLES = WHO MAY DO WHAT
ROLE CONTEXT ≠ AUTHENTICATED ACTOR IDENTITY
HANDOFF AUTHORITY ≤ ACTOR AUTHORITY
SIGNAL AUTHORITY ≤ ACTOR AUTHORITY
```

- [ ] **Step 2: Record exact role boundaries**

Required boundaries:

```text
SPARX / OWNER (`Sparx-Owner-ZB` when authenticated OWNER action is required)
  - owner decisions, runtime activation/HOLD/rollback, optional OWNER LOCK
  - OWNER LOCK never implied

DJANGO (`Django-Sparx-ZB`)
  - architecture review/acceptance within architecture scope
  - cannot self-substitute for independent QC or OWNER

DUNCAN (`Duncan-Sparx-ZB`)
  - independent QC, evidence verification, production-lead coordination within assigned scope
  - cannot create Django acceptance or OWNER action

LESTER (`Lester-Sparx`)
  - build/test/artifact/evidence/candidate creation
  - cannot create QC_PASS, architecture acceptance, runtime approval, activation, OWNER LOCK

SALVADOR
  - assigned visual/canon workflow authority only
  - no engineering/governance privilege transfer
```

- [ ] **Step 3: Integrate resume and signal responsibilities**

Record role-aware resume commands and that RESUME restores context but creates no authority. Record actor-scoped signal raise/clear limits, including `SIGNAL_3` SPARX action plus gate-holder verification before clear.

- [ ] **Step 4: Record the manual-action alarm boundary**

When direct SPARX action is genuinely required and tools cannot perform it, render exactly:

```text
🚨 SPARX — ОТ ТЕБЯ НУЖНО ДЕЙСТВИЕ!!!
```

This message does not itself grant OWNER authority or impersonate `Sparx-Owner-ZB`.

---

### Task 4: Phase A Scope Verification

**Files:**
- Verify only: `docs/ZB_PROJECT_INDEX.md`
- Verify only: `docs/ZB_MASTER_ROADMAP.md`
- Verify only: `docs/ZB_AGENT_ROLES.md`

**Interfaces:**
- Consumes: completed Tasks 1–3.
- Produces: review-ready Phase A candidate.

- [ ] **Step 1: Compare Phase A branch against its exact base**

Expected diff:

```text
3 files changed
3 files added
0 CURRENT checkpoint files
0 hq/state files
0 runtime files
```

- [ ] **Step 2: Scan for placeholders**

Search all three files for:

```text
TODO
TBD
FIXME
PLACEHOLDER
```

Expected: no unresolved placeholder text.

- [ ] **Step 3: Check cross-document semantic separation**

Verify:

```text
INDEX = WHERE THINGS ARE
ROADMAP = WHERE PROJECT IS GOING
ROLES = WHO MAY DO WHAT
```

No file should become CURRENT operational state.

- [ ] **Step 4: Run `hq-validate` through a pull request**

Expected: workflow conclusion `success` on the exact Phase A head SHA.

- [ ] **Step 5: Stop at the Phase A review/merge gate**

Do not create Phase B `CURRENT.json/.md` until the exact Phase A merge commit exists. Phase B initial checkpoint must use that merge as `sharedHq.stateBasisCommit` and `previousCheckpointId=null`.

---

## Self-Review

- Spec coverage: Phase A stable-doc separation, Phase B deferral, resume/roles, Signal integration, REUSE-FIRST, P1 pause and protected gates are each assigned to a concrete task.
- Placeholder scan: this plan contains no unresolved implementation placeholders.
- Type/property consistency: this Phase A plan does not create checkpoint JSON fields; all field names referenced (`sharedHq.stateBasisCommit`, `previousCheckpointId`) match the accepted Checkpoint R01 contract.

## Execution Selection

User has already authorized autonomous continuation without repeated A/B/C prompts. Execute inline using `superpowers:executing-plans`, maintaining branch isolation and stopping only at a genuine governance/manual-action blocker.