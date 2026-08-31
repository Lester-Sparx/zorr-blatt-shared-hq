# Four Engine Command Learning R01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use Superpowers TDD. Execute inline through GitHub CI; no new local/runtime infrastructure.

**Goal:** Add a minimal deterministic command/profile layer for the four existing ZORR engines on top of the existing Unified Archive verified-learning layer.

**Architecture:** Reuse PR #205 learning/archive code unchanged. Add one small standard-library resolver module, bind four profiles in AGENTS.md, and verify cold-start command resolution plus durable-learning/transfer gates. No service, database, daemon, model, scheduler, or external dependency is added.

**Tech Stack:** Python 3 standard library, existing SQLite FTS5 learning/archive stack, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-31-four-engine-command-learning-r01-design.md`

## Global Constraints
- Exactly four engines: SALVADOR, GAUZZ, LYNCH, HOKUSAI.
- DUNCAN PRIME is the common root, not a fifth engine.
- Stack on existing #205 learning layer.
- No merge, production activation, model training, new service, new database, new daemon, new scheduler, or external dependency.
- TDD: RED command tests before resolver implementation.

### Task 1: RED command contract
**Files:** Create `tests/test_hq_four_engine_commands.py`.

Verify: exact four profiles; case-insensitive first-token commands; unknown/embedded names do not activate; common DUNCAN root; unique scopes; required durable restore and unseen-transfer learning gate.

Expected RED: import fails because `scripts.hq_engine_profiles` does not exist.

### Task 2: Minimal resolver GREEN
**Files:** Create `scripts/hq_engine_profiles.py`.

Implement only static profile data plus `resolve_engine_command(message)` and `build_activation_contract(message)`. No archive implementation duplication; activation contract points at existing Unified Archive/verified-learning mechanisms.

### Task 3: Bootstrap binding
**Files:** Modify `AGENTS.md`.

Add one Four Engine command section defining the four exact commands, scopes, DUNCAN-root inheritance, restore order, learning gate, and no-cross-scope silent substitution rule.

### Task 4: Fresh verification
Require on exact candidate HEAD:
- focused `test_hq_four_engine_commands.py` PASS;
- existing Unified Archive/learning tests PASS;
- full `hq-validate` suite PASS;
- no dependency/service/database/model additions;
- PR remains stacked/unmerged.
