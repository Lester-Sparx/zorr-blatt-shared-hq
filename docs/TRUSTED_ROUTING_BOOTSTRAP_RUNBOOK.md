# TRUSTED PR ROUTING — ONE-TIME BOOTSTRAP RUNBOOK

This runbook authorizes exactly one governance-visible bootstrap. It does not
grant a reusable bypass and it does not change ZORR BLATT production data.

## Immutable bootstrap identity

- Repository: `Lester-Sparx/zorr-blatt-shared-hq`
- Pull request: `#3`
- Protected base: `9b41ef0121546c6bb030c3ef2ef1291552be7a19`
- Candidate head: recorded externally in the OWNER review immediately before
  merge. The reviewed SHA must equal the live PR head.
- Authorized files:
  - `.github/workflows/hq-transition.yml`
  - `.github/workflows/hq-artifact-verify.yml`
  - `scripts/hq_pr_scope.py`
  - `tests/test_pr_scope.py`
  - `docs/TRUSTED_ROUTING_BOOTSTRAP_RUNBOOK.md`

Any head change invalidates all approvals and requires a new exact-head review.

## Why an explicit bootstrap is required

`pull_request_target` executes workflow definitions and validator code from
protected `main`. Before this bootstrap, protected `main` has neither the
classifier nor the routing steps. Therefore PR #3 must show the five legacy
transition/artifact checks as red even when its candidate implementation is
correct. The candidate cannot safely make its own trusted checks green.

This is a one-time trust-root installation, not a normal production transition.

## Preconditions

OWNER may approve the bootstrap only when all are true:

1. protected base matches the identity above, and the exact candidate head is
   recorded in the OWNER review immediately before merge;
2. the diff contains only the five authorized files;
3. `hq-schema`, `hq-scope-guard`, and
   `hq-control-tower-integrity` are green;
4. local repository validation passes;
5. the full test suite passes `22/22`;
6. independent DUNCAN code/QC result is PASS;
7. independent DJANGO architecture review accepts this runbook and routing;
8. ruleset bypass list remains empty;
9. OWNER approval is recorded by `Sparx-Owner-ZB`;
10. no merge or OWNER LOCK is produced automatically.

The five legacy-red checks must be recorded as the expected bootstrap
limitation. No other red check is permitted.

## OWNER bootstrap action

After all preconditions pass, OWNER may manually approve PR #3. LESTER may then
perform the exact-head merge through the existing protected PR. This exception
applies only to PR #3 and the exact candidate head recorded in the OWNER
review. Any later commit invalidates that approval.

## Mandatory post-merge proof

Immediately after merge:

1. create a code-only canary PR from the new protected `main`;
2. verify all four `hq-transition` jobs return green through the explicit
   `STATE TRANSITION NOT APPLICABLE` route;
3. verify `hq-artifact-sha` returns green through the explicit
   `ARTIFACT VERIFICATION NOT APPLICABLE` route;
4. verify all ordinary `hq-validate` jobs remain green;
5. create a non-mergeable mixed code + authoritative-state canary and verify it
   enters the strict transition validator and is rejected;
6. close the negative canary without merge;
7. attach the run URLs and exact protected-main SHA to the bootstrap audit.

PR #2 may not merge until this post-merge proof is complete and independently
reviewed.

## Failure and rollback

If any post-merge canary result differs from the requirements:

- stop PR #2 and every later gate;
- do not OWNER LOCK;
- open a dedicated rollback PR restoring the two previous workflow files and
  removing the classifier/test;
- require OWNER approval for that rollback;
- preserve all failed run URLs in the audit.

This runbook is control/workflow metadata only. It does not authorize writes to
ZB CORE, timing, camera, movement, plate, Babylon production data, G2, or
Voice-to-Shot.
