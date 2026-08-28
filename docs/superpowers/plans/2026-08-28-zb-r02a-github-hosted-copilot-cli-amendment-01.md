# ZORR BLATT R02A Implementation Plan — Amendment 01

Status: NORMATIVE ADDENDUM TO `2026-08-28-zb-r02a-github-hosted-copilot-cli.md`

This amendment resolves two self-review ambiguities before implementation authority is requested. Where this file is more specific than the primary plan, this file controls.

## A1. Shared auth-environment interface is explicit

Task 2 SHALL expose the credential deny set as a module-level immutable public constant:

```python
AUTH_ENV_KEYS = frozenset({
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "GITHUB_PAT",
    "ACTIONS_ID_TOKEN_REQUEST_URL",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_RESULTS_URL",
    "COPILOT_GITHUB_TOKEN",
    "COPILOT_PROVIDER_API_KEY",
    "COPILOT_PROVIDER_BASE_URL",
    "COPILOT_ALLOW_ALL",
    "COPILOT_MODEL",
})


def sanitized_execution_env(base=None):
    env = dict(os.environ if base is None else base)
    for key in AUTH_ENV_KEYS:
        env.pop(key, None)
    return env
```

Task 3 SHALL import `AUTH_ENV_KEYS` and `sanitized_execution_env` from `scripts.zb_execution_worker`. It SHALL capture `COPILOT_GITHUB_TOKEN` into an in-memory local value, then remove every key in `AUTH_ENV_KEYS` from `os.environ` before constructing `SubprocessCommand` or invoking any trusted Git/worktree/verification command.

`CopilotWorker` may re-inject only `COPILOT_GITHUB_TOKEN` into the environment of the single Copilot CLI child process. No authentication value may be placed in argv, prompt text, worker stdout/stderr, evidence metadata, or trusted verification environments.

Tests SHALL include a sentinel token value and assert it is absent from recorded argv, prompt, stdout/stderr, and all non-Copilot child environments.

## A2. Exact Go Task installation on `windows-2025`

Task 6 SHALL not rely on a mutable runner-image Task installation. The LESTER and DUNCAN hosted jobs SHALL install Task `3.53.1` from the exact release asset and verify the previously approved SHA256 before use.

Normative PowerShell sequence:

```powershell
$ErrorActionPreference = 'Stop'
$taskVersion = '3.53.1'
$taskUrl = 'https://github.com/go-task/task/releases/download/v3.53.1/task_windows_amd64.zip'
$taskZip = Join-Path $env:RUNNER_TEMP 'task_windows_amd64.zip'
$taskDir = Join-Path $env:RUNNER_TEMP 'zb-task-3.53.1'
$expected = '27c0cd248c12cba03d8958d954a3df981c900be885ec9ce5f6a3cdc4e9a19316'
Invoke-WebRequest -Uri $taskUrl -OutFile $taskZip
$actual = (Get-FileHash -Algorithm SHA256 -Path $taskZip).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw "TASK_PROVENANCE_MISMATCH" }
New-Item -ItemType Directory -Force -Path $taskDir | Out-Null
Expand-Archive -Path $taskZip -DestinationPath $taskDir -Force
$env:PATH = "$taskDir;$env:PATH"
$taskText = (& (Join-Path $taskDir 'task.exe') --version | Out-String)
if ($taskText -notmatch '3\.53\.1') { throw "TASK_VERSION_MISMATCH" }
$env:ZB_TASK_VERSION = '3.53.1'
$env:ZB_TASK_INVENTORY_JSON = (& (Join-Path $taskDir 'task.exe') --list --json | Out-String)
```

The workflow test SHALL assert the exact version, exact URL, and exact SHA256 string are present. LESTER and DUNCAN SHALL use this verified `task.exe`; no setup action or `latest` selector is introduced.

## A3. Exact implementation-branch choreography after plan approval

Planning approval does not create implementation authority. After OWNER approves the exact composite plan HEAD, implementation SHALL begin by:

1. creating branch `impl/zb-r02a-github-hosted-copilot-cli` from that exact approved plan HEAD;
2. opening a DRAFT implementation PR with base `plan/zb-r02a-github-hosted-copilot-cli` before Task 1 code changes;
3. recording the returned implementation PR number and exact starting HEAD in issue #106 with fresh exact-ID read-back;
4. then executing Tasks 1–7 under TDD.

No implementation PR number is hard-coded into the R02A request contract. R02A execution provenance is bound to the already-known design authority `PR #123 / HEAD 2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8` plus the exact runtime/base SHA carried by the request and evidence. This avoids inventing a future PR number and avoids falsely reusing historical R01 implementation PR #122.

## A4. Copilot package provenance

The workflow SHALL install the exact package string:

```powershell
npm install --global @github/copilot@1.0.80
```

and SHALL fail closed unless `copilot --version` reports `1.0.80`. Automatic CLI update remains disabled at runtime with `--no-auto-update`. No prerelease or `latest` selector may appear in the workflow command.

The exact package pin `1.0.80` is the currently selected stable authority; changing it requires a later reviewed authority update, not an automatic workflow edit.

## A5. Gate state

`PLAN_AMENDMENT_01 = MATERIALIZED`

`IMPLEMENTATION = NOT AUTHORIZED`

`PRODUCTION_ACTIVE = NO`

The next OWNER gate must approve the composite plan branch HEAD containing both the primary plan and this amendment before TDD implementation begins.
