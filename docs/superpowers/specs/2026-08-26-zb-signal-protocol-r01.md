# ZORR BLATT — Signal Protocol R01

Status: **APPROVED DESIGN INPUT / GOVERNANCE SPEC CANDIDATE / NOT YET INTEGRATED**

Authority repository: `Lester-Sparx/zorr-blatt-shared-hq`

Spec base commit: `f63d18546b1428128dd39c6e98c093724fef0fd2`

This specification defines a semantic project alert protocol for ZORR BLATT. It extends the approved ZB Checkpoint / Project Ledger System R01 with machine-readable alert semantics that can later be mapped to actual audio by a COMMS ORCHESTRATOR or presentation layer.

This specification is docs-only. It does **not** play audio by itself, mutate `hq/state`, change runtime code, start P1 implementation, authorize G2 or Voice-to-Shot, activate production, or create OWNER LOCK.

---

## 1. Governing purpose

The project needs a small number of deterministic signals that immediately communicate meaningful state without turning normal chat/tool activity into notification noise.

Core law:

```text
SIGNAL = SEMANTIC ALERT.
SIGNAL ≠ GOVERNANCE VERDICT.
SIGNAL ≠ AUTHORIZATION.
SIGNAL ≠ PROJECT MEMORY BY ITSELF.
```

A signal communicates an already-established project condition. It never creates `ACCEPTED`, `QC_PASS`, `LOCKED`, `ACTIVATED`, `OWNER_LOCK`, or any other governance state merely by being emitted.

R01 is semantic only:

```text
SEMANTIC SIGNAL NOW.
ACTUAL AUDIO MAPPING LATER.
```

Future presentation layers may map signal levels to sound patterns without changing the governance meaning defined here.

---

## 2. Signal levels

R01 defines exactly three levels.

### `SIGNAL_1 / MILESTONE`

Purpose: communicate a material successful project transition.

Typical eligible conditions:

```text
ACCEPTED
QC_PASS
COMPLETE
CHECKPOINT PUBLISHED
ACTIVATED
MERGED, only when that merge itself materially changes project state
```

`SIGNAL_1` is transient. It is shown at the transition boundary and may be recorded in the transition evidence or handoff, but it does not remain in `CURRENT.activeAlert`.

Ordinary commit creation, CI success, tool calls, status updates, draft creation, branch creation, or routine messages are not `SIGNAL_1` events.

### `SIGNAL_2 / ATTENTION`

Purpose: communicate a material negative or blocking condition that deserves immediate attention but does not yet require direct SPARX action.

Typical conditions:

```text
BLOCKED
FAIL
CHANGES_REQUIRED
material evidence mismatch
material governance inconsistency
checkpoint stale/conflict requiring actor-side investigation
```

`SIGNAL_2` is persistent until evidence establishes that the condition has been resolved and the authorized actor clears it.

### `SIGNAL_3 / OWNER ACTION`

Purpose: communicate that progress physically or procedurally cannot continue without direct SPARX action.

Examples include owner-only account/repository/UI actions when no connected tool can perform them.

Every `SIGNAL_3` must include the mandatory human-readable alarm:

```text
🚨 SPARX — ОТ ТЕБЯ НУЖНО ДЕЙСТВИЕ!!!
```

`SIGNAL_3` is persistent until the required SPARX action is performed **and** the current gate-holder verifies the evidence.

---

## 3. Priority law

Signal priority is strict:

```text
SIGNAL_3 > SIGNAL_2 > SIGNAL_1
```

A lower-priority event cannot overwrite or hide a higher-priority active alert.

Therefore:

```text
active SIGNAL_3 + new SIGNAL_1 → SIGNAL_3 remains active
active SIGNAL_3 + new SIGNAL_2 → SIGNAL_3 remains active
active SIGNAL_2 + new SIGNAL_1 → SIGNAL_2 remains active
```

A higher-priority persistent condition may replace the visible active alert after the project state transition that raises it is checkpointed.

---

## 4. Persistent versus transient alerts

`SIGNAL_1` is transient.

`SIGNAL_2` and `SIGNAL_3` are persistent.

Checkpoint state therefore follows:

```text
CURRENT.activeAlert = null | SIGNAL_2 | SIGNAL_3
```

`SIGNAL_1` never remains as `CURRENT.activeAlert` after publication of the transition it accompanies.

Historical signal evidence remains available through checkpoint archive, handoffs, PR/commit evidence, or future append-only signal history if later introduced.

---

