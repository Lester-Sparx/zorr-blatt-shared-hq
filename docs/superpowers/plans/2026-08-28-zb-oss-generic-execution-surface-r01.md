# OSS Generic Execution Surface R01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect real bounded LESTER execution and separate DUNCAN QC to the already-proven GitHub-native ZORR BLATT communication workflow, while reusing mature OSS primitives instead of building a custom queue, daemon, artifact bus, or coding-agent loop.

**Architecture:** Keep GitHub-hosted `issue_comment.created` admission as the trust boundary. For an approved substantive task, create an immutable `ZB_EXECUTION_REQUEST_V1`, transfer it through immutable GitHub Actions artifacts, run LESTER and DUNCAN as distinct physical jobs on an eligible execution backend, verify `ZB_EXECUTION_RESULT_V1` evidence independently, then let a GitHub-hosted finalizer write durable tracker/Console state and stop at the existing human OWNER gate. First execution backend is `actions/runner`; static profile launcher is `go-task/task`; first optional coding worker is OpenCode behind a backend-neutral `WorkerPort`. Repository-public state must fail closed before owner-PC runner dispatch.

**Tech Stack:** Python 3 standard library, `unittest`, native `git worktree`, GitHub Actions, `actions/runner` 2.334.0, `go-task/task` 3.53.1, immutable GitHub Actions artifacts, optional OpenCode 1.18.17 worker, existing GitHub REST persistence in `scripts/zb_communication_base.py`.

**Spec:** `docs/superpowers/specs/2026-08-28-zb-oss-generic-execution-surface-r01-design.md` at approved PR #120 HEAD `7bac0b6c10dda0448a8792dd3c97f8cec76bbb03`.

## Global Constraints

- Repository: `Lester-Sparx/zorr-blatt-shared-hq`.
- Plan base is exact approved spec HEAD `7bac0b6c10dda0448a8792dd3c97f8cec76bbb03`.
- Main at spec approval: `b4e208e0e6351aea419b7ad77464e8109efc84dd`.
- Event surface remains PR `#111` / DRAFT / OPEN / DO NOT MERGE.
- Tracker remains issue `#106`; Console target remains issue `#39`.
- Transport actor remains `Lester-Sparx`; logical roles remain protocol roles.
- OWNER is human-only and is never auto-executed.
- Issue `#102` historical proof is immutable; PR `#103` is not mutated.
- No auto-merge, production activation, canon mutation, or OWNER LOCK.
- No arbitrary shell text, binary name, model name, `runs-on`, checkout ref, secret name, Task name, or worker argv may come from a GitHub message.
- Before **every substantive implementation task below**, run an OSS/existing-repo reuse checkpoint. Reuse a mature primitive only if it preserves the approved authority/security/evidence contracts; record any new dependency/pin in the implementation PR description or tracker. Do not add dependencies for convenience when stdlib/native Git already covers the need.
- The current repository is public. `OWNER_PC_SELF_HOSTED_RUNNER = BLOCKED` until a separate gate proves either repository privacy plus workflow re-audit or a disposable isolated execution host.
- Implementation may build and test the adapter while public, but MUST NOT register an owner-PC runner or claim remote substantive execution.
- Existing communication-base task behavior and its historical proof must remain regression-compatible. New substantive routing is additive and deny-by-default.

## Pinned OSS Inputs for R01

Use exact versions/provenance; never `latest` in implementation authority:

```text
ACTIONS_RUNNER_VERSION = 2.334.0
ACTIONS_RUNNER_WIN_X64_SHA256 = a0c896f3acf37841cc17f392a38111d39501e56f2990434567f027ee89cf8981

TASK_VERSION = 3.53.1
TASK_WINDOWS_AMD64_SHA256 = 27c0cd248c12cba03d8958d954a3df981c900be885ec9ce5f6a3cdc4e9a19316

OPENCODE_VERSION = 1.18.17

ACTIONS_CHECKOUT_V4_COMMIT = 11d5960a326750d5838078e36cf38b85af677262
ACTIONS_UPLOAD_ARTIFACT_V7_COMMIT = 043fb46d1a93c77aae656e7c1c64a875d1fc6a0a
ACTIONS_DOWNLOAD_ARTIFACT_V8_COMMIT = 3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c
```

