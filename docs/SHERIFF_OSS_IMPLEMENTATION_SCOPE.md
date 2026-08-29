# SHERIFF OSS Implementation Scope Lock

This implementation is limited to the operational control-plane V1 vertical slice defined by the approved design.

IN SCOPE: OSS provenance, event contract, NATS/JetStream topology, OPA policy, PostgreSQL ledger schema, deterministic remediation core, thin event-driven worker, Glicko-2 library integration contract, observability provisioning, validation/CI.

OUT OF SCOPE: migrating existing repositories from GitHub to Forgejo, provisioning a physical always-on host, changing ZORR production model/Controller/SALVADOR locks, or claiming 24/7 production activation without host evidence.
