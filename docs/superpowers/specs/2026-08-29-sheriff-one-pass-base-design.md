# SHERIFF V1 — ONE-PASS Windows Production Base Design

Status: DESIGN / NOT YET IMPLEMENTED
Tracker: issue #181
Base main at design start: `d805242a8ba6e2b169c1216acd3df86b8f9ddd84`
Authoritative SHERIFF runtime: `47a92fc4a0d685e1a892285c568a59dfc5ccac82`

## Goal

Replace the fragile Windows deployment critical path with one canonical, idempotent installer that reaches the existing SHERIFF V1 owner-PC production gate without runtime source patching, wrapper accumulation, or one-prerequisite-per-run discovery.

This is not SHERIFF V2 and does not change SHERIFF policy, schemas, service topology, event semantics, scoring, or runtime behavior. It is a deployment-path simplification required to finish issue #181.

## Problem

The current Windows path downloads the old merged deployer from `ab816ff383c74d1c72ee36df31bc381cf062f52b`, then mutates that source text at runtime through `Patch-ForWindows10`, `Patch-PodmanMachineFirstInit`, and `Patch-EvidenceTransport` before executing it.

That design creates avoidable failure boundaries:

- host requirements are discovered sequentially instead of preflighted as one dependency set;
- Windows PowerShell 5.1 native stderr behavior can turn expected nonzero native states into terminating errors;
- source-text replacement makes correctness depend on exact historical strings;
- extra launchers and substring guards can fail independently of the installer they are meant to protect;
- physical owner-PC testing repeatedly exposes the next host prerequisite only after the previous one is repaired.

Observed physical progression has already proven the important host facts: Windows build 19044, WSL ready, OpenSSH client ready, Podman 5.8.5 selected for Windows 10, and first Podman VM creation reached `PODMAN_MACHINE_FIRST_INIT_SAFE`. Final production PASS is still not proven.

## Design decision

Use one production PowerShell script as the authoritative Windows host installer:

`config/sheriff/deploy/windows/SheriffHost.ps1`

It directly contains the currently proven host logic instead of downloading and rewriting `ZbSheriffV1.ps1`.

The only launcher responsibility is:

`download exact immutable SheriffHost.ps1 -> verify exact Git blob/hash -> execute`

No launcher may inspect installer internals with substring checks.

## Critical path

The one authoritative path is:

`PRECHECK -> REPAIR -> REBOOT_PENDING (only if required) -> INSTALL -> VERIFY -> PASS`

A repeat invocation is safe and resumes from actual machine state; it does not depend on a versioned R5/R6/R7/R8/R9 wrapper history.

### PRECHECK

Before starting the SHERIFF stack, gather the full host dependency state and print one compact report:

- supported Windows build;
- hardware virtualization signal when Windows exposes it;
- WSL command/status and WSL2 readiness on the Windows 10 path;
- OpenSSH Client / `ssh-keygen.exe` readiness;
- Podman installation/version and expected provider;
- Podman machine existence/running state;
- pinned Compose provider availability/hash;
- network reachability for immutable upstream downloads;
- runtime root/state root writability;
- Task Scheduler availability.

PRECHECK must not call SHERIFF container startup.

### REPAIR

Repair only missing required host prerequisites using native/upstream-supported mechanisms:

- WSL: Windows optional features plus official `wsl.exe` commands;
- OpenSSH Client: Windows capability `OpenSSH.Client~~~~0.0.1.0`;
- Podman: pinned official Podman MSI already selected by supported Windows branch;
- Compose: pinned official Compose binary and hash;
- Podman machine: official `podman machine init/start` flow.

No OpenSSH Server, Docker Desktop, custom SSH service, custom container daemon, or unrelated Windows feature is introduced.

If WSL feature repair requires reboot, register one one-shot resume task, persist only the minimum resume marker, request one reboot, and continue after logon. The resume task removes itself before continuing so a later failure cannot create a repeated login loop.

### Native command execution

All native tools (`wsl.exe`, `podman.exe`, `msiexec.exe`, Compose provider commands, health utilities) go through one common process runner that records:

- executable;
- arguments;
- exit code;
- stdout;
- stderr;
- bounded timeout.

Expected nonzero states are handled by exit code, not by PowerShell error-stream coercion. This removes the `ErrorActionPreference=Stop` / native stderr failure class that affected first Podman machine probing.

### INSTALL

INSTALL reuses the already-proven SHERIFF runtime and service topology:

