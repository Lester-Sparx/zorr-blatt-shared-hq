# ZORR BLATT SHERIFF OSS Control Plane — Design

Status: APPROVED FOR IMPLEMENTATION by OWNER instruction `ДЕЛАЙ ДО PASS` after OSS-only requirement.

## Goal

Build an event-driven, self-hostable, open-source control plane that continuously records agent activity, classifies errors, tracks repeat failures, updates discipline/merit/skill ratings, and produces evidence-bound remediation paths without polling.

`24/7 ACTIVE` is a deployment state and is not implied by CI PASS. CI PASS proves the control-plane code/config/contracts; continuous operation requires an always-on host running the stack.

## Hard constraints

- OPEN-CODE-ONLY for the control plane and runtime dependencies.
- Event-driven only; no polling loop for agent monitoring.
- GitHub is a temporary development transport, not the target runtime authority.
- Target Git forge: Forgejo.
- Every event is durable, replayable, deduplicated, and evidence-bound.
- Honest FAIL/BLOCKED is not a discipline violation.
- FALSE PASS / substituted evidence is critical.
- AUTHOR != QC != SHERIFF for the same incident.
- SHERIFF cannot self-judge.
- Discipline and skill ratings remain separate.
- Safety gates outrank league points.
- Reuse existing OSS components before custom code; custom code is glue only.

## Reused OSS stack

| Responsibility | Component | License policy |
| --- | --- | --- |
| Git forge / PR / Actions | Forgejo 15.x LTS | GPL-3.0-or-later |
| Event envelope | CNCF CloudEvents 1.0 | open specification / SDK ecosystem |
| Event bus / replay / durable consumer | NATS + JetStream | Apache-2.0 |
| Policy decisions | Open Policy Agent / Rego | Apache-2.0 |
| Durable ledger | PostgreSQL | PostgreSQL License |
| Telemetry convention | OpenTelemetry | Apache-2.0 |
| Metrics | Prometheus | Apache-2.0 |
| Logs | Loki | AGPL-3.0 |
| Dashboard | Grafana OSS | AGPL-3.0 |
| Skill rating | `glicko2-py==0.1.0` | MIT |
| NATS Python client | `nats-py` | Apache-2.0 |
| PostgreSQL Python client | Psycopg 3 | LGPL-3.0-only |

Every runtime component must also appear in `config/sheriff/OPEN_SOURCE_COMPONENTS.json` with source URL, license, image/package reference, and purpose. A proprietary/unknown-license component fails validation.

## Event flow

```text
AGENT / QC / SHERIFF / LEAGUE producer
        |
        | CloudEvent 1.0
        v
NATS JetStream  (stream ZB_AGENT_EVENTS, subject zb.>)
        |
        | durable consumer sheriff-v1 / explicit ack
        v
SHERIFF WORKER
  1. validate envelope + event data
  2. insert immutable event id (dedupe key)
  3. ask OPA for policy decision
  4. derive repeat count from durable ledger
  5. create immutable verdict when incident exists
  6. derive remediation path
  7. update derived discipline/merit view
  8. process league match only after safety gate
  9. emit metrics and follow-up CloudEvent
        |
        +--> PostgreSQL authoritative ledger
        +--> Prometheus / Loki / Grafana
```

No timer is required to discover agent mistakes. Agent/QC/automation results are events. JetStream retention plus durable consumers provides replay after SHERIFF downtime.

## Event contract

`schemas/SHERIFF_AGENT_EVENT_V1.schema.json` defines a CloudEvents 1.0 JSON envelope. Required top-level fields:

- `specversion = "1.0"`
- `id` — immutable dedupe key
- `source`
- `type`
- `subject`
- `time`
- `datacontenttype = "application/json"`
- `data`

Initial event types:

- `zb.agent.task.started`
- `zb.agent.result`
- `zb.agent.qc`
- `zb.sheriff.verdict`
- `zb.league.match`

Result/QC data binds `agentId`, `taskRef`, `executionId`, `status`, `evidence`, and optional `errorSignature`. `status=PASS` without evidence is rejected.

## Ledger

PostgreSQL owns runtime truth. Core tables:

- `sheriff_events` — immutable raw normalized events, primary key `event_id`.
- `sheriff_incidents` — incident identity, agent, error signature, class, repeat count.
- `sheriff_verdicts` — immutable SHERIFF decisions and score deltas.
- `sheriff_remediations` — required learning/fix path and completion state.
- `sheriff_agent_scores` — derived current discipline/merit state.
- `sheriff_skill_ratings` — current Glicko-2 values.
- `sheriff_league_matches` — comparable evaluated matches.