## 5. Canonical alert shape

R01 uses a structured machine-readable alert plus human-readable message.

Minimum persistent alert shape:

```json
{
  "signalId": "SIG-20260826T060000Z-001",
  "level": "SIGNAL_3",
  "class": "OWNER_ACTION",
  "status": "ACTIVE",
  "code": "OWNER_ACTION_REQUIRED",
  "summary": "Private runtime repository must be created",
  "raisedBy": "Duncan-Sparx-ZB",
  "raisedAt": "2026-08-26T06:00:00Z",
  "blocks": ["P1_RUNTIME_BOOTSTRAP"],
  "ownerActionRequired": true,
  "requiredAction": "Create PRIVATE Lester-Sparx/zorr-blatt-runtime",
  "evidence": [],
  "clearPolicy": "SPARX_ACTION_PLUS_GATE_HOLDER_VERIFICATION"
}
```

`signalId` is unique within project history and uses UTC time plus a deterministic local sequence suffix if more than one signal is raised at the same second.

Unknown exact values must be `null` or explicit unresolved values; they must never be guessed.

---

## 6. Signal classes

R01 class vocabulary:

```text
MILESTONE
ATTENTION
OWNER_ACTION
```

Mapping is fixed:

```text
SIGNAL_1 → MILESTONE
SIGNAL_2 → ATTENTION
SIGNAL_3 → OWNER_ACTION
```

Future presentation layers may use different labels or sounds, but the semantic mapping above remains authoritative for R01.

---

## 7. Code vocabulary

`code` is machine-readable and stable enough for future orchestration.

Initial allowed examples include:

```text
MILESTONE_ACCEPTED
MILESTONE_QC_PASS
MILESTONE_COMPLETE
MILESTONE_CHECKPOINT_PUBLISHED
MILESTONE_ACTIVATED
ATTENTION_BLOCKED
ATTENTION_FAIL
ATTENTION_CHANGES_REQUIRED
ATTENTION_EVIDENCE_MISMATCH
ATTENTION_CHECKPOINT_CONFLICT
ATTENTION_CHECKPOINT_STALE
OWNER_ACTION_REQUIRED
```

The exact code must describe the condition; generic codes such as `PROBLEM` are forbidden.

Adding new codes later does not require adding a new signal level.

---

## 8. Relationship to `ownerActionRequired`

`SIGNAL_3` and checkpoint owner-action state must never disagree.

Invariant:

```text
CURRENT.activeAlert.level == SIGNAL_3
→ ownerActionRequired.required == true
```

And:

```text
ownerActionRequired.required == true
for a currently blocking direct-SPARX condition
→ CURRENT.activeAlert.level == SIGNAL_3
```

A `SIGNAL_2` must not falsely claim direct owner action is required.

A `SIGNAL_1` does not set `ownerActionRequired`.

---

## 9. Checkpoint integration

The approved ZB Checkpoint System R01 is extended logically with:

```text
CURRENT.activeAlert
checkpointReason.signal
```

`CURRENT.activeAlert` contains only a currently persistent `SIGNAL_2` or `SIGNAL_3` condition, or `null`.

`checkpointReason.signal` may record the signal associated with the transition that produced the checkpoint, including transient `SIGNAL_1`.

Example:

```json
{
  "checkpointReason": {
    "kind": "QC_PASS",
    "source": "DUNCAN_QC",
    "signal": {
      "level": "SIGNAL_1",
      "code": "MILESTONE_QC_PASS"
    },
    "evidence": []
  }
}
```

---

## 10. Signal events that require a checkpoint

R01 treats persistent alert lifecycle changes as material project-state transitions.

Therefore:

```text
SIGNAL_2 ACTIVATED → NEW CHECKPOINT REQUIRED
SIGNAL_3 ACTIVATED → NEW CHECKPOINT REQUIRED
SIGNAL_2 CLEARED   → NEW CHECKPOINT REQUIRED
SIGNAL_3 CLEARED   → NEW CHECKPOINT REQUIRED
```

`SIGNAL_1` does not create a checkpoint by itself. It may only accompany a transition that was independently checkpoint-worthy.

---

## 11. Clear policy

Clear is explicit and evidence-backed.

General law:

```text
RAISED CONDITION
→ RESOLUTION ACTION
→ VERIFICATION
→ CLEAR
```

No alert disappears because a later successful event merely happened nearby in time.

### SIGNAL_1

No persistent clear is needed because `SIGNAL_1` is transient.

### SIGNAL_2

