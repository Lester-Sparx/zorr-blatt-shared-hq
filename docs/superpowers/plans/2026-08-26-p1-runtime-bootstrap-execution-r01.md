# P1 Runtime Bootstrap Execution R01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the minimal, reproducible, PR+CI-governed Rust execution-plane foundation in `Lester-Sparx/zorr-blatt-runtime`, then stop with `P1 RUNTIME BOOTSTRAP = COMPLETE` and `P1 IMPLEMENTATION = NOT STARTED`.

**Architecture:** The runtime remains a separate execution plane bound to the exact accepted Shared HQ architecture. An empty-repository anchor commit exists only to make GitHub branch/PR mechanics possible; all bootstrap foundation content is introduced on a Lester-authored candidate branch through PR + CI. Five empty logical crates establish allowed dependency direction without implementing P1 business logic.

**Tech Stack:** Rust `1.98.0`, Cargo workspace resolver `3`, Python 3 standard library for ZB-specific bootstrap policy validation, GitHub Actions, `actions/checkout` pinned to commit `11d5960a326750d5838078e36cf38b85af677262` (tag `v4.4.0`).

**Spec:** `docs/superpowers/specs/2026-08-26-p1-runtime-bootstrap-design.md`

## Global Constraints

- Runtime repository is exactly `Lester-Sparx/zorr-blatt-runtime` and must remain PRIVATE.
- Builder-authored runtime mutations must be authenticated as `Lester-Sparx`; do not create builder commits as `Duncan-Sparx-ZB` and relabel them.
- Shared HQ remains control / authority / evidence plane; runtime is execution plane only.
- Exact architecture binding is fixed to Shared HQ commit `2e9eb6540c1d07357cb78f44591f6192dbf7b433`, path `docs/ZB_PRODUCTION_INTEGRATION_ARCHITECTURE_R01.md`, blob `3a26469d62d6b7622a477e78c79a0b3cad824695`, revision `R01`.
- Rust toolchain is pinned to `1.98.0`; no `stable`, `latest`, wildcard or floating production toolchain identifier is allowed.
- `Cargo.lock` is committed and all Cargo verification commands use `--locked` where supported.
- Bootstrap introduces no external Rust crates. REUSE-FIRST still applies: no generic implementation is written because bootstrap does not yet require canonicalization/hash business logic.
- Bootstrap crates establish boundaries only; no Character DNA, REST_RIG, body compiler, mesh generation, OxiHuman, Babylon, Motion Truth, Action Truth, animation, camera solver, Grani, coordinate-system lock, G2, Voice-to-Shot, OWNER LOCK or runtime activation.
- `P1 RUNTIME BOOTSTRAP COMPLETE ≠ P1 IMPLEMENTATION STARTED`.
- Direct production development on `main` is forbidden after the mechanical repository anchor exists; foundation changes use candidate branch → PR → CI → review → merge.
- The repository anchor contains no code, dependency, runtime configuration or architecture implementation and is not itself bootstrap completion evidence.
- Every proof/review binds exact commit SHA; branch names are informational only.

---

## File Structure

The bootstrap PR creates exactly this foundation in the runtime repository in addition to the pre-existing `.zb-repository-anchor`:

```text
zorr-blatt-runtime/
├─ .zb-repository-anchor
├─ .gitignore
├─ Cargo.toml
├─ Cargo.lock
├─ README.md
├─ rust-toolchain.toml
├─ .github/
│  └─ workflows/
│     └─ p1-ci.yml
├─ scripts/
│  └─ check_bootstrap.py
├─ provenance/
│  └─ architecture-binding.json
├─ crates/
│  ├─ zb-contracts/
│  │  ├─ Cargo.toml
│  │  └─ src/lib.rs
│  ├─ zb-canonical/
│  │  ├─ Cargo.toml
│  │  └─ src/lib.rs
│  ├─ zb-authority/
│  │  ├─ Cargo.toml
│  │  └─ src/lib.rs
│  ├─ zb-provenance/
│  │  ├─ Cargo.toml
│  │  └─ src/lib.rs
│  └─ zb-validation/
│     ├─ Cargo.toml
│     └─ src/lib.rs
└─ tests/
   ├─ authority-boundary/.gitkeep
   ├─ canonical-determinism/.gitkeep
   ├─ unresolved-policy/.gitkeep
   ├─ source-bindings/.gitkeep
   └─ dependency-direction/.gitkeep
```

