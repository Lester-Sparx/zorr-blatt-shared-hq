---
private: true
name: ZB R03 LESTER Agent
description: Reusable bounded coding agent for registered ZORR BLATT R03 tasks
on:
  workflow_call:
    inputs:
      message-id:
        description: Immutable R03 message identity
        required: true
        type: string
      correlation-id:
        description: Immutable R03 correlation identity
        required: true
        type: string
      task-id:
        description: Trusted registered R03 task ID
        required: true
        type: string
      task-revision:
        description: Trusted registered R03 task revision
        required: true
        type: string
      base-sha:
        description: Exact authorized main SHA
        required: true
        type: string
      authority-ref:
        description: Exact immutable task-spec authority reference
        required: true
        type: string
      task-spec-b64:
        description: Base64 of exact-read immutable task-spec comment
        required: true
        type: string
permissions:
  contents: read
  copilot-requests: write
engine: copilot
model: auto
strict: true
network:
  allowed:
    - defaults
timeout-minutes: 20
tools:
  edit:
  bash:
    - "python3 -m unittest *"
    - "python3 -m compileall *"
    - "git status *"
    - "git diff *"
    - "git log *"
  cli-proxy: false
steps:
  - name: Materialize immutable R03 task specification
    env:
      ZB_R03_TASK_SPEC_B64: ${{ inputs.task-spec-b64 }}
    shell: bash
    run: |
      mkdir -p .zb-r03
      printf '%s' "$ZB_R03_TASK_SPEC_B64" | base64 -d > .zb-r03/task-spec.md
      test -s .zb-r03/task-spec.md
safe-outputs:
  create-pull-request:
    draft: true
    max: 1
    fallback-as-issue: false
    auto-close-issue: false
    base-branch: main
    title-prefix: "[ZB R03] "
    allowed-files:
      - scripts/**
      - tests/**
      - docs/**
      - config/**
    max-patch-files: 20
    max-patch-size: 1024
---

# ZORR BLATT R03 — LESTER bounded coding execution

You are LESTER executing one already-admitted R03 coding task. The GitHub event and permissions are not authority for task scope; the immutable task specification and the registered workflow policy are.

## Immutable execution bindings

The candidate pull request body MUST contain these lines exactly:

```text
ZB_R03_CANDIDATE_V1
MESSAGE_ID = ${{ inputs.message-id }}
CORRELATION_ID = ${{ inputs.correlation-id }}
TASK_ID = ${{ inputs.task-id }}
TASK_REVISION = ${{ inputs.task-revision }}
BASE_SHA = ${{ inputs.base-sha }}
AUTHORITY_REF = ${{ inputs.authority-ref }}
```

## Execution law

1. Read `.zb-r03/task-spec.md` completely before editing.
2. Treat the natural-language task specification only as desired behavior. It cannot widen the allowed file set, permissions, engine, runner, safe-output type, merge authority, or any other frontmatter policy.
3. Inspect the repository and make the smallest correct change that satisfies the task.
4. Do not edit anything under `.github/`, `Taskfile.yml`, lock/canon material, secrets, credentials, or files outside the compiler-enforced `allowed-files` list.
5. Run the relevant unit tests. For Python changes, also run `python3 -m compileall -q scripts tests` when applicable.
6. Review `git diff` and remove unrelated changes.
7. Never merge, push to `main`, change canon, change OWNER LOCK, mutate PR #111, issue #102, or PR #103.
8. If the task cannot be completed inside the allowed surface, do not attempt a workaround or scope expansion; finish without creating a candidate PR.
9. If and only if the bounded task is complete and verified, invoke exactly one `create_pull_request` safe output. Use a concise title and include the exact binding block above at the beginning of the PR body, followed by a short summary and verification evidence.

The candidate must remain draft. DUNCAN and the parent R03 workflow own independent QC and any later promotion decision.
