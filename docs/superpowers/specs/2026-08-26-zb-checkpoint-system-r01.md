# ZORR BLATT — Checkpoint / Project Ledger System R01

Status: **APPROVED DESIGN / GOVERNANCE SPEC CANDIDATE / NOT YET INTEGRATED**

Authority repository: `Lester-Sparx/zorr-blatt-shared-hq`

Spec base commit: `00330fcba42e3b353b8b6159c903598b9e3bc2e0`

This specification records the approved design for a recoverable project-memory system in Shared HQ. It is docs-only. It does **not** mutate `hq/state`, create or modify the runtime repository, authorize P1 implementation, authorize G2 or Voice-to-Shot, activate production, or create OWNER LOCK.

---

## 1. Governing law

```text
NO CHAT IS PROJECT MEMORY.
SHARED HQ CHECKPOINT IS PROJECT MEMORY.

CHAT = TEMPORARY WORK SESSION.
CHECKPOINT = RECOVERABLE PROJECT STATE.
```

A new chat must be able to recover the authoritative project state from Shared HQ without reconstructing long conversation history.

The system separates five responsibilities:

```text
PROJECT INDEX = WHERE THINGS ARE.
MASTER ROADMAP = WHERE THE PROJECT IS GOING.
AGENT ROLES = WHO MAY DO WHAT.
CHECKPOINT = WHERE THE PROJECT IS NOW.
HANDOFF = WHAT ONE ACTOR TRANSFERRED.
GIT = AUDIT / PUBLICATION HISTORY.
```

---

## 2. Storage model

The R01 logical structure is:

```text
docs/
├─ ZB_PROJECT_INDEX.md
├─ ZB_MASTER_ROADMAP.md
├─ ZB_AGENT_ROLES.md
└─ superpowers/specs/2026-08-26-zb-checkpoint-system-r01.md

checkpoints/
├─ ZB_CHECKPOINT_CURRENT.json
├─ ZB_CHECKPOINT_CURRENT.md
└─ archive/
   ├─ <checkpoint-id>.json
   └─ <checkpoint-id>.md

handoffs/
├─ <handoff-id>.json
└─ <handoff-id>.md
```

`checkpoints/ZB_CHECKPOINT_CURRENT.json` is the canonical semantic current-state representation.

`checkpoints/ZB_CHECKPOINT_CURRENT.md` is the human-readable projection of the same state.

`checkpoints/archive/*` is immutable historical state.

`handoffs/*` is immutable actor-to-actor work-transfer history.

---

## 3. Canonical state and projection law

The canonical-current law is:

```text
CURRENT.json
= semantic project-memory authority

CURRENT.md
= human-readable projection of the same checkpoint
```

The Markdown projection may improve readability but must not introduce authoritative information absent from the JSON state.

If JSON and Markdown disagree:

```text
CHECKPOINT_CONFLICT
→ DO NOT GUESS
→ DO NOT CONTINUE FROM CHAT MEMORY
→ RECONCILE CHECKPOINT
```

---

## 4. Checkpoint identity and timestamps

R01 checkpoint IDs use:

```text
YYYY-MM-DD-RNN
```

Examples:

```text
2026-08-26-R01
2026-08-26-R02
2026-08-27-R01
```

Timestamps are UTC ISO-8601.

The date component of `checkpointId` uses UTC date.

---

## 5. State-basis commit erratum

A checkpoint cannot safely contain the SHA of the same Git commit that contains the checkpoint file, because modifying the SHA inside the file changes the resulting blob/tree/commit identity.

Therefore R01 uses:

```text
sharedHq.stateBasisCommit
= exact Shared HQ commit relative to which the project state was constructed

checkpointPublicationCommit
= derived from Git history; never self-recorded inside the checkpoint
```

An ordinary newer Shared HQ commit does not automatically make a checkpoint stale.

Validation rules:

```text
stateBasisCommit not in authoritative main ancestry
→ CHECKPOINT_CONFLICT

material project-state transition occurred after checkpoint
without required checkpoint update
→ CHECKPOINT_STALE
```

---