Responsibilities:

- `.zb-repository-anchor`: neutral first commit enabling GitHub branch/PR mechanics in an otherwise empty repository.
- `Cargo.toml`: single workspace membership and shared package metadata only.
- `Cargo.lock`: exact Cargo resolution; initially contains only the five local packages.
- `rust-toolchain.toml`: exact Rust `1.98.0` + `rustfmt` + `clippy`.
- `provenance/architecture-binding.json`: exact immutable Shared HQ architecture binding.
- `scripts/check_bootstrap.py`: ZB-specific structural, binding and dependency-direction verification.
- `.github/workflows/p1-ci.yml`: baseline bootstrap checks only.
- five `crates/*`: empty boundary crates; no P1 business logic.
- `tests/*`: reserved harness locations only; no substantive P1 test suite yet.

---

### Task 1: Create the Empty-Repository Anchor as Lester

**Files:**
- Create on runtime `main`: `.zb-repository-anchor`

**Interfaces:**
- Consumes: existing empty PRIVATE repository `Lester-Sparx/zorr-blatt-runtime`.
- Produces: first immutable commit SHA on `main`, used only as the base for `bootstrap/p1-runtime-bootstrap-r01`.

- [ ] **Step 1: Verify authenticated builder identity**

Run connector identity check and require exact login:

```text
Lester-Sparx
```

If the authenticated actor is not `Lester-Sparx`, STOP. Do not create runtime commits.

- [ ] **Step 2: Verify repository preconditions**

Require:

```text
repository = Lester-Sparx/zorr-blatt-runtime
visibility = private
size = 0
```

If the repository contains user-created bootstrap files, inspect them before proceeding; do not overwrite silently.

- [ ] **Step 3: Create the neutral anchor file on `main`**

Exact file content:

```text
ZORR BLATT RUNTIME REPOSITORY ANCHOR

This commit exists only to establish the first Git object required for branch and pull-request mechanics in an otherwise empty repository.

It contains no runtime implementation and does not constitute P1 Runtime Bootstrap completion or P1 Implementation authorization.
```

Commit message:

```text
chore: establish empty runtime repository anchor
```

- [ ] **Step 4: Record the exact anchor commit SHA**

Record as:

```text
RUNTIME_ANCHOR_SHA=<exact commit>
```

Do not call it bootstrap completion evidence.

- [ ] **Step 5: Create candidate branch from the exact anchor SHA**

Branch:

```text
bootstrap/p1-runtime-bootstrap-r01
```

Expected: candidate branch points exactly at `RUNTIME_ANCHOR_SHA` before bootstrap files are added.

---

### Task 2: Create the Pinned Rust Workspace Skeleton

**Files:**
- Create: `Cargo.toml`
- Create: `rust-toolchain.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: five crate manifests and five `src/lib.rs` files listed in File Structure.

**Interfaces:**
- Consumes: exact runtime anchor branch.
- Produces: a valid five-crate Cargo workspace with no external dependencies and no P1 business logic.

- [ ] **Step 1: Create root `Cargo.toml`**

Exact content:

```toml
[workspace]
members = [
    "crates/zb-contracts",
    "crates/zb-canonical",
    "crates/zb-authority",
    "crates/zb-provenance",
    "crates/zb-validation",
]
resolver = "3"

[workspace.package]
version = "0.0.0"
edition = "2024"
rust-version = "1.98"
publish = false
```

- [ ] **Step 2: Create `rust-toolchain.toml`**

Exact content:

```toml
[toolchain]
channel = "1.98.0"
profile = "minimal"
components = ["rustfmt", "clippy"]
```

- [ ] **Step 3: Create `.gitignore`**

Exact content:

```gitignore
/target/
.DS_Store
*.swp
*.swo
```

- [ ] **Step 4: Create root `README.md`**

Exact content:

```markdown
# ZORR BLATT Runtime

