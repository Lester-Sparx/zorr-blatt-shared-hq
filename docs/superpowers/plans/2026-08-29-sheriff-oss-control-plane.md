# SHERIFF OSS Control Plane V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a testable event-driven OSS SHERIFF control plane that records agent events, classifies incidents, tracks repeat errors, generates remediation paths, and maintains separate discipline/merit/Glicko-2 ratings.

**Architecture:** Reuse CloudEvents + NATS JetStream + OPA + PostgreSQL + OpenTelemetry/Prometheus/Loki/Grafana OSS + Forgejo. Keep custom Python as thin orchestration/core glue. CI validates OSS provenance, contracts, policy, compose topology, and regression behavior; production 24/7 activation is a separate physical-host gate.

**Tech Stack:** Python 3.12, JSON Schema documents, Rego, PostgreSQL SQL, Docker Compose, NATS JetStream, OPA, Forgejo 15.x LTS, Prometheus, Loki, Grafana OSS, OpenTelemetry Collector, `glicko2-py`.

**Spec:** `docs/superpowers/specs/2026-08-29-sheriff-oss-control-plane-design.md`

## Global Constraints

- OPEN-CODE-ONLY.
- Event-driven; no polling monitor loop.
- GitHub is development transport only; target forge is Forgejo.
- Honest FAIL is not a violation; FALSE PASS is critical.
- AUTHOR != QC != SHERIFF for the same incident; SHERIFF cannot self-judge.
- Safety gates outrank league rating.
- Reuse OSS components; custom code is glue only.
- CI PASS is not production-active proof.

---

### Task 1: OSS provenance and runtime topology

**Files:**
- Create: `config/sheriff/OPEN_SOURCE_COMPONENTS.json`
- Create: `config/sheriff/docker-compose.yml`
- Create: `config/sheriff/nats.conf`
- Create: `config/sheriff/otel-collector.yml`
- Create: `config/sheriff/prometheus.yml`
- Create: `config/sheriff/loki.yml`
- Create: `config/sheriff/grafana/provisioning/datasources/datasources.yml`
- Create: `requirements-sheriff.txt`
- Test: `tests/test_sheriff_oss_control_plane.py`

**Interfaces:**
- Consumes: approved OSS-only design.
- Produces: declarative stack/provenance contract used by all later tasks.

- [ ] **Step 1: Write failing provenance/topology tests**

Tests assert required components exist, every component has non-empty `source`, `license`, `runtimeRef`, `purpose`, all licenses are in an explicit OSI/open allow-list, no forbidden proprietary providers appear, Compose references only declared component images, NATS enables JetStream, and no polling scheduler is present.

- [ ] **Step 2: Run PR CI to verify RED**

Expected: new SHERIFF tests fail because the config files do not exist.

- [ ] **Step 3: Add minimal OSS manifest/topology**

Use declared OSS components only. Pin Forgejo to `15.0.7`; pin `glicko2-py==0.1.0`. Keep external image references explicit and centrally declared.

- [ ] **Step 4: Re-run SHERIFF tests**

Expected: provenance/topology tests PASS.

- [ ] **Step 5: Commit**

Commit message: `feat(sheriff): declare OSS runtime topology`.

---

### Task 2: Event contracts and fail-closed policy

**Files:**
- Create: `schemas/SHERIFF_AGENT_EVENT_V1.schema.json`
- Create: `config/sheriff/opa/sheriff.rego`
- Create: `config/sheriff/opa/sheriff_test.rego`
- Modify: `tests/test_sheriff_oss_control_plane.py`

**Interfaces:**
- Consumes: CloudEvents 1.0 envelope and SHERIFF policy.
- Produces: accepted event types and OPA decision object `{admit, incidentClass, disciplineDelta, meritDelta, hardHold, reason}`.

- [ ] **Step 1: Write failing event/policy tests**

Cover PASS-without-evidence rejection, honest FAIL admission with no automatic penalty, FALSE PASS/evidence substitution classification as `I3_CRITICAL_INTEGRITY`, SHERIFF self-judgement rejection, and unknown event type rejection.

- [ ] **Step 2: Verify RED**

Expected: tests fail because schema/Rego do not exist.

- [ ] **Step 3: Implement schema and Rego policy**

Do not duplicate rating math or database logic in Rego. Policy owns admission/classification/gating only.

- [ ] **Step 4: Verify local static tests plus OPA container test contract**

Expected: Python contract tests PASS; `opa test` command is representable in CI and Rego contains its own unit cases.

- [ ] **Step 5: Commit**

Commit message: `feat(sheriff): add CloudEvent and OPA policy contracts`.

---

### Task 3: Durable ledger and deterministic remediation core