The Task and runner package hashes above are upstream release-asset SHA-256 values. The OpenCode binary is not installed by CI in this implementation plan; runtime preflight checks its exact version and the first physical activation must separately pin installation provenance/checksum for the chosen Windows installation method.

---

### Task 1: Strict execution request/result contracts and replay identity

**OSS/existing-repo checkpoint:** Reuse the existing strict `KEY = VALUE` parsing conventions from `scripts/zb_communication_base.py`. Do **not** add Pydantic/jsonschema; fixed schemas do not justify a new dependency.

**Files:**
- Create: `scripts/zb_execution_contract.py`
- Create: `tests/test_zb_execution_contract.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ExecutionRequest: ...

@dataclass(frozen=True)
class ExecutionResult: ...

def parse_execution_request(body: str) -> ExecutionRequest: ...
def render_execution_request(request: ExecutionRequest) -> str: ...
def parse_execution_result(body: str) -> ExecutionResult: ...
def render_execution_result(result: ExecutionResult) -> str: ...
def execution_replay_key(request: ExecutionRequest) -> str: ...
```

- [ ] **Step 1: Write RED contract tests.** Cover one exact valid request and result, duplicate/missing/unknown field rejection, malformed identifiers, invalid SHA, illegal terminal state, `NO_AUTO_MERGE != TRUE`, `PRODUCTION_ACTIVE != NO`, negative/zero attempt, nonnumeric timeout/exit code, renderer round-trip, and deterministic replay key.

Canonical replay assertion:

```python
self.assertEqual(
    execution_replay_key(req),
    f"{req.execution_request_id}:{req.execution_profile_version}:{req.base_sha}:{req.task_revision}",
)
```

- [ ] **Step 2: Verify RED.**

```bash
python3 -m unittest tests.test_zb_execution_contract -v
```

Expected: missing module/symbol failures.

- [ ] **Step 3: Implement strict dependency-free contracts.** Use exact marker-first parsing, exact field sets, immutable dataclasses, existing bounded identifier grammar, `_SHA40`, recognized result terminal states `PASS|FAIL|BLOCKED|TIMEOUT|EXECUTION_ERROR`, and exact render order. Parsers must reject duplicate fields and trailing unknown authority fields rather than ignore them.

- [ ] **Step 4: Verify GREEN.**

```bash
python3 -m unittest tests.test_zb_execution_contract -v
```

- [ ] **Step 5: Commit.**

```bash
git add scripts/zb_execution_contract.py tests/test_zb_execution_contract.py
git commit -m "feat: add execution request and result contracts"
```

---

### Task 2: Static task/profile authority and pinned OSS toolchain policy

**OSS/existing-repo checkpoint:** Use `go-task/task` for named profile dispatch. Do not build a custom task scheduler or queue. Native Python owns policy validation; Task only launches static profiles.

**Files:**
- Create: `scripts/zb_execution_profiles.py`
- Create: `config/zb-execution/toolchain-r01.json`
- Create: `Taskfile.yml`
- Create: `tests/test_zb_execution_profiles.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ExecutionProfile:
    name: str
    version: int
    logical_role: str
    task_name: str
    worker_backend: str
    max_timeout_seconds: int
    max_write_prefixes: tuple[str, ...]

PROFILES: Mapping[str, ExecutionProfile]
def resolve_profile(request: ExecutionRequest) -> ExecutionProfile: ...
def validate_task_inventory(task_json: str, profile: ExecutionProfile) -> None: ...
def validate_toolchain_versions(*, task_version: str, opencode_version: str | None) -> None: ...
```

Initial static profiles:

```text
LESTER_IMPLEMENT_R01 / v1 / role=LESTER / task=zb:exec:lester:implement-r01 / worker=opencode / max_timeout=1800
DUNCAN_QC_R01        / v1 / role=DUNCAN / task=zb:exec:duncan:qc-r01       / worker=deterministic-qc / max_timeout=900
```

`ALLOWED_WRITE_SCOPE` from a request must be a subset of the profile's trusted prefixes; it never expands them.

- [ ] **Step 1: Write RED profile-policy tests.** Require unknown profile rejection, role mismatch rejection, version mismatch rejection, timeout escalation rejection, write-scope expansion rejection, exact Task inventory match, and no dynamic task names.

Also load `Taskfile.yml` as text and require:

```text
version: '3'
zb:exec:lester:implement-r01
zb:exec:duncan:qc-r01
```

Reject `includes:` with remote URLs, `CLI_ARGS`, templated task names, or body-derived command variables.

- [ ] **Step 2: Verify RED.**

```bash
python3 -m unittest tests.test_zb_execution_profiles -v
```

- [ ] **Step 3: Implement registry + toolchain manifest + minimal Taskfile.** `config/zb-execution/toolchain-r01.json` must contain the exact version/hash/action pins from this plan. Task tasks call only the trusted Python CLI:

```yaml
version: '3'

tasks:
  zb:exec:lester:implement-r01:
    cmds:
      - cmd: python scripts/zb_execution_cli.py execute --request "$ZB_EXECUTION_REQUEST_PATH" --out "$ZB_EXECUTION_RESULT_PATH" --evidence-dir "$ZB_EVIDENCE_DIR"
        timeout: 30m
  zb:exec:duncan:qc-r01:
    cmds:
      - cmd: python scripts/zb_execution_cli.py qc --request "$ZB_EXECUTION_REQUEST_PATH" --candidate "$ZB_CANDIDATE_EVIDENCE_DIR" --out "$ZB_QC_RESULT_PATH"
        timeout: 15m
```

Taskfile must not download tools, remote includes, or interpolate arbitrary message values into executable names.

- [ ] **Step 4: Verify GREEN and inventory behavior with a fake Task JSON fixture.**

```bash
python3 -m unittest tests.test_zb_execution_profiles -v
```

- [ ] **Step 5: Commit.**

```bash
git add scripts/zb_execution_profiles.py config/zb-execution/toolchain-r01.json Taskfile.yml tests/test_zb_execution_profiles.py
git commit -m "feat: add static execution profiles and toolchain policy"
```

---

### Task 3: Native Git worktree isolation and evidence snapshotting

**OSS/existing-repo checkpoint:** Use native `git worktree`, `git diff`, `git status`, and Python `hashlib`. Do not add a workspace library, file-watcher, or hashing package.

**Files:**
- Create: `scripts/zb_execution_workspace.py`
- Create: `scripts/zb_execution_evidence.py`
- Create: `tests/test_zb_execution_workspace.py`
- Create: `tests/test_zb_execution_evidence.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class WorkspaceSnapshot:
    start_head: str
    end_head: str
    changed_files: tuple[str, ...]
    patch_sha256: str

class CommandPort(Protocol):
    def run(self, argv: Sequence[str], *, cwd: Path | None = None, timeout: int | None = None, env: Mapping[str, str] | None = None) -> Completed: ...

def create_detached_worktree(repo_root: Path, base_sha: str, worktree: Path, command: CommandPort) -> None: ...
def audit_workspace(worktree: Path, allowed_scope: tuple[str, ...], command: CommandPort) -> WorkspaceSnapshot: ...
def remove_worktree(repo_root: Path, worktree: Path, command: CommandPort) -> None: ...
def build_evidence_bundle(..., evidence_dir: Path) -> dict[str, str]: ...
```

- [ ] **Step 1: Write RED tests using temporary Git repositories.** Cover exact detached worktree at base SHA, dirty source checkout rejection, changed-file collection, path escape rejection, disallowed file detection, binary patch capture, SHA-256 stability, unchanged HEAD requirement for R01 LESTER profile, and cleanup.

