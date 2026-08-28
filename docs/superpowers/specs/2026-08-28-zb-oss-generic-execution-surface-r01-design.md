# ZORR BLATT — OSS Generic Execution Surface R01

Date: 2026-08-28
Status: exact written spec candidate / OWNER-approved design family
Tracker: issue #106
Base main at spec start: `b4e208e0e6351aea419b7ad77464e8109efc84dd`
OWNER execution-surface decision: issue #106 comment `5453353254`
OWNER exact R01 approval: issue #106 comment `5453370450`
OSS reuse scout: issue #106 comment `5453409956`
Existing communication event surface: PR #111 / DRAFT / OPEN / DO NOT MERGE
Existing GitHub-native base: merged PR #118
Existing Console projection: merged PR #119

## 1. Purpose

Connect real substantive task execution to the already-proven GitHub-native communication base without creating a second controller architecture and without binding ZORR BLATT to one AI vendor or one executor implementation.

The execution surface must turn a validated logical stage into real bounded work and return machine-verifiable evidence:

`GitHub event -> existing ZB admission/routing -> ZB_EXECUTION_REQUEST_V1 -> executor backend -> ZB_EXECUTION_RESULT_V1 -> DUNCAN QC -> existing human OWNER gate -> Console`

The communication base, durable GitHub receipts, replay law, human OWNER gate, and Console projection remain authoritative. This R01 only adds the missing substantive execution layer.

## 2. Owner intent and non-goals

OWNER intent is:

- automate workflow, not personalities;
- OWNER is not the courier;
- use open-source reusable code before writing custom infrastructure;
- keep one authenticated GitHub transport actor, `Lester-Sparx`;
- logical roles remain protocol roles;
- no arbitrary command text from GitHub messages;
- no automatic OWNER execution, merge, production activation, canon mutation, or OWNER LOCK.

R01 does not create a new agent, replace the existing communication bus, reopen issue #102, mutate PR #103, or restore historical account-switching authority.

## 3. OSS reuse decision

R01 deliberately minimizes custom infrastructure by reusing two mature OSS primitives.

### 3.1 Job delivery backend: `actions/runner`

Preferred first transport backend for owner-machine execution:

- upstream: `actions/runner`;
- license: MIT;
- purpose: official open-source GitHub Actions runner application;
- Windows 10/11 x64 supported;
- can run as a Windows service;
- receives real GitHub Actions jobs directly;
- removes the need for a custom queue server, task daemon, webhook receiver, or owner polling loop.

The ZB contract must not depend on `actions/runner`-specific fields except inside the backend adapter. A future local daemon, isolated VM runner, container runner, or other OSS executor may replace it without changing `ZB_EXECUTION_REQUEST_V1` or `ZB_EXECUTION_RESULT_V1`.

### 3.2 Named execution profiles: `go-task/task`

Preferred first command-profile engine:

- upstream: `go-task/task`;
- license: MIT;
- cross-platform;
- named static Taskfile tasks;
- `task --list --json` provides machine-readable task inventory;
- explicit Task exit codes;
- platform gates;
- current v3.53.x line supports per-command timeout.

ZB never forwards a GitHub-provided shell string to Task. ZB maps a validated `EXECUTION_PROFILE` enum to a static Task name from a pinned repository Taskfile.

### 3.3 Explicitly deferred/rejected base dependencies

- `Pueue`: not used in R01. It duplicates job queuing already provided by the runner and is intentionally human-oriented rather than a heavy programmable executor.
- `Dagger`: not a base dependency. It remains an optional future isolation profile where containerized repeatability is worth the extra runtime dependency.
- `nektos/act`: not used. It locally re-implements GitHub Actions through Docker and is redundant when a real self-hosted runner can receive the actual job.
- `adnanh/webhook`: not used as the trust boundary. It would require exposing an inbound service and current upstream has an unresolved 2026 pre-auth request-size DoS report.

## 4. Critical security precondition

The repository is currently `PUBLIC`.

A persistent owner-PC self-hosted runner MUST NOT be registered to the current public repository. GitHub's own security guidance warns that self-hosted runners should almost never be used with public repositories because untrusted fork/PR workflows may execute code on and persistently compromise the runner host.

Therefore:

`OWNER_PC_SELF_HOSTED_RUNNER = ACTIVATION_BLOCKED_WHILE_REPOSITORY_PUBLIC`