## 6. Canonical checkpoint schema

R01 canonical schema identifier:

```text
ZB_CHECKPOINT_V1
```

Minimum shape:

```json
{
  "schemaId": "ZB_CHECKPOINT_V1",
  "schemaVersion": 1,
  "checkpointId": "2026-08-26-R01",
  "createdAt": "2026-08-26T00:00:00Z",
  "createdBy": "Duncan-Sparx-ZB",
  "previousCheckpointId": null,
  "project": "ZORR BLATT",
  "sharedHq": {
    "repository": "Lester-Sparx/zorr-blatt-shared-hq",
    "stateBasisCommit": "<exact sha>"
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
  "checkpointReason": {
    "kind": "ACCEPTED",
    "source": "<transition/review/decision>",
    "evidence": []
  }
}
```

Unknown exact values are represented by `null` or an explicit unresolved object according to the field contract. They must never be invented.

---

## 7. Status vocabulary

R01 base status vocabulary:

```text
NOT_STARTED
NOT_AUTHORIZED
DESIGN
DESIGN_APPROVED
IN_PROGRESS
CANDIDATE
AWAITING_REVIEW
ACCEPTED
QC_PASS
CHANGES_REQUIRED
FAIL
BLOCKED
PAUSED
COMPLETE
LOCKED
ACTIVE
INACTIVE
UNCHANGED
UNRESOLVED
```

Not every entity may use every status. Future schema validation may restrict allowed status values per field/entity.

Free-form states such as `almost done`, `probably accepted`, or `pretty much ready` are forbidden in canonical state.

---

## 8. Global status

`globalStatus` records coarse authoritative status of major project stages and protected gates.

Example categories include:

```text
integrationArchitecture
checkpointSystem
p1Bootstrap
p1Implementation
p2BodyCompiler
p3MotionAction
p4Cinematography
p5BabylonRuntime
p6GraniPresentation
g2
voiceToShot
productionActivation
ownerLock
```

Where exact accepted bindings exist, the state may include exact commit, document, blob, artifact, or review bindings.

---

## 9. Active work

`activeWork` is actor-scoped current assignment, not a role definition.

Example:

```json
{
  "Duncan-Sparx-ZB": {
    "role": "QC_PRODUCTION_LEAD",
    "task": "ZB_CHECKPOINT_SYSTEM_R01",
    "status": "DESIGN",
    "step": "SECTION_4_OF_4",
    "currentDeliverable": "checkpoint system governance specification",
    "nextRequiredTransition": "CHECKPOINT_SYSTEM_SPEC_REVIEW",
    "blockedBy": []
  }
}
```

Actor role authority itself belongs in `docs/ZB_AGENT_ROLES.md`.

---

## 10. Latest accepted decisions

`latestAcceptedDecisions` stores currently effective project decisions, not brainstorming history.

Minimum decision form:

```json
{
  "decisionId": "P1-RUNTIME-VISIBILITY",
  "status": "ACCEPTED",
  "value": "PRIVATE",
  "source": {
    "type": "DESIGN_APPROVAL",
    "binding": "<artifact/commit>"
  }
}
```

If a decision is superseded, CURRENT records the new effective decision and may include `supersedesDecisionId`. Historical checkpoints preserve the earlier decision.

---

## 11. Blockers

Every blocker must be actionable.

Example:

```json
{
  "blockerId": "BLK-001",
  "status": "OPEN",
  "summary": "Runtime repository does not yet exist",
  "blocks": ["P1_RUNTIME_BOOTSTRAP"],
  "owner": "SPARX",
  "resolutionRequired": "Create PRIVATE Lester-Sparx/zorr-blatt-runtime",
  "evidence": []
}
```

Resolved blockers leave `CURRENT.openBlockers` but remain preserved in archived checkpoint history.

---

## 12. Next transitions

`nextTransitions` contains legal next governance transitions only. It is not a general todo list and does not replace the roadmap.

R01 should normally expose no more than the next five transitions.

Each entry may contain:

```text
order
transition
actor
status
blockedBy
```

