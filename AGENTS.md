# ZORR BLATT — Agent Restart Map

This file is a short bootstrap map for coding/review agents. It is not the project archive and must not become a second source of truth.

## First law

GitHub is the durable system of record. Chat/session memory is never authoritative.

On every new session or execution, restore context from GitHub before acting. Do not ask SPARX to retell information that is already recoverable from the repository, tracker, PRs, workflow evidence, or permanent archive.

## Restore order

1. Fresh-read the current `main` HEAD.
2. Fresh-read the durable tracker for the exact task/correlation. Current communication tracker: issue #106, until a newer verified tracker record explicitly supersedes it.
3. Fresh-read the exact task/source PR, immutable source comment/message, base SHA, candidate HEAD, CI/workflow evidence, and any required authority PR. Current communication authority anchor: PR #110, subject to newer verified supersession.
4. For historical reconstruction or disputes, read the original event from branch `zb-archive-v1` under `hq/archive-v1`. Prefer RAW archived evidence over summaries.
5. Treat `hq/state/HQ_STATE.json`, `checkpoints/*CURRENT*`, summaries, indexes, and context packets as derived/legacy snapshots. Never let an older snapshot override fresher GitHub tracker/PR/workflow evidence.

If required durable context is missing, contradictory, or unreadable, fail closed with `DURABLE_CONTEXT_NOT_PROVEN`. Never guess.

## Evidence precedence

`RAW ORIGINAL EVENT > VERIFIED GITHUB HISTORY > CURRENT TRACKER/PR/WORKFLOW EVIDENCE > SNAPSHOT > INDEX > SUMMARY > CHAT MEMORY`

## Role continuity

- LESTER: restore the exact task and bindings, reuse existing/open/native solutions first, implement only the smallest necessary glue, verify, then persist the result/evidence back to GitHub.
- DUNCAN: independently fresh-read the exact candidate HEAD and evidence, run/recompute required verification, and persist PASS/FAIL plus exact evidence back to GitHub.
- OWNER gates remain human-only where repository policy explicitly requires them.

No terminal result may exist only in chat. Persist terminal RESULT/BLOCKED/DEAD_LETTER state with role, task/correlation/message IDs, exact PR/base/HEAD bindings, evidence/run IDs, next legal gate, and blocker/owner action when required.

## Reuse-first engineering

Before writing new infrastructure, search for and prefer existing repository code, standard library/native platform features, maintained open-source libraries, and upstream-supported mechanisms. Custom code should be minimal glue around proven components.

Do not expand architecture while a narrower existing mechanism can finish the current goal.

## Permanent archive

Permanent Archive V1 is already the GitHub-side historical archive:

- workflow: `.github/workflows/zb-permanent-archive-v1.yml`
- branch: `zb-archive-v1`
- root: `hq/archive-v1`
- rule: original RAW event bytes are authoritative and content-addressed by SHA-256.

Do not rewrite archived RAW history. Derived search/memory layers must remain rebuildable from durable evidence.
