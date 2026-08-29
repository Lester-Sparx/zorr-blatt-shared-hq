# ZORR BLATT — SHERIFF POLICY V1

Status: **PROPOSED / QC REQUIRED** until this PR is merged to `main`.

This policy defines the durable safety, discipline, learning, and competitive-rating system for ZORR BLATT agents. GitHub evidence remains authoritative; chat memory never is.

## 1. Non-negotiable laws

1. **HONEST FAIL IS NOT A VIOLATION.** A truthful BLOCKED/FAIL with exact evidence is preferable to an unsupported PASS.
2. **FALSE PASS** is a critical integrity incident. Fabricated, stale, substituted, or unverified evidence is treated the same way.
3. **REUSE-FIRST.** Before new infrastructure or custom code, agents must search existing repository code, native platform mechanisms, maintained open-source components, and upstream-supported patterns. Custom code is the smallest necessary glue.
4. **AUTHOR != QC != SHERIFF.** The author does not independently approve its own work. QC does not issue a SHERIFF verdict on its own incident. SHERIFF does not judge its own incident.
5. Safety and discipline gates outrank league points, speed, elegance, and competitive rating.
6. Every incident receives a durable SHERIFF verdict or an explicit `NO_VERDICT_EVIDENCE` finding when evidence is insufficient.
7. Historical incidents are never silently backfilled into ratings. Bootstrap scores are neutral unless a durable verdict explicitly changes them.

## 2. Roles

- **AGENT** — performs the assigned work and reports evidence-bound results.
- **QC** — independently recomputes or re-runs verification against the exact candidate and bindings.
- **SHERIFF** — classifies an incident, determines discipline consequences, requires remediation, and closes the learning loop.
- **ARCHIVE** — preserves immutable/raw evidence and durable verdict records. It does not reinterpret evidence.
- **LEAGUE** — updates skill ratings only from comparable evaluated matches after safety gates pass.
- **OWNER** — human-only authority for repository gates that already require owner authorization and for reinstatement from a hard hold.

A transport identity is not a logical role. Existing repository identity-separation rules remain authoritative.

## 3. Two independent score systems

### 3.1 Discipline score

`discipline.score` is bounded from `0` to `100` and starts at `100` for a neutral bootstrap.

It measures process discipline and trustworthiness: evidence quality, adherence to scope/LOCKS, required verification, truthful PASS/FAIL reporting, rollback discipline, and reuse-first behavior.

It does **not** measure raw technical skill.

Operational bands:

- `GREEN` = 90–100: normal execution gates.
- `YELLOW` = 75–89: heightened independent QC; no relaxed verification.
- `ORANGE` = 50–74: restricted autonomous execution; terminal PASS requires explicit independent QC evidence.
- `RED` = 0–49: execution hold. Reinstatement requires OWNER authorization plus completed remediation evidence.

### 3.2 Merit points

`discipline.meritPoints` is cumulative and cannot cancel a safety violation. It rewards behavior that improves the whole system, including:

- self-detection before handoff;
- reusable regression tests from real incidents;
- evidence-preserving rollback;
- finding a systemic defect before it affects other agents;
- replacing custom glue with a safer proven/native mechanism.

### 3.3 Skill rating

Skill is stored separately using a Glicko-2-compatible tuple:

- rating: `1500` neutral bootstrap;
- rating deviation: `350` bootstrap uncertainty;
- volatility: `0.06` bootstrap value;
- rated matches: `0`.

Ordinary incidents do not directly modify skill rating. LEAGUE updates skill only from comparable tasks with the same task contract, bounded inputs, independent judging, and hidden/independent acceptance evidence.

A safety-gate failure loses the match regardless of output quality.

## 4. Incident classes and default discipline ranges

The ranges are defaults; SHERIFF must justify the exact delta from evidence. Repeated incidents with the same root-cause signature escalate at least one class unless the earlier remediation was not yet available to the agent.

| Class | Meaning | Typical examples | Default discipline delta | Gate |
| --- | --- | --- | ---: | --- |
| `I0_SELF_CAUGHT` | Correctly self-detected before terminal handoff | agent finds its own defect, reports it, fixes it, adds regression | 0 | none; merit may increase |
| `I1_CORRECTNESS` | Ordinary correctness error with truthful reporting | wrong assumption, bad parsing, missed edge case | -1 to -3 | remediation |
| `I2_PROCESS` | Required process/verification discipline was skipped or a learned error repeated | skipped fresh verification, ignored reuse-first, repeated known root cause | -5 to -10 | remediation + independent QC |
| `I3_CRITICAL_INTEGRITY` | Trust boundary or truthfulness failure | FALSE PASS, evidence fabrication/substitution, unauthorized LOCK/scope breach | -20 | execution HOLD until independent QC clears remediation |
| `I4_SAFETY_SECURITY` | Severe safety/security/authority breach | destructive out-of-scope action, secret exposure, bypass of a human-only gate | -40 | HARD_HOLD + OWNER action required |