A roadmap item does not become authorized merely because it appears in `nextTransitions` or `ZB_MASTER_ROADMAP.md`.

---

## 13. Owner action required

Owner action is always explicit:

```json
{
  "required": false,
  "action": null
}
```

or:

```json
{
  "required": true,
  "action": "Create private runtime repository Lester-Sparx/zorr-blatt-runtime",
  "reason": "No available connected tool can create repositories"
}
```

Agents must not invent workarounds for an explicit owner-only blocker.

---

## 14. When a checkpoint is required

A new checkpoint is created only for a meaningful project-state transition, including:

```text
ACCEPTED
QC_PASS
FAIL
CHANGES_REQUIRED
BLOCKED
UNBLOCKED
PAUSED
RESUMED
COMPLETE
ACTIVATED
LOCKED
material scope or authority decision
current phase change
exact authoritative binding change
next actor change
legal next transition change
critical blocker creation/removal
```

A checkpoint is not required after ordinary messages, questions, explanations, status pings, in-progress CI, unaccepted brainstorming proposals, ordinary tool reads, or any action that does not materially change project state.

Governing rule:

```text
ONE MATERIAL STATE TRANSITION
→ ONE NEW CHECKPOINT STATE

NO MATERIAL STATE CHANGE
→ NO CHECKPOINT
```

---

## 15. Checkpoint transaction

An ordinary checkpoint transition is logically atomic:

```text
READ OLD CURRENT
↓
READ EXACT NEW EVIDENCE
↓
APPLY ONE KNOWN MATERIAL TRANSITION
↓
ARCHIVE OLD CURRENT
↓
BUILD NEW CURRENT.json
↓
VALIDATE
↓
GENERATE CURRENT.md
↓
VERIFY JSON/MD EQUIVALENCE
↓
COMMIT TRANSITION TOGETHER
```

For non-initial transitions, the transition commit normally includes:

```text
checkpoints/archive/<previous-id>.json
checkpoints/archive/<previous-id>.md
checkpoints/ZB_CHECKPOINT_CURRENT.json
checkpoints/ZB_CHECKPOINT_CURRENT.md
```

If a relevant handoff is created in the same logical transition, its `.json` and `.md` pair may be included in the same reviewable candidate.

---

## 16. Archive law

Checkpoint archive is append-only.

Forbidden:

```text
edit old checkpoint
rewrite FAIL into ACCEPTED
delete inconvenient history
change historical exact bindings
```

Historical errors are corrected by a new checkpoint with an explicit correction relationship, for example:

```json
{
  "correctsCheckpointId": "2026-08-26-R04"
}
```

The incorrect historical checkpoint remains visible.

---

## 17. Evidence law

Checkpoint stores evidence bindings, not complete evidence bytes or long discussions.

Supported R01 evidence classes include at minimum:

```text
GITHUB_COMMIT
GITHUB_PR
GITHUB_REVIEW
WORKFLOW_RUN
ARTIFACT
REPORT_SHA256
GIT_BLOB
DOCUMENT
IMAGE_EVIDENCE
EXTERNAL_BINDING
HANDOFF
```

Example:

```json
{
  "type": "GITHUB_PR",
  "repository": "Lester-Sparx/zorr-blatt-shared-hq",
  "number": 22,
  "headSha": "255656883bff4d5775753c9fcdda3880a07bcd63",
  "result": "MERGED"
}
```

Governing law:

```text
CHECKPOINT = INDEX OF CURRENT TRUTH.
NOT ARCHIVE OF ALL EVIDENCE BYTES.
```

---

## 18. Checkpoint generation law

R01 may be docs-driven, but agents must not manually recreate current state from memory.

Correct process:

```text
READ previous CURRENT
+
READ exact new evidence
+
apply ONE known transition
+
produce next CURRENT
```

Forbidden process:

```text
remember chat
→ write a new project summary from memory
```

---

## 19. Handoff model

A handoff is distinct from a checkpoint:

```text
CHECKPOINT = current state of the whole project.
HANDOFF = immutable transfer of one concrete work unit.
```

A handoff may provide evidence but may not self-promote into global project truth.