Private execution-plane repository for ZORR BLATT.

## Bootstrap boundary

This repository implements the exact Shared HQ architecture binding in `provenance/architecture-binding.json`.

Current authorized scope is **P1 Runtime Bootstrap foundation only**.

```text
P1 RUNTIME BOOTSTRAP COMPLETE ≠ P1 IMPLEMENTATION STARTED
```

The bootstrap may contain workspace boundaries, exact toolchain/dependency locking, provenance binding, baseline CI and empty test-harness structure. It must not contain Character DNA, body generation, motion/action, cinematography, Babylon, Grani, coordinate lock, G2, Voice-to-Shot, OWNER LOCK or production activation logic.

Shared HQ remains the control / authority / evidence plane. This runtime may produce implementation evidence; it may not approve itself or redefine Shared HQ authority.
```

- [ ] **Step 5: Create each crate manifest**

For `crates/zb-contracts/Cargo.toml`:

```toml
[package]
name = "zb-contracts"
version.workspace = true
edition.workspace = true
rust-version.workspace = true
publish.workspace = true

[dependencies]
```

For `crates/zb-canonical/Cargo.toml`:

```toml
[package]
name = "zb-canonical"
version.workspace = true
edition.workspace = true
rust-version.workspace = true
publish.workspace = true

[dependencies]
```

For `crates/zb-authority/Cargo.toml`:

```toml
[package]
name = "zb-authority"
version.workspace = true
edition.workspace = true
rust-version.workspace = true
publish.workspace = true

[dependencies]
```

For `crates/zb-provenance/Cargo.toml`:

```toml
[package]
name = "zb-provenance"
version.workspace = true
edition.workspace = true
rust-version.workspace = true
publish.workspace = true

[dependencies]
```

For `crates/zb-validation/Cargo.toml`:

```toml
[package]
name = "zb-validation"
version.workspace = true
edition.workspace = true
rust-version.workspace = true
publish.workspace = true

[dependencies]
```

No dependency is added merely to imitate the allowed arrow graph.

- [ ] **Step 6: Create each crate `src/lib.rs`**

Exact contents:

`crates/zb-contracts/src/lib.rs`

```rust
//! ZORR BLATT contract boundary.
//!
//! Bootstrap only: P1 contract behavior is not implemented in this crate yet.
```

`crates/zb-canonical/src/lib.rs`

```rust
//! ZORR BLATT canonicalization boundary.
//!
//! Bootstrap only: canonical JSON and hashing behavior are not implemented yet.
```

`crates/zb-authority/src/lib.rs`

```rust
//! ZORR BLATT authority boundary.
//!
//! Bootstrap only: authority/writeback behavior is not implemented yet.
```

`crates/zb-provenance/src/lib.rs`

```rust
//! ZORR BLATT provenance boundary.
//!
//! Bootstrap only: runtime provenance behavior is not implemented yet.
```

`crates/zb-validation/src/lib.rs`

```rust
//! ZORR BLATT validation boundary.
//!
//! Bootstrap only: P1 validation behavior is not implemented yet.
```

- [ ] **Step 7: Commit the workspace skeleton**

Commit message:

```text
chore: scaffold pinned P1 runtime workspace
```

Expected: only foundation files from this task changed; no external dependencies and no runtime business logic.

---

### Task 3: Bind the Exact Shared HQ Architecture and Test-Harness Locations

**Files:**
- Create: `provenance/architecture-binding.json`
- Create: five `.gitkeep` files under `tests/`.

**Interfaces:**
- Consumes: accepted Integration Architecture R01 exact binding.
- Produces: machine-readable authority reference plus empty locations for later separately-authorized P1 tests.

- [ ] **Step 1: Create `provenance/architecture-binding.json`**

Exact content:

```json
{
  "authorityRepository": "Lester-Sparx/zorr-blatt-shared-hq",
  "authorityCommit": "2e9eb6540c1d07357cb78f44591f6192dbf7b433",
  "architecturePath": "docs/ZB_PRODUCTION_INTEGRATION_ARCHITECTURE_R01.md",
  "architectureGitBlob": "3a26469d62d6b7622a477e78c79a0b3cad824695",
  "architectureRevision": "R01"
}
```

- [ ] **Step 2: Create empty harness markers**

Create zero-byte `.gitkeep` files at:

```text
tests/authority-boundary/.gitkeep
tests/canonical-determinism/.gitkeep
tests/unresolved-policy/.gitkeep
tests/source-bindings/.gitkeep
tests/dependency-direction/.gitkeep
```

These paths reserve later P1 test categories; they contain no test implementation at bootstrap.

- [ ] **Step 3: Commit provenance and harness skeleton**

Commit message:

```text
chore: bind runtime bootstrap to exact HQ architecture
```

---

### Task 4: Add ZB-Specific Bootstrap Validator

**Files:**
- Create: `scripts/check_bootstrap.py`

**Interfaces:**
- Consumes: workspace manifests, toolchain file, lockfile, architecture binding.
- Produces: exit code `0` only when bootstrap structure/binding/dependency direction satisfies the accepted foundation contract.

- [ ] **Step 1: Create `scripts/check_bootstrap.py`**

Exact content:

```python
#!/usr/bin/env python3
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