Before owner-PC activation, one of these must be true:

A. `Lester-Sparx/zorr-blatt-shared-hq` is private and repository workflow access is re-audited; or
B. execution occurs on an actually disposable isolated VM/host whose compromise cannot expose the owner workstation or durable credentials.

Design/spec/CI work may continue while the repository is public. Real owner-PC runner registration is forbidden until this gate passes.

## 5. Architecture

R01 extends the current base with four narrow units.

### 5.1 Execution contract module

Owns only:

- parsing/rendering `ZB_EXECUTION_REQUEST_V1`;
- parsing/rendering `ZB_EXECUTION_RESULT_V1`;
- identifier/SHA/profile validation;
- replay identity derivation;
- result/evidence consistency checks.

It does not run commands.

### 5.2 Profile registry

A static deny-by-default mapping from `EXECUTION_PROFILE` to a pinned Taskfile task.

Example shape:

```text
LESTER_IMPLEMENT_R01 -> zb:exec:lester:implement-r01
DUNCAN_QC_R01        -> zb:exec:duncan:qc-r01
```

Unknown profile => `EXECUTION_PROFILE_REJECTED` before any local process starts.

The registry may also bind:

- legal logical role;
- working-directory policy;
- timeout;
- network policy declaration;
- allowed write scope;
- expected result schema version;
- required verification commands;
- whether source checkout must be read-only before a dedicated worktree is created.

### 5.3 Backend adapter

The adapter receives one already-validated execution request and invokes one static profile. The first implementation substrate is a trusted GitHub Actions job running on an eligible self-hosted runner and invoking Task.

The adapter may translate trusted workflow metadata into physical provenance fields such as workflow run ID, run attempt, runner name, and runner labels. It may not derive logical authority from those fields.

### 5.4 Evidence verifier

After execution, independent ZB code verifies the result instead of trusting process exit code alone.

Required checks include, as applicable:

- result schema valid;
- request/result IDs match;
- expected profile/version matches actual profile/version;
- exact base SHA and task revision match;
- terminal state is recognized;
- exit/result code is consistent;
- reported changed files stay within allowed scope;
- actual Git HEAD/diff/evidence matches the report;
- required tests/checks have evidence;
- no forbidden merge/activation/canon mutation occurred.

## 6. `ZB_EXECUTION_REQUEST_V1`

Every substantive execution request must contain exactly one immutable request identity and enough data to reproduce the authority boundary.

Minimum fields:

```text
ZB_EXECUTION_REQUEST_V1
EXECUTION_REQUEST_ID
MESSAGE_ID
EVENT_ID
CORRELATION_ID
CAUSATION_MESSAGE_ID
TASK_ID
TASK_REVISION
LOGICAL_ROLE
EXECUTION_PROFILE
EXECUTION_PROFILE_VERSION
BASE_SHA
AUTHORITY_REF
DESIGN_HEAD
SOURCE_REFS
EVIDENCE_INPUT_REFS
ALLOWED_WRITE_SCOPE
TIMEOUT_SECONDS
NO_AUTO_MERGE = TRUE
PRODUCTION_ACTIVE = NO
```

Rules:

- identifiers must match the existing ZB bounded identifier grammar;
- SHA fields are exact 40-hex where a Git SHA is required;
- `LOGICAL_ROLE` must be legal for the selected profile;
- `EXECUTION_PROFILE` must exist in the static registry;
- `ALLOWED_WRITE_SCOPE` must be resolved from trusted registry policy, not expanded by message text;
- `TIMEOUT_SECONDS` may only reduce the registry maximum, never increase it;
- request body is immutable after durable admission;
- retry creates a new physical attempt receipt, not a mutated request.

## 7. `ZB_EXECUTION_RESULT_V1`

Every started substantive run must end in exactly one machine-readable terminal result.

Minimum fields:

```text
ZB_EXECUTION_RESULT_V1
EXECUTION_REQUEST_ID
EXECUTION_ID
ATTEMPT
MESSAGE_ID
CORRELATION_ID
TASK_ID
TASK_REVISION
LOGICAL_ROLE
EXECUTION_PROFILE
EXECUTION_PROFILE_VERSION
BASE_SHA
START_HEAD
END_HEAD
TERMINAL_STATE
RESULT_CODE
PROCESS_EXIT_CODE
CHANGED_FILES
TEST_EVIDENCE_REFS
ARTIFACT_EVIDENCE_REFS
WORKFLOW_RUN_ID
WORKFLOW_RUN_ATTEMPT
RUNNER_PROVENANCE
STARTED_AT
FINISHED_AT
PRODUCTION_ACTIVE = NO
```

