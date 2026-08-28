# ZORR BLATT — R03 GH-AW Production Router — Amendment 01

Date: 2026-08-28
Status: standing R03 OWNER authorization applies
Amends: `2026-08-28-zb-r03-gh-aw-production-router-design.md`
Reason: pre-implementation upstream verification of gh-aw CI-trigger behavior

## Finding

GitHub Agentic Workflows documents that pull requests created by `safe-outputs.create-pull-request` with the default Actions `GITHUB_TOKEN` do not trigger new CI workflow runs because GitHub suppresses event cascades from `GITHUB_TOKEN`.

Upstream offers an additional PAT or GitHub App token to push an extra empty commit and trigger CI. R03 deliberately rejects adding that extra credential because it is unnecessary for the ZB architecture.

## Corrected topology

The original design sentence that DUNCAN is triggered by later candidate PR activity is superseded.

R03 uses a single root-event parent workflow:

`PR #111 issue_comment.created -> admit -> reusable gh-aw LESTER -> gh-aw safe-output draft candidate PR -> same parent run DUNCAN job -> same parent run finalizer -> exact-head merge/BLOCKED -> tracker/Console`

The reusable gh-aw job completes only after its safe-output jobs complete. A downstream traditional Actions job may depend on the reusable workflow call. DUNCAN therefore runs after candidate creation without requiring a second GitHub event.

## Candidate discovery

The parent workflow does not trust a user-supplied PR number.

After the gh-aw reusable job completes, DUNCAN discovers exactly one candidate PR using deterministic bindings produced by the dispatch:

- candidate is OPEN and DRAFT;
- base branch is `main`;
- body contains exact `ZB_R03_CANDIDATE_V1` marker;
- exact `MESSAGE_ID`;
- exact `CORRELATION_ID`;
- exact `TASK_ID` and revision;
- exact authorized `BASE_SHA`;
- exact `AUTHORITY_REF`;
- candidate creation/update time is bounded to the current workflow attempt;
- more than one matching candidate is `R03_CANDIDATE_AMBIGUOUS` and fails closed.

The exact discovered PR number and HEAD SHA become DUNCAN evidence.

## DUNCAN / finalizer execution identity

DUNCAN remains physically separate because it is a distinct GitHub Actions job from the reusable gh-aw LESTER call.

Canonical physical identities are:

- LESTER: reusable gh-aw workflow job/run provenance;
- DUNCAN: `github-actions:<parent-run-id>:<attempt>:duncan_qc`;
- finalizer: `github-actions:<parent-run-id>:<attempt>:finalize`.

No second event is necessary for trust separation.

## Credential effect

R03 does not require:

- `GH_AW_CI_TRIGGER_TOKEN`;
- another PAT;
- another GitHub App;
- an empty-commit CI trigger;
- polling for candidate workflow runs.

The gh-aw safe-output credential remains limited to creating the bounded draft candidate PR. DUNCAN/finalizer use the parent workflow's explicit least-privilege jobs.

## Success criterion amendment

The production proof succeeds when one PR #111 root event produces the entire chain in a single parent workflow run, with the gh-aw reusable workflow as one job dependency and DUNCAN/finalizer as later deterministic jobs.

A second candidate-PR-triggered workflow is neither required nor allowed for R03 v1.
