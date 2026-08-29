# ZB R03 GH-AW Production Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the custom LESTER AI runner with a pinned reusable `github/gh-aw` Copilot workflow and connect it to deterministic ZB admission, independent DUNCAN QC, standing-policy merge, and real production activation.

**Architecture:** Traditional GitHub Actions remains the multi-stage orchestrator. A deterministic R03 dispatcher validates PR #111 root messages and task-spec comments, then calls a reusable gh-aw workflow for the LESTER reasoning/edit step. gh-aw creates one bounded draft PR via `safe-outputs`; a separate candidate workflow performs deterministic DUNCAN QC and merges only under the standing R03 OWNER policy after exact-head PASS.

**Tech Stack:** Python 3 stdlib, GitHub Actions, GitHub Agentic Workflows `github/gh-aw` v0.86.2, GitHub Copilot engine, unittest.

**Spec:** `docs/superpowers/specs/2026-08-28-zb-r03-gh-aw-production-router-design.md`

## Global Constraints

- Permanent event surface is PR #111 and MUST remain OPEN / DRAFT / UNMERGED.
- Trigger is event-driven only; no polling or scheduled communication substitute.
- Transport actor must be exactly `Lester-Sparx`.
- R03 task authority is deny-by-default and registry-backed.
- Initial coding profile may modify only `scripts/**`, `tests/**`, `docs/**`, `config/**`.
- `.github/**`, `Taskfile.yml`, canon/lock assets, issue #102, and PR #103 are outside the initial R03 task profile.
- gh-aw version is exactly `v0.86.2`; Linux amd64 SHA256 is `b8fd100d1d56a77b842ad28375ff361215a5aa1277db6b9a05d70054cde7260e`.
- gh-aw source and compiled `.lock.yml` must both be committed; pinned recompilation must be clean.
- LESTER candidate PR is always draft and never auto-merges from gh-aw safe-output.
- DUNCAN must review the exact candidate HEAD in a distinct GitHub job before promotion.
- Standing OWNER authorization is issue #106 comment `5457544639` and applies only to R03 automation.
- No canon change, OWNER LOCK change, merge of PR #111, mutation of issue #102, or mutation of PR #103.

---

### Task 1: R03 task registry and admission contract

**Files:**
- Create: `config/zb-r03/tasks.json`
- Create: `scripts/zb_r03_router.py`
- Create: `tests/test_zb_r03_router.py`

**Interfaces:**
- Consumes: GitHub issue-comment event JSON plus a `GitHubPort` capable of exact comment read and tracker comment listing/writes.
- Produces: `R03Dispatch` with `message_id`, `correlation_id`, `task_id`, `task_revision`, `base_sha`, `authority_ref`, `task_spec_sha256`, `task_spec_b64`, and immutable registry policy.

- [ ] **Step 1: Write failing registry/admission tests**

Add unittest coverage that requires:

```python
self.assertEqual(resolve_task("ZB_CODE_CHANGE_R03", 1).allowed_files,
                 ("scripts/**", "tests/**", "docs/**", "config/**"))
```

and rejects unknown task IDs, wrong revisions, wrong repository/PR/actor/marker, stale base SHA, malformed task-spec refs, task-spec binding mismatch, and duplicate replay keys.

- [ ] **Step 2: Run focused RED**

Run:

`python -m unittest tests.test_zb_r03_router -v`

Expected: FAIL because `scripts.zb_r03_router` / registry behavior does not yet exist.

- [ ] **Step 3: Implement minimal immutable registry + parser**

`config/zb-r03/tasks.json` contains exactly one entry:

```json
{
  "schema": "ZB_R03_TASK_REGISTRY_V1",
  "tasks": {
    "ZB_CODE_CHANGE_R03": {
      "revision": 1,
      "profile": "LESTER_GH_AW_CODE_R03",
      "allowed_files": ["scripts/**", "tests/**", "docs/**", "config/**"],
      "max_changed_files": 20,
      "max_patch_kb": 1024,
      "timeout_minutes": 20,
      "auto_merge_after_duncan": true
    }
  }
}
```

`zb_r03_router.py` must use strict exact-field parsing for `ZB_AGENT_TASK_R03_V1`, exact-ID read-back of `ZB_TASK_SPEC_V1`, SHA256 binding of the full task-spec comment body, base-SHA equality with trusted workflow SHA, and a replay key derived from the spec.