Existing `hq/sheriff/SHERIFF_SCOREBOARD_V1.json` remains a neutral bootstrap/portable snapshot, not an append-only runtime ledger.

## Discipline policy

OPA owns classification/gating, not the worker.

Base incident classes:

- `I0_SELF_CAUGHT`: no discipline loss; merit may increase when the agent detects/correctly reports before handoff.
- `I1_CORRECTNESS`: ordinary technical error; base discipline delta `-2`.
- `I2_PROCESS`: procedure/scope/reuse/verification violation; base delta `-5`.
- `I3_CRITICAL_INTEGRITY`: FALSE PASS, evidence substitution/fabrication; base delta `-20`, hard hold.
- `I4_SAFETY_SECURITY`: safety/security boundary breach; base delta `-25`, hard hold.

Repeat multipliers are derived from prior verdicts for the same `(agentId,errorSignature)` and are capped so one ordinary incident cannot underflow the score below zero.

## Remediation path

Every non-I0 incident yields a durable remediation path.

- first occurrence: root-cause note + regression test + fresh verification;
- first repeat: mandatory preflight/regression gate before similar work;
- second-or-later repeat: restricted gate + independent QC before handoff;
- I3/I4: hard hold, evidence review, remediation proof, independent QC, OWNER reinstatement where repository policy requires it.

Learning is therefore generated from error history instead of simply subtracting points.

## Skill / competition rating

Skill rating uses the external open-source `glicko2-py` library. No local reimplementation of Glicko-2 math.

League updates are admitted only when:

1. the task/eval is comparable for both competitors;
2. both result records have evidence;
3. safety/QC gate passed;
4. neither competitor is under a hard hold;
5. the match id was not previously applied.

Stored fields: rating, rating deviation, volatility, rated match count. Discipline score never enters the Glicko calculation; it only gates whether a match may be rated.

## Runtime glue boundaries

Custom Python is intentionally small:

- `scripts/sheriff_core.py`: deterministic incident/repeat/remediation helpers; no transport.
- `scripts/sheriff_worker.py`: NATS -> OPA -> PostgreSQL orchestration; uses OSS client libraries.
- `scripts/sheriff_validate.py`: offline fail-closed configuration/provenance validation.

The worker must not implement a custom message broker, policy language, database, telemetry backend, dashboard, Git forge, or Glicko algorithm.

## Observability

Minimum exported metrics:

- `zb_sheriff_events_total{type}`
- `zb_sheriff_incidents_total{agent,class}`
- `zb_sheriff_repeat_incidents_total{agent}`
- `zb_sheriff_discipline_score{agent}`
- `zb_sheriff_active_holds{agent}`
- `zb_sheriff_consumer_lag`
- `zb_sheriff_verdict_latency_seconds`

Grafana dashboard reads Prometheus and PostgreSQL. Loki receives service logs. OpenTelemetry resource attributes include `service.name=zb-sheriff` and execution/task identifiers where available.

## Failure behavior

Fail closed on:

- malformed/unknown event type;
- duplicate event id with different body hash;
- PASS without evidence;
- OPA unavailable or invalid decision;
- database unavailable;
- SHERIFF self-judgement;
- rating update without safety gate;
- unknown/non-OSS runtime dependency in manifest.

A duplicate event with the same body hash is an idempotent replay and must not change ratings/scores twice.

## Verification gates

CI PASS requires:

1. existing `hq-validate` full suite remains green;
2. contract tests prove event validation, evidence requirement, dedupe and score/remediation invariants;
3. provenance validator proves every declared component is OSS and rejects proprietary/unknown entries;
4. Docker Compose parses successfully;
5. OPA policy tests pass;
6. Python worker/core compile;
7. exact branch read-back proves all required artifacts.

`SHERIFF_OSS_CONTROL_PLANE_V1 = PASS` means implementation/CI PASS only.

`SHERIFF_OSS_CONTROL_PLANE_V1_PRODUCTION_ACTIVE = YES` requires separate physical evidence from a continuously running host: healthy Forgejo/NATS/OPA/PostgreSQL/worker/Prometheus/Loki/Grafana, durable event replay proof, and at least one end-to-end agent incident/score update.