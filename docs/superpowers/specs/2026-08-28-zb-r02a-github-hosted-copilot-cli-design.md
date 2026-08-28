# ZORR BLATT — R02A GitHub-hosted + Copilot CLI Execution Surface Design

Status: OWNER-APPROVED DESIGN MATERIALIZATION / AWAITING WRITTEN-SPEC REVIEW
Date: 2026-08-28
Base main SHA: `bbe64b83cd19f387fc9a066a15675a49bef4c211`
Authority command: `УТВЕРЖДАЮ R02A GITHUB-HOSTED + COPILOT CLI + GITHUB_TOKEN`

## 1. Purpose

Replace the R01 self-hosted Windows execution dependency with GitHub-hosted Windows jobs while preserving the already-landed R01 execution contracts, evidence model, deterministic DUNCAN QC, OWNER gate, Console projection, replay protection, and fail-closed behavior.

R02A changes only the execution transport/backend used by LESTER. It does not redesign the communication base or the evidence/authority model.

## 2. Superseded option

The previously proposed `GitHub-hosted + GitHub Models` backend is not implementable because GitHub Models inference was retired on 2026-07-30. R02A therefore uses GitHub Copilot CLI, which GitHub documents for GitHub Actions authentication through the built-in `GITHUB_TOKEN` with `copilot-requests: write`.

## 3. Selected runtime

- Runner: `windows-2025`.
- Each LESTER and DUNCAN job runs on a separate GitHub-hosted VM.
- Copilot CLI package: `@github/copilot@1.0.80` exactly; no `latest` in the final workflow.
- LESTER model: `gpt-5.3-codex` exactly; no automatic model fallback.
- Task remains pinned at `3.53.1`.
- Python module execution and native `git worktree` remain unchanged where already used by R01.
- Existing action SHA pins remain unchanged unless a separate reviewed patch is required.

If the pinned Copilot CLI package or pinned model is unavailable at execution time, execution fails closed. Automatic upgrade or model substitution is forbidden.

## 4. Authentication and permissions

### LESTER job

Required workflow permissions only:

- `contents: read`
- `copilot-requests: write`

The worker authenticates Copilot CLI using the job-scoped built-in `GITHUB_TOKEN`. No PAT, repository secret, organization secret, external provider API key, OIDC cloud credential, or persistent machine credential is introduced.

`actions/checkout` remains `persist-credentials: false`.

The GitHub token is not exported at job scope. The Copilot execution step passes `${{ github.token }}` only as `COPILOT_GITHUB_TOKEN` to the Copilot CLI process. GitHub documents this variable as a supported Copilot CLI authentication variable and redacts it in programmatic CLI output.

### DUNCAN job

DUNCAN remains deterministic and receives no `copilot-requests: write` permission and no AI worker token requirement. DUNCAN keeps only the existing read permissions needed for independent verification.

### Finalizer

The finalizer keeps only its existing bounded Actions/read and issue-write permissions needed for artifact verification, durable records, OWNER gate, and Console projection.

## 5. Worker architecture

R01 `WorkerPort` remains the stable interface.

Add a new `CopilotWorker` backend alongside the existing `OpenCodeWorker`; do not replace or broaden `WorkerPort`.

`LESTER_IMPLEMENT_R02A` resolves to `copilot-cli` and preserves the same bounded request contract, timeout ceiling, allowed write prefixes, detached worktree model, filesystem-diff evidence, and no-commit/no-push/no-merge rules.

`DUNCAN_QC_R01` remains deterministic and unchanged unless a minimal compatibility field is required for provenance verification.

The R01 OpenCode implementation remains in the repository as historical/alternative code but is not the active R02A LESTER backend.

## 6. Copilot CLI confinement

The R02A invocation must be non-interactive and fail closed.

Required controls:

- exact `--model=gpt-5.3-codex`
- `--no-ask-user`
- exact `--available-tools='edit,view,grep,glob'`
- write permission only for the editing tool required to modify the isolated worktree
- no shell/powershell/bash tool exposed to the model
- no `--yolo`, `--allow-all`, `--allow-all-tools`, or equivalent permissive mode
- no web-fetch or web-search tool
- no GitHub MCP tools
- no subagent/delegation tool
- no session transcript publication or gist sharing

