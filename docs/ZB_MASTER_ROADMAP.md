# ZORR BLATT — Master Roadmap

Status: **STABLE COARSE ROADMAP**

```text
MASTER ROADMAP = WHERE THE PROJECT IS GOING
ROADMAP STATUS ≠ AUTHORIZATION
```

This document records the coarse production path and stable phase ordering. It does not grant permission to start a phase, approve a runtime, activate production, or create OWNER LOCK.

---

## 1. Governing rollout law

```text
NO STAGE AUTHORIZES THE NEXT GOVERNANCE STAGE IMPLICITLY.
```

Every implementation/review/activation transition still requires its own governing evidence and authorized actor.

Roadmap labels such as `NEXT`, `PLANNED`, `PAUSED`, or `COMPLETE` are navigational project-state summaries only.

---

## 2. Current coarse placement

The project is currently completing the Project Memory / Checkpoint integration before resuming runtime bootstrap.

Coarse placement:

```text
CHECKPOINT SYSTEM PHASE A
  stable project-memory docs integration
  → COMPLETE when this Phase A stable-doc set is present on protected main

CHECKPOINT SYSTEM PHASE B
  initial CURRENT.json / CURRENT.md publication
  → follows the exact Phase A merge

P1 RUNTIME BOOTSTRAP
  → PAUSED pending checkpoint integration
  → may resume only under its existing bootstrap gate after Phase B publication

P1 IMPLEMENTATION
  → NOT AUTHORIZED
  → remains a separate explicit future transition
```

This roadmap must be updated when those coarse facts materially change.

---

## 3. Project-memory foundation

### Phase A — stable documents

Deliverables:

```text
docs/ZB_PROJECT_INDEX.md
docs/ZB_MASTER_ROADMAP.md
docs/ZB_AGENT_ROLES.md
```

Purpose:

```text
PROJECT INDEX = map
MASTER ROADMAP = path
AGENT ROLES = stable authority
```

Phase A does not publish operational CURRENT state.

### Phase B — first recoverable current checkpoint

Deliverables:

```text
checkpoints/ZB_CHECKPOINT_CURRENT.json
checkpoints/ZB_CHECKPOINT_CURRENT.md
```

Initial publication rules:

```text
previousCheckpointId = null
sharedHq.stateBasisCommit = exact Phase A merge commit
checkpointPublicationCommit = derived from Git after publication
```

The checkpoint is reconstructed from exact repository/evidence state, not from chat memory.

After Phase B, a new chat/actor session should be able to restore project context through the checkpoint/resume protocol.

---

## 4. P1 — Runtime Bootstrap

Accepted bootstrap direction:

```text
execution repo: Lester-Sparx/zorr-blatt-runtime
visibility: PRIVATE
language: Rust-first
future execution form: ZB CORE WASM
workspace: single Cargo workspace
```

Logical foundation:

```text
zb-contracts
zb-canonical
zb-authority
zb-provenance
zb-validation
```

Bootstrap establishes only the minimal execution-plane skeleton, exact toolchain/dependency pins, CI baseline and Shared HQ architecture binding.

It does **not** itself authorize P1 implementation.

Current coarse state:

```text
P1 RUNTIME BOOTSTRAP = PAUSED
reason = complete project-memory/checkpoint integration first
```

---

## 5. P1 — Runtime Contract Foundation

Separate transition required:

```text
P1 IMPLEMENTATION START
```

P1 purpose:

```text
versioned truth/intent/presentation packet contracts
canonical serialization
SHA-256 hashing
source/provenance bindings
UNRESOLVED safety
authority/writeback enforcement
dependency-direction enforcement
negative tests
determinism tests
```

P1 explicitly excludes full body generation, production Babylon rendering, motion solving, cinematography realization, Grani effects, coordinate lock, G2, Voice-to-Shot, OWNER LOCK and production activation.

Canonical production contract:

```text
docs/ZB_PRODUCTION_INTEGRATION_ARCHITECTURE_R01.md
```

---

## 6. P2 — Body Compiler

Target domain:

```text
REFERENCE EVIDENCE
→ CHARACTER_DNA
→ CHARACTER-SPECIFIC REST_RIG + SURFACE CONTRACT
→ ZB ANTHROPOMETRY ADAPTER/SOLVER
→ COMPILED BODY MESH
→ BODY_TRUTH
```

Existing OxiHuman result remains a replaceable donor/backend feasibility result only.

```text
OxiHuman params ✗→ CHARACTER_DNA
OxiHuman skeleton ✗→ REST_RIG
```

Open-source acceleration direction:

```text
reuse suitable donor/backend/authoring/geometry tooling
build only ZB-specific authority, solver, validation and integration gaps
```

P2 requires its own design/build/evidence/QC/architecture-review sequence.

---

## 7. P3 — Motion / Action

Target laws:

```text
POSE IS NOT MOTION.
MOTION DNA MUST NOT MUTATE BODY DNA.
BODY TRUTH + SPACE TRUTH + MOTION TRUTH = ACTION TRUTH.
```

Canonical motion phases include:

```text
PREPARE
LOAD
LAUNCH
AIR / TRANSFER
CONTACT
RECOVERY
```

External mocap/keypoint systems may be probed as evidence sources only.

```text
MOCAP / KEYPOINT OUTPUT ≠ MOTION_TRUTH
```

P3 remains separately authorized.

---

## 8. P4 — Cinematography

Target direction:

```text
ACTION TRUTH
→ SHOT INTENT
→ CAMERA TRUTH
→ OPERATOR PERFORMANCE
→ FRAME COMPOSITION
```

Core laws:

```text
CAMERA DOES NOT FOLLOW ACTION.
CAMERA INTERPRETS ACTION.
THE OPERATOR IS A PERFORMER.
```

Open-source acceleration direction may include Blender Shot Builder/Kitsu adapters and OpenTimelineIO for editorial interchange, but those systems cannot redefine Action Truth or Camera Truth.

P4 remains separately authorized.

---

## 9. P5 — Babylon Runtime

Target boundary:

```text
ZB-derived runtime representation
→ validated/optimized glTF/GLB
→ Babylon runtime
```

Babylon is downstream execution/presentation infrastructure and does not become Body/Motion/Action authority.

Reuse-first candidates at this boundary include:

```text
glTF Transform
Khronos glTF Validator
```

Actual adoption requires exact version/revision/license/provenance binding at the P5 gate.

---

## 10. P6 — Grani Presentation

Target direction:

```text
PHYSICAL CAMERA
→ OPERATOR PERFORMANCE
→ FRAME COMPOSITION
→ VIEW PRESENTATION / GRANI
→ PERCEIVED FRAME
```

Core law:

```text
PHYSICAL CAMERA REMAINS RECOVERABLE WHEN PRESENTATION / GRANI DISAGREES.
```

OpenColorIO/OpenImageIO/review/render infrastructure may be reused where appropriate, but presentation remains downstream and cannot write back into canonical truth.

P6 remains separately authorized.

---

## 11. Parallel Studio-S operations track

The accepted open-source acceleration study recommends a separate Studio Operations track so generic studio plumbing can advance without contaminating P1–P6 authority.

Canonical study:

```text
docs/superpowers/specs/2026-08-26-zb-open-source-studio-acceleration-r01.md
```

Proposed coarse sequence:

```text
STUDIO-S0 — OPERATIONS FOUNDATION
  Kitsu/Zou probe
  production entity model mapping
  binary storage probe
  Blender project-template probe

STUDIO-S1 — ASSET + SHOT FACTORY
  Blender Kitsu / Shot Builder
  Asset Pipeline
  thin ZB adapters

STUDIO-S2 — EDIT / REVIEW / RENDER
  OTIO
  Flamenco
  Kitsu/Render Review
  OCIO/OIIO where required

STUDIO-S3 — WORKSTATION / ASSET SCALE
  Rez if justified
  OpenAssetIO if justified
  professional review tool only if built-in review is insufficient

STUDIO-S4 — SCALE HARDENING
  OpenUSD / MaterialX / OpenCue only from demonstrated production need
```

Hard separation:

```text
STUDIO-S* DOES NOT AUTHORIZE P*.
P* DOES NOT SILENTLY AUTHORIZE STUDIO-S*.
```

No Studio-S probe/adoption is authorized merely by appearing here.

---

## 12. REUSE-FIRST engineering path

Governing law:

```text
REUSE OPEN SOURCE WHEN IT IS FIT-FOR-PURPOSE.
DO NOT REBUILD GENERIC WORK WITHOUT A DOCUMENTED GAP.
```

For generic subsystems, the default decision process is:

```text
SEARCH
→ VERIFY FIT / LICENSE / MAINTENANCE / BOUNDARY
→ ADOPT or ADAPT
→ PROBE if uncertain
→ CUSTOM BUILD only for a documented real gap
```

This does not allow floating dependencies or casual package adoption.

Every production adoption must still record:

```text
exact repository/source
exact version/tag/commit
license
selected packages/files
hashes/provenance
ZB authority boundary
replacement plan
probe/test evidence
```

---

## 13. Governance sequence for production waves

Each production implementation wave follows the same separation of powers:

```text
DESIGN / SCOPE
→ BUILD / CANDIDATE
→ EVIDENCE
→ DUNCAN QC
→ DJANGO ARCHITECTURE REVIEW
→ APPROVED CANDIDATE
→ OWNER decision where activation is involved
```

Role boundaries are defined in:

```text
docs/ZB_AGENT_ROLES.md
```

Build authority, QC authority, architecture authority and production activation authority remain distinct.

---

## 14. OWNER / activation / lock boundary

Runtime technical approval and production activation are separate:

```text
RUNTIME_APPROVED ≠ RUNTIME_ACTIVATED
```

Only the authenticated OWNER may decide activation/HOLD/rollback at the owner gate.

OWNER LOCK is a separate optional action and is never implied by:

```text
merge
QC_PASS
architecture ACCEPTED
RUNTIME_APPROVED
RUNTIME_ACTIVATED
checkpoint publication
roadmap status
signal
```

---

## 15. G2 and Voice-to-Shot

These remain outside the current authorized path:

```text
G2 = NOT AUTHORIZED
VOICE-TO-SHOT = NOT AUTHORIZED
```

They require independent future gates. No P1–P6 or Studio-S phase implicitly unlocks them.

---

## 16. Signal / project-state behavior

Signal semantics are defined by:

```text
docs/superpowers/specs/2026-08-26-zb-signal-protocol-r01.md
```

Signals communicate already-established project conditions.

```text
SIGNAL LEVEL ≠ GOVERNANCE VERDICT
```

`SIGNAL_1` accompanies material milestone transitions but does not itself create a checkpoint.

Persistent `SIGNAL_2/3` activation/clear are checkpoint-worthy project-state transitions under the accepted protocol.

---

## 17. Roadmap update policy

Update this document only when one of these stable/coarse facts changes:

```text
phase structure
coarse phase placement/status
new major parallel track
accepted ordering/dependency between phases
protected gate topology
```

Do not use this document for:

```text
per-commit status
CI run status
individual task logs
active blocker details
review transcripts
current alert details
```

Those belong in checkpoint/handoff/evidence systems.

---

## 18. Governing summary

```text
PROJECT MEMORY FIRST.
THEN RESUME RUNTIME BOOTSTRAP.

P1 CONTRACT FOUNDATION
→ P2 BODY
→ P3 MOTION / ACTION
→ P4 CINEMATOGRAPHY
→ P5 BABYLON
→ P6 GRANI

STUDIO-S OPERATIONS MAY ADVANCE SEPARATELY,
BUT NEVER GRANTS P* AUTHORITY.

REUSE GENERIC OPEN-SOURCE TECHNOLOGY WHEN FIT-FOR-PURPOSE.
BUILD CUSTOM ONLY FOR ZB-SPECIFIC AUTHORITY/TRUTH/INTEGRATION OR A DOCUMENTED GAP.

ROADMAP STATUS ≠ AUTHORIZATION.
OWNER LOCK IS NEVER IMPLIED.
G2 IS NOT AUTHORIZED.
VOICE-TO-SHOT IS NOT AUTHORIZED.
```