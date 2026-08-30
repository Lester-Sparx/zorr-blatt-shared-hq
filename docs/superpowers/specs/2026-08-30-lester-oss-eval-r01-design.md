# LESTER OSS Eval R01 — Design

Status: OWNER-APPROVED R02 BASE CANDIDATE
Tracker: #216
Base main: `b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1`

## Goal

Prove the smallest real OSS evaluation boundary for DUNCAN PRIME teaching LESTER without building a ZORR-specific eval, scoring, training, memory, scheduler, or agent framework.

## Critical path

`DUNCAN PRIME -> existing LESTER execution surface -> Inspect AI -> existing SHERIFF event contract -> existing Permanent Archive / verified learning -> DUNCAN PRIME`

SWE-Gym / Inspect Evals are the approved real-task expansion path after this base smoke. SWE-smith and mini-swe-agent remain later bounded slices.

## Upstream pin

Inspect AI repository: `UKGovernmentBEIS/inspect_ai`
Exact upstream ref: `fbee5b35c656f1c7653af3adf682172033ee0590`
License: MIT

R01 installs Inspect AI from that exact Git commit in a dedicated GitHub Actions smoke job. The smoke uses Inspect's own `Task`, `Sample`, `generate`, `match`, `eval`, `EvalLog`, and built-in `mockllm/model`; ZORR does not implement a scorer.

## Minimal ZORR glue

One small bridge script may:

1. create a deterministic one-sample Inspect smoke task;
2. run it through Inspect with `mockllm/model`;
3. require a successful Inspect log and Inspect `CORRECT` score;
4. map that upstream result into the existing `SHERIFF_AGENT_EVENT_V1` `zb.agent.result` envelope;
5. mark the single successful smoke as `PARTIAL_ONLY` with `transferRequired=true` and `historicalBackfill=false`.

The bridge must not assign Glicko ratings, discipline deltas, verdicts, PROVEN skill, curriculum scores, or historical competence.

## Evidence boundary

The emitted result binds:
- LESTER;
- issue #216 task reference;
- candidate `GITHUB_SHA`;
- exact Inspect upstream ref;
- Inspect log location;
- upstream score value;
- `verifiedPass=true` only when Inspect itself reports success + CORRECT.

The existing SHERIFF JSON Schema validates the event. SHERIFF policy/runtime remains unchanged.

## PASS gate

`LESTER_PROGRAMMING_SCHOOL_OSS_R01 = PASS` requires on one exact candidate HEAD:

- standard `hq-validate` jobs green;
- dedicated `lester-oss-eval-r01` real Inspect smoke green;
- emitted event validates against existing `SHERIFF_AGENT_EVENT_V1.schema.json`;
- exact upstream ref/license readback;
- no custom eval/scoring/training framework;
- one-pass state is not PROVEN and changed/unseen transfer remains required;
- fresh candidate readback;
- `main` unchanged and candidate not merged.