If the handoff changes phase, accepted/fail status, next actor, blocker, authority binding, or legal next transition, a new checkpoint is required.

---

## 20. Handoff identity and storage

Handoff IDs use UTC:

```text
YYYYMMDDTHHMMSSZ-<ACTOR>-<TASK>-RNN
```

Example:

```text
20260826T061500Z-DUNCAN-P1-BOOTSTRAP-SPEC-R01
```

Canonical handoff:

```text
handoffs/<handoff-id>.json
```

Human projection:

```text
handoffs/<handoff-id>.md
```

Published handoffs are immutable. Errors are corrected by a new handoff using `correctsHandoffId`.

---

## 21. Canonical handoff schema

R01 handoff schema identifier:

```text
ZB_HANDOFF_V1
```

Minimum shape:

```json
{
  "schemaId": "ZB_HANDOFF_V1",
  "schemaVersion": 1,
  "handoffId": "20260826T061500Z-DUNCAN-P1-BOOTSTRAP-SPEC-R01",
  "createdAt": "2026-08-26T06:15:00Z",
  "actor": {
    "role": "DUNCAN",
    "githubIdentity": "Duncan-Sparx-ZB"
  },
  "basedOnCheckpointId": "2026-08-26-R03",
  "task": {
    "id": "P1_RUNTIME_BOOTSTRAP_SPEC",
    "status": "COMPLETE"
  },
  "bindings": {
    "repository": "Lester-Sparx/zorr-blatt-shared-hq",
    "baseSha": null,
    "headSha": null
  },
  "whatChanged": [],
  "evidence": [],
  "whatWasNotChanged": [],
  "limitations": [],
  "openBlockers": [],
  "nextActor": "DJANGO",
  "nextRequiredTransition": "P1_BOOTSTRAP_REVIEW",
  "ownerActionRequired": {
    "required": false,
    "action": null
  }
}
```

Unknown exact SHA values are `null`; they are never guessed.

---

## 22. Handoff scope requirements

`whatChanged` contains only factual scoped changes.

`whatWasNotChanged` is mandatory for governance-sensitive work and explicitly records untouched authority boundaries such as:

```text
hq/state
P1 implementation
OWNER LOCK
G2
Voice-to-Shot
production activation
```

`limitations` records known evidence or scope limits.

`openBlockers` records blockers carried forward by the handoff.

---

## 23. Role-scoped handoff authority

Governing law:

```text
HANDOFF AUTHORITY
≤ ACTOR AUTHORITY
```

R01 role boundaries include:

```text
LESTER
MAY: BUILT, TESTED, CANDIDATE_READY, ARTIFACT_PRODUCED
MAY NOT: QC_PASS own work, ARCHITECTURE_ACCEPTED, RUNTIME_APPROVED, ACTIVATE, OWNER_LOCK

DUNCAN
MAY: QC_PASS, CHANGES_REQUIRED, BLOCKED, technical evidence verdicts
MAY NOT: impersonate Django, create OWNER LOCK, activate production

DJANGO
MAY: ARCHITECTURE_ACCEPTED, ARCHITECTURE_CHANGES_REQUIRED
MAY NOT: self-substitute for independent QC, create OWNER LOCK, silently activate production

OWNER / SPARX
MAY: ACTIVATE, HOLD, explicit OWNER LOCK decision

SALVADOR
MAY: claims inside assigned visual/canon workflow
MAY NOT: acquire engineering/governance authority by role transfer
```

---

## 24. Role context versus authenticated identity

A resume command may select role context, but it never authorizes identity impersonation.

```text
ROLE CONTEXT
≠ AUTHENTICATED ACTOR IDENTITY
```

Before any authenticated mutation, the agent must verify the actual connected account identity when the transition depends on actor identity.

Example:

```text
Required actor = Django-Sparx-ZB
Connected actor = Duncan-Sparx-ZB
→ DO NOT POST AS DJANGO
```

---

## 25. Resume commands

Canonical resume commands:

```text
DJANGO — RESUME FROM ZB CHECKPOINT
DUNCAN — RESUME FROM ZB CHECKPOINT
LESTER — RESUME FROM ZB CHECKPOINT
SALVADOR — RESUME FROM ZB CHECKPOINT
```

Short form is acceptable:

```text
<ROLE> — RESUME FROM CHECKPOINT
```

---

## 26. Resume protocol

A new chat must restore context in this order:

```text
1. Open Shared HQ.
2. Read checkpoints/ZB_CHECKPOINT_CURRENT.json.
3. Validate schema, checkpointId, stateBasisCommit ancestry, and JSON integrity.
4. Read docs/ZB_PROJECT_INDEX.md.
5. Read docs/ZB_MASTER_ROADMAP.md.
6. Read docs/ZB_AGENT_ROLES.md.
7. Select the actor's activeWork entry.
8. Read the latest handoff(s) referenced for that actor/task.
9. Follow only exact evidence required for the next transition.
10. Produce a ZB RESUME REPORT.
11. Continue only if no CHECKPOINT_CONFLICT, CHECKPOINT_STALE, EVIDENCE_BINDING_FAILURE, or blocking owner action exists.
```

If Shared HQ is available and the checkpoint is valid, the agent must not ask SPARX to reconstruct project history from chat.

---

## 27. Resume report

Before first substantive resumed action, produce a compact report containing:

```text
ZB RESUME REPORT

ROLE
CHECKPOINT
CURRENT PHASE
STATE BASIS
MY ACTIVE TASK
MY STATUS
LATEST HANDOFF
OPEN BLOCKERS
NEXT LEGAL TRANSITION
OWNER ACTION REQUIRED
```

The report is a state readout, not a rewritten project history.

---

## 28. Resume failure modes

```text
CURRENT.json absent
→ CHECKPOINT_MISSING → STOP

JSON/MD mismatch
→ CHECKPOINT_CONFLICT → STOP

stateBasisCommit not in authoritative main ancestry
→ CHECKPOINT_CONFLICT → STOP

material transition newer than required checkpoint
→ CHECKPOINT_STALE → STOP

evidence exact binding failure
→ EVIDENCE_BINDING_FAILURE → STOP affected transition

explicit owner-only blocker
→ OWNER_ACTION_REQUIRED → report exact action; do not improvise
```

Governing law:

```text
RESUME RESTORES CONTEXT.
RESUME DOES NOT CREATE AUTHORITY.
```

---

## 29. Project index contract

`docs/ZB_PROJECT_INDEX.md` is a stable map of project topology.

It should point to, not duplicate, authoritative sources.

Minimum sections:

```text
CONTROL / AUTHORITY PLANE
EXECUTION PLANE
ARCHITECTURE
PROJECT MEMORY
ROADMAP
ROLES
PROOFS
VISUAL / ART CANON
PROTECTED / SEPARATE GATES
```

Governing law:

```text
PROJECT INDEX POINTS.
IT DOES NOT DUPLICATE ENTIRE SOURCES.
```

---

## 30. Master roadmap contract

`docs/ZB_MASTER_ROADMAP.md` is the stable phase-level path of the project.

R01 baseline roadmap:

```text
FOUNDATION
IA — ACCEPTED
ZB Checkpoint / Project Ledger — current design/integration stage
P1 Runtime Bootstrap — DESIGN APPROVED; physical bootstrap paused pending project-memory integration
P1 Contract Foundation — NOT STARTED; requires separate P1 IMPLEMENTATION START

CORE
P2 Body Compiler — NOT AUTHORIZED
P3 Motion / Action — NOT AUTHORIZED
P4 Cinematography — NOT AUTHORIZED
P5 Babylon Runtime — NOT AUTHORIZED
P6 Grani Presentation — NOT AUTHORIZED

SEPARATE / LATER GATES
G2 — LOCKED
Voice-to-Shot — LOCKED
Production Activation — OWNER transition
OWNER LOCK — separate OWNER-only decision
```

Governing laws:

```text
ROADMAP STATUS ≠ AUTHORIZATION.
ROADMAP = PHASE-LEVEL STATUS.
CHECKPOINT = OPERATIONAL CURRENT STATUS.
```

