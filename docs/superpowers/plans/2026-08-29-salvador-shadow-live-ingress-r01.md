# SALVADOR SHADOW LIVE INGRESS R01 — Implementation Plan

Goal: connect the already-PASS shadow-learning archive to real SALVADOR controller evidence without changing production execution behavior.

Reuse only:
- exact SALVADOR production controller tree from `425ad97c508c4f55f7d7052435a7a2cb4aa3b015`;
- existing `zb_local_controller.task_contract.parse_task` for task validation;
- GitHub CLI (`gh`) for read-only issue/comment retrieval;
- existing HQ `ArchiveStore`, immutable RAW, `SourceRecord`, search and shadow context.

Hard boundary:
`RESULT_READY != QC_PASS`.
Runtime RUNNING/RESULT_READY/FAILED events are archived as evidence only. They must not advance SALVADOR skill state, create LOCKED rules, mutate canon, alter prompts/models/workflows/denoise/dimensions, or write to production controller state.

## Task 1 — RED
Add focused tests using the real issue #72 event format. Require:
- authorized SALVADOR event is archived immutably;
- repeat ingestion is idempotent;
- same GitHub comment id with changed body fails closed;
- wrong actor / wrong task / malformed event is ignored or rejected;
- RESULT_READY and execution FAILED do not become visual QC or capability state.

Run focused test and require expected RED because ingress module does not exist.

## Task 2 — Minimal adapter
Add one thin `zb_hq_memory.salvador_ingress` module:
- read candidate issues via fixed-argv `gh issue list --json number,body,comments`;
- reuse `parse_task`;
- accept only `AGENT = SALVADOR` controller events from configured authenticated actor;
- archive exact comment bytes with `ArchiveStore.ingest_raw`;
- append deterministic `SourceRecord` keyed by immutable GitHub comment id;
- never post/edit/delete GitHub content and never touch controller result/inbox/config.

## Task 3 — GREEN / regression
Run focused test, full HQ-memory suite, compile, and production-controller suite. Confirm the complete `agent-controller` subtree is byte/tree-identical to production tree `31053ef64b43d0cd2a01ebaf309f5a48287983ce`.

## Task 4 — Live-format proof / QC
Fresh-read issue #72 real RUNNING/RESULT_READY evidence and #71 `VISUAL_QC = PENDING`; verify parser compatibility and no false PASS promotion. Persist exact-head QC in draft PR.

No merge. No physical owner-PC activation in this sandbox gate.