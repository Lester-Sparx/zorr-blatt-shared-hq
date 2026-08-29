# ZORR BLATT — R03 GH-AW Production Router — Amendment 04

Date: 2026-08-29
Status: standing R03 OWNER authorization applies
Amends: R03 design + Amendments 01–03
Reason: pre-live verification of gh-aw PR-context checkout behavior

## Finding

Pinned `github/gh-aw v0.86.2` compiles a `Checkout PR branch` runtime step whenever the inherited event contains pull-request context. For an `issue_comment` event on PR #111, upstream `checkout_pr_branch.cjs` resolves `issue.pull_request`, fetches `refs/pull/111/head`, and checks that branch out. An explicit `checkout.ref` does not suppress this later PR-specific checkout.

Therefore calling the reusable LESTER workflow directly from the PR #111 `issue_comment` run would violate R03's exact `BASE_SHA` law.

## Corrected event topology

R03 uses a GitHub-native two-run handoff with no polling and no manual relay:

`PR #111 issue_comment.created -> deterministic admit -> durable DISPATCHED record -> repository_dispatch(type=zb-r03-execute) -> deterministic revalidation -> reusable gh-aw LESTER -> DUNCAN -> finalizer`

GitHub documents `repository_dispatch` as an explicit exception to `GITHUB_TOKEN` recursion suppression: repository-dispatch events created by a workflow's own `GITHUB_TOKEN` create workflow runs. Creating the dispatch requires only repository `contents: write`; no PAT, App secret, or long-lived credential is added.

## Authority law

`client_payload` is transport, never authority.

The root run sends only immutable identifiers and digests. The repository-dispatch run MUST:

1. fresh-read the exact PR #111 root comment by ID;
2. fresh-read the exact task-spec comment by ID;
3. fresh-read the trusted tracker `ZB_R03_DISPATCH_V1` record written by `github-actions[bot]`;
4. reconstruct and revalidate the R03 dispatch using current default-branch code;
5. require exact equality for message/correlation/task/revision/base/spec digest/replay key;
6. require the trusted tracker state to be exactly `DISPATCHED` before LESTER is unlocked.

Unknown, duplicate, stale, missing, or mismatched dispatch state fails closed.

## Checkout consequence

The `repository_dispatch` execution event carries no pull-request context. The reusable gh-aw source keeps explicit:

```yaml
checkout:
  repository: ${{ github.repository }}
  ref: ${{ inputs.base-sha }}
  fetch-depth: 0
```

so agent code starts at the exact authorized main SHA. The compiled PR-specific checkout step remains present but its condition is false in the `repository_dispatch` run.

## DUNCAN and finalizer

DUNCAN and finalizer remain in the same repository-dispatch execution run after the reusable LESTER call. Candidate identity comes only from `needs.lester.outputs.created_pr_number`, followed by a fresh exact API read.

No candidate-PR CI event, no CI-trigger token, no polling, and no manual relay are required.