The roadmap must not contain low-level current details such as active CI run IDs, current review step numbers, or transient PR diagnostics.

---

## 31. Agent roles contract

`docs/ZB_AGENT_ROLES.md` records stable authority and prohibition boundaries for at least:

```text
SPARX / OWNER
DJANGO
DUNCAN
LESTER
SALVADOR
```

Each role section must define:

```text
ROLE PURPOSE
MAY
MAY NOT
AUTHENTICATED IDENTITY REQUIREMENT
HANDOFF AUTHORITY
TRANSITIONS THEY MAY ISSUE
```

The roles document never stores current active task.

```text
ROLE = CAPABILITY / AUTHORITY.
ACTIVE WORK = CURRENT ASSIGNMENT.
```

---

## 32. Stable-document change policy

`ZB_PROJECT_INDEX.md`, `ZB_MASTER_ROADMAP.md`, and `ZB_AGENT_ROLES.md` do not change after every checkpoint.

Update only documents whose semantic truth changed.

Typical triggers:

```text
PROJECT INDEX
→ new authoritative subsystem/repository/document family
→ canonical location changed
→ project topology changed

MASTER ROADMAP
→ global phase structure changed
→ phase moved to new coarse status
→ approved phase/gate added or removed

AGENT ROLES
→ actual role/authority/identity policy changed
```

Governing law:

```text
UPDATE ONLY DOCUMENTS WHOSE SEMANTIC TRUTH CHANGED.
```

---

## 33. No silent checkpoint mutation

Checkpoint changes must be explicit project-state mutations.

An unrelated PR must not secretly rewrite CURRENT.

A checkpoint transition PR/commit description should identify:

```text
old checkpoint
new checkpoint
reason
evidence
affected global state
```

A concise checkpoint delta is strongly recommended:

```text
FROM: <checkpoint-id>
TO: <checkpoint-id>
CHANGED: <semantic fields>
UNCHANGED: protected authority fields
```

---

## 34. Initial two-phase bootstrap

The first checkpoint system integration must avoid self-referential commit identity.

### Phase A — system integration

A docs-only candidate integrates stable system documents and the approved checkpoint-system specification.

Target documents include:

```text
docs/ZB_PROJECT_INDEX.md
docs/ZB_MASTER_ROADMAP.md
docs/ZB_AGENT_ROLES.md
docs/superpowers/specs/2026-08-26-zb-checkpoint-system-r01.md
```

After review and merge, the resulting exact Shared HQ main is `M1`.

### Phase B — initial checkpoint

A separate candidate is created from exact `M1` and publishes:

```text
checkpoints/ZB_CHECKPOINT_CURRENT.json
checkpoints/ZB_CHECKPOINT_CURRENT.md
```

with:

```text
sharedHq.stateBasisCommit = M1
previousCheckpointId = null
```

After merge, the publication commit is `M2`, derived from Git history and not self-recorded inside the checkpoint.

This two-phase protocol is mandatory for the initial R01 deployment.

---

## 35. Initial checkpoint truth requirements

The first CURRENT must describe the real project state at the time of creation and must include, at minimum, the then-valid status of:

```text
IA R01
Checkpoint System R01
P1 Runtime Bootstrap Design/Spec
physical P1 Runtime Bootstrap
P1 Implementation
P2
G2
Voice-to-Shot
Production Activation
OWNER LOCK
```

The initial checkpoint must use exact evidence bindings where available.

It must not reconstruct missing Salvador/art state from chat memory.

If no authoritative visual handoff exists:

```text
SALVADOR / ART STATE = UNRESOLVED or NO_CURRENT_HANDOFF
```

Governing law:

```text
MISSING ART STATE
≠ PERMISSION TO RECONSTRUCT IT FROM CHAT MEMORY.
```

---

## 36. R01 validation requirements

R01 is docs-first. It does not require a full orchestrator.

The initial validation design must cover at least:

