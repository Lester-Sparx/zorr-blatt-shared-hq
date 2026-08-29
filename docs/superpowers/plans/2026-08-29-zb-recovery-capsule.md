# ZB Recovery Capsule R01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one `recovery/` folder that verifies the authorized GitHub identity/permissions, rebuilds exact continuation state from Shared HQ, and prepares a secret-free official GitHub MCP connection config.

**Architecture:** Reuse the repository's existing checkpoint/archive/communication-bus state and Task pattern. A Python-stdlib-only core shells to `gh api` for read-only remote facts, fails closed on identity/permission/state errors, and generates local recovery artifacts; official `github-mcp-server` is configured separately for OAuth-based MCP access.

**Tech Stack:** Python 3 stdlib, GitHub CLI, Task, official GitHub MCP Server, optional age; GitHub Actions existing `hq-validate` suite.

**Spec:** `docs/superpowers/specs/2026-08-29-zb-recovery-capsule-design.md`

## Global Constraints

- Work only on `duncan3/recovery-capsule-r01` until fresh sandbox PASS.
- Base SHA is `4aea1565c0f231d9a2b165ce7a300b6f9901b5b7`.
- Expected GitHub actor is exactly `Lester-Sparx`.
- Repository is exactly `Lester-Sparx/zorr-blatt-shared-hq`.
- Required repository permissions are `admin=true`, `push=true`, `pull=true`.
- State sources are GitHub only: main, `zb-archive-v1`, current checkpoint, PR #111 conversation, and current open PR inventory.
- No GitHub mutations, polling loops, schedules, merges, production/canon/model/prompt/profile changes.
- No token, PAT, private key, or secret material may be committed or serialized into generated state.
- Reuse only approved open-source components recorded by the spec.

---

### Task 1: Recovery contract and fail-closed core

**Files:**
- Create: `recovery/recovery_manifest.json`
- Create: `recovery/zb_recovery.py`
- Create: `tests/test_zb_recovery_capsule.py`

**Interfaces:**
- Consumes: `gh api` JSON and GitHub Contents API base64 payloads.
- Produces: `collect_recovery_state(manifest, gh_json) -> dict`, `render_resume_packet(manifest, state) -> str`, `write_outputs(manifest_path, output_dir) -> tuple[Path, Path]`.

- [ ] **Step 1: Write failing tests for identity, permissions, and deterministic state**

Tests must provide a fake `gh_json(endpoint: str) -> object` mapping and assert:

```python
with self.assertRaisesRegex(RecoveryError, "RECOVERY_ACTOR_MISMATCH"):
    collect_recovery_state(manifest, fake_wrong_actor)

with self.assertRaisesRegex(RecoveryError, "RECOVERY_PERMISSION_MISSING:admin"):
    collect_recovery_state(manifest, fake_missing_admin)

state = collect_recovery_state(manifest, fake_valid)
self.assertEqual(state["actor"], "Lester-Sparx")
self.assertEqual(state["main_sha"], "a" * 40)
self.assertEqual(state["archive_sha"], "b" * 40)
self.assertEqual(state["checkpoint"]["checkpointId"], "2026-08-29-RC")
self.assertEqual(state["bus"]["number"], 111)
```

- [ ] **Step 2: Run full repository unittest discovery and verify RED**

Run: `python3 -m unittest discover -s tests -v`

Expected: failure because `recovery.zb_recovery` does not exist.

- [ ] **Step 3: Add the manifest with exact reusable bindings**

`recovery_manifest.json` must contain:

```json
{
  "schema": "ZB_RECOVERY_CAPSULE_V1",
  "repository": "Lester-Sparx/zorr-blatt-shared-hq",
  "expected_actor": "Lester-Sparx",
  "required_permissions": ["admin", "push", "pull"],
  "main_branch": "main",
  "archive_branch": "zb-archive-v1",
  "checkpoint_path": "checkpoints/ZB_CHECKPOINT_CURRENT.json",
  "communication_bus_pr": 111,
  "components": {
    "github_cli": {"minimum_version": "2.93.0", "license": "MIT"},
    "github_mcp_server": {"version": "1.0.5", "license": "MIT", "windows_x86_64_sha256": "92523838eaaac426aeb4ffc4540c5d3c49a6c1f627ff5f61ce585553240c2e09"},
    "task": {"minimum_version": "3.52.0", "license": "MIT"},
    "age": {"minimum_version": "1.3.1", "license": "BSD-3-Clause", "optional": true}
  }
}
```