- [ ] **Step 2: Verify RED.**

```bash
python3 -m unittest tests.test_zb_execution_workspace tests.test_zb_execution_evidence -v
```

- [ ] **Step 3: Implement using argv lists only.** Required Git calls include:

```text
git status --porcelain
git worktree add --detach <path> <base_sha>
git -C <worktree> rev-parse HEAD
git -C <worktree> diff --name-only --no-renames
git -C <worktree> diff --binary --no-ext-diff
git worktree remove --force <path>
```

No `shell=True`. Normalize repository-relative paths and fail closed on absolute paths, `..`, NUL, or prefix violations.

Evidence bundle contains at minimum `request.txt`, `result.txt` when available, `patch.diff`, `changed-files.txt`, `tests.txt`, `worker-events.jsonl`, and `manifest.json` with per-file SHA-256.

- [ ] **Step 4: Verify GREEN.**

```bash
python3 -m unittest tests.test_zb_execution_workspace tests.test_zb_execution_evidence -v
```

- [ ] **Step 5: Commit.**

```bash
git add scripts/zb_execution_workspace.py scripts/zb_execution_evidence.py tests/test_zb_execution_workspace.py tests/test_zb_execution_evidence.py
git commit -m "feat: add isolated worktree and execution evidence"
```

---

### Task 4: Backend-neutral WorkerPort and strict OpenCode adapter

**OSS/existing-repo checkpoint:** Reuse OpenCode for the first coding-agent worker; do not implement a custom LLM/tool loop. Keep it behind a replaceable port so Codex or another OSS worker can be added later without changing ZB contracts.

**Files:**
- Create: `scripts/zb_execution_worker.py`
- Create: `config/zb-execution/opencode-r01.json`
- Create: `tests/test_zb_execution_worker.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class WorkerOutcome:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool

class WorkerPort(Protocol):
    def execute(self, request: ExecutionRequest, *, worktree: Path, timeout_seconds: int) -> WorkerOutcome: ...

class OpenCodeWorker:
    def execute(...): ...
```

- [ ] **Step 1: Write RED adapter tests.** Inject a fake command runner and assert exact argv; GitHub message fields must never become executable/agent/model flags. Require timeout propagation, exit-code preservation, JSON-event capture, version mismatch rejection, and environment stripping of GitHub credentials.

Expected argv shape:

```python
[
    "opencode", "run", "--pure", "--auto", "--format", "json",
    "--agent", "build", "--dir", str(worktree), prompt,
]
```

The prompt is deterministic from trusted normalized request fields and source refs; it must explicitly instruct the worker not to commit/push/merge and to stay inside `ALLOWED_WRITE_SCOPE`.

- [ ] **Step 2: Verify RED.**

```bash
python3 -m unittest tests.test_zb_execution_worker -v
```

- [ ] **Step 3: Implement strict OpenCode policy.** `config/zb-execution/opencode-r01.json` must use deny-by-default permissions for R01, allow workspace reads/edits and only the minimum verification shell command families needed by the current Python repository, and deny at least `git commit`, `git push`, external directory access, web search/fetch, subagent/task launch, and interactive questions. The adapter sets `OPENCODE_CONFIG` to this file, `OPENCODE_DISABLE_AUTOUPDATE=true`, `OPENCODE_AUTO_SHARE=false`, uses `--pure`, and explicitly removes `GITHUB_TOKEN`, `GH_TOKEN`, Actions OIDC request variables, and repository write credentials from the worker environment.

R01 runtime policy: project-local `opencode.json`, `opencode.jsonc`, or `.opencode/` in the execution worktree is rejected before worker start, preventing project config from weakening the static worker policy. Provider credentials, if needed, must be dedicated host-local credentials and never appear in GitHub evidence.

- [ ] **Step 4: Verify GREEN.**

```bash
python3 -m unittest tests.test_zb_execution_worker -v
```

- [ ] **Step 5: Commit.**

