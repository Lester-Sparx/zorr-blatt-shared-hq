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
| Runtime schema validation | python-jsonschema | MIT |
| Telemetry convention | OpenTelemetry | Apache-2.0 |
| Metrics | Prometheus | Apache-2.0 |
| Logs | Loki | AGPL-3.0 |
| Dashboard | Grafana OSS | AGPL-3.0 |
| Skill rating | `glicko2-py==0.1.0` | MIT |
| NATS Python client | `nats-py` | Apache-2.0 |
| PostgreSQL Python client | Psycopg 3 | LGPL-3.0-only |

Every runtime component must also appear in `config/sheriff/OPEN_SOURCE_COMPONENTS.json` with source URL, license, image/package reference, and purpose. A proprietary/unknown-license component fails validation, and the Compose image set must match the declared runtime image set exactly.

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
  1. validate envelope + event data against JSON Schema Draft 2020-12
  2. ask OPA for policy decision
  3. insert immutable event id (dedupe key)
  4. derive repeat count from durable ledger
  5. create immutable verdict when incident exists
  6. derive remediation path and score/gate projection
  7. enqueue follow-up verdict in the same PostgreSQL transaction
  8. commit durable state
  9. publish transactional outbox, then explicit-ack source event
        |
        +--> PostgreSQL authoritative ledger + outbox + dead letters
        +--> Prometheus / Loki / Grafana
```

No timer is required to discover agent mistakes. Agent/QC/automation results are events. JetStream retention plus durable consumers provides replay after SHERIFF downtime. Poison events use bounded redelivery and durable dead-letter recording.

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

PostgreSQL owns operational runtime truth. Core tables:

- `sheriff_events` — immutable raw normalized events, primary key `event_id`.
- `sheriff_incidents` — incident identity, agent, error signature, class, repeat count.
- `sheriff_verdicts` — immutable SHERIFF decisions and score deltas.
- `sheriff_remediations` — required learning/fix path and completion state.
- `sheriff_agent_scores` — derived current discipline/merit state.
- `sheriff_skill_ratings` — current Glicko-2 values.
- `sheriff_league_matches` — comparable evaluated matches.
- `sheriff_outbox` — durable follow-up events pending/recording publication.
- `sheriff_dead_letters` — terminal poison-event evidence after bounded redelivery.

Git/Forgejo owns code, policy, schemas, regression tests, review evidence, and portable exports. Existing `hq/sheriff/SHERIFF_SCOREBOARD_V1.json` remains a neutral bootstrap/portable snapshot, not an append-only runtime ledger.

## Discipline policy

`docs/SHERIFF_POLICY_V1.md` is canonical. OPA implements that policy; the worker applies the returned gate plus score-band/repeat restrictions.

Base incident classes:

- `I0_SELF_CAUGHT`: no discipline loss; merit may increase when the agent detects/correctly reports before handoff.
- `I1_CORRECTNESS`: ordinary technical error; base discipline delta `-2`.
- `I2_PROCESS`: procedure/scope/reuse/verification violation; base delta `-5`.
- `I3_CRITICAL_INTEGRITY`: FALSE PASS, evidence substitution/fabrication; base delta `-20`, execution `HOLD` until independent remediation/QC clears it.
- `I4_SAFETY_SECURITY`: safety/security/authority boundary breach; base delta `-40`, `HARD_HOLD`; OWNER action is required for reinstatement.

Repeat history strengthens required controls for the same `(agentId,errorSignature)` without allowing one ordinary incident to underflow the score below zero. Discipline score bands independently raise the minimum execution gate.

## Remediation path

Every non-I0 incident yields a durable remediation path.

- first occurrence: root-cause note + regression test + fresh verification;
- first repeat: mandatory preflight/regression gate + independent QC;
- second-or-later repeat: restricted similar work + independent QC before handoff;
- I3: execution HOLD + evidence review + remediation proof + independent QC;
- I4: HARD_HOLD + evidence review + remediation proof + independent QC + OWNER reinstatement.

Learning is therefore generated from error history instead of simply subtracting points.

## Skill / competition rating

Skill rating uses the external open-source `glicko2-py` library. No local reimplementation of Glicko-2 math.

League updates are admitted only when:

1. the task/eval is comparable for both competitors;
2. both result records have evidence;
3. safety/QC gate passed;
4. neither competitor is under an active restrictive/hold gate;
5. the match id was not previously applied.

Stored fields: rating, rating deviation, volatility, rated match count. Discipline score never enters the Glicko calculation; it only gates whether a match may be rated.

## Runtime glue boundaries

Custom Python is intentionally small:

- `scripts/sheriff_core.py`: deterministic incident/repeat/remediation helpers; no transport.
- `scripts/sheriff_worker.py`: NATS -> OPA -> PostgreSQL orchestration; uses OSS client libraries.
- `scripts/sheriff_validate.py`: offline fail-closed configuration/provenance validation.

The worker must not implement a custom message broker, policy language, database, telemetry backend, dashboard, Git forge, JSON-Schema engine, or Glicko algorithm.

## Security baseline

V1 requires authenticated NATS access. Internal NATS, OPA, PostgreSQL, OpenTelemetry, Prometheus, Loki, and worker-metrics endpoints remain Compose-internal; only Forgejo and Grafana publish host ports. Fine-grained producer identities/ACLs and production secret provisioning are deployment hardening steps and must not break JetStream control subjects in the V1 bootstrap.

## Observability

Minimum exported metrics:

- `zb_sheriff_events_total{type}`
- `zb_sheriff_incidents_total{agent,class}`
- `zb_sheriff_repeat_incidents_total{agent}`
- `zb_sheriff_discipline_score{agent}`
- `zb_sheriff_active_holds{agent}`
- `zb_sheriff_verdict_latency_seconds`

Grafana may read Prometheus and PostgreSQL. Loki/OpenTelemetry remain optional observability layers for the initial base and are not authorities over verdict/score state.

## Failure behavior

Fail closed on:

- malformed/unknown event type or schema-invalid data;
- duplicate event id with different body hash;
- PASS without evidence;
- OPA unavailable or invalid decision;
- database unavailable;
- SHERIFF self-judgement;
- rating update without safety gate;
- unknown/non-OSS runtime dependency in manifest;
- poison events after bounded retries are preserved in the durable dead-letter ledger.

A duplicate event with the same body hash is an idempotent replay and must not change ratings/scores twice. Verdict publication uses a transactional outbox so a process crash between ledger commit and broker publication can be replayed without creating a second verdict.

## Verification gates

CI PASS requires:

1. existing `hq-validate` full suite remains green;
2. contract tests prove event validation, evidence requirement, dedupe, score/gate and remediation invariants;
3. provenance validator proves every runtime image/package is declared OSS and Compose images match the manifest;
4. Docker Compose parses successfully;
5. OPA policy tests pass;
6. Python worker/core compile with pinned runtime dependencies;
7. exact branch read-back proves all required artifacts.

`SHERIFF_OSS_CONTROL_PLANE_V1 = PASS` means implementation/CI PASS only.

`SHERIFF_OSS_CONTROL_PLANE_V1_PRODUCTION_ACTIVE = YES` requires separate physical evidence from a continuously running host: healthy Forgejo/NATS/OPA/PostgreSQL/worker, durable event/replay/outbox/dead-letter proof, and at least one end-to-end agent incident/score update.