Recognized terminal states for R01:

- `PASS`;
- `FAIL`;
- `BLOCKED`;
- `TIMEOUT`;
- `EXECUTION_ERROR`.

No terminal result may claim PASS if the independent evidence verifier fails.

## 8. Physical execution identity

Each physical backend invocation gets a unique immutable `EXECUTION_ID`.

For the first GitHub self-hosted backend, the canonical form is derived from trusted workflow identity, for example:

`github-actions:<workflow_run_id>:<run_attempt>:<job_name>`

LESTER and DUNCAN MUST use different physical job executions and therefore different `EXECUTION_ID` values even if the same Windows machine performs both jobs.

A logical role field alone never proves independence.

## 9. LESTER execution flow

After existing communication admission proves a legal `JINGO -> LESTER / ASSIGN`:

1. create durable execution request evidence bound to exact task/revision/base/design;
2. fresh-read request evidence;
3. dispatch one LESTER backend job only if security/runner eligibility gates pass;
4. backend checks exact profile inventory before execution;
5. create a dedicated temporary execution workspace/worktree;
6. invoke the static Task profile;
7. capture terminal result and actual repository evidence;
8. independently verify the result;
9. write durable `LESTER RESULT_READY` only after verification passes;
10. fresh-read exact durable result before routing to DUNCAN.

No LESTER result automatically grants OWNER approval.

## 10. DUNCAN independent QC flow

DUNCAN receives the exact immutable LESTER result plus its evidence references.

Required separation:

- a different workflow job/execution ID;
- a fresh QC workspace/read context;
- no reuse of mutable LESTER process state as authority;
- DUNCAN profile is distinct from LESTER profile;
- DUNCAN independently reads the exact target HEAD/diff/test evidence;
- DUNCAN returns PASS/FAIL/BLOCKED only for the exact request/result pair.

Only a verified DUNCAN PASS may advance the existing workflow toward the human OWNER gate.

## 11. Workspace and host safety

A self-hosted runner is not assumed to provide a clean VM per job.

R01 therefore requires:

- dedicated low-privilege OS account for the runner where feasible;
- no administrator requirement for normal execution profiles;
- no long-lived secrets copied into the repository workspace;
- fresh temporary worktree or equivalent bounded workspace per execution;
- preflight dirty-state check;
- post-run changed-file audit;
- cleanup of temporary execution workspace after evidence capture;
- fail closed when cleanup or provenance checks cannot be established;
- no task may modify the runner service installation/configuration.

A future Dagger/container profile may strengthen isolation without changing the ZB contract.

## 12. Taskfile law

The Taskfile is executable policy and therefore must be pinned and reviewed like code.

R01 requirements:

- Taskfile exists in repository authority, not downloaded dynamically at runtime;
- remote Taskfiles are forbidden for R01;
- dynamic profile names are forbidden;
- `CLI_ARGS` from untrusted GitHub body are forbidden;
- Task inventory is inspected with `task --list --json` before execution;
- selected task name must exactly equal the trusted registry mapping;
- Task binary version is recorded in result provenance;
- implementation pins an accepted Task release/checksum before activation;
- per-command/profile timeout must be bounded;
- Taskfile changes require ordinary PR/QC/OWNER authority before becoming live execution policy.

## 13. GitHub workflow law

The current `issue_comment.created` admission remains on the GitHub-hosted validation job. Untrusted source text must never directly choose `runs-on`, command text, checkout ref, or secret name.

The substantive job may target a custom self-hosted label only after the repository-visibility security gate passes.

The execution workflow must preserve:

- exact actor `Lester-Sparx` at transport admission;
- exact communication surface PR #111;
- default-branch workflow authority;
- least permissions;
- human OWNER stop;
- no `pull_request_target` path to substantive untrusted checkout;
- no arbitrary checkout ref from message fields;
- no automatic merge or production activation.

## 14. Replay and idempotency

Canonical replay key:

`EXECUTION_REQUEST_ID + EXECUTION_PROFILE_VERSION + BASE_SHA + TASK_REVISION`

Before dispatch, durable state is checked for an existing in-progress or terminal attempt for the same replay key.