- [ ] **Step 4: Run focused GREEN**

`python -m unittest tests.test_zb_r03_router -v`

Expected: PASS.

- [ ] **Step 5: Run full regression**

`python -m unittest discover -s tests -v`

Expected: all tests PASS.

### Task 2: gh-aw reusable LESTER source and pinned compiler gate

**Files:**
- Create: `.github/workflows/zb-r03-lester-agent.md`
- Create: `.github/workflows/zb-r03-gh-aw-compile.yml`
- Create: `tests/test_zb_r03_gh_aw_source.py`
- Create later from pinned compiler artifact: `.github/workflows/zb-r03-lester-agent.lock.yml`
- Modify/Create: `.gitattributes` only if required to mark `*.lock.yml` generated.

**Interfaces:**
- Consumes workflow_call inputs: `message-id`, `correlation-id`, `task-id`, `task-revision`, `base-sha`, `authority-ref`, `task-spec-b64`.
- Produces one gh-aw safe-output draft PR with `ZB_R03_CANDIDATE_V1` marker.

- [ ] **Step 1: Write source-policy RED tests**

Tests assert source contains all of:

```text
workflow_call:
engine: copilot
strict: true
copilot-requests: write
create-pull-request:
draft: true
max: 1
fallback-as-issue: false
```

and exclusive allowed patterns exactly `scripts/**`, `tests/**`, `docs/**`, `config/**`; assert `.github/**` and auto-merge are absent.

- [ ] **Step 2: Run focused RED**

`python -m unittest tests.test_zb_r03_gh_aw_source -v`

Expected: FAIL because the source workflow is absent.

- [ ] **Step 3: Implement gh-aw source**

Use `workflow_call` inputs, `engine: copilot`, `strict: true`, `network.allowed: [defaults]`, and `safe-outputs.create-pull-request` with draft-only, max-one, no fallback issue, bounded patch limits, and exclusive allowed-files.

A deterministic `steps:` entry decodes `task-spec-b64` into `.zb-r03/task-spec.md`; the Markdown prompt reads that file and requires one candidate PR with exact machine-readable bindings.

- [ ] **Step 4: Add pinned compile CI**

`.github/workflows/zb-r03-gh-aw-compile.yml` downloads:

`https://github.com/github/gh-aw/releases/download/v0.86.2/linux-amd64`

verifies exact SHA256, chmods it, runs:

`gh-aw compile zb-r03-lester-agent --strict`

then uploads `.github/workflows/zb-r03-lester-agent.lock.yml` as an artifact and fails if committed lock content differs from pinned recompilation.

- [ ] **Step 5: Obtain generated lock artifact and commit it**

After the PR compile workflow runs, download its generated lock artifact, commit the exact generated file, rerun compile verification, and require a clean diff.

- [ ] **Step 6: Run focused + full GREEN**

`python -m unittest tests.test_zb_r03_gh_aw_source -v`

`python -m unittest discover -s tests -v`

Expected: PASS.

### Task 3: Event dispatcher workflow

**Files:**
- Create: `.github/workflows/zb-r03-production-router.yml`
- Create: `tests/test_zb_r03_workflow.py`

**Interfaces:**
- Consumes `issue_comment.created` from PR #111.
- Produces reusable-workflow call inputs from `admit` job outputs.

- [ ] **Step 1: Write workflow RED tests**

Require exact trigger, PR 111 guard, actor guard, `ZB_AGENT_TASK_R03_V1` guard, no polling/schedule, checkout credentials disabled, `admit` job using `scripts.zb_r03_router`, and `lester` job calling `./.github/workflows/zb-r03-lester-agent.lock.yml`.

- [ ] **Step 2: Run focused RED**

`python -m unittest tests.test_zb_r03_workflow -v`

Expected: FAIL because router workflow is absent.

- [ ] **Step 3: Implement dispatcher workflow**

`admit` checks out exact default-branch workflow authority and serializes sanitized outputs; `lester` calls the reusable lock workflow only when `dispatch_ready == true`.

The called workflow receives no repository secret. Caller grants only the permissions required by the compiled gh-aw workflow (`actions: read`, `contents`, `pull-requests`, `copilot-requests`) while the compiled agent job remains read-only and gh-aw safe-output jobs own the write boundary.

- [ ] **Step 4: Run focused + full GREEN**

Expected: all tests PASS.

### Task 4: Independent DUNCAN candidate QC

