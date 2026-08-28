# ZORR BLATT R02A GitHub-hosted Copilot CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the inactive self-hosted LESTER execution path with a public-repository-safe GitHub-hosted Windows execution path using GitHub Copilot CLI, while preserving R01 request/result contracts, immutable evidence, deterministic DUNCAN QC, replay protection, finalizer behavior, OWNER gate, and Console projection.

**Architecture:** Reuse the existing R01 seams. Add one static `LESTER_IMPLEMENT_R02A` profile and one `CopilotWorker` behind the existing `WorkerPort`; capture the job-scoped Copilot token once, remove all authentication variables from the trusted process environment, and inject only `COPILOT_GITHUB_TOKEN` into the Copilot child process. Keep the four-stage `admit -> lester_execute -> duncan_qc -> finalize` topology, but run LESTER and DUNCAN as separate `windows-2025` GitHub-hosted jobs and make public-repository execution possible only for the exact R02A authority tuple after existing authenticated ZB admission.

**Tech Stack:** Python stdlib, GitHub Actions, `windows-2025`, Go Task `3.53.1`, GitHub Copilot CLI `@github/copilot@1.0.80`, model `gpt-5.3-codex`, native `git worktree`, existing pinned checkout/upload/download actions.

**Spec:** `docs/superpowers/specs/2026-08-28-zb-r02a-github-hosted-copilot-cli-design.md` at exact approved HEAD `2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8` (PR #123).

## Global Constraints

- Repository remains `Lester-Sparx/zorr-blatt-shared-hq` and may remain PUBLIC.
- R02A active runner label is exactly `windows-2025`; no self-hosted label in the active R02A jobs.
- LESTER and DUNCAN execute in distinct jobs/VMs and distinct `ZB_EXECUTION_ID` values.
- Copilot CLI is exactly `@github/copilot@1.0.80`; no `latest`, no automatic update, no version fallback.
- Copilot model is exactly `gpt-5.3-codex`; no automatic model fallback.
- Copilot visible tool set is exactly `edit,view,grep,glob`; do not add `create`, `apply_patch`, shell, PowerShell, Bash, GitHub, MCP, web, or delegation tools in R02A.
- `--yolo`, `--allow-all`, `--allow-all-tools`, `--allow-all-paths`, and equivalent permissive modes are forbidden.
- LESTER permissions are exactly `contents: read` plus `copilot-requests: write`; no `contents: write`, `issues: write`, or `pull-requests: write` in LESTER.
- DUNCAN has no `copilot-requests: write` permission.
- `actions/checkout` remains `persist-credentials: false` for execution jobs.
- Built-in `GITHUB_TOKEN` reaches only the Copilot child process as `COPILOT_GITHUB_TOKEN`; trusted Git/worktree/test/audit commands run after the token and all GitHub/Copilot auth variables are removed from the parent environment.
- R01 request/result contracts, evidence manifest, replay rules, artifact ID/digest/run binding, DUNCAN deterministic QC, finalizer failure terminalization, OWNER gate, and Console projection remain authoritative.
- Historical R01 self-hosted public-repository blocking remains represented in code/tests; R02A is an additive authority, not a rewrite of history.
- No new daemon, queue, DB, webhook service, artifact bus, persistent runner manager, or external provider secret.
- No auto-merge, production activation, canon mutation, OWNER LOCK mutation, issue #102 reopen, or PR #103 mutation.
- Implementation uses TDD RED -> GREEN for each task and frequent commits.

---

### Task 1: Add the static R02A execution profile and task authority

**Files:**
- Modify: `scripts/zb_execution_profiles.py`
- Modify: `Taskfile.yml`
- Modify: `tests/test_zb_execution_profiles.py`

**Interfaces:**
- Produces: `COPILOT_CLI_VERSION = "1.0.80"`, `COPILOT_MODEL = "gpt-5.3-codex"`, `PROFILES["LESTER_IMPLEMENT_R02A"]`, task `zb:exec:lester:implement-r02a`.
- Preserves: `LESTER_IMPLEMENT_R01`, `DUNCAN_QC_R01`, `resolve_profile()`, and existing static task validation.

- [ ] **Step 1: Write failing profile tests**

Add tests that require exactly three registered profiles and the new profile values:

```python
self.assertEqual(
    set(PROFILES),
    {"LESTER_IMPLEMENT_R01", "LESTER_IMPLEMENT_R02A", "DUNCAN_QC_R01"},
)
r02a = PROFILES["LESTER_IMPLEMENT_R02A"]
self.assertEqual(r02a.logical_role, "LESTER")
self.assertEqual(r02a.task_name, "zb:exec:lester:implement-r02a")
self.assertEqual(r02a.worker_backend, "copilot-cli")
self.assertEqual(r02a.max_timeout_seconds, 1800)
self.assertEqual(COPILOT_CLI_VERSION, "1.0.80")
self.assertEqual(COPILOT_MODEL, "gpt-5.3-codex")
```

Update task inventory assertions so the exact set includes `zb:exec:lester:implement-r02a`, and add an R02A request using `EXECUTION_PROFILE=LESTER_IMPLEMENT_R02A` that resolves successfully while role/version/scope escalation still fails closed.

- [ ] **Step 2: Run the focused test and confirm RED**

Run:

```bash
python -m unittest tests.test_zb_execution_profiles -v
```

Expected: FAIL because `LESTER_IMPLEMENT_R02A`, `COPILOT_CLI_VERSION`, and `COPILOT_MODEL` do not exist and Taskfile inventory is missing the R02A task.

- [ ] **Step 3: Add the minimal profile and static Taskfile entry**

In `scripts/zb_execution_profiles.py` add:

```python
COPILOT_CLI_VERSION = "1.0.80"
COPILOT_MODEL = "gpt-5.3-codex"

"LESTER_IMPLEMENT_R02A": ExecutionProfile(
    name="LESTER_IMPLEMENT_R02A",
    version=1,
    logical_role="LESTER",
    task_name="zb:exec:lester:implement-r02a",
    worker_backend="copilot-cli",
    max_timeout_seconds=1800,
    max_write_prefixes=("scripts/", "tests/", "config/zb-execution/", ".github/workflows/", "Taskfile.yml"),
),
```

In `Taskfile.yml`, add only a static module-mode task:

```yaml
  zb:exec:lester:implement-r02a:
    cmds:
      - python -m scripts.zb_execution_cli execute --from-env
```

Extend `validate_taskfile_text()` required strings to include the R02A task; keep all dynamic/remote include prohibitions.

- [ ] **Step 4: Run the focused test and confirm GREEN**

Run:

```bash
python -m unittest tests.test_zb_execution_profiles -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/zb_execution_profiles.py Taskfile.yml tests/test_zb_execution_profiles.py
git commit -m "feat: add R02A execution profile"
```

---

### Task 2: Add a confined CopilotWorker with process-only authentication

**Files:**
- Create: `scripts/zb_execution_copilot.py`
- Modify: `scripts/zb_execution_worker.py`
- Create: `tests/test_zb_execution_copilot.py`
- Modify: `tests/test_zb_execution_worker.py`

**Interfaces:**
- Consumes: `WorkerOutcome`, `WorkerError`, `CommandRunner` from `scripts.zb_execution_worker`.
- Produces: `CopilotWorker(command, auth_token, home_path, binary="copilot", expected_version="1.0.80", model="gpt-5.3-codex")` implementing `WorkerPort.execute()`.
- Produces: shared `sanitized_execution_env(base: Mapping[str, str] | None = None) -> dict[str, str]` which strips GitHub, Actions, Copilot, and provider credentials.

- [ ] **Step 1: Write failing confinement and token tests**

Create `tests/test_zb_execution_copilot.py` using the existing fake-command pattern. Require:

```python
self.assertEqual(fake.calls[0]["argv"], ("copilot", "--version"))
argv = fake.calls[1]["argv"]
self.assertIn("--model=gpt-5.3-codex", argv)
self.assertIn("--no-ask-user", argv)
self.assertIn("--available-tools=edit,view,grep,glob", argv)
self.assertIn("--allow-tool=write", argv)
self.assertIn("--disable-builtin-mcps", argv)
self.assertIn("--no-auto-update", argv)
self.assertIn("--no-custom-instructions", argv)
self.assertIn("--no-experimental", argv)
self.assertIn("--no-remote", argv)
self.assertIn("--no-remote-export", argv)
self.assertIn("--disallow-temp-dir", argv)
self.assertIn("--output-format=json", argv)
self.assertIn("--no-banner", argv)
self.assertIn("--no-color", argv)
for forbidden in ("--yolo", "--allow-all", "--allow-all-tools", "create", "apply_patch", "bash", "powershell", "web_fetch", "task"):
    self.assertNotIn(forbidden, argv)
```

Require the Copilot run environment to contain exactly the supplied token as `COPILOT_GITHUB_TOKEN` while excluding `GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_PAT`, OIDC/runtime/result tokens, and BYOK variables. Require `COPILOT_HOME` to equal the explicit trusted home directory. Add failures for empty token, version mismatch, home path inside worktree, nonzero exit, and timeout.

Extend the existing OpenCode credential test to prove `COPILOT_GITHUB_TOKEN` and provider API variables are stripped there too.

- [ ] **Step 2: Run tests and confirm RED**

```bash
python -m unittest tests.test_zb_execution_copilot tests.test_zb_execution_worker -v
```

Expected: FAIL because `CopilotWorker` and shared sanitization do not exist.

- [ ] **Step 3: Implement shared sanitization and CopilotWorker**

In `scripts/zb_execution_worker.py` expose a sanitizer using this deny set at minimum:

```python
_AUTH_ENV_KEYS = frozenset({
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT",
    "ACTIONS_ID_TOKEN_REQUEST_URL", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_RESULTS_URL",
    "COPILOT_GITHUB_TOKEN", "COPILOT_PROVIDER_API_KEY",
    "COPILOT_PROVIDER_BASE_URL", "COPILOT_ALLOW_ALL", "COPILOT_MODEL",
})

def sanitized_execution_env(base=None):
    env = dict(os.environ if base is None else base)
    for key in _AUTH_ENV_KEYS:
        env.pop(key, None)
    return env
```

Implement `CopilotWorker` so its version check runs without any auth token, then its execution child env is `sanitized_execution_env()` plus only:

```python
env["COPILOT_GITHUB_TOKEN"] = self._auth_token
env["COPILOT_HOME"] = str(self._home_path)
```

Use a static argv equivalent to:

```python
[
    "copilot",
    "-p", prompt,
    "--model=gpt-5.3-codex",
    "--no-ask-user",
    "--available-tools=edit,view,grep,glob",
    "--allow-tool=write",
    "--disable-builtin-mcps",
    "--no-auto-update",
    "--no-custom-instructions",
    "--no-experimental",
    "--no-remote",
    "--no-remote-export",
    "--disallow-temp-dir",
    "--output-format=json",
    "--no-banner",
    "--no-color",
]
```

Keep stdout/stderr diagnostic only. Do not parse model text as success authority.

- [ ] **Step 4: Run focused tests and confirm GREEN**

```bash
python -m unittest tests.test_zb_execution_copilot tests.test_zb_execution_worker -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/zb_execution_worker.py scripts/zb_execution_copilot.py tests/test_zb_execution_worker.py tests/test_zb_execution_copilot.py
git commit -m "feat: add confined Copilot worker"
```

---

### Task 3: Select the R02A backend in CLI and sanitize trusted verification

**Files:**
- Modify: `scripts/zb_execution_cli.py`
- Modify: `tests/test_zb_execution_cli.py`
- Modify: `tests/test_zb_execution_pipeline.py`

**Interfaces:**
- Consumes: `CopilotWorker`, `sanitized_execution_env`, `resolve_profile()`.
- Produces: backend selection by `profile.worker_backend`, not by remote text.
- Produces: trusted command execution after credential removal.

- [ ] **Step 1: Write failing backend-selection and environment tests**

Add tests that execute an R02A request and require the CLI to select a Copilot worker only for `LESTER_IMPLEMENT_R02A`. Add a command spy proving every trusted Git/worktree/verification command receives or inherits an environment without:

```python
{
    "GITHUB_TOKEN", "COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT",
    "ACTIONS_ID_TOKEN_REQUEST_URL", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_RESULTS_URL",
    "COPILOT_PROVIDER_API_KEY", "COPILOT_PROVIDER_BASE_URL",
}
```

Also assert R01 still selects `OpenCodeWorker` and DUNCAN remains deterministic.

- [ ] **Step 2: Run focused tests and confirm RED**

```bash
python -m unittest tests.test_zb_execution_cli tests.test_zb_execution_pipeline -v
```

Expected: FAIL because CLI currently imports/instantiates only `OpenCodeWorker`, and trusted verification inherits the parent environment.

- [ ] **Step 3: Implement deterministic worker construction and token capture**

At CLI start for `execute`, resolve the request/profile first. For R02A:

```python
copilot_token = os.environ.get("COPILOT_GITHUB_TOKEN", "")
for key in AUTH_ENV_KEYS:
    os.environ.pop(key, None)
worker = CopilotWorker(
    command=command,
    auth_token=copilot_token,
    home_path=job_root / "copilot-home",
)
```

For R01 retain `OpenCodeWorker`. Reject unknown backends with `WorkerError("WORKER_BACKEND_REJECTED")`.

Change `_run_verification_commands()` so each trusted command receives a fresh `sanitized_execution_env()` explicitly:

```python
completed = command.run(list(argv), cwd=worktree, env=sanitized_execution_env())
```

Use sanitized environments for any newly added trusted child processes. Preserve existing evidence/result semantics.

- [ ] **Step 4: Run focused tests and confirm GREEN**

```bash
python -m unittest tests.test_zb_execution_cli tests.test_zb_execution_pipeline -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/zb_execution_cli.py tests/test_zb_execution_cli.py tests/test_zb_execution_pipeline.py
git commit -m "feat: route R02A through Copilot backend"
```

---

### Task 4: Extend implementation preflight for exact Copilot provenance

**Files:**
- Modify: `scripts/zb_execution_preflight.py`
- Modify: `scripts/zb_execution_profiles.py`
- Modify: `tests/test_zb_execution_preflight.py`
- Modify: `tests/test_zb_execution_profiles.py`

**Interfaces:**
- Produces: `run_implementation_preflight(..., copilot_version: str | None = None)` with exact `1.0.80` enforcement for `worker_backend == "copilot-cli"`.
- Preserves: historical self-hosted `run_activation_preflight()` semantics for R01.

- [ ] **Step 1: Write failing preflight tests**

Require:

```python
run_implementation_preflight(
    profile=PROFILES["LESTER_IMPLEMENT_R02A"],
    task_version="3.53.1",
    task_inventory_json=inventory,
    opencode_version=None,
    copilot_version="1.0.80",
)
```

and failures:

```python
with self.assertRaisesRegex(PreflightError, "COPILOT_VERSION_MISSING"):
    ... copilot_version=None
with self.assertRaisesRegex(PreflightError, "COPILOT_VERSION_MISMATCH"):
    ... copilot_version="1.0.79"
```

Also assert R01 still requires OpenCode and DUNCAN requires neither AI CLI.

- [ ] **Step 2: Run and confirm RED**

```bash
python -m unittest tests.test_zb_execution_preflight tests.test_zb_execution_profiles -v
```

Expected: FAIL because preflight has no Copilot version input/validation.

- [ ] **Step 3: Add the minimal exact-version gate**

Extend `validate_toolchain_versions()` or add a focused validator so:

```python
if profile.worker_backend == "copilot-cli":
    if copilot_version is None:
        raise PreflightError("COPILOT_VERSION_MISSING")
    if copilot_version != COPILOT_CLI_VERSION:
        raise PreflightError("COPILOT_VERSION_MISMATCH")
```

Read `ZB_COPILOT_VERSION` in implementation preflight mode. Do not weaken or repurpose the R01 private/disposable self-hosted activation gate.

- [ ] **Step 4: Run and confirm GREEN**

```bash
python -m unittest tests.test_zb_execution_preflight tests.test_zb_execution_profiles -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/zb_execution_preflight.py scripts/zb_execution_profiles.py tests/test_zb_execution_preflight.py tests/test_zb_execution_profiles.py
git commit -m "feat: preflight exact Copilot runtime"
```

---

### Task 5: Add R02A admission authority while preserving historical R01 safety

**Files:**
- Modify: `scripts/zb_communication_base.py`
- Modify: `tests/test_zb_execution_dispatch.py`
- Modify: `tests/test_zb_communication_base.py`
- Create: `tests/fixtures/zb-execution-proof/result.txt`

**Interfaces:**
- Produces: exact R02A authority tuple `(TASK_ID=ZB_EXECUTION_PROOF_R01, TASK_REVISION=2, DESIGN_HEAD=2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8)` -> profile `LESTER_IMPLEMENT_R02A` -> GitHub-hosted eligibility.
- Preserves: revision 1 / R01 design authority and public-repo `RUNNER_SECURITY_GATE_BLOCKED` behavior for the historical self-hosted profile.
- Proof fixture: pre-existing file under already-bounded scope so the approved Copilot toolset can edit it without `create`/`apply_patch` authority.

- [ ] **Step 1: Write failing dual-authority dispatch tests**

Refactor test helpers so they can emit revision 1/R01 or revision 2/R02A messages. Require:

```python
r01_public = prepare_substantive_dispatch(r01_message, public_event, port)
self.assertEqual(r01_public.state, "BLOCKED")
self.assertIn("RUNNER_SECURITY_GATE_BLOCKED", port.comments[-1]["body"])

r02a_public = prepare_substantive_dispatch(r02a_message, public_event, port)
self.assertEqual(r02a_public.state, "REQUEST_RECORDED")
parsed = parse_execution_request(r02a_public.request_body)
self.assertEqual(parsed.execution_profile, "LESTER_IMPLEMENT_R02A")
self.assertEqual(parsed.task_revision, 2)
self.assertEqual(parsed.design_head, "2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8")
```

Require rejection of wrong actor, issue, task revision, design head, message kind, dynamic profile/model/tool text, and changed write scope. Require replay to reuse the exact same R02A request body/hash.

- [ ] **Step 2: Run focused tests and confirm RED**

```bash
python -m unittest tests.test_zb_execution_dispatch tests.test_zb_communication_base -v
```

Expected: FAIL because current authority knows only revision 1 and blocks all public substantive dispatch.

- [ ] **Step 3: Implement explicit revisioned authority selection**

Use a static authority mapping, for example:

```python
_SUBSTANTIVE_AUTHORITIES = {
    (1, "7bac0b6c10dda0448a8792dd3c97f8cec76bbb03"): {
        "profile": "LESTER_IMPLEMENT_R01",
        "transport": "self-hosted",
    },
    (2, "2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8"): {
        "profile": "LESTER_IMPLEMENT_R02A",
        "transport": "github-hosted",
    },
}
```

`prepare_substantive_dispatch()` must select only from that mapping after existing `admit_event()` actor/repository/issue/message validation. Public repository is permitted only when selected transport is `github-hosted`; R01 self-hosted remains blocked while public.

For R02A provenance records, bind `DESIGN_PR = 123` and `DESIGN_HEAD = 2bdf508e...` rather than falsely reusing R01 `IMPLEMENTATION_PR = 122`. Keep historical R01 record formatting for revision 1.

Create `tests/fixtures/zb-execution-proof/result.txt` with deterministic initial content:

```text
ZB_R02A_PROOF_TARGET_V1
STATE = BEFORE
```

Do not expand `SUBSTANTIVE_ALLOWED_WRITE_SCOPE` beyond `tests/fixtures/zb-execution-proof/`.

- [ ] **Step 4: Run focused tests and confirm GREEN**

```bash
python -m unittest tests.test_zb_execution_dispatch tests.test_zb_communication_base -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/zb_communication_base.py tests/test_zb_execution_dispatch.py tests/test_zb_communication_base.py tests/fixtures/zb-execution-proof/result.txt
git commit -m "feat: authorize hosted R02A dispatch"
```

---

### Task 6: Move active LESTER/DUNCAN execution to separate GitHub-hosted Windows jobs

**Files:**
- Modify: `.github/workflows/zb-communication-base.yml`
- Modify: `tests/test_zb_execution_workflow.py`

**Interfaces:**
- Consumes: R02A request readiness/profile from `admit`; existing immutable artifact IDs/digests.
- Produces: hosted `lester_execute`, hosted `duncan_qc`, unchanged `finalize` authority.

- [ ] **Step 1: Rewrite workflow-shape tests first**

Require:

```python
self.assertIn("runs-on: windows-2025", lester)
self.assertIn("runs-on: windows-2025", duncan)
self.assertNotIn("self-hosted", lester)
self.assertNotIn("self-hosted", duncan)
self.assertIn("copilot-requests: write", lester)
self.assertIn("contents: read", lester)
self.assertNotIn("contents: write", lester)
self.assertNotIn("issues: write", lester)
self.assertNotIn("copilot-requests: write", duncan)
self.assertIn("persist-credentials: false", lester)
self.assertIn("persist-credentials: false", duncan)
self.assertIn("@github/copilot@1.0.80", lester)
self.assertIn("gpt-5.3-codex", lester)
self.assertIn("ZB_EXECUTION_PROFILE: LESTER_IMPLEMENT_R02A", lester)
self.assertIn("ZB_RUNNER_PROVENANCE: github-actions:github-hosted:windows-2025", lester)
```

Keep all existing tests for pinned checkout/upload/download SHAs, artifact metadata binding, finalizer `always()`, no dynamic `runs-on`, no PAT/secrets, and no comment-body shell interpolation.

- [ ] **Step 2: Run workflow tests and confirm RED**

```bash
python -m unittest tests.test_zb_execution_workflow -v
```

Expected: FAIL because workflow still uses self-hosted labels/private guard/OpenCode.

- [ ] **Step 3: Implement hosted workflow with narrow permissions**

`admit` must materialize a request based on `prepare_substantive_dispatch()` rather than repository visibility alone. Export a static output proving the request profile is `LESTER_IMPLEMENT_R02A`; only that output may unlock hosted LESTER.

Set LESTER:

```yaml
runs-on: windows-2025
permissions:
  contents: read
  copilot-requests: write
```

Install exact Copilot CLI:

```powershell
npm install --global @github/copilot@1.0.80
$copilotText = (copilot --version | Out-String)
if ($copilotText -match '1\.0\.80') { $env:ZB_COPILOT_VERSION = '1.0.80' } else { $env:ZB_COPILOT_VERSION = '' }
```

Install/verify Task `3.53.1` using the existing approved release/hash mechanism; do not rely on a mutable preinstalled Task version. Run implementation preflight with `LESTER_IMPLEMENT_R02A`.

Pass `${{ github.token }}` only on the actual LESTER execution step as:

```yaml
env:
  COPILOT_GITHUB_TOKEN: ${{ github.token }}
```

Do not set `GITHUB_TOKEN`, `GH_TOKEN`, or Copilot token at job scope. Keep the execution command static:

```powershell
task zb:exec:lester:implement-r02a
```

Set DUNCAN to a separate `windows-2025` job, no Copilot permission/token, deterministic `DUNCAN_QC_R01`, and hosted runner provenance. Preserve artifact uploads/downloads and distinct execution IDs.

Preserve finalizer behavior exactly: on any LESTER/DUNCAN failure, durable FAIL + Console; on success, verify exact artifact metadata before OWNER gate.

- [ ] **Step 4: Run workflow tests and confirm GREEN**

```bash
python -m unittest tests.test_zb_execution_workflow -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/zb-communication-base.yml tests/test_zb_execution_workflow.py
git commit -m "feat: run R02A on GitHub-hosted Windows"
```

---

### Task 7: Close E2E, security, replay, failure, and full-regression gates

**Files:**
- Modify as needed only within already-touched tests:
  - `tests/test_zb_execution_pipeline.py`
  - `tests/test_zb_execution_dispatch.py`
  - `tests/test_zb_execution_release_and_artifact_gate.py`
  - `tests/test_zb_execution_workflow.py`
  - `tests/test_zb_execution_copilot.py`
- No production activation file or command in this task.

**Interfaces:**
- Produces: complete local/CI proof that R02A preserves R01 authority and is ready for a later real remote execution proof.

- [ ] **Step 1: Add any missing acceptance tests from the spec coverage checklist**

The test suite must explicitly prove all eighteen spec requirements:

1. R02A profile resolves only to Copilot backend.
2. exact CLI `1.0.80` required.
3. exact model `gpt-5.3-codex`; no fallback.
4. LESTER/DUNCAN use `windows-2025`.
5. no self-hosted labels in active R02A jobs.
6. LESTER permission set is narrow.
7. DUNCAN has no Copilot permission.
8. checkout credentials not persisted.
9. Copilot tools exactly `edit,view,grep,glob`; permissive modes rejected.
10. no shell/Git/GitHub/network/delegation tool exposed.
11. trusted post-worker commands cannot see auth tokens.
12. public execution requires authenticated ZB admission + exact R02A authority.
13. untrusted actor/PR/fork/user content cannot create R02A request.
14. LESTER/DUNCAN execution IDs distinct.
15. artifact ID/digest/run binding fail closed.
16. silent execution job failure creates durable terminal failure.
17. R01 contract/evidence/replay tests remain green.
18. full repository tests pass.

Add one fake-worker E2E that starts from an R02A request, modifies only the committed proof fixture, creates LESTER evidence, runs distinct DUNCAN QC, and reaches OWNER gate. Add negative variants for tampered evidence, same execution ID, out-of-scope write, HEAD movement, worker timeout, and verification failure.

- [ ] **Step 2: Run the new R02A-focused suite**

```bash
python -m unittest \
  tests.test_zb_execution_profiles \
  tests.test_zb_execution_copilot \
  tests.test_zb_execution_worker \
  tests.test_zb_execution_cli \
  tests.test_zb_execution_preflight \
  tests.test_zb_execution_dispatch \
  tests.test_zb_execution_pipeline \
  tests.test_zb_execution_release_and_artifact_gate \
  tests.test_zb_execution_workflow -v
```

Expected: PASS with zero failures/errors.

- [ ] **Step 3: Run the full repository suite**

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: PASS with zero failures/errors.

- [ ] **Step 4: Run HQ/static security gates**

Run the same repository validation commands used by `hq-validate`, `hq-transition`, and `hq-artifact-verify` workflows. Confirm the Control Tower lock integrity test remains PASS and no historical protected artifact was modified.

Expected: all PASS.

- [ ] **Step 5: Inspect the final diff against the approved spec base**

```bash
git diff --check 2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8..HEAD
git diff --name-status 2bdf508e1f265bcf3ce56170cfa4ab08f04c2ec8..HEAD
```

Expected: only the approved R02A execution/profile/worker/preflight/communication/workflow/tests/fixture/plan surfaces; no canon, OWNER LOCK, historical #102/#103, or unrelated refactor.

- [ ] **Step 6: Commit final test-only repairs if any**

```bash
git add tests
git commit -m "test: close R02A security and regression gates"
```

If Step 5 requires no repair and the index is clean, do not create an empty commit.

- [ ] **Step 7: Stop before production activation**

After implementation CI and DUNCAN review pass, request exact-head OWNER merge approval. After the implementation is merged to `main`, run a separate real remote proof:

```text
OWNER/JINGO request
-> authenticated admit
-> GitHub-hosted LESTER/Copilot CLI edits existing proof fixture
-> trusted verification
-> immutable LESTER evidence
-> separate GitHub-hosted DUNCAN deterministic QC
-> finalizer artifact metadata verification
-> OWNER gate
-> Console projection
```

Record workflow run/job IDs, execution IDs, artifact IDs/digests, request/result/QC identities, Copilot version/model provenance, and fresh durable read-back. `PRODUCTION_ACTIVE = YES` remains a separate OWNER decision after that proof.

---

## Plan Self-Review

### Spec coverage

- Runtime/version/model pins: Tasks 1, 2, 4, 6.
- WorkerPort preservation and Copilot backend: Tasks 1–3.
- Tool confinement/no shell/no network/no delegation: Task 2 + Task 7.
- Process-only token and trusted sanitized verification: Tasks 2–3 + Task 7.
- Hosted LESTER/DUNCAN topology and permissions: Task 6.
- Public-repo authenticated admission and historical R01 block: Task 5 + Task 6.
- Evidence/DUNCAN/artifact/finalizer/OWNER/Console preservation: Tasks 5–7.
- Replay/failure terminalization: Tasks 5–7.
- No file-creation authority for Copilot: Tasks 2 and 5 use a committed pre-existing proof fixture.
- Real remote activation proof and separate production gate: Task 7.

### Placeholder scan

No `TBD`, `TODO`, `latest`, dynamic model selection, dynamic tool selection, unspecified runner label, unspecified version, or unspecified write scope is permitted by this plan.

### Type/interface consistency

- `CopilotWorker` conforms to existing `WorkerPort.execute(request, *, worktree, timeout_seconds) -> WorkerOutcome`.
- `LESTER_IMPLEMENT_R02A` uses existing `ExecutionProfile` fields and version `1`.
- R02A continues to emit existing `ZB_EXECUTION_REQUEST_V1` / `ZB_EXECUTION_RESULT_V1`; no schema fork.
- DUNCAN remains `DUNCAN_QC_R01` and consumes the same evidence bundle.
- Workflow still passes immutable artifacts and exact IDs/digests into the unchanged finalizer authority boundary.

## Execution Gate

`PLAN = MATERIALIZED`

`IMPLEMENTATION = NOT AUTHORIZED BY THIS PLAN FILE ALONE`

`PRODUCTION_ACTIVE = NO`

`RUNNER_REGISTERED = NO`

Next OWNER gate: approve the exact plan PR HEAD for TDD implementation. After that approval, use `superpowers:executing-plans` (inline execution is preferred in this environment) plus `superpowers:test-driven-development` and `superpowers:using-git-worktrees` before touching implementation code.