EXPECTED_FILES = [
    "Cargo.toml",
    "Cargo.lock",
    "rust-toolchain.toml",
    "README.md",
    "provenance/architecture-binding.json",
    "crates/zb-contracts/Cargo.toml",
    "crates/zb-contracts/src/lib.rs",
    "crates/zb-canonical/Cargo.toml",
    "crates/zb-canonical/src/lib.rs",
    "crates/zb-authority/Cargo.toml",
    "crates/zb-authority/src/lib.rs",
    "crates/zb-provenance/Cargo.toml",
    "crates/zb-provenance/src/lib.rs",
    "crates/zb-validation/Cargo.toml",
    "crates/zb-validation/src/lib.rs",
    "tests/authority-boundary/.gitkeep",
    "tests/canonical-determinism/.gitkeep",
    "tests/unresolved-policy/.gitkeep",
    "tests/source-bindings/.gitkeep",
    "tests/dependency-direction/.gitkeep",
]

EXPECTED_BINDING = {
    "authorityRepository": "Lester-Sparx/zorr-blatt-shared-hq",
    "authorityCommit": "2e9eb6540c1d07357cb78f44591f6192dbf7b433",
    "architecturePath": "docs/ZB_PRODUCTION_INTEGRATION_ARCHITECTURE_R01.md",
    "architectureGitBlob": "3a26469d62d6b7622a477e78c79a0b3cad824695",
    "architectureRevision": "R01",
}

RANK = {
    "zb-contracts": 0,
    "zb-canonical": 1,
    "zb-authority": 2,
    "zb-provenance": 3,
    "zb-validation": 4,
}


