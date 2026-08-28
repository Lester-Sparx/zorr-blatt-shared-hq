# ZB R02B — Implementation Plan Amendment 02

Date: 2026-08-28
Applies to: R02A plan PR #124 / exact historical plan HEAD `cf186deca3a0ce9a5b26d2fd4bf58c12b42715e9`
OWNER authority: `УТВЕРЖДАЮ R02B PERSONAL REPO + COPILOT_GITHUB_TOKEN SECRET`

This amendment changes only authentication-related implementation steps. The seven-task RED→GREEN plan remains otherwise unchanged.

## Task 2 delta — CopilotWorker

`CopilotWorker` still receives an explicit `auth_token` and injects it only as `COPILOT_GITHUB_TOKEN` into the Copilot child environment. Empty token is fail-closed. Shared sanitization MUST strip `COPILOT_GITHUB_TOKEN`, GitHub tokens, Actions OIDC/runtime tokens, and provider BYOK variables from OpenCode and all trusted children.

## Task 3 delta — CLI token capture

The execution CLI captures `COPILOT_GITHUB_TOKEN` once at R02B execution start, removes all auth variables from `os.environ`, then constructs the R02B Copilot worker with the captured value. Trusted verification always receives sanitized environment.

## Task 6 delta — workflow

LESTER remains `runs-on: windows-2025`, but permissions are reduced to:

```yaml
permissions:
  contents: read
```

Do NOT grant `copilot-requests: write` for R02B. Do NOT pass `${{ github.token }}` to Copilot.

Only the actual static LESTER execution step receives:

```yaml
env:
  COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT_GITHUB_TOKEN }}
```

Add a fail-closed preflight immediately before worker invocation that rejects missing/empty secret without printing it. No secret may be placed at workflow/job scope or written into `$GITHUB_ENV`.

DUNCAN remains a separate hosted Windows job with no Copilot secret and no Copilot permission.

## Acceptance deltas

Add tests proving:
1. workflow has no `copilot-requests: write`;
2. workflow never passes `${{ github.token }}` to Copilot;
3. only one LESTER step references `secrets.COPILOT_GITHUB_TOKEN`;
4. secret is absent from job/global env and DUNCAN;
5. missing secret fails closed before worker execution;
6. trusted verification cannot observe the captured token.

`PRODUCTION_ACTIVE = NO` remains unchanged. Real remote proof cannot pass until the OWNER manually creates the repository secret because the connected GitHub surface does not expose secret-write APIs.
