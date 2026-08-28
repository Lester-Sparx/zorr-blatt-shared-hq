# ZORR BLATT — R03 GH-AW Production Task Router Design

Date: 2026-08-28
Status: OWNER-approved Design B / standing R03 authorization active
Tracker: issue #106
Base main at design start: `1bb4ada5270b4d0fc48eba0fb152259d08b15085`
Permanent event bus: PR #111 / OPEN / DRAFT / DO NOT MERGE
Upstream execution substrate: `github/gh-aw`
Pinned upstream release: `v0.86.2`
Pinned Linux amd64 SHA256: `b8fd100d1d56a77b842ad28375ff361215a5aa1277db6b9a05d70054cde7260e`

## 1. Purpose

R03 turns the already-proven R02B remote execution path into a reusable production coding automation without maintaining a custom AI-runner implementation.

The target chain is:

`PR #111 event -> deterministic ZB admission -> registered task authority -> reusable gh-aw LESTER job -> gh-aw safe-output draft PR -> independent DUNCAN QC -> policy finalizer -> merge or BLOCKED -> durable Console/tracker projection`

R03 does not replace the GitHub-native communication bus, ZB role model, replay law, immutable provenance, DUNCAN independence, or durable owner-facing state.

## 2. Reuse decision

R03 adopts GitHub Agentic Workflows (`github/gh-aw`) instead of extending the custom Copilot process wrapper.

Upstream properties used by R03:

- agentic workflow source is Markdown with YAML frontmatter;
- `gh aw compile` generates ordinary GitHub Actions lock workflows;
- reusable `workflow_call` workflows with inputs are supported;
- Copilot is a built-in engine;
- the main agent job is read-only/sandboxed by default;
- writes are routed through permission-controlled `safe-outputs` jobs;
- `create-pull-request.allowed-files` is an exclusive allowlist;
- agentic workflows are single-agent-job units, while traditional Actions remains the correct substrate for multi-stage orchestration.

Therefore R03 deliberately keeps ordinary GitHub Actions around the agentic job for deterministic admission, independent DUNCAN QC, and finalization.

## 3. Standing OWNER authorization

Issue #106 comment `5457544639` records standing human OWNER authority for the R03 automation track.

This standing authority permits the automation implementation to proceed through spec, plan, TDD, review, exact-head merge, and R03 activation without repeatedly asking the OWNER for each intermediate SHA, provided all hard guards in this design pass.

It does not authorize:

- canon mutation;
- OWNER LOCK mutation;
- merging PR #111;
- mutation of issue #102 or PR #103;
- unrelated production changes;
- bypassing DUNCAN or CI;
- merging a candidate whose exact HEAD changed after QC.

R03 merge automation is execution of this pre-authorized policy, not AI self-approval.

## 4. Architecture

R03 consists of four bounded units.

### 4.1 Deterministic dispatcher

A traditional GitHub Actions workflow listens only to `issue_comment.created` on PR #111.

It requires:

- repository exactly `Lester-Sparx/zorr-blatt-shared-hq`;
- issue/PR number exactly `111`;
- top-level PR Conversation comment;
- authenticated actor `Lester-Sparx`;
- marker `ZB_AGENT_TASK_R03_V1`;
- exact current default-branch SHA equal to message `BASE_SHA`;
- registered `TASK_ID` + `TASK_REVISION`;
- immutable task-spec reference;
- replay key not previously dispatched.

The dispatcher never forwards shell text, runner labels, secret names, permissions, model names, or write scopes from the root message.

### 4.2 Static task registry

`config/zb-r03/tasks.json` is executable authority.

R03 initially registers exactly one general production coding profile:

`ZB_CODE_CHANGE_R03`

Registry-controlled fields include:

- revision;
- gh-aw workflow/profile;
- maximum timeout;
- maximum changed-file count;
- allowed file patterns;
- required verification commands;
- DUNCAN policy;
- auto-merge eligibility under the standing R03 OWNER policy.

Initial allowed paths are deliberately limited to:

- `scripts/**`
- `tests/**`
- `docs/**`
- `config/**`