def fail(message: str) -> None:
    print(f"bootstrap-check: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


for rel in EXPECTED_FILES:
    if not (ROOT / rel).exists():
        fail(f"missing required bootstrap path: {rel}")

binding = json.loads((ROOT / "provenance/architecture-binding.json").read_text())
if binding != EXPECTED_BINDING:
    fail("architecture binding does not match exact accepted R01 binding")

toolchain_text = (ROOT / "rust-toolchain.toml").read_text()
if 'channel = "1.98.0"' not in toolchain_text:
    fail("rust-toolchain.toml must pin channel 1.98.0")

metadata = json.loads(
    subprocess.check_output(
        ["cargo", "metadata", "--format-version", "1", "--no-deps", "--locked"],
        cwd=ROOT,
        text=True,
    )
)

workspace_packages = {
    package["name"]: package
    for package in metadata["packages"]
    if package["name"] in RANK
}

if set(workspace_packages) != set(RANK):
    fail(
        "workspace packages differ from required foundation crates: "
        + ", ".join(sorted(workspace_packages))
    )

for package_name, package in workspace_packages.items():
    package_rank = RANK[package_name]
    for dep in package["dependencies"]:
        dep_name = dep["name"]
        if dep_name not in RANK:
            continue
        if RANK[dep_name] >= package_rank:
            fail(
                f"forbidden dependency direction: {package_name} -> {dep_name}"
            )

print("bootstrap-check: PASS")
```

The rank rule encodes **allowed direction only**: a downstream crate may depend on any genuinely required upstream crate; no adjacency dependency is forced.

- [ ] **Step 2: Verify the validator fails before `Cargo.lock` exists**

Run:

```bash
python3 scripts/check_bootstrap.py
```

Expected: FAIL with `missing required bootstrap path: Cargo.lock`.

This is the RED check for the bootstrap validator.

- [ ] **Step 3: Generate `Cargo.lock` using the pinned toolchain**

Run:

```bash
rustup toolchain install 1.98.0 --profile minimal --component rustfmt,clippy
cargo +1.98.0 generate-lockfile
```

Expected: `Cargo.lock` created with only the five local workspace packages and no third-party package dependency entries.

- [ ] **Step 4: Re-run validator**

Run:

```bash
python3 scripts/check_bootstrap.py
```

Expected:

```text
bootstrap-check: PASS
```

- [ ] **Step 5: Prove forbidden direction detection**

Temporarily add this line under `[dependencies]` in `crates/zb-contracts/Cargo.toml`:

```toml
zb-validation = { path = "../zb-validation" }
```

Run:

```bash
cargo +1.98.0 generate-lockfile
python3 scripts/check_bootstrap.py
```

Expected: FAIL containing:

```text
forbidden dependency direction: zb-contracts -> zb-validation
```

Revert the temporary dependency and regenerate the clean lockfile:

```bash
git checkout -- crates/zb-contracts/Cargo.toml
cargo +1.98.0 generate-lockfile
python3 scripts/check_bootstrap.py
```

Expected: PASS.

- [ ] **Step 6: Commit validator and clean lockfile**

Commit message:

```text
test: enforce P1 bootstrap structure and dependency direction
```

---

### Task 5: Add Baseline PR CI with Pinned Reusable Tooling

**Files:**
- Create: `.github/workflows/p1-ci.yml`

**Interfaces:**
- Consumes: exact workspace/toolchain/validator.
- Produces: PR and `main` baseline verification for bootstrap scope only.

- [ ] **Step 1: Create `.github/workflows/p1-ci.yml`**

Exact content:

```yaml
name: p1-bootstrap

on:
  pull_request:
  push:
    branches:
      - main

permissions:
  contents: read

jobs:
  bootstrap:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - name: Checkout
        uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262

      - name: Install pinned Rust toolchain
        run: rustup toolchain install 1.98.0 --profile minimal --component rustfmt,clippy

      - name: Verify toolchain
        run: |
          rustc --version
          cargo --version
          rustfmt --version
          cargo clippy --version

      - name: Verify bootstrap contract
        run: python3 scripts/check_bootstrap.py

      - name: Formatting
        run: cargo fmt --check

      - name: Cargo check
        run: cargo check --workspace --locked

      - name: Tests
        run: cargo test --workspace --locked

      - name: Clippy
        run: cargo clippy --workspace --all-targets --locked -- -D warnings
```

`actions/checkout` is reused rather than rewritten and is pinned to an exact commit. No cache action is introduced because the workspace has no external dependencies and bootstrap speed does not justify another dependency.

- [ ] **Step 2: Run all baseline commands before opening PR**

Run from repository root:

```bash
python3 scripts/check_bootstrap.py
cargo fmt --check
cargo check --workspace --locked
cargo test --workspace --locked
cargo clippy --workspace --all-targets --locked -- -D warnings
```

Expected: all commands exit `0`; tests may report zero substantive tests because P1 implementation is not authorized.

- [ ] **Step 3: Verify no scope leakage**

Run:

```bash
grep -RniE 'Character DNA|REST_RIG|OxiHuman|Babylon|Motion Truth|Action Truth|camera solver|Grani|Voice-to-Shot|OWNER LOCK' crates scripts tests || true
```

Expected: no implementation occurrences. Documentation comments explaining prohibited scope are permitted only if inspected and clearly non-implementation.

- [ ] **Step 4: Commit CI**

Commit message:

```text
ci: add pinned P1 bootstrap verification
```

---

### Task 6: Open Bootstrap PR and Verify Exact Candidate

**Files:**
- No new file required.

**Interfaces:**
- Consumes: candidate branch `bootstrap/p1-runtime-bootstrap-r01`.
- Produces: immutable candidate head SHA plus CI evidence for independent QC.

- [ ] **Step 1: Verify branch diff against anchor**

Require only bootstrap-foundation paths from this plan. Reject any body/motion/camera/Babylon/Grani/production code.

- [ ] **Step 2: Open pull request**

Title:

```text
P1: bootstrap ZORR BLATT runtime foundation
```

PR body must bind:

```text
anchor SHA: <exact RUNTIME_ANCHOR_SHA>
head SHA: <exact candidate head>
Shared HQ architecture commit: 2e9eb6540c1d07357cb78f44591f6192dbf7b433
architecture blob: 3a26469d62d6b7622a477e78c79a0b3cad824695
Rust: 1.98.0
P1 implementation: NOT STARTED
```

- [ ] **Step 3: Wait for `p1-bootstrap` CI**

Expected all CI steps green:

```text
bootstrap-check
cargo fmt --check
cargo check --workspace --locked
cargo test --workspace --locked
cargo clippy --workspace --all-targets --locked -- -D warnings
```

- [ ] **Step 4: Record candidate evidence**

Record exact:

```text
candidate head SHA
workflow run ID
workflow conclusion
changed-file set
Cargo.lock blob SHA
architecture-binding.json blob SHA
```

- [ ] **Step 5: Lester handoff to Duncan**

Create immutable handoff containing:

```text
whatChanged = bootstrap foundation only
whatWasNotChanged = hq/state, P1 business logic, body, motion, camera, Babylon, Grani, OWNER LOCK, G2, Voice-to-Shot, production activation
nextActor = Duncan-Sparx-ZB
nextRequiredTransition = P1_RUNTIME_BOOTSTRAP_QC
```

Lester does not issue `QC_PASS`.

---

### Task 7: Independent Duncan Bootstrap QC

**Files:**
- Shared HQ handoff/checkpoint/evidence files only if required by their accepted protocols.

**Interfaces:**
- Consumes: exact Lester candidate and CI evidence.
- Produces: `QC_PASS` or `CHANGES_REQUIRED` for bootstrap scope only.

- [ ] **Step 1: Verify actor separation**

Require runtime candidate mutations to be authored/authenticated by `Lester-Sparx`; Duncan performs only independent QC/governance-side records.

- [ ] **Step 2: Verify repository and candidate bindings**

Require:

```text
repository = Lester-Sparx/zorr-blatt-runtime
visibility = private
candidate branch = bootstrap/p1-runtime-bootstrap-r01
exact head = handoff head
architecture binding = exact accepted R01 values
```

- [ ] **Step 3: Verify bootstrap scope**

Inspect all changed paths and confirm no P1 implementation or later-phase logic leaked into candidate.

- [ ] **Step 4: Verify CI evidence fresh at exact head**

Require current workflow conclusion `success` for the exact candidate SHA. Previous runs on older heads are not evidence.

- [ ] **Step 5: Verify dependency-direction negative proof**

Review `scripts/check_bootstrap.py` and evidence that the temporary forbidden edge caused failure and clean state passed.

- [ ] **Step 6: Issue Duncan bootstrap QC verdict**

Only if every criterion passes:

```text
P1 RUNTIME BOOTSTRAP QC — PASS
```

Otherwise:

```text
P1 RUNTIME BOOTSTRAP QC — CHANGES_REQUIRED
```

Do not call P1 implementation authorized.

---

### Task 8: Django Architecture Review, Merge, Protection, and STOP

**Files:**
- No runtime implementation files beyond bootstrap candidate.

**Interfaces:**
- Consumes: exact candidate + Duncan QC_PASS.
- Produces: architecture acceptance if valid, merged bootstrap baseline, protected-main evidence, then STOP.

- [ ] **Step 1: Route exact candidate to authenticated `Django-Sparx-ZB`**

Django reviews architecture conformance only. Do not impersonate Django from another actor.

- [ ] **Step 2: Obtain architecture verdict**

Required accepted form:

```text
P1 RUNTIME BOOTSTRAP ARCHITECTURE — ACCEPTED
```

If Django requires changes, return to Lester; do not merge.

- [ ] **Step 3: Merge exact accepted bootstrap candidate**

Merge only the exact head that passed CI/QC/architecture review. Record merge SHA.

- [ ] **Step 4: Enable `main` branch protection / rules after CI exists**

Required policy outcome:

```text
main = protected integration baseline
pull request required for future integration
p1-bootstrap status check required while it is the bootstrap baseline check
```

If the available GitHub connector cannot mutate branch protection/rulesets, this becomes a direct SPARX/Lester repository-settings action. It is not OWNER LOCK and not production activation.

- [ ] **Step 5: Verify post-merge `main`**

At exact merge SHA verify:

```text
PRIVATE repo
architecture binding exact
Rust toolchain pin exact 1.98.0
Cargo.lock present
five foundation crates present
baseline CI green
main protection/rules confirmed
no P1 business logic
no governance writeback
```

- [ ] **Step 6: Publish bootstrap completion state in Shared HQ**

Only after independent evidence is complete:

```text
P1 RUNTIME BOOTSTRAP = COMPLETE
P1 IMPLEMENTATION = NOT STARTED / NOT_AUTHORIZED
```

Archive prior CURRENT according to Checkpoint System R01 and publish the new checkpoint atomically.

- [ ] **Step 7: STOP**

Do not create Character DNA schemas, canonical JSON implementation, SHA-256 implementation, P1 packet contracts or any other P1 behavior.

Required next gate remains exactly:

```text
P1 IMPLEMENTATION START
```

---

## Final Verification Checklist

Before claiming bootstrap completion, verify all of the following from fresh evidence:

```text
[ ] runtime repo is PRIVATE
[ ] runtime candidate authored by authenticated Lester-Sparx
[ ] anchor commit contains no bootstrap/runtime implementation
[ ] exact Rust pin = 1.98.0
[ ] Cargo.lock committed
[ ] five foundation crates exist
[ ] no unnecessary crate dependencies
[ ] forbidden dependency direction check proven to fail on bad edge
[ ] exact Shared HQ architecture binding present
[ ] actions/checkout pinned to 11d5960a326750d5838078e36cf38b85af677262
[ ] bootstrap CI green at exact candidate
[ ] Duncan QC_PASS at exact candidate
[ ] Django ACCEPTED at exact candidate
[ ] exact accepted candidate merged
[ ] main branch protection/rules confirmed
[ ] no P1 business logic present
[ ] Shared HQ checkpoint says BOOTSTRAP COMPLETE / P1 IMPLEMENTATION NOT STARTED
[ ] STOP respected
```

## Reuse / Custom-Code Decision Record

```text
REUSED:
- Rust/Cargo toolchain
- rustfmt
- clippy
- GitHub Actions
- actions/checkout exact commit
- Python standard library JSON/subprocess/path tooling

CUSTOM:
- scripts/check_bootstrap.py

DOCUMENTED GAP FOR CUSTOM SCRIPT:
The dependency-direction and exact Shared HQ binding rules are ZORR BLATT-specific governance/architecture constraints. A generic off-the-shelf dependency checker would add unnecessary bootstrap dependencies and would still require ZB-specific policy configuration. The small standard-library script implements only that ZB-specific gap and no generic build-system replacement.
```

No RFC 8785/JCS or SHA-256 implementation is added at bootstrap; when P1 implementation is separately authorized, REUSE-FIRST requires evaluating mature existing libraries before custom implementation.