**Files:**
- Create: `config/sheriff/postgres/001_sheriff.sql`
- Create: `scripts/sheriff_core.py`
- Create: `tests/test_sheriff_core.py`

**Interfaces:**
- Consumes: incident class, `agentId`, `errorSignature`, prior repeat count, policy score deltas.
- Produces: `body_hash(event) -> sha256`, `remediation_path(incident_class, repeat_count) -> tuple[str,...]`, `apply_discipline(score, delta) -> int`, `is_idempotent_replay(existing_hash, incoming_hash) -> bool`.

- [ ] **Step 1: Write failing core tests**

Tests prove identical replay is idempotent, same event id/different hash fails closed, score remains `[0,100]`, first/repeated/critical remediation escalates deterministically, and I0 does not impose a remediation hold.

- [ ] **Step 2: Verify RED**

Expected: import/file missing failures for `sheriff_core`.

- [ ] **Step 3: Implement minimal deterministic core and SQL schema**

Use Python standard library only in `sheriff_core.py`. PostgreSQL tables use primary/unique keys to enforce event/match idempotency and immutable verdict identity.

- [ ] **Step 4: Verify GREEN**

Run full unittest suite; expected all existing tests plus new core tests PASS.

- [ ] **Step 5: Commit**

Commit message: `feat(sheriff): add durable ledger and remediation core`.

---

### Task 4: Event-driven worker and Glicko-2 reuse

**Files:**
- Create: `scripts/sheriff_worker.py`
- Create: `tests/test_sheriff_worker_contract.py`
- Modify: `requirements-sheriff.txt`

**Interfaces:**
- Consumes: NATS subject `zb.>`, OPA HTTP decision endpoint, PostgreSQL DSN, event schema, `sheriff_core` helpers.
- Produces: durable event/incident/verdict/remediation records, derived score updates, league rating updates, emitted `zb.sheriff.verdict` CloudEvents.

- [ ] **Step 1: Write failing worker-contract tests**

Static/behavioral tests assert durable JetStream consumer with explicit ack, DB insert before ack, OPA decision required before incident mutation, duplicate body-hash handling, no polling/sleep loop, external `glicko2` import, and safety gate before rating update.

- [ ] **Step 2: Verify RED**

Expected: worker file missing.

- [ ] **Step 3: Implement thin worker**

Use `nats-py`, Psycopg 3, `glicko2-py`, and `prometheus-client`; use standard-library HTTP for OPA. Do not reimplement NATS/Postgres/Glicko internals.

- [ ] **Step 4: Compile and run contract tests**

Expected: worker compiles and contract tests PASS. Network integration stays behind runtime configuration and is not required for the existing repository unit suite.

- [ ] **Step 5: Commit**

Commit message: `feat(sheriff): add event-driven OSS worker`.

---

### Task 5: Validator, dashboard provisioning, and CI gate

**Files:**
- Create: `scripts/sheriff_validate.py`
- Create: `config/sheriff/grafana/provisioning/dashboards/dashboards.yml`
- Create: `config/sheriff/grafana/dashboards/sheriff-overview.json`
- Create: `.github/workflows/sheriff-oss-validate.yml`
- Modify: `AGENTS.md`
- Modify: `tests/test_sheriff_oss_control_plane.py`

**Interfaces:**
- Consumes: all SHERIFF config/contracts.
- Produces: one fail-closed validation command and CI evidence for OSS provenance, Python tests/compile, Compose parse, and OPA tests.

- [ ] **Step 1: Write failing validator/AGENTS tests**

Require AGENTS restart map to point to operational control-plane spec, OSS manifest, and event-driven/no-polling rule. Validator must reject missing/unknown/proprietary components and inconsistent Compose image references.

- [ ] **Step 2: Verify RED**

Expected: validator/dashboard/workflow missing.

- [ ] **Step 3: Implement validator/dashboard/CI**

CI runs existing `hq_validate.py` + full unittest suite, `python3 scripts/sheriff_validate.py`, Python compile, `docker compose ... config`, and OPA policy tests using the declared OPA image.

- [ ] **Step 4: Fresh full verification**

Required evidence: `hq-validate` SUCCESS and `sheriff-oss-validate` SUCCESS on exact final HEAD.

- [ ] **Step 5: Fresh read-back and PR evidence**

Read exact HEAD copies of spec, manifest, event schema, OPA policy, SQL, worker, validator, dashboard, requirements, and AGENTS. Record final HEAD + workflow run IDs in PR body/comment.

- [ ] **Step 6: Do not claim production active**

Final implementation status may be `SHERIFF_OSS_CONTROL_PLANE_V1 = PASS`. Production activation remains blocked until a persistent host proves all services healthy and a real end-to-end event updates the ledger/scoreboard.