- [ ] **Step 4: Implement minimal Python core**

Core rules:

```python
class RecoveryError(RuntimeError):
    pass


def _require_sha(value: object, code: str) -> str:
    if not isinstance(value, str) or len(value) != 40 or any(c not in "0123456789abcdef" for c in value.lower()):
        raise RecoveryError(code)
    return value.lower()
```

`collect_recovery_state` calls only these endpoints through injected `gh_json`:

```text
user
repos/Lester-Sparx/zorr-blatt-shared-hq
repos/Lester-Sparx/zorr-blatt-shared-hq/branches/main
repos/Lester-Sparx/zorr-blatt-shared-hq/branches/zb-archive-v1
repos/Lester-Sparx/zorr-blatt-shared-hq/contents/checkpoints/ZB_CHECKPOINT_CURRENT.json?ref=main
repos/Lester-Sparx/zorr-blatt-shared-hq/pulls/111
repos/Lester-Sparx/zorr-blatt-shared-hq/issues/111/comments?per_page=100
repos/Lester-Sparx/zorr-blatt-shared-hq/pulls?state=open&per_page=100
```

The checkpoint contents are `base64.b64decode(content).decode("utf-8")` and parsed with `json.loads`.

- [ ] **Step 5: Run full unittest discovery and verify GREEN for Task 1**

Run: `python3 -m unittest discover -s tests -v`

Expected: all tests pass.

---

### Task 2: Resume packet and secret-exclusion law

**Files:**
- Modify: `recovery/zb_recovery.py`
- Modify: `tests/test_zb_recovery_capsule.py`

**Interfaces:**
- Consumes: Task 1 state dict.
- Produces: deterministic Markdown continuation packet and canonical JSON output.

- [ ] **Step 1: Add RED tests for exact bindings and no secrets**

Tests assert the packet includes:

```text
GITHUB_ACTOR = Lester-Sparx
REPOSITORY = Lester-Sparx/zorr-blatt-shared-hq
MAIN_SHA = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
ARCHIVE_SHA = bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
CHECKPOINT_ID = 2026-08-29-RC
COMMUNICATION_BUS_PR = 111
```

and includes the hard instruction:

```text
NO CHAT IS PROJECT MEMORY. GITHUB DURABLE EVIDENCE IS PROJECT MEMORY.
```

The tests must inject obvious sentinel secrets into environment-like fixture data and assert none appear in either output:

```python
for secret in ("ghp_TEST_SENTINEL", "PRIVATE_KEY_SENTINEL"):
    self.assertNotIn(secret, json_text)
    self.assertNotIn(secret, packet)
```

- [ ] **Step 2: Run the focused recovery tests and verify RED**

Run: `python3 -m unittest tests.test_zb_recovery_capsule -v`

Expected: packet/output functions absent or assertions fail.

- [ ] **Step 3: Implement deterministic packet rendering and atomic local writes**

The packet must state:

```text
1. Verify authenticated actor before any mutation.
2. Fresh-read repository, main, zb-archive-v1, checkpoint, PR #111, and active PR heads.
3. Treat this packet as a bootstrap index, not authority over newer GitHub evidence.
4. Never infer missing privileges; fail closed.
5. Continue from the newest mutually consistent immutable GitHub evidence.
```

Write JSON with `sort_keys=True, indent=2` and UTF-8. Use temporary file + `Path.replace` for each local output.

- [ ] **Step 4: Run focused and full tests and verify GREEN**

Run:

```text
python3 -m unittest tests.test_zb_recovery_capsule -v
python3 -m unittest discover -s tests -v
```

Expected: both pass.

---

### Task 3: One-folder Windows entrypoint and official MCP config

**Files:**
- Create: `recovery/START_RECOVERY.cmd`
- Create: `recovery/Taskfile.yml`
- Create: `recovery/mcp.github.oauth.json`
- Create: `recovery/GITHUB_APP_FALLBACK.env.example`
- Modify: `tests/test_zb_recovery_capsule.py`