The actor responsible for verifying the blocker/fail condition may clear it only after evidence demonstrates resolution.

### SIGNAL_3

`SIGNAL_3` clear requires both:

```text
1. SPARX performs the required action.
2. The current gate-holder verifies exact evidence that the required condition is resolved.
```

Critical law:

```text
SPARX ACTION ≠ AUTOMATIC CLEAR.
ACTION → VERIFY → CLEAR.
```

---

## 12. Actor-scoped authority

Signal emission and clear authority may not exceed actor authority.

```text
SIGNAL AUTHORITY ≤ ACTOR AUTHORITY
```

Examples:

- Lester may raise an implementation blocker that is within his build scope but may not turn that signal into `QC_PASS` or architecture acceptance.
- Duncan may raise or clear technical QC alerts within his verification scope but may not impersonate Django or OWNER.
- Django may raise or clear architecture/governance alerts within architecture review scope but may not self-substitute for independent QC or OWNER.
- SPARX may perform owner-required actions, but a `SIGNAL_3` still requires gate-holder verification before clear when the governing rule requires independent verification.
- Salvador may raise visual/canon workflow alerts only within assigned visual/canon authority.

---

## 13. Handoff integration

`ZB_HANDOFF_V1` is extended logically with an optional `alert` field.

Example:

```json
{
  "alert": {
    "level": "SIGNAL_2",
    "code": "ATTENTION_BLOCKED",
    "status": "ACTIVE",
    "summary": "Candidate cannot proceed until evidence binding is corrected"
  }
}
```

The handoff alert describes the transferred work condition.

It may not self-promote into global project state. If it changes global state or persistent alert state, the corresponding checkpoint transition is required.

---

## 14. Resume protocol integration

On:

```text
<ROLE> — RESUME FROM ZB CHECKPOINT
```

the agent reads `CURRENT.activeAlert` after validating the checkpoint.

If `activeAlert == null`, no alert banner is emitted.

If `activeAlert.level == SIGNAL_2`, the RESUME REPORT must visibly include the active ATTENTION condition and its blocking scope.

If `activeAlert.level == SIGNAL_3`, the RESUME REPORT must visibly include:

```text
🚨 SPARX — ОТ ТЕБЯ НУЖНО ДЕЙСТВИЕ!!!
```

plus the exact required action and evidence state.

Resume never clears an alert and never creates authority.

---

## 15. Anti-spam law

Signals are not status decoration.

Do not emit a new signal for:

```text
ordinary assistant reply
routine tool read
branch creation
ordinary commit
CI starting
CI success without material governance transition
routine merge with no project-state change
status ping
draft brainstorming
re-reading known evidence
```

`SIGNAL_1` is restricted to checkpoint-worthy material milestones.

`SIGNAL_2` or `SIGNAL_3` is restricted to persistent material conditions that affect legal progress, evidence integrity, governance, or required owner action.

---

## 16. Deduplication law

An already-active material condition must not generate repeated equivalent signal spam.

Before raising a persistent alert, compare:

```text
level
code
blocking scope
required action, when applicable
```

If those identify the same unresolved condition, update only the evidence/status through the next legitimate checkpoint transition rather than creating a duplicate alert.

If a genuinely different higher-priority condition appears, normal priority replacement rules apply.

---

## 17. Multiple simultaneous conditions

R01 intentionally keeps only one `CURRENT.activeAlert`.

`CURRENT.activeAlert` is the highest-priority currently actionable notification, not the complete blocker registry.

Complete unresolved conditions continue to live in canonical fields such as `openBlockers`, `unresolved`, handoffs, and evidence bindings.

Selection rule:

```text
1. Highest signal level wins.
2. At equal level, prefer the condition that blocks the current phase or next legal transition.
3. If still equal, prefer the earlier raised condition.
4. If still equal, lexical signalId order is deterministic.
```

When the selected active condition is cleared, the next checkpoint recomputes `activeAlert` from remaining material conditions.

---

## 18. Failure consistency rules

The following states are invalid:

```text
SIGNAL_3 active + ownerActionRequired.required == false
SIGNAL_2 active claiming direct SPARX action is mandatory
SIGNAL_1 persisted as CURRENT.activeAlert
CLEARED alert still blocking next transition
lower-priority alert replacing unresolved higher-priority alert
alert code contradicting governance status
alert emitted as substitute for required ACCEPTED/QC/OWNER transition
```

A validator should classify these as signal/checkpoint consistency failures.

---

## 19. Human-readable rendering