```bash
git add scripts/zb_execution_worker.py config/zb-execution/opencode-r01.json tests/test_zb_execution_worker.py
git commit -m "feat: add replaceable OpenCode execution worker"
```

---

### Task 5: Execution CLI, host/toolchain preflight, and deterministic terminal results

**OSS/existing-repo checkpoint:** Keep orchestration in small Python stdlib code. Task owns profile launch; worker owns coding; native Git owns workspace. Do not add Click/Typer/process supervisors.

**Files:**
- Create: `scripts/zb_execution_cli.py`
- Create: `scripts/zb_execution_preflight.py`
- Create: `tests/test_zb_execution_cli.py`
- Create: `tests/test_zb_execution_preflight.py`

**CLI surfaces:**

```text
python scripts/zb_execution_cli.py execute --request PATH --out PATH --evidence-dir PATH
python scripts/zb_execution_cli.py qc --request PATH --candidate DIR --out PATH
python scripts/zb_execution_preflight.py --mode implementation
python scripts/zb_execution_preflight.py --mode activation
```

- [ ] **Step 1: Write RED tests.** Cover valid fake-worker PASS, worker nonzero => FAIL, timeout => TIMEOUT, never-started => BLOCKED/EXECUTION_ERROR not RUNNING/PASS, evidence mismatch => FAIL, DUNCAN distinct execution ID, public repository activation => `RUNNER_SECURITY_GATE_BLOCKED`, wrong Task/OpenCode versions, and Task inventory mismatch.

- [ ] **Step 2: Verify RED.**

```bash
python3 -m unittest tests.test_zb_execution_cli tests.test_zb_execution_preflight -v
```

- [ ] **Step 3: Implement orchestration.** `execute` must:

```text
parse request
resolve trusted profile
run implementation preflight
create detached worktree at BASE_SHA
verify clean workspace + static Task inventory
invoke WorkerPort
run required verification commands
collect actual diff/head/evidence
render one terminal ZB_EXECUTION_RESULT_V1
write result into evidence bundle
cleanup worktree
```

`qc` does not invoke the coding worker. It fresh-loads request + LESTER result/evidence, recomputes hashes/diff/scope/test evidence, requires a distinct physical execution ID, and produces DUNCAN PASS/FAIL/BLOCKED.

`activation` preflight requires repository-private evidence (or explicit disposable-host mode), exact Task 3.53.1, exact OpenCode 1.18.17 when the LESTER profile is enabled, static Task inventory, and the pinned runner package version/provenance record. It must fail before runner use while the repository is public.

- [ ] **Step 4: Verify GREEN.**

```bash
python3 -m unittest tests.test_zb_execution_cli tests.test_zb_execution_preflight -v
```

- [ ] **Step 5: Commit.**

```bash
git add scripts/zb_execution_cli.py scripts/zb_execution_preflight.py tests/test_zb_execution_cli.py tests/test_zb_execution_preflight.py
git commit -m "feat: add execution CLI and fail-closed preflight"
```

---

### Task 6: Local end-to-end execution/QC pipeline with fake worker

**OSS/existing-repo checkpoint:** Do not add a workflow simulator. Exercise the Python seams directly with a temporary Git repo and fake worker; GitHub Actions behavior is tested separately as workflow structure.

**Files:**
- Create: `tests/test_zb_execution_pipeline.py`
- Modify: `scripts/zb_execution_evidence.py` only if the integration test exposes a missing narrow seam.

- [ ] **Step 1: Write RED integration test.** Build a temp Git repo at known SHA, a request limited to one fixture path, and a fake LESTER worker that edits that file. Run LESTER execution, then DUNCAN QC from a freshly copied/download-shaped evidence directory.

Required assertions:

```text
LESTER execution ID != DUNCAN execution ID
LESTER terminal = PASS only with valid evidence
DUNCAN terminal = PASS only after recomputation
changed files exactly match allowed scope
START_HEAD == END_HEAD == BASE_SHA for R01 no-commit worker
patch digest stable
replaying same request does not invoke fake worker twice
```

