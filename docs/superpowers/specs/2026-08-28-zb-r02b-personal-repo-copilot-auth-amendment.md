# ZB R02B — Personal Repository Copilot Authentication Amendment

Date: 2026-08-28
Status: OWNER AUTHORIZED
Authority command: `УТВЕРЖДАЮ R02B PERSONAL REPO + COPILOT_GITHUB_TOKEN SECRET`

## Scope

This amendment changes only the Copilot authentication boundary of R02A. All other R02A design requirements remain authoritative: GitHub-hosted `windows-2025` LESTER/DUNCAN jobs, confined Copilot CLI, existing R01 execution/evidence contracts, deterministic DUNCAN QC, artifact binding, OWNER gate, Console projection, no auto-merge, and no production activation.

## Authentication decision

R02B MUST authenticate Copilot CLI with repository secret `COPILOT_GITHUB_TOKEN` containing a user-owned fine-grained personal access token with the GitHub **Copilot Requests** account permission.

The secret MUST be exposed only to the single LESTER step that launches the confined Copilot process. It MUST NOT be job-scoped, written to disk, copied into evidence, logs, artifacts, prompts, or trusted verification processes.

The workflow's built-in `GITHUB_TOKEN` MUST NOT be used as Copilot authentication in R02B. The LESTER job therefore needs repository permission `contents: read` only; `copilot-requests: write` is not required for the workflow token.

Before trusted Git/worktree/test/evidence commands execute, all Copilot/GitHub/OIDC/provider authentication variables MUST be removed from the parent process environment and explicit child environments.

If `COPILOT_GITHUB_TOKEN` is absent or empty, R02B MUST fail closed before the Copilot worker starts and MUST surface a terminal execution failure through the existing finalizer/Console path.

## Documentation consistency note

Current GitHub documentation surfaces are not fully uniform about built-in `GITHUB_TOKEN` behavior for personally-owned repositories. The PAT route is explicitly documented for Copilot CLI automation and personal repositories. R02B deliberately selects that route to remove organization-policy and billing ambiguity.

## Non-goals

No new executor, queue, daemon, state store, runner manager, schema fork, or orchestration subsystem. No repository visibility change. No persistent/self-hosted runner. No canon or OWNER LOCK mutation.

## Gate

`R02B_AUTH_DESIGN = OWNER AUTHORIZED`

`IMPLEMENTATION = CONTINUE IN PR #125`

`PRODUCTION_ACTIVE = NO`
