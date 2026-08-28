# ZB R03 GH-AW Production Router Plan — Amendment 01

Amends `2026-08-28-zb-r03-gh-aw-production-router.md`.

## Superseded plan steps

Task 4/5 references to a separate `.github/workflows/zb-r03-candidate.yml` triggered by `pull_request` are superseded.

## Revised Task 3

`.github/workflows/zb-r03-production-router.yml` is the single parent event workflow and contains four trust-separated stages:

1. `admit`
2. `lester` reusable call to `./.github/workflows/zb-r03-lester-agent.lock.yml`
3. `duncan_qc` with `needs: [admit, lester]`
4. `finalize` with `needs: [admit, lester, duncan_qc]` and `if: always()`

The workflow must not contain `schedule`, polling, `workflow_run`, repository dispatch, or a dependency on a second PR-generated workflow.

## Revised Task 4

Create `scripts/zb_r03_qc.py` and `tests/test_zb_r03_qc.py`; extend the same parent `.github/workflows/zb-r03-production-router.yml`.

DUNCAN discovers exactly one R03 candidate PR by immutable bindings after the reusable gh-aw job completes. Tests must cover zero-match, multi-match, wrong marker/bindings, out-of-scope files, stale main/base, changed head, and exact PASS.

## Revised Task 5

Finalizer remains in the same parent workflow. It consumes DUNCAN exact-head evidence and may merge only under standing R03 policy after a fresh API read proves candidate HEAD and main BASE_SHA are unchanged.

No extra CI trigger PAT/App is introduced.

## New mandatory security regression

Tests and workflow-shape checks must prove all of:

- no `GH_AW_CI_TRIGGER_TOKEN`;
- no `github-token-for-extra-empty-commit`;
- no second candidate PR event workflow;
- DUNCAN is a distinct parent-run job after the reusable gh-aw LESTER job;
- candidate discovery is exact-binding and fails on ambiguity.
