# ZB Console v0 Design

**Status:** OWNER APPROVED CONCEPT / WRITTEN SPEC FOR REVIEW

**Owner:** SPARX
**Coordinator:** JINGO
**Implementation role:** LESTER
**Independent QC:** DUNCAN

## Purpose

Provide a fast, read-only PowerShell owner view so SPARX can type `zb` and immediately see the real ZORR BLATT production state without reading GitHub threads or opening a web dashboard.

The console is a visibility surface, not an authority surface.

## User commands

- `zb` — full owner summary.
- `zb watch` — refresh the same summary every 10 seconds until Ctrl+C.
- `zb why` — explain the current wait/blocker in plain language.
- `zb agents` — agent cards only.
- `zb gates` — active gate states only.
- `zb scout` — latest scout check/findings summary.
- `zb output` — validate and open the latest real local output; if none exists, print `NO VALID OUTPUT FOUND` and exit without fabricating a preview.

No mutating commands exist in v0. Specifically there is no `approve`, `reject`, `redo`, `merge`, `activate`, `run`, `submit`, `download`, or gate-opening command.

## Owner-facing layout

The default `zb` view must show, in this order:

1. `SPARX CONTROL` — overall state and whether owner action is required.
2. `AGENTS` — JINGO, LESTER, DUNCAN, SALVADOR, LYNCH, MAO, CHARLIE, MEMORO.
3. `GATES` — current named gates with state.
4. `LAST REAL OUTPUT` — local validated output metadata and path.
5. `SCOUT` — latest scout check and short finding summary.
6. `WHY WAITING` — one plain-language reason for the current wait/blocker.

Technical details such as commit SHA, PR number and evidence IDs may be shown only in a short `DETAILS` tail; they must not replace the human-readable summary.

## Status vocabulary

Owner-facing status is limited to:

- `WORKING`
- `WAITING`
- `BLOCKED`
- `FAIL`
- `DONE`
- `UNKNOWN`
- `STALE`

The console must never reinterpret missing data as success. Missing or unverifiable state renders `UNKNOWN`.

## Remote source contract

The console does not infer team state from arbitrary GitHub prose. It reads the latest valid structured snapshot in Shared HQ issue #39 with marker:

```text
ZB_OWNER_VIEW_V0
```

Required snapshot keys:

```text
UPDATED_AT = <ISO-8601 UTC>
OVERALL_STATUS = WORKING|WAITING|BLOCKED|FAIL|DONE|UNKNOWN
SPARX_ACTION = NONE|<one exact owner action>
WHY = <one plain-language sentence>
SCOUT_LAST_CHECK = <ISO-8601 UTC>|UNKNOWN
SCOUT_SUMMARY = <short text>|NONE
```

Required agent lines:

```text
AGENT = <NAME> | <STATUS> | <DOING> | <DONE_OR_NONE> | <BLOCKER_OR_NONE> | <NEXT>
```

Required gate lines:

```text
GATE = <NAME> | <STATUS> | <REASON>
```

Allowed agent names in v0:

```text
JINGO
LESTER
DUNCAN
SALVADOR
LYNCH
MAO
CHARLIE
MEMORO
```

The latest syntactically valid `ZB_OWNER_VIEW_V0` comment wins. A malformed newer comment must not hide the last valid snapshot.

If no valid snapshot exists, remote team/gate/scout fields render `UNKNOWN`; the console may still show a valid local output.

If `UPDATED_AT` is older than 2 hours, the snapshot is visibly marked `STALE`. No hidden fallback to older informal text is allowed.

## Local output contract

Default result root remains:

```text
D:\BLATT2\ZB_AGENT_RESULTS
```

Each task result is expected at:

```text
<RESULT_ROOT>\<TASK_ID>\result.png
<RESULT_ROOT>\<TASK_ID>\result.json
```

A local output is valid only when all of the following hold:

1. both files exist;
2. `result.json` parses as JSON;
3. metadata `taskId` matches the directory name;
4. metadata `state == RESULT_READY`;
5. metadata `sha256` equals the SHA-256 of `result.png` bytes;
6. the PNG is non-empty and begins with the PNG signature;
7. `createdAt` is a parseable timestamp.

