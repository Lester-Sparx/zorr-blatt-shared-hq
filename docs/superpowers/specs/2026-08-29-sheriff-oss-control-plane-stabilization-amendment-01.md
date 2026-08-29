# SHERIFF OSS Control Plane V1 — Stabilization Amendment 01

Status: IMPLEMENTATION BINDING for PR #170.

This amendment resolves the first live code-review findings and supersedes conflicting consequence values in the earlier design text. `docs/SHERIFF_POLICY_V1.md` is the canonical discipline policy.

## Canonical consequence table

- `I0_SELF_CAUGHT`: discipline `0`, gate `NONE`, merit may increase.
- `I1_CORRECTNESS`: base discipline `-2`, gate derived from current discipline band/repeat history.
- `I2_PROCESS`: base discipline `-5`, mandatory remediation + independent QC on repeat.
- `I3_CRITICAL_INTEGRITY`: discipline `-20`, execution `HOLD`, independent remediation/QC required. This is not an OWNER-only hard hold by default.
- `I4_SAFETY_SECURITY`: discipline `-40`, `HARD_HOLD`, OWNER action required for reinstatement.

## Runtime authority boundaries

- PostgreSQL is the operational source of truth for runtime events, verdicts, remediations, scores, ratings, outbox state, and dead letters.
- Git/Forgejo is the source of truth for code, policy, schemas, regression tests, review evidence, and portable exports.
- `SHERIFF_SCOREBOARD_V1.json` is a derived/bootstrap snapshot only.

## Reliability baseline

The V1 worker uses:
- Draft 2020-12 JSON Schema validation before OPA/DB mutation;
- immutable event-id/body-hash deduplication;
- transactional outbox for verdict publication;
- NATS `Nats-Msg-Id` on outbox publication;
- bounded push-consumer redelivery (`max_deliver=5`) with backoff;
- durable PostgreSQL dead-letter recording before terminal acknowledgement.

## Security baseline

For V1 local/self-hosted operation:
- NATS requires an authenticated SHERIFF user;
- NATS/OPA/PostgreSQL/OTel/Prometheus/Loki/worker metrics are Compose-internal only;
- only Forgejo and Grafana publish host ports;
- production secret hardening remains a deployment concern and is not implied by CI PASS.

No polling is introduced.