Rules:

- terminal PASS/FAIL/BLOCKED => no duplicate execution;
- in-progress recognized attempt => no second concurrent execution;
- retry after approved retryable failure uses a new physical `ATTEMPT` and `EXECUTION_ID` while preserving immutable request identity;
- a replay may repair missing projection/evidence publication only when the underlying completed execution is uniquely identified and exact-read verified;
- replay never silently re-runs substantive work.

## 15. Timeouts and failures

Every profile has a finite maximum timeout.

Failure classes include:

- `EXECUTION_PROFILE_REJECTED`;
- `RUNNER_UNAVAILABLE`;
- `RUNNER_SECURITY_GATE_BLOCKED`;
- `BASE_SHA_MISMATCH`;
- `TASK_REVISION_MISMATCH`;
- `PROFILE_INVENTORY_MISMATCH`;
- `WORKSPACE_DIRTY`;
- `PROCESS_FAILED`;
- `TIMEOUT`;
- `RESULT_SCHEMA_INVALID`;
- `EVIDENCE_MISMATCH`;
- `WRITE_SCOPE_VIOLATION`;
- `DUNCAN_QC_FAIL`.

Authenticated failures may write one compact durable blocker. Missing evidence is never converted into PASS.

## 16. Permissions

R01 does not expand the existing communication base into repository-owner automation.

Cloud admission/persistence stays least privilege.

The owner-machine backend receives only what the selected execution profile needs. Registration credentials, runner private keys, AI-tool credentials, or local tokens must never appear in GitHub comments, result payloads, test fixtures, or committed config.

No profile may grant itself wider repository authority than its registry entry.

## 17. Required implementation tests

Before activation review, TDD must cover at minimum:

### Contract

- valid request parses;
- unknown/missing/duplicate fields reject;
- unknown profile rejects;
- role/profile mismatch rejects;
- stale base/task revision rejects;
- timeout escalation rejects;
- write-scope expansion rejects.

### Profile registry

- static mapping only;
- no GitHub-body shell interpolation;
- Task inventory exact match required;
- remote Taskfile forbidden;
- invalid Task version/provenance blocks.

### Backend adapter

- correct physical execution ID;
- LESTER and DUNCAN IDs differ;
- unavailable/ineligible runner blocks;
- subprocess/Task failure maps to terminal failure;
- timeout maps correctly;
- no result on never-started job is mislabeled RUNNING/PASS.

### Evidence

- actual changed files outside allowlist fail;
- head/diff mismatch fails;
- missing required test evidence fails;
- exact result read-back required;
- replay does not duplicate substantive execution.

### Safety

- OWNER never auto-executes;
- merge/auto-merge helpers absent;
- production activation remains NO;
- issue #102 and PR #103 untouched;
- public-repository owner-PC runner activation is rejected by explicit preflight/config gate.

## 18. Implementation sequence

After OWNER accepts this written spec:

1. write a separate implementation plan;
2. TDD contract + static profile registry first;
3. add Taskfile profiles and version/provenance checks;
4. add backend abstraction with a fake/local test backend;
5. add GitHub self-hosted backend wiring but keep activation blocked while repo is public;
6. DUNCAN code review and full regression;
7. OWNER exact implementation HEAD merge gate;
8. resolve repository-visibility/disposable-host security gate;
9. register/configure execution backend only after that separate gate;
10. run one disposable substantive proof;
11. run separate DUNCAN QC proof;
12. require existing OWNER gate + Console projection.

## 19. Success criterion

R01 is complete only when one authenticated ZB root message causes:

1. existing GitHub-native admission;
2. one real bounded LESTER execution on an authorized OSS-backed execution surface;
3. schema-valid and independently verified `ZB_EXECUTION_RESULT_V1` bound to exact base/task/profile/evidence;
4. a separate DUNCAN execution instance independently reviewing that exact result;
5. durable fresh-read-matched PASS/FAIL evidence;
6. continuation to the existing human OWNER gate and Console projection;
7. exact replay causing no duplicate substantive execution;
8. no arbitrary shell injection, merge, production activation, canon mutation, OWNER LOCK, issue #102 mutation, or PR #103 mutation.

Until the repository-visibility/isolated-host gate and physical proof are satisfied:

`PRODUCTION_ACTIVE = NO`

`SUBSTANTIVE_EXECUTION = NOT YET ACTIVATED`