**Files:**
- Create: `scripts/zb_r03_qc.py`
- Create: `.github/workflows/zb-r03-candidate.yml`
- Create: `tests/test_zb_r03_qc.py`

**Interfaces:**
- Consumes pull_request event for a `ZB_R03_CANDIDATE_V1` draft PR.
- Produces exact-head `ZB_R03_DUNCAN_QC_V1` verdict and merge eligibility output.

- [ ] **Step 1: Write QC RED tests**

Cover marker parsing, task registry lookup, exact allowed-file matching, max-file count, base/main drift rejection, head-change rejection, forbidden `.github/**` rejection, and PASS rendering with exact PR/head/base bindings.

- [ ] **Step 2: Run focused RED**

`python -m unittest tests.test_zb_r03_qc -v`

Expected: FAIL because QC module/workflow is absent.

- [ ] **Step 3: Implement deterministic QC**

Use GitHub event/base/head metadata as trusted physical provenance. Run full unittest discovery, `python -m compileall -q scripts tests`, HQ validation, and scope checks in the candidate checkout. Post exact-head QC comment only after all deterministic checks pass.

- [ ] **Step 4: Run focused + full GREEN**

Expected: PASS.

### Task 5: Standing-policy exact-head finalizer

**Files:**
- Extend: `scripts/zb_r03_qc.py`
- Extend: `.github/workflows/zb-r03-candidate.yml`
- Extend: `tests/test_zb_r03_qc.py`

**Interfaces:**
- Consumes DUNCAN exact-head PASS and standing R03 OWNER policy.
- Produces merge or BLOCKED durable state.

- [ ] **Step 1: Write promotion RED tests**

Require promotion rejection unless all are true: candidate marker valid, DUNCAN PASS exact HEAD, current main equals authorized base, candidate still open/draft, task registry marks auto-merge eligible, and standing authorization comment ID equals `5457544639`.

- [ ] **Step 2: Run focused RED**

Expected: FAIL for missing promotion policy.

- [ ] **Step 3: Implement guarded merge**

Use GitHub REST merge API with expected candidate HEAD SHA. Never mark ready or merge when base drifted or HEAD changed. On success, fresh-read PR/main and write durable tracker/Console projection. On failure, write `BLOCKED` and leave PR open.

- [ ] **Step 4: Run focused + full GREEN**

Expected: PASS.

### Task 6: PR review, merge infrastructure, and live production activation

**Files:**
- No new architecture files unless review finds a bounded defect.
- Activation task candidate is expected to modify only `tests/test_r02b_task_inventory_live_proof.py`.

**Interfaces:**
- Consumes merged R03 infrastructure on main.
- Produces a real R03-generated maintenance PR, independent DUNCAN PASS, exact-head standing-policy merge, and `PRODUCTION_ACTIVE = YES` record.

- [ ] **Step 1: Fresh exact-head DUNCAN review of R03 infrastructure PR**

Verify diff scope, pinned gh-aw compile, full test suite, compile gate, no forbidden mutation, and workflow permissions.

- [ ] **Step 2: Merge infrastructure under standing R03 OWNER authorization**

Fresh-read main + PR head, require no drift, merge exact reviewed head, then fresh-read new main.

- [ ] **Step 3: Create immutable real task spec on PR #111**

Task: convert the two top-level pytest-style checks in `tests/test_r02b_task_inventory_live_proof.py` into unittest-discovered tests, with no production-code changes.

- [ ] **Step 4: Post one fresh `ZB_AGENT_TASK_R03_V1` root bound to exact new main**

No manual relay after this point.

- [ ] **Step 5: Verify event chain physically**

Require router admission -> gh-aw reusable LESTER -> one draft candidate PR -> DUNCAN exact-head PASS -> standing-policy exact-head merge -> fresh main read-back.

- [ ] **Step 6: Verify the maintenance result**

Require the two checks are now included by unittest discovery and the full repository suite remains green.

- [ ] **Step 7: Activate R03 coding automation**

Write durable tracker/Console record only after successful real task:

```text
ZB_R03_PRODUCTION_ACTIVATION_V1
PRODUCTION_ACTIVE = YES
AUTOMATION_SURFACE = ZB_CODE_CHANGE_R03
UPSTREAM_EXECUTION = github/gh-aw@v0.86.2
```

Fresh-read the exact activation record and verify PR #111 remains OPEN / DRAFT / UNMERGED.
