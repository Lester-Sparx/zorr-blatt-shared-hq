# LESTER OSS Eval R01

Tracker: #216

This base proves one narrow boundary only:

`existing LESTER -> Inspect AI objective eval -> existing SHERIFF result event contract`.

It does not create a new agent, scorer, training framework, scheduler, database, archive, rating engine, or SHERIFF implementation.

## Upstream

- Framework: Inspect AI
- Repository: `UKGovernmentBEIS/inspect_ai`
- Exact ref: `fbee5b35c656f1c7653af3adf682172033ee0590`
- License: MIT
- R01 evaluator: Inspect `Task` + `Sample` + `generate()` + `match()` + `eval()` using built-in `mockllm/model` for a deterministic zero-API smoke.

Inspect Evals and SWE-Gym are the approved real-task expansion path after this base passes. SWE-smith task synthesis and mini-swe-agent control competition are not part of R01.

## Evidence semantics

The bridge emits an existing `SHERIFF_AGENT_EVENT_V1` `zb.agent.result` envelope only after Inspect completes. `verifiedPass=true` requires Inspect status `success` and Inspect's own correct scorer value.

The event records exact candidate HEAD, GitHub Actions run/attempt, exact Inspect upstream ref, Inspect log location and score.

## Learning law

A single successful eval is never `PROVEN`.

R01 emits:

- `skillStateAfter = PARTIAL_ONLY`
- `transferRequired = true`
- `historicalBackfill = false`
- `disciplineAffectsCompetence = false`

A later skill promotion requires a changed/unseen transfer task with fresh objective evidence and the existing independent gates.