```text
CURRENT.json parses
schemaId/schemaVersion valid
checkpointId format valid
UTC timestamp format valid
previousCheckpointId coherent
stateBasisCommit present
stateBasisCommit ancestry valid
CURRENT.md checkpointId matches JSON
status vocabulary valid
actor roles known
ownerActionRequired shape valid
handoff references resolvable where required
archive filename matches archived checkpointId
normal transitions do not modify historical archive entries
no required dependency on chat memory
```

Automation may be added incrementally after the documents and state semantics are stable.

```text
DOCS FIRST.
VALIDATION SECOND.
AUTOMATION LATER.
```

---

## 37. Future orchestrator boundary

A future COMMS ORCHESTRATOR may:

```text
observe exact evidence
prepare handoff
prepare checkpoint candidate
validate checkpoint delta
route next actor
```

It does not receive governance powers merely by automating the process.

```text
ORCHESTRATOR MAY PREPARE.
AUTHORIZED ACTOR MUST AUTHORIZE.
```

---

## 38. R01 recovery target

R01 is successful only if a completely new chat, given Shared HQ access and a command such as:

```text
DUNCAN — RESUME FROM ZB CHECKPOINT
```

can recover within approximately 2–3 minutes:

```text
where the project is
what is already accepted
what is forbidden
what the selected actor is doing
what the previous relevant actor transferred
which exact SHA/bindings anchor the state
what the next legal transition is
whether SPARX action is required
```

without reconstructing hundreds of prior chat messages.

---

## 39. Scope exclusions

Checkpoint System R01 does not itself authorize or implement:

```text
hq/state mutation
runtime repository bootstrap
P1 contract implementation
Body Compiler
Motion / Action implementation
Cinematography implementation
Babylon runtime implementation
Grani implementation
coordinate lock
G2
Voice-to-Shot
production activation
OWNER LOCK
```

The P1 Runtime Bootstrap remains paused until the project-memory system is integrated and the initial checkpoint becomes operational.

---

## 40. Post-spec integration sequence

After this specification is approved and recorded:

```text
1. ZB CHECKPOINT SYSTEM R01 spec accepted
2. create docs-only system-integration candidate
3. add ZB_PROJECT_INDEX.md
4. add ZB_MASTER_ROADMAP.md
5. add ZB_AGENT_ROLES.md
6. review and merge Phase A → exact M1
7. create initial checkpoint candidate from M1
8. validate CURRENT.json / CURRENT.md
9. review and merge Phase B → publication M2
10. test RESUME protocol from a fresh role context
11. mark project-memory system operational
12. resume paused P1 Runtime Bootstrap
```

No step in this sequence authorizes `P1 IMPLEMENTATION START`.

---

## 41. Final governing summary

```text
NO CHAT IS PROJECT MEMORY.
SHARED HQ CHECKPOINT IS PROJECT MEMORY.

PROJECT INDEX = MAP.
MASTER ROADMAP = PATH.
AGENT ROLES = AUTHORITY.
CHECKPOINT = CURRENT TRUTH.
HANDOFF = IMMUTABLE WORK TRANSFER.
GIT = AUDIT / PUBLICATION HISTORY.

CURRENT.json IS CANONICAL.
CURRENT.md IS HUMAN PROJECTION.

CURRENT IS REPLACEABLE.
ARCHIVE IS IMMUTABLE.
HISTORY IS NEVER REWRITTEN.

CHECKPOINT IS STATE, NOT CHAT SUMMARY.
HANDOFF CLAIMS MAY NEVER EXCEED ACTOR AUTHORITY.
ROLE CONTEXT ≠ AUTHENTICATED IDENTITY.
RESUME RESTORES CONTEXT, NOT AUTHORITY.

ONE MATERIAL STATE TRANSITION → ONE NEW CHECKPOINT.
NO MATERIAL STATE CHANGE → NO CHECKPOINT.

INITIAL DEPLOYMENT IS TWO-PHASE:
SYSTEM INTEGRATION → M1
THEN INITIAL CHECKPOINT BASED ON M1 → M2 PUBLICATION.

P1 RUNTIME BOOTSTRAP REMAINS PAUSED.
P1 IMPLEMENTATION REMAINS NOT AUTHORIZED.
```