Excluded from the initial profile:

- `.github/workflows/**`
- `.github/**` generally
- `Taskfile.yml`
- lock/canon assets
- secrets or credential material

Workflow/config maintenance will require a later separate profile with its own stronger permissions and QC.

### 4.3 Reusable gh-aw LESTER workflow

Source:

`.github/workflows/zb-r03-lester-agent.md`

Compiled artifact:

`.github/workflows/zb-r03-lester-agent.lock.yml`

The agentic workflow uses:

- `workflow_call` only;
- `engine: copilot`;
- `strict: true`;
- GitHub-hosted runner;
- `permissions: contents: read, copilot-requests: write` for the agent job;
- minimal network allowlist (`defaults` only unless compilation proves an additional required domain);
- no arbitrary secrets inherited into the agent;
- `safe-outputs.create-pull-request` as the only write path;
- `draft: true`;
- `max: 1`;
- `fallback-as-issue: false`;
- `auto-close-issue: false`;
- exclusive `allowed-files` matching the R03 coding profile;
- bounded patch file count and size;
- no safe-output auto-merge.

The reusable workflow receives only sanitized deterministic inputs:

- `message-id`;
- `correlation-id`;
- `task-id`;
- `task-revision`;
- `base-sha`;
- `authority-ref`;
- `task-spec-b64`.

A deterministic pre-agent step decodes `task-spec-b64` to a workspace file. The prompt instructs LESTER to read that file, make the smallest compliant change, run relevant local checks, and emit exactly one draft pull request.

The PR body must contain the machine-readable marker:

`ZB_R03_CANDIDATE_V1`

with exact message/correlation/task/revision/base/authority bindings.

### 4.4 Independent DUNCAN + finalizer

A separate traditional workflow is triggered by R03 candidate pull-request activity.

DUNCAN validates independently:

- candidate marker and all immutable bindings;
- exact PR head SHA;
- PR base branch is `main`;
- candidate ancestry contains the authorized `BASE_SHA`;
- current `main` has not drifted from authorized `BASE_SHA` before promotion;
- every changed file matches the registry allowlist;
- changed-file count is within policy;
- no forbidden path or workflow file is touched;
- full repository unit tests pass;
- Python compile verification passes;
- HQ policy/control-tower guards pass;
- no merge/canon/OWNER LOCK mutation is present in the candidate;
- DUNCAN execution is physically distinct from the LESTER reusable job.

DUNCAN posts one exact-head QC record:

`ZB_R03_DUNCAN_QC_V1`

with `VERDICT = PASS|FAIL`, candidate PR number, exact HEAD, base SHA, changed files, and verification evidence.

The finalizer may merge only when:

- DUNCAN verdict is PASS;
- exact HEAD still equals the reviewed HEAD;
- current main still equals authorized BASE_SHA;
- candidate remains draft/open and is R03-owned;
- standing R03 OWNER authorization remains the applicable policy;
- all forbidden-mutation checks are false.

If any condition fails, finalizer records `BLOCKED` and never widens authority.

## 5. Task-spec transport

The R03 root message does not contain executable shell or permissions.

It references one immutable top-level PR #111 comment containing:

`ZB_TASK_SPEC_V1`

Required binding fields:

- `TASK_SPEC_ID`
- `TASK_ID`
- `TASK_REVISION`
- `BASE_SHA`

The remaining body is natural-language task intent. The dispatcher fresh-reads that exact comment ID and binds its SHA256 into the dispatch record before the LESTER job starts.

The task text may describe desired code behavior, but it cannot expand the registry-defined write scope, permissions, runner, model, safe-output type, or merge policy.

## 6. Replay law

Canonical dispatch replay key:

`MESSAGE_ID + TASK_ID + TASK_REVISION + BASE_SHA + TASK_SPEC_SHA256`

Before dispatch, tracker state is searched for an existing R03 dispatch or terminal state using the same key.

A terminal PASS/FAIL/BLOCKED is never silently re-executed. A retry requires a new `MESSAGE_ID` and fresh task-spec authority when applicable.

## 7. gh-aw supply-chain pin