Default text semantics:

```text
SIGNAL_1 / MILESTONE
BEEP
<material milestone summary>

SIGNAL_2 / ATTENTION
BEEP — BEEP
<blocking/attention summary>

SIGNAL_3 / OWNER ACTION
BEEP — BEEP — BEEP
🚨 SPARX — ОТ ТЕБЯ НУЖНО ДЕЙСТВИЕ!!!
<exact required action>
```

The words `BEEP` are semantic/rendering markers only in text chat. They do not claim that the client actually played audio.

---

## 20. Actual audio is downstream presentation

R01 does not define audio files, frequencies, codecs, volume, browser APIs, operating-system notification sounds, or device playback.

Future COMMS ORCHESTRATOR / UI mapping may define, for example:

```text
SIGNAL_1 → one short sound
SIGNAL_2 → two attention sounds
SIGNAL_3 → distinct urgent sound pattern
```

Such mapping is presentation behavior only and must not change semantic level, actor authority, checkpoint state, or governance meaning.

Law:

```text
AUDIO PRESENTATION MAY REPRESENT A SIGNAL.
AUDIO PRESENTATION MAY NOT REDEFINE THE SIGNAL.
```

---

## 21. Stable-doc integration target

When Phase A of the Checkpoint System is implemented, Signal Protocol R01 should be referenced where semantically appropriate:

- `docs/ZB_PROJECT_INDEX.md` — pointer to Signal Protocol R01 as part of project-memory/governance infrastructure.
- `docs/ZB_AGENT_ROLES.md` — actor-scoped signal and clear authority boundaries.
- `docs/ZB_MASTER_ROADMAP.md` — no operational alert state; at most a stable pointer if useful.
- Checkpoint System spec/protocol — `activeAlert`, checkpoint transition and resume behavior remain the operational integration point.

Do not turn stable docs into alert logs.

---

## 22. Initial checkpoint behavior

When the first `ZB_CHECKPOINT_CURRENT.json` is later created in Checkpoint Phase B, it must include:

```text
activeAlert: null
```

unless exact evidence at that time proves an unresolved `SIGNAL_2` or `SIGNAL_3` condition.

Do not reconstruct an alert merely from old chat memory.

If a direct owner action is actually required at that time and independently verified, the initial checkpoint may contain a `SIGNAL_3` with exact evidence and matching `ownerActionRequired` state.

---

## 23. Validation target

R01 validation should eventually verify at minimum:

```text
signal level vocabulary
level/class mapping
persistent-vs-transient rule
SIGNAL_3 ↔ ownerActionRequired consistency
priority replacement safety
clear actor/evidence requirements
no SIGNAL_1 persisted in activeAlert
handoff alert does not self-promote
resume rendering consistency
signal code is non-generic and machine-readable
no duplicate persistent signal for the same unresolved condition
```

Automation is not required for this spec candidate; these are governance/validation requirements for the Checkpoint System integration and later tooling.

---

## 24. Non-goals

Signal Protocol R01 does not:

```text
play actual sound
create audio assets
change ChatGPT client behavior
change browser notification settings
create runtime code
mutate hq/state
start P1 implementation
approve runtime work
activate production
create OWNER LOCK
unlock G2
unlock Voice-to-Shot
change actor identities
replace Checkpoint / Handoff / Resume governance
```

---

## 25. Final governing law

```text
SIGNAL_1 = TRANSIENT MATERIAL MILESTONE.
SIGNAL_2 = PERSISTENT ATTENTION / BLOCKER.
SIGNAL_3 = PERSISTENT SPARX ACTION REQUIRED.

SIGNAL_3 > SIGNAL_2 > SIGNAL_1.

CURRENT.activeAlert STORES ONLY SIGNAL_2 OR SIGNAL_3.

LOWER PRIORITY MAY NOT HIDE HIGHER PRIORITY.

PERSISTENT ALERT RAISE/CLEAR IS A CHECKPOINT TRANSITION.

SPARX ACTION ≠ AUTOMATIC CLEAR.
ACTION → VERIFY → CLEAR.

SIGNAL AUTHORITY ≤ ACTOR AUTHORITY.

SIGNAL ≠ GOVERNANCE VERDICT.
SIGNAL ≠ AUTHORIZATION.

SEMANTIC SIGNAL NOW.
ACTUAL AUDIO LATER.
```

P1 Runtime Bootstrap remains paused until the Checkpoint / Project Ledger system is operational. P1 implementation remains not authorized.