- materialize exact runtime commit `47a92fc4a0d685e1a892285c568a59dfc5ccac82`;
- preserve the existing pinned SHERIFF Compose definition and nine required services;
- generate local secrets once and reuse them;
- start the stack with Podman + pinned Compose provider;
- register the existing current-user Task Scheduler lifecycle pattern for `ZB Sheriff V1`;
- start the scheduled task.

No policy/schema/runtime semantic change is allowed in this migration.

### VERIFY

VERIFY is the only production gate. It must freshly prove:

- scheduled task registered;
- scheduled task enabled;
- all required services running;
- health harness passes;
- live synthetic event path passes;
- sheriff-worker restart passes;
- health and live smoke pass again after restart.

Local GitHub CLI/authentication is not a production dependency. Evidence posting may be performed by connected ChatGPT/GitHub after the physical result exists.

## Actions and idempotency

`SheriffHost.ps1` exposes only the operations needed by the base:

- `RunToPass` — default; PRECHECK, repair if needed, install, verify;
- `Preflight` — read/diagnose host readiness without starting SHERIFF;
- `Verify` — verify an already installed base;
- `Status` — compact read-only status;
- `Uninstall` — remove the SHERIFF scheduled task/stack while leaving unrelated host prerequisites intact.

There is no runtime `Patch-*` stage.

Repeated `RunToPass` on an already healthy machine should perform no destructive reinstall and end at the same PASS evidence.

## Version selection

Preserve the proven compatibility policy unless fresh upstream evidence requires a separate authorized change:

- Windows 10 build >= 19043 and < 22000: Podman 5.8.5 / WSL provider;
- Windows 11 build >= 22000: proven Podman 6.1.0 path;
- unsupported Windows build: fail closed before mutation.

Exact download hashes remain pinned and verified.

## Testing strategy

Tests verify behavior and execution order, not just source-string presence.

Required deterministic cases:

1. WSL absent -> repair plan includes WSL before Podman.
2. WSL repair requires reboot -> one-shot resume, no install before reboot.
3. `ssh-keygen` absent -> OpenSSH Client repair before Podman machine init.
4. OpenSSH installed but PATH missing -> process PATH repair without reinstall.
5. Podman machine absent -> `machine init` then start.
6. Podman machine already exists -> reuse without init.
7. Native command writes stderr with an expected nonzero exit -> caller decides by exit code; PowerShell does not terminate implicitly.
8. Repeat `RunToPass` on healthy state -> no duplicate machine/task/secrets; verification still runs.
9. Physical evidence output format contains exactly one final PASS/FAIL state.

Fresh gates before merge:

- Windows PowerShell 5.1 parse/execution validation;
- host-state/state-machine tests on Windows CI;
- existing `hq-validate`;
- existing `sheriff-oss-validate`;
- existing full `sheriff-runtime-e2e`;
- independent review of exact candidate HEAD.

## Migration

1. Implement `SheriffHost.ps1` by consolidating existing proven logic, not rewriting SHERIFF behavior.
2. Change the repository one-click runner to call the canonical installer.
3. Keep legacy `ZbSheriffV1.ps1` and `BootstrapSheriffV1Host.ps1` only long enough for migration comparison, clearly marked non-authoritative; remove them from the critical path.
4. After exact candidate CI/QC PASS, merge with SHA lock.
5. Build one final exact-blob launcher artifact from the merged canonical installer.
6. Run once on owner PC.
7. If physical VERIFY passes, post durable evidence to issue #181, mark SHERIFF V1 base PASS/LOCKED, and stop changing the base.
8. If physical VERIFY fails, repair only the first new evidenced boundary in the canonical installer; do not create another wrapper generation.

## Explicit non-goals

- no SHERIFF V2;
- no dashboard/league/competition work;
- no new agent or daemon;
- no self-hosted GitHub runner as part of this base;
- no Docker Desktop dependency;
- no OpenSSH Server;
- no change to the authoritative SHERIFF runtime commit;
- no change to production policy/schema/event semantics;
- no owner-PC remote shell architecture.

## Acceptance criteria

Implementation is code-ready only when all fresh exact-HEAD CI/QC gates pass.

Production is PASS only when fresh owner-PC evidence proves:

```text
TASK_REGISTERED = YES
TASK_ENABLED = YES
STACK_SERVICES_RUNNING = PASS
SHERIFF_LIVE_PATH = PASS
WORKER_RESTART = PASS
SHERIFF_V1_24_7_PRODUCTION_ACTIVE = YES
BLOCKER = NONE
```

Then and only then record:

`SHERIFF_V1_BASE = PASS / LOCKED`

Until that physical evidence exists, state remains `NOT PROVEN`.