R03 pins gh-aw `v0.86.2` for compilation/validation.

Linux amd64 release asset:

`https://github.com/github/gh-aw/releases/download/v0.86.2/linux-amd64`

Expected SHA256:

`b8fd100d1d56a77b842ad28375ff361215a5aa1277db6b9a05d70054cde7260e`

No `latest`, `main`, install-script curl pipe, or unverified binary is accepted by R03 CI.

Both source `.md` and generated `.lock.yml` are committed. CI recompiles with the pinned binary and fails if the committed lock differs.

## 8. Failure visibility

R03 removes the R02B UX ambiguity where a substantive worker could fail under `continue-on-error` while the job stayed green.

For R03:

- agent/reusable workflow failure is a failed GitHub job;
- DUNCAN failure is a failed GitHub job;
- finalizer still writes durable terminal state when possible;
- missing evidence never converts to PASS;
- failed agentic output never creates or merges a candidate PR.

## 9. First production activation task

R03 activation is proven with a real repository maintenance task rather than the old fixture proof.

First task:

Convert the currently undiscovered top-level pytest-style checks in `tests/test_r02b_task_inventory_live_proof.py` into `unittest`-discovered tests without changing production code.

Expected production value:

- two previously skipped checks become part of normal unittest discovery;
- repository test coverage improves permanently;
- only `tests/**` is expected to change;
- full suite and DUNCAN verification must pass.

If this real task travels through R03, creates a bounded draft PR, receives independent exact-head DUNCAN PASS, is merged by the standing policy, and fresh read-back proves the merge, then R03 may write:

`PRODUCTION_ACTIVE = YES`

for the R03 coding automation surface only.

## 10. Non-goals

R03 does not:

- make arbitrary GitHub comments executable;
- allow dynamic shell commands;
- allow agent-selected permissions or runner labels;
- expose repository secrets to the agent job;
- auto-merge without exact-head DUNCAN PASS;
- merge PR #111;
- mutate issue #102 or PR #103;
- change canon or OWNER LOCK;
- delete R02B historical code during initial activation;
- add self-hosted runners;
- use polling.

## 11. Required TDD coverage

Before R03 activation, tests must prove at minimum:

1. only the exact R03 marker on PR #111 from `Lester-Sparx` admits;
2. unknown task IDs/revisions reject;
3. stale `BASE_SHA` rejects;
4. task spec is exact-ID fresh-read and SHA256-bound;
5. replay rejects duplicate dispatch;
6. task text cannot alter trusted write scope or permissions;
7. gh-aw source is `workflow_call`, `strict: true`, Copilot engine, and read-only agent permissions;
8. safe-output PR is draft, max one, no fallback issue, no auto-merge;
9. `allowed-files` is exclusive and excludes `.github/workflows/**`;
10. gh-aw compile uses v0.86.2 and pinned SHA256;
11. committed lock file matches pinned recompilation;
12. DUNCAN rejects any out-of-scope changed file;
13. DUNCAN rejects main/base drift;
14. DUNCAN rejects stale/changed PR head;
15. DUNCAN full tests + compile + HQ guards must pass;
16. finalizer cannot merge without exact-head DUNCAN PASS;
17. finalizer uses the standing R03 OWNER policy only for R03 candidate PRs;
18. PR #111, issue #102, PR #103, canon and OWNER LOCK remain untouched;
19. existing R02B regression suite remains green.

## 12. Success criterion

R03 is production-active only after one authenticated R03 root task causes, without manual relay:

1. deterministic admission from PR #111;
2. registry resolution and immutable task-spec binding;
3. reusable pinned gh-aw/Copilot LESTER execution;
4. safe-output creation of one bounded draft candidate PR;
5. independent DUNCAN exact-head QC;
6. policy finalizer exact-head merge under standing human OWNER authorization;
7. fresh merge/main read-back;
8. durable tracker and Console projection;
9. `PRODUCTION_ACTIVE = YES` for the R03 coding automation surface.

Until all nine are physically proven, R03 remains `PRODUCTION_ACTIVE = NO`.