The model therefore cannot execute `git`, `gh`, test commands, package managers, arbitrary shell, or network-fetch tools at all.

After Copilot exits, the trusted ZB executor — not the model — runs the static verification command surface already defined by the execution profile, with GitHub/Copilot authentication variables absent from that verification environment.

The worker may read repository files and edit the isolated worktree. Existing post-execution diff/scope auditing remains authoritative: any write outside the request/profile allowed scope produces terminal failure.

## 7. Token containment

The existing R01 environment stripping is extended to include `COPILOT_GITHUB_TOKEN` anywhere a child verification process or deterministic executor environment is constructed.

The Copilot token exists only in the environment of the Copilot CLI process. Because R02A exposes no shell tool to Copilot, the model has no approved mechanism to spawn token-inheriting child commands.

After Copilot completion, all trusted verification commands execute under a sanitized environment with at least these variables absent:

- `GITHUB_TOKEN`
- `COPILOT_GITHUB_TOKEN`
- `GH_TOKEN`
- `GITHUB_PAT`
- Actions OIDC request URL/token
- Actions runtime/result tokens

Implementation must include regression tests proving that the trusted post-worker command environment contains none of these values and that the Copilot argv/config never enables a shell tool.

## 8. Workflow topology

The existing four-stage topology remains:

1. `admit` — GitHub-hosted Ubuntu; validates and materializes immutable request.
2. `lester_execute` — `windows-2025`; installs/verifies pinned Task and Copilot CLI; runs bounded LESTER profile; runs trusted verification after model edits; uploads immutable evidence.
3. `duncan_qc` — a different `windows-2025` job/VM; independently recomputes evidence and verdict; uploads immutable QC evidence.
4. `finalize` — GitHub-hosted Ubuntu; verifies exact artifact IDs/digests/run IDs, records terminal state, projects Console state, and opens OWNER gate only after LESTER PASS + distinct DUNCAN PASS.

No self-hosted runner labels remain in the active R02A path.

## 9. Public repository rule

R02A is specifically designed to operate while `Lester-Sparx/zorr-blatt-shared-hq` remains public.

The old R01 guard `repository.private == true` must be replaced only for the R02A substantive path after tests prove that:

- execution occurs only on GitHub-hosted runners;
- untrusted fork/PR code cannot trigger privileged substantive execution;
- admission still requires the authenticated OWNER transport actor and the exact ZB message contract;
- no write credential is persisted in the checkout;
- Copilot authorization is job-scoped and limited to `copilot-requests: write` plus `contents: read`;
- the model has no shell or GitHub mutation tool surface.

The existing historical public-repo self-hosted safety block remains valid for any self-hosted profile.

## 10. Trigger and trust boundary

The active trigger remains the existing admitted GitHub communication event. R02A must not introduce arbitrary workflow dispatch text, repository dispatch payload execution, PR-body shell execution, or user-controlled runner labels/commands.

The substantive request remains schema-validated and mapped to a static execution profile. The remote message cannot choose arbitrary shell commands, model names, tools, runner labels, package versions, or write scopes.

## 11. Evidence and success authority

Copilot stdout/stderr is diagnostic only and cannot declare PASS.

LESTER PASS remains derived from:

- exact request identity
- exact base/task revision
- bounded filesystem diff
- scope audit
- trusted static tests/verification executed after Copilot exits
- canonical evidence hashes
- terminal result contract

DUNCAN independently recomputes the candidate evidence in a distinct execution ID/job/VM.

OWNER gate remains closed unless both LESTER and DUNCAN are PASS and artifact metadata verification succeeds.

## 12. Failure handling

All of the following must produce durable terminal FAIL/BLOCKED evidence and must not open OWNER gate:

- missing Copilot entitlement/policy
- Copilot authentication failure
- exact CLI version mismatch
- exact model unavailable
- unexpected interactive prompt
- unavailable required edit/read tool
- timeout
- worker process error
- scope violation
- Git HEAD movement
- token containment regression
- trusted verification failure
- evidence/artifact mismatch
- LESTER job failure
- DUNCAN job failure

Replay remains idempotent and reuses already-verified terminal evidence where the R01 contract permits it.