The newest valid output by `createdAt` is `LAST REAL OUTPUT`.

`zb output` opens only a validated output using the Windows default image viewer. Invalid or partial files are ignored and never opened as the official result.

The output card displays at minimum:

```text
TASK
AGENT
STATE
CREATED
SHA256
PATH
```

Production/canon status must not be inferred from the existence of a result file. If the remote snapshot does not explicitly classify a result as production-approved, the console labels it `PRODUCTION APPROVAL: NOT ESTABLISHED`.

## Read-only boundary

ZB Console v0 may perform only:

- local filesystem reads under the configured result root;
- `gh auth status`;
- GitHub read operations needed to fetch issue #39 comments;
- opening a validated local image for `zb output`.

It must not post GitHub comments, mutate files, submit ComfyUI jobs, modify runtime state, change canon, merge PRs, open gates, or trigger downloads.

## Failure behavior

- GitHub CLI missing: render local output if possible, remote state `UNKNOWN`, and print `GH_CLI_UNAVAILABLE` in details.
- GitHub unauthenticated: same behavior with `GH_NOT_AUTHENTICATED`.
- GitHub request failure: same behavior with `GH_READ_FAILED`.
- No valid snapshot: remote state `UNKNOWN`.
- No valid local output: `NO VALID OUTPUT FOUND`.
- Invalid local metadata/hash: ignore that candidate and continue searching older results.
- Unsupported platform for opening output: show the validated path and return a clear non-destructive error.

No failure path may fabricate `WORKING`, `PASS`, `DONE`, a preview, or owner approval.

## Implementation location

ZB Console v0 extends the existing zero-budget controller package already merged in `agent-controller/`.

Expected implementation files:

```text
agent-controller/src/zb_local_controller/owner_snapshot.py
agent-controller/src/zb_local_controller/owner_output.py
agent-controller/src/zb_local_controller/console.py
agent-controller/scripts/install-zb-console.ps1
agent-controller/tests/test_owner_snapshot.py
agent-controller/tests/test_owner_output.py
agent-controller/tests/test_console.py
```

Expected existing files modified:

```text
agent-controller/src/zb_local_controller/github_cli.py
agent-controller/pyproject.toml
agent-controller/README.md
```

The existing controller execution path and ComfyUI backend must remain behaviorally unchanged.

## Command installation

After a one-time local install step, typing `zb` in PowerShell must invoke the console from any working directory.

The repository must expose a Python console entry point:

```text
zb = zb_local_controller.console:main
```

`install-zb-console.ps1` performs the local editable package install and verifies that `zb --help` is callable. It must not alter machine-wide policy, require administrator privileges, download a model, or start the controller.

## Acceptance criteria

DUNCAN must independently verify at minimum:

1. `zb` renders a complete human-view snapshot from a valid fixture.
2. missing remote data becomes `UNKNOWN`, never a fake healthy state.
3. a malformed newest snapshot falls back to the last valid structured snapshot.
4. a snapshot older than 2 hours is visibly `STALE`.
5. a valid local `result.png` + matching `result.json` is shown as last real output.
6. hash mismatch causes the file to be ignored.
7. `zb output` opens only a validated result.
8. `zb watch` refreshes without mutating GitHub or local result files.
9. GitHub unavailable still allows local-only status/output reporting.
10. no v0 command can post comments, submit jobs, change canon, merge, approve or activate production.
11. the pre-existing controller test suite remains green.
12. the new console tests pass on the exact candidate HEAD.

## Non-goals

Not in v0:

- web UI;
- owner decision buttons;
- voice control;
- direct agent task dispatch;
- starting ComfyUI/controller processes;
- model installation;
- production activation;
- automatic canon changes;
- telemetry service;
- database;
- background daemon for the console itself.

## Future extension boundary

A later version may add owner actions, but only behind a separate approved write contract and independent QC. The v0 read-only implementation must not contain dormant hidden write paths for future use.