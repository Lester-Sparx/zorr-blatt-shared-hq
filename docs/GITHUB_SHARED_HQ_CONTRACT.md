# GITHUB SHARED HQ — CONTRACT v0

This repository is an external transport and persistence adapter around the
immutable Control Tower v1 artifact pinned in
`hq/policy/control-tower-v1.lock.json`.

Authority boundaries:

```text
ZB CORE / LOCKED ARTIFACTS = production source-of-truth
CONTROL TOWER v1           = immutable enforcement semantics
protected GitHub main      = shared authoritative control/workflow state
dashboard                  = read-only projection
```

The adapter may store task ids, revisions, commit ids, artifact hashes, review
hashes and lock evidence. It must not store or drive mechanics, timing, camera,
set, animation, weapon, contact, plate or rendering values.

The current gate is only `GITHUB_SHARED_HQ`. `G2` and `VOICE_TO_SHOT` remain
blocked. A QC PASS never creates a LOCK. LOCK requires a separate legal OWNER
logical-role transition after bound Duncan QC PASS and Django architecture
ACCEPTED.

## Single-account authority migration R01

For this Shared HQ adapter, the former role-specific GitHub-login model is
superseded. `Lester-Sparx` is the approved GitHub transport identity. LESTER,
DUNCAN, DJANGO, JINGO and OWNER are logical protocol roles; GitHub actor proves
transport provenance only and never proves a logical role.

Role authority requires the protected-base validator to confirm the legal
transition order, exact base/revision CAS and exact task/candidate/artifact/evidence
bindings. Historical records using `builderGitHubLogin`, `reviewerGitHubLogin` or
`ownerGitHubLogin` remain immutable historical provenance and are not rewritten.