## 13. Implementation surface

Expected files are limited to the smallest additive set, primarily:

- `.github/workflows/zb-communication-base.yml`
- `scripts/zb_execution_worker.py` or a focused sibling worker module if separation materially improves clarity
- `scripts/zb_execution_profiles.py`
- preflight/config only where needed for exact Copilot version/model/tool policy
- tests covering worker confinement, workflow security, hosted-runner routing, permissions, token containment, failure terminalization, and E2E fake-worker behavior
- documentation/authority records

No new queue daemon, database, artifact bus, webhook service, persistent runner manager, or external orchestration service.

## 14. TDD and verification requirements

Implementation must follow RED -> GREEN for every new behavior.

Minimum new tests:

1. R02A profile resolves only to the Copilot backend.
2. exact Copilot CLI version `1.0.80` required.
3. exact model `gpt-5.3-codex` required; no fallback/auto.
4. GitHub-hosted `windows-2025` used for LESTER and DUNCAN.
5. self-hosted labels absent from active R02A path.
6. LESTER has `contents: read` + `copilot-requests: write` and no broader repo write permission.
7. DUNCAN has no Copilot request permission.
8. checkout credentials are not persisted.
9. Copilot tool surface is exactly the approved non-shell file-navigation/edit set and permissive CLI modes are rejected.
10. Copilot cannot invoke shell/Git/GitHub/network tools.
11. trusted post-worker commands cannot see GitHub/Copilot auth tokens.
12. public-repo substantive path can proceed only through authenticated ZB admission.
13. untrusted PR/fork/user content cannot create a substantive execution request.
14. LESTER and DUNCAN execution IDs remain distinct.
15. artifact ID/digest/run binding remains fail closed.
16. silent job failure still creates durable terminal failure.
17. existing R01 contract/evidence/replay tests remain green.
18. full repository test suite passes.

## 15. Activation proof

After implementation lands on `main`, code presence alone is not production activation.

A separate real remote proof must execute:

`OWNER/JINGO request -> admission -> GitHub-hosted LESTER/Copilot CLI -> trusted verification -> immutable evidence -> separate GitHub-hosted DUNCAN deterministic QC -> finalizer -> OWNER gate -> Console projection`

Proof must record exact workflow run/job IDs, execution IDs, artifact IDs/digests, request/result/QC identities, model/version provenance, and fresh durable read-back.

Only after that proof passes may a separate OWNER activation record set `PRODUCTION_ACTIVE = YES`.

## 16. Non-goals

R02A does not:

- auto-merge
- auto-approve OWNER gates
- change canon or OWNER LOCK
- reopen issue #102
- mutate historical PR #103
- reintroduce Work transport
- add persistent self-hosted runners
- grant arbitrary shell authority from GitHub messages
- replace the existing Console or communication base

## 17. Current external authority snapshot

Verified 2026-08-28 against current GitHub documentation/package metadata:

- Copilot CLI supports Actions authentication through built-in `GITHUB_TOKEN` with `copilot-requests: write` and no PAT requirement.
- In personally-owned repositories, that usage is billed to the repository owner's Copilot seat.
- Copilot CLI exposes `--available-tools`, `--allow-tool`, `--deny-tool`, `--no-ask-user`, and exact `--model` selection.
- GitHub-hosted standard Windows runners provision a new VM for each job.
- `windows-2025` is an available standard x64 runner label.
- Current stable npm tag for `@github/copilot` is `1.0.80`.
- `gpt-5.3-codex` is currently listed by GitHub as a supported code-focused Copilot CLI model.

Reference documentation:

- https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli-in-actions
- https://docs.github.com/en/copilot/concepts/agents/copilot-cli/copilot-cli-in-github-actions
- https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/allowing-tools
- https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-programmatic-reference
- https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners

## 18. Gate state

`DESIGN = MATERIALIZED`

`IMPLEMENTATION = NOT AUTHORIZED BY WRITTEN-SPEC REVIEW YET`

`PRODUCTION_ACTIVE = NO`

`RUNNER_REGISTERED = NO`

Next required gate after this document is reviewed: approve this exact written R02A spec, then create the implementation plan and begin TDD.
