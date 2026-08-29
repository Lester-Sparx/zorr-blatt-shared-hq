# ZB Recovery Capsule R01 — Design

## Goal

Create one portable `recovery/` folder that can rebuild a trustworthy ZORR BLATT continuation packet from GitHub and prepare a GitHub MCP connection surface for a fresh AI chat/client without reconstructing project state from chat memory.

The capsule MUST NOT manufacture privileges. It verifies that the authenticated GitHub identity is `Lester-Sparx` and that repository permissions already include `admin`, `push`, and `pull`; otherwise it fails closed.

## Reuse-first architecture

No generic orchestration subsystem is written. R01 reuses:

- existing `checkpoints/ZB_CHECKPOINT_CURRENT.json` and `checkpoints/ZB_CHECKPOINT_CURRENT.md` as the explicit Shared HQ checkpoint;
- existing `zb-archive-v1` branch as the durable event archive head;
- existing PR #111 as the permanent communication bus;
- existing `Taskfile.yml` pattern for deterministic command orchestration;
- GitHub CLI `gh` for authenticated GitHub API reads;
- official `github/github-mcp-server` for the MCP tool surface;
- optional `age` only for an externally provisioned encrypted GitHub App private key fallback.

Open-source component policy:

| Component | R01 binding | License | Purpose |
| --- | --- | --- | --- |
| GitHub CLI | `>= 2.93.0` | MIT | authenticated API/read/permission verification |
| GitHub MCP Server | `v1.0.5` | MIT | fresh AI-client GitHub tool surface; OAuth by default |
| Task | `>= 3.52.0` | MIT | cross-platform task runner |
| age | `>= 1.3.1`, optional | BSD-3-Clause | encrypted emergency GitHub App key material |

No binary or credential is committed to this repository.

## Folder contract

`recovery/` contains:

- `START_RECOVERY.cmd` — Windows one-click entrypoint. It invokes the recovery Taskfile and never embeds a token.
- `Taskfile.yml` — `doctor`, `recover`, and `mcp` tasks.
- `recovery_manifest.json` — authoritative repository, expected actor, required permissions, state sources, component/license bindings, and MCP release checksum binding.
- `zb_recovery.py` — Python-stdlib-only recovery core. It shells only to `gh` for remote state; it never uses direct network libraries and never writes to GitHub.
- `mcp.github.oauth.json` — generic stdio MCP config with no PAT and no secret. Official GitHub MCP OAuth is the primary auth path.
- `GITHUB_APP_FALLBACK.env.example` — names only for optional app authentication. No values/private key are stored.
- `.runtime/` — generated locally and ignored by design. Outputs are `RECOVERY_STATE.json` and `RESUME_PACKET.md`.

## Recovery data flow

1. `doctor` checks that `python`, `gh`, and `task` are callable. `github-mcp-server` is checked separately because a connected ChatGPT GitHub app may already provide the tool surface.
2. `gh api user` must return login `Lester-Sparx`.
3. `gh api repos/Lester-Sparx/zorr-blatt-shared-hq` must report `permissions.admin=true`, `permissions.push=true`, and `permissions.pull=true`.
4. The capsule reads exact remote state:
   - `branches/main` → current main SHA;
   - `branches/zb-archive-v1` → archive SHA;
   - `contents/checkpoints/ZB_CHECKPOINT_CURRENT.json?ref=main` → durable checkpoint bytes and blob SHA;
   - `pulls/111` → current permanent-bus metadata;
   - `issues/111/comments?per_page=100` → latest top-level bus comments;
   - `pulls?state=open&per_page=100` → current open PR inventory.
5. The checkpoint content is decoded from GitHub Contents API base64 and parsed as JSON. A malformed/missing checkpoint is fatal.
6. A canonical local `RECOVERY_STATE.json` is written with the exact collected facts and no auth material.
7. A deterministic `RESUME_PACKET.md` is generated. It binds actor, repo, main SHA, archive SHA, checkpoint ID/blob SHA, PR #111 state/head/base, latest bus comment IDs/bodies, and open PR heads. It orders a fresh AI chat to re-read GitHub before mutation and to continue from durable evidence, never chat memory.
8. `mcp.github.oauth.json` starts `github-mcp-server stdio` with no token. The official server performs OAuth and can fall back to device-code flow when browser callback is unavailable.

## Authentication and privilege law

- `ROLE CONTEXT != AUTHENTICATED ACTOR IDENTITY` remains enforced.
- The capsule never copies, prints, serializes, or commits GitHub tokens.
- OAuth is primary for GitHub MCP.
- GitHub App auth is optional emergency fallback only when the owner has separately provisioned an app with the required repository permissions. The capsule can reference a private-key file path but never stores the PEM in source control.
- Missing identity or permissions is `RECOVERY_BLOCKED`, never a degraded-success state.

## State resolution law

The capsule does not pretend that the historical checkpoint alone is always newest. The generated continuation packet combines the checkpoint with live GitHub heads, PR #111 conversation, archive head, and open PR inventory. The receiving chat must fresh-read those sources and treat immutable GitHub evidence as authoritative.

No automatic merge, issue mutation, PR mutation, comment write, schedule, polling loop, production-profile mutation, canon mutation, or model/prompt mutation is allowed by recovery R01.

## Security and failure handling

Fail closed on:

- wrong authenticated actor;
- repository unreadable;
- any required repository permission false/missing;
- malformed GitHub JSON;
- missing/malformed checkpoint;
- missing `main` or `zb-archive-v1` SHA;
- PR #111 not readable;
- attempted output containing known credential environment names/values.

`RESUME_PACKET.md` must explicitly state that it cannot grant privileges and that the new chat/client must have an authorized GitHub connector or MCP connection.

## Acceptance tests

R01 is a sandbox PASS only when all are fresh-green on one exact branch HEAD:

1. actor mismatch fails closed;
2. missing admin/push/pull fails closed;
3. valid mocked GitHub state produces canonical recovery JSON and resume packet bound to exact SHAs/checkpoint;
4. generated outputs contain no token/PAT/private-key material;
5. old/stale chat text is never used as a state source;
6. MCP OAuth config contains no secret and pins official GitHub MCP Server v1.0.5 in the manifest;
7. Windows entrypoint invokes only the folder Taskfile and contains no secret;
8. component manifest records only approved open-source dependencies/licenses;
9. full existing HQ validation/test suite remains green;
10. changed-file scope is limited to the recovery capsule, its tests, and design/plan docs.

Sandbox PASS does **not** mean a fresh external ChatGPT account has been granted privileges or that a physical Windows cold boot has been executed. Those require an authorized external client/account and, for physical proof, a real machine run. R01 proves the capsule implementation and fail-closed continuation contract.