# SHERIFF OSS Component Research Basis

This note records the reuse-first basis for the operational control plane.

- Forgejo: self-hosted Git forge, GPL-3.0-or-later from v9 onward. V15 is the current LTS line; v15.0.7 was released 2026-08-20 and is supported through 2027-07-15.
- Open Policy Agent: open-source general-purpose policy engine, Apache-2.0.
- `glicko2-py==0.1.0`: MIT-licensed Python Glicko-2 implementation released 2026-04-01, Python >=3.11, zero dependencies. We reuse it rather than reimplement rating mathematics.
- Psycopg 3: PostgreSQL driver, LGPL-3.0-only.
- NATS / JetStream, OpenTelemetry Collector, Prometheus: Apache-2.0 families.
- PostgreSQL: PostgreSQL License.
- Loki and Grafana OSS: AGPL-3.0 family.

The machine-readable authoritative runtime provenance list is `config/sheriff/OPEN_SOURCE_COMPONENTS.json`; this prose file is explanatory only.
