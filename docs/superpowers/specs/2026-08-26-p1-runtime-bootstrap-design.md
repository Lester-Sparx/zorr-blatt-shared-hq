# ZORR BLATT — P1 Runtime Bootstrap Design R01

Status: **APPROVED DESIGN / GOVERNANCE ARTIFACT / NOT P1 IMPLEMENTATION AUTHORIZATION**

Authority repository: `Lester-Sparx/zorr-blatt-shared-hq`

Authority main commit: `2e9eb6540c1d07357cb78f44591f6192dbf7b433`

Architecture source: `docs/ZB_PRODUCTION_INTEGRATION_ARCHITECTURE_R01.md`

Architecture Git blob: `3a26469d62d6b7622a477e78c79a0b3cad824695`

This artifact records the approved design for the separate P1 runtime bootstrap. It authorizes only the bootstrap foundation described below. It does **not** authorize P1 implementation, body compilation, motion/action logic, cinematography, Babylon integration, Grani, production activation, OWNER LOCK, G2, or Voice-to-Shot.

---

## 1. Runtime repository identity

The execution-plane repository is fixed as:

```text
Lester-Sparx/zorr-blatt-runtime
```

Required visibility:

```text
PRIVATE
```

The runtime is a separate execution plane. `Lester-Sparx/zorr-blatt-shared-hq` remains the control / authority / evidence plane.

The runtime may implement an accepted HQ contract and produce evidence. It may not redefine HQ authority or approve itself.

---

## 2. Technology and workspace model

P1 bootstrap is Rust-first with a future path to ZB CORE WASM.

The repository is a single Cargo workspace, not a collection of separate repositories.

Initial logical crates:

```text
crates/
  zb-contracts/
  zb-canonical/
  zb-authority/
  zb-provenance/
  zb-validation/
```

The workspace also contains bootstrap test harnesses and provenance binding files.

The bootstrap must remain minimal. Crates exist to establish architectural boundaries; they do not need substantive P1 business logic at bootstrap time.

---

## 3. Dependency-direction law

The approved logical direction is:

```text
zb-contracts
    ↓
zb-canonical
    ↓
zb-authority
    ↓
zb-provenance
    ↓
zb-validation
```

**This is an allowed dependency direction, not a requirement that every crate depend on the immediately preceding crate.**

Unnecessary dependencies must not be added. A crate may depend only on the minimum upstream crates it actually needs. Reverse or circular dependencies that violate the authority direction are forbidden.

Examples:

```text
ALLOWED:
zb-validation → zb-contracts
zb-validation → zb-authority
zb-provenance → zb-canonical

NOT REQUIRED:
zb-provenance does not need to depend on zb-authority unless its implementation genuinely requires it.

FORBIDDEN:
zb-contracts → zb-validation
zb-canonical → zb-provenance
any dependency cycle
```

The bootstrap CI must be capable of detecting forbidden dependency direction without forcing artificial dependencies.

---

## 4. Canonical wire and hash foundation

Canonical wire/storage representation is JSON.

Canonicalization is:

```text
RFC 8785 / JSON Canonicalization Scheme (JCS)
+ ZB domain restrictions
→ exact canonical UTF-8 bytes
→ SHA-256
```

ZB restrictions include at minimum:

```text
NO implicit defaults
NO undefined values
NO NaN
NO positive or negative Infinity
NO ambiguous null semantics
NO implementation-specific serializer output as authority
NO hashing of pretty-printed JSON
NO numeric representation outside the accepted canonical domain
```

`serde_json` may be used for parsing or transport convenience, but its ordinary serialization output is not automatically canonical authority bytes.

The bootstrap foundation must keep the distinction between semantic data, canonical bytes, and SHA-256 identity explicit.

---

## 5. Toolchain and dependency reproducibility

The runtime must pin the supported Rust toolchain through:

```text
rust-toolchain.toml
```

The Cargo dependency resolution must be committed through:

```text
Cargo.lock
```

Production-provable dependencies may not float.

Bootstrap law:

```text
NO FLOATING PRODUCTION TOOLCHAIN
NO FLOATING DEPENDENCIES
```

A future dependency provenance manifest will carry exact versions/revisions/hashes as required by the accepted Integration Architecture R01.

---

## 6. Exact HQ architecture binding

The runtime foundation must contain a machine-readable provenance binding equivalent to:

```json
{
  "authorityRepository": "Lester-Sparx/zorr-blatt-shared-hq",
  "authorityCommit": "2e9eb6540c1d07357cb78f44591f6192dbf7b433",
  "architecturePath": "docs/ZB_PRODUCTION_INTEGRATION_ARCHITECTURE_R01.md",
  "architectureGitBlob": "3a26469d62d6b7622a477e78c79a0b3cad824695",
  "architectureRevision": "R01"
}
```

Recommended path:

```text
provenance/architecture-binding.json
```

This binding means only:

```text
THIS RUNTIME FOUNDATION IMPLEMENTS THIS EXACT ACCEPTED CONTRACT.
```

It does not grant the runtime authority to modify or reinterpret that contract.

---

## 7. Repository bootstrap structure

