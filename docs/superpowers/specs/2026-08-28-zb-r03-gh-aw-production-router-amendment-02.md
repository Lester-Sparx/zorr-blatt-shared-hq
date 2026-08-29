# ZORR BLATT — R03 GH-AW Production Router — Amendment 02

Date: 2026-08-28
Status: standing R03 OWNER authorization applies
Amends: R03 design + Amendment 01
Evidence: pinned `gh-aw v0.86.2` strict compilation run `33210304140`

## Compiler-proven reusable outputs

The pinned generated reusable workflow exposes:

- `created_pr_number = ${{ jobs.safe_outputs.outputs.created_pr_number }}`
- `created_pr_url = ${{ jobs.safe_outputs.outputs.created_pr_url }}`

R03 therefore supersedes search-based candidate discovery from Amendment 01.

DUNCAN receives the candidate identity only from:

`needs.lester.outputs.created_pr_number`

and then performs a fresh exact GitHub API read of that PR before trusting any candidate metadata.

A missing/non-numeric output, non-open candidate, non-draft candidate, wrong repository/base, wrong R03 marker/bindings, or changed HEAD is fail-closed.

## Optional gh-aw secrets

The generated reusable lock declares optional gh-aw magic secrets including `GH_AW_CI_TRIGGER_TOKEN`. R03 intentionally passes **no reusable-workflow secrets** and MUST NOT use `secrets: inherit`.

Therefore the optional CI-trigger secret is not part of R03 authority or runtime. No additional PAT/App credential is introduced.

## Trust consequence

Candidate identity no longer depends on search queries, timing windows, branch naming, or title matching. The gh-aw safe-output job returns the exact created PR number to the parent workflow, and DUNCAN independently re-reads that exact PR and exact HEAD.
