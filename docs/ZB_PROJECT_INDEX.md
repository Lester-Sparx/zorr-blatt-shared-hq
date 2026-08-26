# ZORR BLATT — Project Index

Status: **STABLE PROJECT MAP**

```text
PROJECT INDEX = WHERE THINGS ARE
```

This file is a navigation map. It points to canonical project sources and stable system locations. It is **not** the current operational state, not a roadmap, not a role verdict, and not a substitute for the documents it references.

Core law:

```text
NO CHAT IS PROJECT MEMORY.
PROJECT INDEX = MAP.
ROADMAP = PATH.
ROLES = AUTHORITY.
CHECKPOINT = CURRENT TRUTH.
HANDOFF = WORK TRANSFER.
GIT = AUDIT / PUBLICATION HISTORY.
```

---

## 1. Control / authority / evidence plane

Repository:

```text
Lester-Sparx/zorr-blatt-shared-hq
```

Role:

```text
SHARED HQ
= CONTROL / AUTHORITY / EVIDENCE PLANE
```

Shared HQ records and verifies governance, authority, contracts, exact source/release/evidence bindings, accepted architecture, checkpoints, handoffs, signals and protected gates.

Canonical production architecture:

```text
docs/ZB_PRODUCTION_INTEGRATION_ARCHITECTURE_R01.md
```

Architecture law:

```text
HQ CAN AUTHORIZE / VERIFY RUNTIME.
RUNTIME CANNOT REDEFINE HQ AUTHORITY.
```

---

## 2. Execution plane

Target production runtime repository:

```text
Lester-Sparx/zorr-blatt-runtime
```

Role:

```text
ZB PRODUCTION RUNTIME
= EXECUTION PLANE
```

The runtime is Rust-first with a future ZB CORE WASM boundary. Runtime bootstrap/implementation state is governed separately from this index.

Canonical P1 bootstrap design/spec:

```text
docs/superpowers/specs/2026-08-26-p1-runtime-bootstrap-design.md
```

Canonical P1 production-integration contract:

```text
docs/ZB_PRODUCTION_INTEGRATION_ARCHITECTURE_R01.md
```

---

## 3. Project-memory system

Checkpoint / Project Ledger design:

```text
docs/superpowers/specs/2026-08-26-zb-checkpoint-system-r01.md
```

Stable navigation/authority documents:

```text
docs/ZB_PROJECT_INDEX.md
  = where things are

docs/ZB_MASTER_ROADMAP.md
  = where the project is going

docs/ZB_AGENT_ROLES.md
  = who may do what
```

Operational current-state targets:

```text
checkpoints/ZB_CHECKPOINT_CURRENT.json
  = canonical machine-readable current project state

checkpoints/ZB_CHECKPOINT_CURRENT.md
  = human-readable projection of CURRENT.json
```

These CURRENT files are created in **Checkpoint Phase B**, not Phase A. If they are absent before Phase B publication, that absence is explicit and must not be filled from chat memory or guessed state.

Checkpoint history target:

```text
checkpoints/archive/
```

Archive rule:

```text
ARCHIVE IS APPEND-ONLY / IMMUTABLE.
CORRECTION = NEW CHECKPOINT.
```

Actor work-transfer target:

```text
handoffs/
```

Handoff contract is defined by Checkpoint System R01. A handoff records actor-scoped work transfer and cannot grant authority beyond the actor that produced it.

---

## 4. Signal protocol

Canonical semantic signal contract:

```text
docs/superpowers/specs/2026-08-26-zb-signal-protocol-r01.md
```

Stable semantics:

```text
SIGNAL_1 / MILESTONE = transient material success notification
SIGNAL_2 / ATTENTION = persistent material attention/blocker condition
SIGNAL_3 / OWNER ACTION = persistent direct-SPARX action condition
```

Signals communicate state. They do not create governance verdicts or authorization.

Actual audio/device playback is downstream presentation and is not defined by Shared HQ signal semantics.

---

## 5. Open-source acceleration / REUSE-FIRST

Canonical study:

```text
docs/superpowers/specs/2026-08-26-zb-open-source-studio-acceleration-r01.md
```

Governing engineering direction:

```text
REUSE OPEN SOURCE WHEN IT IS FIT-FOR-PURPOSE.
DO NOT REBUILD GENERIC WORK WITHOUT A DOCUMENTED GAP.
```

The study maps open-source studio candidates using:

```text
ADOPT
ADAPT
PROBE
WATCH
DEFER
REJECT-AS-BACKBONE
```

The study is not itself dependency adoption. Every real adoption still requires its own exact version/revision/license/provenance gate.

---

## 6. Production roadmap

Canonical coarse roadmap:

```text
docs/ZB_MASTER_ROADMAP.md
```

The roadmap describes sequence and coarse phase placement only.

```text
ROADMAP STATUS ≠ AUTHORIZATION
```

---

## 7. Agent / owner authority

Canonical stable role contract:

```text
docs/ZB_AGENT_ROLES.md
```

The role file defines stable authority boundaries for:

```text
SPARX / OWNER
DJANGO
DUNCAN
LESTER
SALVADOR
```

Authenticated identity requirements remain separate from conversational role context.

---

## 8. Architecture staging history

Architecture staging source:

```text
docs/ZB_ARCHITECTURE_STAGING_R01.md
```

Production-integration source:

```text
docs/ZB_PRODUCTION_INTEGRATION_ARCHITECTURE_R01.md
```

Completed proof lineage is preserved as evidence, not production code:

```text
O0    = OxiHuman donor/body feasibility
B0    = Babylon body compiler boundary proof
M0    = Motion Truth / Action Truth boundary proof
C1    = Cinematography boundary proof
GRANI = Presentation Truth boundary proof
```

Exact accepted proof heads, report hashes and artifact hashes are recorded in the Production Integration Architecture. This index intentionally does not duplicate those bindings.

---

## 9. P1 implementation planning

P1 bootstrap implementation plan history:

```text
docs/superpowers/plans/
```

Checkpoint Phase A plan:

```text
docs/superpowers/plans/2026-08-26-zb-checkpoint-phase-a-r01.md
```

Plan files describe how approved work is executed. They do not create authorization by themselves.

---

## 10. Shared HQ governance/security references

Repository governance/security references include:

```text
docs/GITHUB_SHARED_HQ_CONTRACT.md
docs/SECURITY_BOUNDARIES.md
docs/TRUSTED_ROUTING_BOOTSTRAP_RUNBOOK.md
docs/DEPLOYMENT_PREREQUISITES_RU.md
docs/ACCEPTANCE_A01_A20.md
```

Use these sources for their stated scopes rather than copying their contents into this index.

---

## 11. Visual / canon production source

ZORR BLATT visual/canon production rules exist as a separate production workflow domain.

At the time this stable index is introduced, no single canonical Shared HQ file path for the full visual/canon production guide is asserted here unless it is independently present and verified in the repository.

Law:

```text
NO CANONICAL PATH → DO NOT INVENT A PATH FROM CHAT MEMORY.
```

When a canonical visual/canon guide is published to Shared HQ, update this index with that exact repository location.

---

## 12. Protected gates

The following are always separate explicit gates and are not unlocked by being referenced anywhere in the index:

```text
P1 IMPLEMENTATION START
RUNTIME_APPROVED
RUNTIME_ACTIVATED
OWNER LOCK
G2
VOICE-TO-SHOT
```

Owner-only authenticated actions require the correct owner identity. No document, signal, roadmap item, handoff or assistant role can impersonate that identity.

---

## 13. Semantic separation

```text
PROJECT INDEX
= WHERE THINGS ARE

MASTER ROADMAP
= WHERE PROJECT IS GOING

AGENT ROLES
= WHO MAY DO WHAT

CHECKPOINT CURRENT
= WHERE PROJECT IS NOW

HANDOFF
= WHAT ONE ACTOR JUST TRANSFERRED
```

If two canonical sources disagree about CURRENT state, do not resolve the conflict by guessing from this index or from chat. Apply the Checkpoint System conflict/staleness rules.