Also mutate the candidate patch/manifest between LESTER and DUNCAN and require DUNCAN FAIL.

- [ ] **Step 2: Verify RED, implement only missing narrow integration seam, then GREEN.**

```bash
python3 -m unittest tests.test_zb_execution_pipeline -v
```

- [ ] **Step 3: Commit.**

```bash
git add tests/test_zb_execution_pipeline.py scripts/zb_execution_evidence.py
git commit -m "test: prove local execution and independent QC pipeline"
```

---

### Task 7: Integrate substantive dispatch/finalization with existing communication base without breaking historical mode

**OSS/existing-repo checkpoint:** Reuse the existing GitHub REST port, `WRITE -> exact-ID GET -> MATCH`, tracker replay records, and Console projection. Do not create a second GitHub API client or state store.

**Files:**
- Modify: `scripts/zb_communication_base.py`
- Modify: `tests/test_zb_communication_base.py`
- Create: `tests/test_zb_execution_dispatch.py`

**Behavior:** Existing `ZB_GITHUB_NATIVE_BASE_R01` messages retain their previously proven path. Add an explicit substantive task authority registry entry for the R01 proof/integration task; unknown substantive task/revision/design tuples fail closed.

Add functions shaped like:

```python
@dataclass(frozen=True)
class DispatchDecision:
    state: str
    request_body: str | None
    request_sha256: str | None

def prepare_substantive_dispatch(message: RootMessage, event: dict[str, Any], port: GitHubPort) -> DispatchDecision: ...
def finalize_substantive_execution(request_body: str, lester_result: str, duncan_result: str, port: GitHubPort) -> str: ...
```

- [ ] **Step 1: Write RED tests.** Require public-repo dispatch to write one authenticated `RUNNER_SECURITY_GATE_BLOCKED` tracker record and a Console projection with `SUBSTANTIVE_EXECUTION = BLOCKED`, with no synthetic LESTER/DUNCAN PASS. Require private/eligible path to create and fresh-read an immutable execution-request record and return a request hash. Require finalization to accept only exact matching verified LESTER + DUNCAN PASS and then produce the existing human OWNER gate. DUNCAN FAIL/BLOCKED must never advance.

- [ ] **Step 2: Verify RED.**

```bash
python3 -m unittest tests.test_zb_communication_base tests.test_zb_execution_dispatch -v
```

- [ ] **Step 3: Implement additive routing.** Preserve old proof behavior behind its exact task authority. New substantive flow must replace synthetic role PASS records with truthful states:

```text
REQUEST_RECORDED
LESTER_RUNNING/RESULT_READY or BLOCKED
DUNCAN_QC_RUNNING/PASS|FAIL|BLOCKED
OWNER_GATE_REQUIRED only after DUNCAN PASS
```

Every authoritative tracker/Console comment still uses exact remote read-back before progression.

- [ ] **Step 4: Verify GREEN plus existing base regressions.**

```bash
python3 -m unittest tests.test_zb_communication_base tests.test_zb_execution_dispatch -v
```

- [ ] **Step 5: Commit.**

```bash
git add scripts/zb_communication_base.py tests/test_zb_communication_base.py tests/test_zb_execution_dispatch.py
git commit -m "feat: route verified substantive execution through communication base"
```

---

### Task 8: GitHub Actions pipeline using immutable artifacts and distinct LESTER/DUNCAN jobs

**OSS/existing-repo checkpoint:** Reuse GitHub Actions job scheduling and immutable `actions/upload-artifact`/`download-artifact`; do not build a custom artifact server, queue, webhook receiver, or polling relay.

**Files:**
- Modify: `.github/workflows/zb-communication-base.yml`
- Create: `tests/test_zb_execution_workflow.py`

**Pinned actions:**

```text
actions/checkout@11d5960a326750d5838078e36cf38b85af677262
actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a
actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c
```

- [ ] **Step 1: Write RED workflow-shape tests.** Load YAML as text and require four trust-separated jobs for the substantive path:

```text
admit / GitHub-hosted
lester_execute / self-hosted + custom zorr-blatt-exec-r01 label
duncan_qc / separate self-hosted job
finalize / GitHub-hosted
```

Require both self-hosted jobs to contain a repository-private eligibility condition and to depend on the prior verified job. Require different job names so physical execution IDs differ.

Require:
- pinned action commit SHAs above;
- `persist-credentials: false` on self-hosted checkouts;
- no `pull_request_target`, schedule, workflow_dispatch, PAT, dynamic `runs-on`, or body-derived checkout ref;
- self-hosted jobs do not receive `issues: write`;
- LESTER artifact upload returns immutable `artifact-id` + `artifact-digest`;
- DUNCAN downloads the exact LESTER artifact ID/name and recomputes candidate evidence;
- finalizer is the only post-execution job allowed to write tracker/Console state;
- public repository path skips self-hosted jobs and leaves a truthful blocker.

- [ ] **Step 2: Verify RED.**

```bash
python3 -m unittest tests.test_zb_execution_workflow -v
```

- [ ] **Step 3: Implement workflow.** Keep the existing top-level `issue_comment.created` admission. For substantive messages:

```text
admit (ubuntu) -> immutable request artifact
if repository.private && request_ready:
  lester_execute ([self-hosted, Windows, X64, zorr-blatt-exec-r01])
    -> Task LESTER profile -> immutable LESTER evidence artifact
  duncan_qc ([self-hosted, Windows, X64, zorr-blatt-exec-r01])
    -> download exact LESTER artifact -> Task DUNCAN QC profile -> immutable QC artifact
  finalize (ubuntu)
    -> download exact artifacts -> verify IDs/digests/body -> write tracker + Console -> human OWNER gate
else:
  admit/finalize blocker only; no self-hosted dispatch
```

Use `retention-days: 7` for disposable execution artifacts and `if-no-files-found: error`. Record action-provided artifact digest in durable result metadata and independently hash the evidence manifest contents.

- [ ] **Step 4: Verify GREEN.**

```bash
python3 -m unittest tests.test_zb_execution_workflow -v
```

- [ ] **Step 5: Commit.**

```bash
git add .github/workflows/zb-communication-base.yml tests/test_zb_execution_workflow.py
git commit -m "feat: add guarded substantive execution jobs"
```

---

### Task 9: Full regression, security matrix, implementation evidence, and stop before activation

**OSS/existing-repo checkpoint:** No new dependency is allowed during cleanup unless a failing requirement cannot be satisfied with the approved primitives. Prefer deleting custom code over adding wrappers.

**Files:**
- Modify only files from Tasks 1-8 as required by verified failures.
- Do not create runner-registration scripts in R01 implementation while repository is public.

- [ ] **Step 1: Run targeted execution suite.**

```bash
python3 -m unittest \
  tests.test_zb_execution_contract \
  tests.test_zb_execution_profiles \
  tests.test_zb_execution_workspace \
  tests.test_zb_execution_evidence \
  tests.test_zb_execution_worker \
  tests.test_zb_execution_cli \
  tests.test_zb_execution_preflight \
  tests.test_zb_execution_pipeline \
  tests.test_zb_execution_dispatch \
  tests.test_zb_execution_workflow -v
```

- [ ] **Step 2: Run full repository regression.**

```bash
python3 -m unittest discover -s tests -v
python3 scripts/hq_validate.py
```

Expected: all tests PASS; `CONTROL TOWER` integrity unchanged; scope guard PASS.

- [ ] **Step 3: Run explicit negative/security matrix.** Confirm tests prove:

```text
PUBLIC_REPO -> NO SELF_HOSTED DISPATCH
FOREIGN_ACTOR -> REJECT
UNKNOWN_TASK/PROFILE -> REJECT
PROFILE_TIMEOUT_ESCALATION -> REJECT
BODY_SELECTS_BINARY/MODEL/TASK/RUNS_ON/REF -> IMPOSSIBLE
WORKER_GITHUB_TOKEN -> ABSENT
WORKER_GIT_PUSH/COMMIT -> DENIED
WORKTREE_SCOPE_ESCAPE -> FAIL
ARTIFACT_OR_MANIFEST_TAMPER -> DUNCAN_FAIL
DUNCAN_EXECUTION_ID == LESTER_EXECUTION_ID -> REJECT
DUNCAN_FAIL -> NO OWNER_GATE
REPLAY -> NO SECOND SUBSTANTIVE EXECUTION
OWNER_AUTO_EXECUTION -> ABSENT
AUTO_MERGE/PRODUCTION/CANON/OWNER_LOCK -> ABSENT
ISSUE_102/PR_103 MUTATION -> ABSENT
```

- [ ] **Step 4: Verify exact changed-file scope.**

```bash
git diff --name-only <implementation-base>...HEAD
git status --short
```

No unrelated refactor. No runner config/credentials. No generated model/provider secrets.

- [ ] **Step 5: Record implementation evidence in PR/tracker.** Include exact implementation HEAD, exact changed files, targeted/full test counts, `hq-validate` workflow run/jobs, OSS pins, and explicit:

```text
OWNER_PC_RUNNER_REGISTERED = NO
REMOTE_SUBSTANTIVE_PROOF = NOT_RUN
PRODUCTION_ACTIVE = NO
NEXT = DUNCAN implementation review -> OWNER exact HEAD merge gate -> resolve PRIVATE/DISPOSABLE HOST security gate -> separate activation/proof
```

- [ ] **Step 6: STOP.** Do not merge, register a runner, make the repository private, install owner-PC services, or post a substantive proof message without the next explicit OWNER gate.

---

## Plan Self-Review

### Spec coverage

- `ZB_EXECUTION_REQUEST_V1` / `ZB_EXECUTION_RESULT_V1`: Task 1.
- Static deny-by-default profile registry and Task law: Task 2.
- Native worktree isolation + changed-file/evidence checks: Task 3.
- Backend-neutral worker with OSS coding worker: Task 4.
- Finite timeout, terminal result, public-repo security preflight: Task 5.
- Physical LESTER -> separate DUNCAN proof in-process: Task 6.
- Existing GitHub persistence, replay, Console and human OWNER gate preserved: Task 7.
- Real job topology + immutable artifact transport + separate physical executions: Task 8.
- Negative matrix and activation stop: Task 9.

### OSS reuse ledger

```text
actions/runner 2.334.0        -> job delivery; replaces custom queue/daemon/polling
go-task/task 3.53.1           -> static named profile runner; replaces custom task scheduler
OpenCode 1.18.17              -> optional first coding worker; replaces custom LLM/tool loop
git worktree                  -> workspace isolation; replaces custom workspace copy manager
hashlib / subprocess / pathlib -> evidence/process/path primitives; no extra Python deps
actions/upload-artifact v7    -> immutable inter-job artifact + digest; replaces custom evidence transport
actions/download-artifact v8  -> exact artifact retrieval; replaces custom relay
existing zb_communication_base -> durable GitHub state/read-back/Console; no second controller
```

### Explicitly not reused

- Pueue: redundant queue layer.
- Dagger: useful future isolation option, not needed for R01 base.
- nektos/act: redundant local workflow runner.
- adnanh/webhook: unnecessary exposed inbound trust boundary.
- OpenHands CLI: current upstream maintenance status unsuitable for first backend.
- Pydantic/jsonschema/Click/Typer: unnecessary dependencies for fixed contracts and tiny CLI surface.

### No placeholders

This plan contains no `TBD`, `latest`, unspecified worker/backend, or unresolved activation behavior. Tool versions and action refs are exact. Physical activation remains intentionally gated, not unspecified.

### Next authority gate

Implementation code starts only after DUNCAN plan review and explicit OWNER approval of the exact plan HEAD. Approval of SPEC #120 does not authorize skipping the plan gate.