**Interfaces:**
- Consumes: system `task`, `python`, `gh`, and optional `github-mcp-server`.
- Produces: one-command local recovery artifacts plus a secret-free stdio MCP config.

- [ ] **Step 1: Add RED structural tests**

Tests must assert:

```python
self.assertIn("task", start_cmd.lower())
self.assertIn("Taskfile.yml", start_cmd)
self.assertNotIn("ghp_", start_cmd)
self.assertEqual(mcp["mcpServers"]["github"]["command"], "github-mcp-server")
self.assertEqual(mcp["mcpServers"]["github"]["args"], ["stdio"])
self.assertNotIn("env", mcp["mcpServers"]["github"])
```

Taskfile must expose `doctor`, `recover`, and `mcp` and `recover` must depend on `doctor` before running `python -m recovery.zb_recovery`.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python3 -m unittest tests.test_zb_recovery_capsule -v`

Expected: missing folder entrypoint/config assertions fail.

- [ ] **Step 3: Implement the thin orchestration files**

`START_RECOVERY.cmd`:

```bat
@echo off
setlocal
cd /d "%~dp0\.."
where task >nul 2>nul || (echo RECOVERY_BLOCKED: task not found & exit /b 2)
task -t recovery/Taskfile.yml recover
exit /b %ERRORLEVEL%
```

`mcp.github.oauth.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "github-mcp-server",
      "args": ["stdio"]
    }
  }
}
```

`GITHUB_APP_FALLBACK.env.example` contains variable names only:

```text
GITHUB_APP_ID=
GITHUB_APP_INSTALLATION_ID=
GITHUB_APP_PRIVATE_KEY_PATH=
```

- [ ] **Step 4: Run focused and full tests and verify GREEN**

Run:

```text
python3 -m unittest tests.test_zb_recovery_capsule -v
python3 -m unittest discover -s tests -v
```

Expected: both pass.

---

### Task 4: PR, exact-head CI, scope verification, durable DUNCAN3 QC

**Files:**
- No new functional scope beyond Tasks 1–3.

**Interfaces:**
- Consumes: exact branch HEAD and GitHub Actions evidence.
- Produces: draft sandbox PR and durable PASS/CHANGES_REQUIRED record.

- [ ] **Step 1: Create one draft PR from `duncan3/recovery-capsule-r01` to `main`**

Body must state open-source reuse, no privilege escalation, no secrets, no merge, and physical cold-boot limitation.

- [ ] **Step 2: Read exact PR head and changed filenames**

Expected allowed scope only:

```text
docs/superpowers/specs/2026-08-29-zb-recovery-capsule-design.md
docs/superpowers/plans/2026-08-29-zb-recovery-capsule.md
recovery/START_RECOVERY.cmd
recovery/Taskfile.yml
recovery/recovery_manifest.json
recovery/zb_recovery.py
recovery/mcp.github.oauth.json
recovery/GITHUB_APP_FALLBACK.env.example
tests/test_zb_recovery_capsule.py
```

- [ ] **Step 3: Wait for fresh exact-head `hq-validate` and inspect every job**

Required:

```text
hq-schema = success
hq-scope-guard = success
hq-control-tower-integrity = success
full unittest discovery = zero failures/errors
```

- [ ] **Step 4: Re-read authenticated identity and repository permissions**

Required current evidence:

```text
actor = Lester-Sparx
admin = true
push = true
pull = true
```

- [ ] **Step 5: Record durable DUNCAN3 verdict on the PR**

PASS is allowed only when Steps 2–4 are fresh and green on the exact PR HEAD. Record:

```text
DUNCAN3_ZB_RECOVERY_CAPSULE_R01_QC
VERDICT = PASS
SANDBOX_CAPSULE_PASS = YES
PHYSICAL_WINDOWS_COLD_BOOT_PASS = NO
EXTERNAL_CHATGPT_AUTHORIZATION_PROVEN = NO
MERGED = NO
```

If any required check is missing or red, record `VERDICT = CHANGES_REQUIRED` instead.