The approved bootstrap skeleton is logically equivalent to:

```text
zorr-blatt-runtime/
├─ Cargo.toml
├─ Cargo.lock
├─ rust-toolchain.toml
├─ README.md
├─ .gitignore
├─ .github/
│  └─ workflows/
│     └─ p1-ci.yml
├─ crates/
│  ├─ zb-contracts/
│  ├─ zb-canonical/
│  ├─ zb-authority/
│  ├─ zb-provenance/
│  └─ zb-validation/
├─ tests/
│  ├─ authority-boundary/
│  ├─ canonical-determinism/
│  ├─ unresolved-policy/
│  ├─ source-bindings/
│  └─ dependency-direction/
└─ provenance/
   └─ architecture-binding.json
```

Equivalent organization is acceptable only if it preserves the same boundaries and bootstrap scope. The bootstrap must not use structure changes as a way to introduce P1 implementation early.

---

## 8. Git governance

`main` is the protected integration baseline.

Development flow from the first integration is:

```text
main
→ candidate branch
→ pull request
→ CI
→ authorized review / evidence
→ merge only when the relevant gate allows it
```

Direct production development in `main` is not the intended workflow.

Bootstrap itself must be integrated through PR + CI rather than treating the initial repository state as a governance exception.

Branch names are informational only. Exact commit hashes are authoritative bindings.

---

## 9. Bootstrap CI scope

Bootstrap CI establishes foundation quality only. It is not the full P1 PASS suite.

Minimum bootstrap checks:

```text
cargo fmt --check
cargo check --workspace --locked
cargo test --workspace --locked
cargo clippy --workspace --all-targets -- -D warnings

workspace structure valid
Cargo.lock present
exact toolchain pin present
architecture binding valid
forbidden dependency direction absent
```

The later, separately authorized P1 implementation must add the complete P1 contract suite defined in Integration Architecture R01, including schema validation, canonical serialization, determinism, authority boundaries, negative writeback tests, UNRESOLVED handling, source bindings, stale-derivation detection, dependency direction, and provenance completeness.

Bootstrap CI must not claim those later guarantees before they exist.

---

## 10. Bootstrap allowed scope

Bootstrap may create only the minimal foundation:

```text
Cargo workspace
foundation crates
architecture binding
toolchain pin
dependency lock
baseline CI
README / governance notes
test harness skeleton
```

Bootstrap must not implement:

```text
Character DNA fields
REST_RIG
body compiler
mesh generation
OxiHuman integration
Babylon integration
Motion Truth
Action Truth
animation generation
camera solver
Grani
coordinate-system lock
G2
Voice-to-Shot
OWNER LOCK
runtime activation
```

The governing distinction is:

```text
BOOTSTRAP COMPLETE
≠ P1 IMPLEMENTATION STARTED
```

---

## 11. Bootstrap PASS criteria

Bootstrap is complete only when all of the following are true:

```text
PRIVATE Lester-Sparx/zorr-blatt-runtime exists
exact HQ architecture binding exists
Rust toolchain is pinned
single Cargo workspace is valid
Cargo.lock is committed
main uses PR + CI governance
foundation crates exist
only necessary allowed-direction dependencies exist
baseline CI is green
no P1 business logic leaked into bootstrap
runtime has no governance writeback into Shared HQ
```

The only permitted resulting state is:

```text
P1 RUNTIME BOOTSTRAP — COMPLETE
P1 IMPLEMENTATION — NOT STARTED
```

A separate explicit gate is required before P1 implementation.

---

## 12. Role separation

Repository ownership does not override governance roles.

```text
LESTER  = builder / implementation
DUNCAN  = independent QC / production lead
DJANGO  = architecture reviewer
OWNER   = activation / OWNER LOCK authority
```

Neither repository ownership nor CI administration permits the runtime or Lester to issue QC_PASS, architecture acceptance, RUNTIME_APPROVED, production activation, or OWNER LOCK outside the accepted governance chain.

---

## 13. Post-bootstrap STOP gate

After the skeleton is created and bootstrap PASS criteria are independently verified, work stops.

No implementation of P1 contract behavior begins automatically.

Required next event is a separate explicit authorization:

```text
P1 IMPLEMENTATION START
```

Without that event:

```text
P1 implementation remains NOT AUTHORIZED.
```

---

## 14. Governing summary

```text
PRIVATE EXECUTION REPO.
RUST-FIRST SINGLE CARGO WORKSPACE.
RFC 8785 / JCS + ZB RESTRICTIONS.
SHA-256 CANONICAL IDENTITY.
PINNED TOOLCHAIN AND DEPENDENCIES.
PR + CI FROM FIRST INTEGRATION.
EXACT BINDING TO HQ R01.
DEPENDENCY ARROWS DEFINE ALLOWED DIRECTION, NOT MANDATORY IMPORTS.
NO UNNECESSARY DEPENDENCIES.
BOOTSTRAP IS FOUNDATION ONLY.
BOOTSTRAP APPROVAL DOES NOT AUTHORIZE P1 IMPLEMENTATION.
AFTER SKELETON VERIFICATION: STOP.
```