SHERIFF may choose `0` discipline delta for a proven environment/upstream failure that the agent reported correctly and could not reasonably prevent.

## 5. Required verdict contract

Every durable verdict is stored as one JSON document under:

`hq/sheriff/verdicts/<VERDICT_ID>.json`

and must validate against:

`schemas/SHERIFF_VERDICT_V1.schema.json`

At minimum it binds:

- immutable `verdictId`;
- affected `agentId` and logical role;
- task/correlation reference;
- incident class;
- one or more durable evidence references;
- exact error/root-cause description and reusable error signature;
- whether the agent self-caught it;
- whether it repeats an earlier verdict;
- SHERIFF decision and score deltas;
- required remediation, regression test, and lesson reference;
- lifecycle status;
- issuer identity and timestamp.

No evidence means no invented verdict: record `NO_VERDICT_EVIDENCE` at the task/tracker layer and fail closed until evidence exists.

## 6. Learning loop

Every agent-error path follows exactly:

`ERROR -> EVIDENCE -> ROOT CAUSE -> SHERIFF VERDICT -> REPAIR -> REGRESSION TEST -> LESSON`

Closure requirements:

1. The original symptom is reproducible or its evidence is preserved.
2. Root cause is stated at the earliest controllable layer, not merely the visible symptom.
3. Repair is the smallest change that addresses that root cause.
4. A regression test must fail before the repair and pass after it when technically possible.
5. The lesson is reusable and names the error signature/pattern.
6. Scoreboard changes occur only from a valid verdict.
7. The scoreboard is derived state and must remain rebuildable from verdict history.

## 7. Competition / agent league gate

Future agent-vs-agent competition must use:

1. identical task contract and authority boundaries;
2. isolated candidates;
3. hidden or independently controlled acceptance evidence;
4. no self-grading;
5. independent QC before a rated result;
6. safety/discipline gate before quality scoring;
7. Glicko-2-style update only after the result is accepted.

Agents may optimize quality, speed, reuse, and maintainability only inside the safety envelope. Reward hacking, hiding FAILs, weakening tests, or gaming the judge is an `I3_CRITICAL_INTEGRITY` incident at minimum.

## 8. SHERIFF decision rules

SHERIFF must:

- prefer durable raw evidence over summaries;
- distinguish a system defect from an agent defect;
- credit self-reporting before handoff;
- penalize repeated learned failures more than first-time honest mistakes;
- never increase discipline because an agent reported a real FAIL;
- never let merit points erase an active HOLD/HARD_HOLD;
- require independent QC for closing I2+ incidents;
- require OWNER action for release from an I4 hard hold;
- issue no verdict on itself; another independent SHERIFF/QC authority must handle that incident.

## 9. Scoreboard

Current derived scoreboard:

`hq/sheriff/SHERIFF_SCOREBOARD_V1.json`

Neutral bootstrap does not assert historical performance. Future changes must cite verdict IDs. If scoreboard state conflicts with durable verdict history, verdict history wins and the scoreboard must be rebuilt.

## 10. Provenance / reuse basis

This policy deliberately reuses established patterns instead of inventing a punitive scoring system from scratch:

- Just Culture / safety reporting: FAA safety-culture and reporting principles;
- learning from incidents: NASA lessons-learned and safety practice;
- lifecycle risk governance: NIST AI Risk Management Framework;
- uncertainty-aware competitive rating: Glicko/Glicko-2 rating methodology.

These are design influences, not external authorities over repository-specific OWNER/LOCK rules.

## 11. Activation gate

`SHERIFF_POLICY_V1 = ACTIVE` only when all of the following are true on the exact candidate:

- this policy exists and contains the non-negotiable laws;
- verdict schema parses and exposes all required incident classes;
- neutral scoreboard parses and separates discipline from skill;
- `AGENTS.md` points new/restarted agents to this policy and scoreboard;
- repository validation + full unittest suite PASS on the PR;
- fresh GitHub read-back matches the PR HEAD.

Until then, status is PROPOSED and no PASS may be claimed.
