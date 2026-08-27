# ZORR REFERENCE BRIDGE V1 — DESIGN SPEC

STATE = SPEC CANDIDATE / OWNER REVIEW REQUIRED
ISSUE = #92
UMBRELLA = #73
INHERITS = #76 Studio Constitution R02
DESIGN_AUTHORITY = OWNER-approved in #92
BASE_CONTROLLER = Controller Daemon v1 production exact `9e2ccfbaca88a95eac2e119e5eac720f9074dd35`
IMPLEMENTATION = NOT AUTHORIZED
PRODUCTION = NO

## 1. Purpose

Reference Bridge v1 removes manual copying of one owner-provided image reference into:

`D:\BLATT2\ZB_AGENT_INBOX\<TASK_ID>\`

while preserving exact task binding, byte integrity, authority boundaries, fail-closed behavior, and the existing Controller Daemon v1 execution semantics.

The bridge is a transport validator, not a creative agent and not a task-state authority.

Core laws:

- `REFERENCE ARRIVAL != TASK AUTHORITY`
- `FILE PRESENT != FILE TRUSTED`
- `DRIVE IS TRANSPORT, NOT AUTHORITY`
- `UNKNOWN TASK_ID -> QUARANTINE / STOP`
- `HASH MISMATCH -> QUARANTINE / STOP`
- `DUPLICATE CONFLICT -> QUARANTINE / STOP`
- `VALIDATED REFERENCE -> ATOMIC LOCAL PUBLISH`
- `REFERENCE_EVENT != AGENT_EVENT`

## 2. Selected v1 approach

Selected transport:

`OWNER/CHAT -> Google Drive drop -> Google Drive Desktop sync -> local Reference Bridge validator -> ZB_AGENT_INBOX -> existing Controller Daemon`

Rejected for v1:

1. GitHub issue attachments as primary transport — more brittle attachment discovery/auth/download behavior and unnecessary coupling to attachment URLs.
2. Local manual companion/drop UI — still requires owner-PC interaction and does not remove the manual relay.

Google Drive Desktop is an OWNER-approved free dependency for Reference Bridge v1. Approval of this dependency does not itself authorize installation or implementation.

## 3. Existing compatibility and non-modification rule

Controller Daemon v1 exact `9e2ccfbaca88a95eac2e119e5eac720f9074dd35` already supports a task existing before its reference arrives:

- missing reference -> `WAITING_REFERENCE`;
- later valid reference arrival -> next daemon poll continues normal processing;
- normal execution remains `RUNNING -> RESULT_READY / FAILED`.

Therefore Reference Bridge v1 MUST NOT require Controller Daemon code changes.

Current local reference contract already enforces:

- exactly one supported image per task directory;
- extensions: `.png`, `.jpg`, `.jpeg`, `.webp`;
- magic-byte validation;
- non-empty content;
- maximum size 20 MiB.

Reference Bridge v1 MUST preserve this contract rather than expand it.

## 4. Authority model

The GitHub task issue containing `ZB_AGENT_TASK_V0` remains task authority.

Google Drive is transport only.

`manifest.json` and `READY.json` are transport metadata only. They cannot create, activate, approve, canonize, or mutate a task.

The bridge may publish a local reference only when the delivery points to an existing valid task whose `TASK_ID` and issue number match the package metadata.

The bridge MUST NOT infer authority from filename, Drive folder name, upload account, or mere file presence.

The bridge MUST NOT write or modify `ZB_AGENT_EVENT_V0` execution-state comments.

## 5. V1 task/reference contract

V1 supports exactly one image reference per `TASK_ID`.

Multi-reference tasks are explicitly out of scope and require a separate future design gate.

Destination is derived only from validated `TASK_ID`:

`D:\BLATT2\ZB_AGENT_INBOX\<TASK_ID>\source.<ext>`

No filesystem destination from transport metadata is trusted.

Task IDs MUST satisfy the existing Controller path-boundary contract: uppercase letters, digits, underscore, hyphen only.

## 6. Delivery package

Each delivery is one Drive folder named by a unique `DELIVERY_ID`.

Required members:

- exactly one `source.<png|jpg|jpeg|webp>`;
- `manifest.json`;
- `READY.json` uploaded last.

`READY.json` is a commit marker indicating the sender has finished constructing the delivery package. The bridge MUST ignore incomplete delivery folders until `READY.json` exists.

### 6.1 `manifest.json` minimum schema

```json
{
  "schemaVersion": "zb-reference-bridge-v1",
  "taskId": "ZB-...",
  "githubIssueNumber": 123,
  "deliveryId": "...",
  "sourceFileName": "source.png",
  "sizeBytes": 12345,
  "sha256": "64-lowercase-hex",
  "mimeType": "image/png",
  "createdAtUtc": "2026-08-27T00:00:00Z",
  "sourceStatus": "OWNER_PROVIDED_REFERENCE",
  "transport": "GOOGLE_DRIVE"
}
```

Required constraints:

- schema version exact match;
- `taskId` valid and exact;
- `githubIssueNumber` positive integer;
- `deliveryId` non-empty and unique by sender contract;
- `sourceFileName` must identify the sole image file and contain no path traversal;
- `sizeBytes` exact byte count;
- `sha256` exact SHA256 of the source bytes;
- `mimeType` must agree with supported extension and magic bytes;
- `sourceStatus` exact `OWNER_PROVIDED_REFERENCE` for v1;
- `transport` exact `GOOGLE_DRIVE`.

`createdAtUtc` is provenance metadata only; local wall-clock ordering must not override identity checks.

### 6.2 `READY.json`

`READY.json` MUST include at minimum:

```json
{
  "schemaVersion": "zb-reference-ready-v1",
  "deliveryId": "...",
  "manifestSha256": "64-lowercase-hex"
}
```

The bridge MUST hash the actual `manifest.json` bytes and require an exact match before validating the source.

## 7. Local Reference Bridge process

Reference Bridge runs as a process independent from Controller Daemon v1.

It has no authority over:

- Controller Daemon lifecycle;
- ComfyUI lifecycle;
- SALVADOR model/workflow/prompt/denoise/dimensions;
- canon state;
- task creation;
- agent execution-state transitions.

Proposed runtime root:

`D:\BLATT2\ZB_AGENT_RUNTIME\reference-bridge\`

Required local areas:

- `staging\`
- `journal\`
- `receipts\`
- `logs\`
- `health.json`

Quarantine root:

`D:\BLATT2\ZB_REFERENCE_QUARANTINE\<DELIVERY_ID>\`

The bridge configuration MUST pin:

- Drive synced drop root;
- GitHub repository identity;
- inbox root;
- runtime root;
- quarantine root;
- polling interval;
- maximum source bytes = 20 MiB;
- allowed extensions/MIME mappings.

No credentials or tokens may be stored in delivery manifests, receipts, health, or logs.

## 8. Validation sequence

For each delivery folder with `READY.json`, the bridge MUST execute this order and fail closed:

1. Read and validate `READY.json` schema.
2. Read `manifest.json` only after commit marker exists.
3. Verify `manifestSha256` against actual manifest bytes.
4. Validate manifest schema and all required fields.
5. Validate `TASK_ID` path boundary.
6. Resolve the exact GitHub issue referenced by `githubIssueNumber`.
7. Parse the issue body as an existing valid `ZB_AGENT_TASK_V0`.
8. Require issue task ID == manifest task ID.
9. Require task reference contract to be compatible with `LOCAL_INBOX`.
10. Require exactly one supported source image in the package.
11. Ensure source filename == manifest filename.
12. Read actual source bytes completely.
13. Require non-empty and <= 20 MiB.
14. Require byte length == `sizeBytes`.
15. Require SHA256 == manifest SHA256.
16. Require extension, declared MIME, and magic bytes to agree.
17. Apply duplicate/replay/conflict rules.
18. Copy validated source to same-volume local staging under `D:`.
19. Re-hash staged bytes and require identical SHA256.
20. Atomically publish the completed task directory into final inbox.
21. Persist accepted receipt/journal state.
22. Post durable `ZB_REFERENCE_EVENT_V1 / REFERENCE_READY` on the task issue.

No final inbox path may be created or overwritten before all validation steps pass.

## 9. Partial sync and cloud-placeholder handling

Google Drive Desktop may expose a folder before all bytes are locally readable.

Bridge behavior:

- no `READY.json` -> ignore as incomplete;
- `READY.json` present but manifest/source not yet locally readable -> transient retry, not failure;
- Drive/cloud read errors that may resolve -> bounded retry/backoff, no publish;
- hash mismatch after a complete readable file -> quarantine/failure;
- bridge MUST never publish from a partial or placeholder stream.

The exact implementation may use file stability checks or complete-read semantics, but source bytes MUST be fully readable and hash-verifiable before acceptance.

## 10. Atomic publish

Validated content MUST first be staged on the same `D:` volume as the inbox.

The staging directory is private to Reference Bridge and must not be visible as a valid Controller task inbox.

After validation and staged re-hash:

- if final `ZB_AGENT_INBOX\<TASK_ID>` does not exist, atomically rename staged directory to final task directory;
- if final directory already contains the exact same accepted source SHA, treat as idempotent accepted replay and do not overwrite;
- if final directory exists with conflicting bytes or unexpected files, quarantine the incoming delivery and fail closed;
- bridge MUST never delete or overwrite an already accepted conflicting inbox reference automatically.

## 11. Journal, receipts, duplicates, replay

Persistent acceptance identity is the tuple:

`deliveryId + taskId + sha256`

The journal MUST survive bridge restarts.

Required behavior:

- exact already-accepted package appears again -> idempotent skip;
- same `deliveryId` with changed manifest/source/hash -> `REFERENCE_DELIVERY_ID_CONFLICT`;
- same task ID with a different source SHA after acceptance -> `REFERENCE_TASK_CONFLICT`;
- same source SHA under a new delivery ID for the same task may be treated as idempotent duplicate after exact task/issue validation;
- unknown task/issue -> quarantine;
- late package for a task already terminal in execution state must not overwrite existing inbox. It is rejected or quarantined as `REFERENCE_TASK_TERMINAL`.

Historical receipts are append-only evidence. A later delivery cannot rewrite prior receipt identity.

## 12. Quarantine and failure codes

On a hard validation failure, the delivery is moved/copied into quarantine where practical and a narrow durable bridge failure event is posted.

Minimum error-code vocabulary:

- `REFERENCE_READY_INVALID`
- `REFERENCE_MANIFEST_INVALID`
- `REFERENCE_MANIFEST_HASH_MISMATCH`
- `REFERENCE_TASK_ID_INVALID`
- `REFERENCE_TASK_NOT_FOUND`
- `REFERENCE_TASK_CONTRACT_INVALID`
- `REFERENCE_TASK_ID_MISMATCH`
- `REFERENCE_TASK_TERMINAL`
- `REFERENCE_SOURCE_COUNT_INVALID`
- `REFERENCE_EXTENSION_INVALID`
- `REFERENCE_MAGIC_INVALID`
- `REFERENCE_MIME_INVALID`
- `REFERENCE_EMPTY`
- `REFERENCE_TOO_LARGE`
- `REFERENCE_SIZE_MISMATCH`
- `REFERENCE_HASH_MISMATCH`
- `REFERENCE_DELIVERY_ID_CONFLICT`
- `REFERENCE_TASK_CONFLICT`
- `REFERENCE_DESTINATION_CONFLICT`
- `REFERENCE_STAGING_HASH_MISMATCH`
- `REFERENCE_PUBLISH_FAILED`

Transient cloud-read failures MUST NOT be misreported as permanent validation failures until the configured bounded retry policy is exhausted.

## 13. Durable GitHub bridge events

Reference Bridge posts a separate schema:

`ZB_REFERENCE_EVENT_V1`

### Success event

```text
ZB_REFERENCE_EVENT_V1
TASK_ID = <task id>
DELIVERY_ID = <delivery id>
STATE = REFERENCE_READY
SOURCE_SHA256 = <sha256>
TRANSPORT = GOOGLE_DRIVE
```

`REFERENCE_READY` is allowed only after successful atomic local publish.

### Failure event

```text
ZB_REFERENCE_EVENT_V1
TASK_ID = <task id or NONE if unverifiable>
DELIVERY_ID = <delivery id or NONE>
STATE = REFERENCE_FAILED
ERROR_CODE = <narrow code>
TRANSPORT = GOOGLE_DRIVE
```

These events describe reference transport only.

They MUST NOT create or imply `RUNNING`, `RESULT_READY`, `QC_PASS`, `OWNER_APPROVED`, or canon state.

## 14. Security boundaries

- Google Drive drop folder is private; no public sharing is required.
- Exact Drive folder ID is pinned in producer-side configuration where applicable.
- Exact local synced root is pinned in bridge configuration.
- Destination paths derive only from validated `TASK_ID`.
- Manifest filenames cannot contain `..`, absolute paths, drive letters, alternate separators used to escape the package directory, or arbitrary destination paths.
- Symlink/reparse-point escapes from transport/staging roots must be rejected.
- Bridge must not execute delivered files.
- Bridge only reads supported image bytes and JSON metadata.
- Secrets must never be emitted to GitHub comments or logs.
- Google Drive account compromise is treated as untrusted transport input; validation still applies and task authority remains GitHub.

## 15. Process lifecycle and deployment

Reference Bridge v1 may have its own Windows Task Scheduler deployment tooling, but it remains a separate scheduled task/process from `ZB Controller Daemon v1`.

Required management actions:

- install;
- start;
- stop;
- restart;
- status;
- enable;
- disable;
- uninstall;
- non-mutating preflight.

Normal operation must not require administrator privileges if Windows current-user Task Scheduler allows the approved contract.

Bridge startup/preflight MUST fail closed when required local roots, config, GitHub access, or Drive synced root are invalid.

Bridge failure must not stop or mutate Controller Daemon v1.

## 16. Health and logs

Bridge runtime status MUST expose at least:

- schema/version;
- process PID;
- instance ID;
- state: `STARTING | HEALTHY | DEGRADED | FATAL | STOPPING`;
- last heartbeat UTC;
- pinned config SHA256;
- Drive root reachability;
- last scan time;
- accepted delivery count;
- quarantined delivery count;
- last error code if any.

Logs must be bounded/rotated and must not contain secrets or image bytes.

## 17. Exactly-once and restart behavior

Reference Bridge must be restart-safe.

A crash between staging and publish must not create a partial final inbox.

A crash after atomic publish but before receipt/event write must be recoverable by comparing:

- final inbox source SHA;
- journal/receipt state;
- GitHub reference events.

Recovery must converge to one accepted local reference without duplicate overwrite or fabricated agent execution state.

## 18. Interaction with Controller Daemon

No direct IPC is required for v1.

The integration boundary is the validated final inbox directory.

Expected flow:

`task ASSIGNED -> Controller may emit WAITING_REFERENCE -> bridge publishes validated reference -> bridge emits REFERENCE_READY -> Controller next poll sees local reference -> existing execution path continues`.

Controller may consume a valid reference regardless of whether the bridge event comment is momentarily delayed, because local atomic publish is the data-plane event. GitHub bridge event is durable observability, not a second execution gate.

Reference Bridge MUST NOT attempt to acquire or bypass the Controller global execution lock because it does not execute tasks.

## 19. Producer-side behavior

Producer/JINGO flow for one reference delivery:

1. Ensure a valid GitHub task issue exists.
2. Compute source bytes, extension, size, MIME, and SHA256.
3. Generate unique `DELIVERY_ID`.
4. Create delivery folder in the pinned private Drive drop folder.
5. Upload source image.
6. Upload exact `manifest.json`.
7. Compute manifest SHA256.
8. Upload `READY.json` last.
9. Do not claim local readiness from cloud upload alone.
10. Wait for durable `ZB_REFERENCE_EVENT_V1 / REFERENCE_READY` before saying the local bridge accepted the reference.

`UPLOAD_COMPLETE != LOCAL_REFERENCE_READY`.

## 20. V1 scope

### In scope

- Google Drive Desktop dependency;
- private Drive drop folder;
- one image per task;
- manifest + READY commit marker;
- local validator daemon/process;
- SHA256 integrity;
- extension/MIME/magic/size validation;
- GitHub task cross-check;
- staging + atomic publish;
- persistent journal/receipts;
- duplicate/replay/conflict handling;
- quarantine;
- `ZB_REFERENCE_EVENT_V1` comments;
- Windows install/status/uninstall tooling;
- preflight/health/logging;
- disposable owner-PC end-to-end smoke.

### Out of scope

- multi-reference tasks;
- video/audio/reference bundles;
- folder asset bundles;
- semantic interpretation of character/location content;
- ControlNet/IP-Adapter/Depth/SAM/Blender processing;
- ComfyUI lifecycle;
- Controller Daemon v1 code changes;
- SALVADOR profile/model/workflow/prompt/denoise/dimensions changes;
- paid APIs/services;
- canon mutation;
- automatic QC approval;
- public Drive sharing;
- generic arbitrary PC file transport.

## 21. Testing requirements

Implementation must be TDD and include unit/integration coverage for at least:

- valid PNG/JPEG/WebP delivery;
- READY absent -> ignored;
- manifest hash mismatch;
- invalid JSON/schema;
- task not found;
- task ID mismatch;
- invalid task ID/path traversal;
- extra image files;
- unsupported extension;
- magic/MIME mismatch;
- zero bytes;
- >20 MiB;
- size mismatch;
- source hash mismatch;
- transient unreadable cloud placeholder -> retry/no failure;
- duplicate exact package -> idempotent;
- delivery ID conflict;
- task conflicting second image;
- final destination conflict;
- staged re-hash mismatch;
- crash before publish;
- crash after publish before receipt;
- restart recovery;
- quarantine behavior;
- GitHub reference event formatting;
- GitHub event failure does not roll back valid local publish;
- health/status fail-closed parsing;
- no modification of Controller/SALVADOR production files.

## 22. Owner-PC disposable end-to-end acceptance smoke

No Reference Bridge production activation is allowed before independent QC and owner-PC live smoke.

Smoke sequence:

1. Google Drive Desktop installed and authenticated on owner-PC.
2. Private pinned Drive drop folder is confirmed syncing to an exact local path.
3. Bridge candidate is installed in disposable test mode while Controller Daemon v1 remains unchanged.
4. Create one disposable `ZB_AGENT_TASK_V0` that is eligible to wait for a reference.
5. Confirm Controller can show `WAITING_REFERENCE` with no local inbox image.
6. From the producer side, upload one package: source -> manifest -> READY last.
7. No owner manual file copy is permitted.
8. Confirm Bridge detects the synced package, validates bytes/task/hash, atomically publishes one local image, and posts `REFERENCE_READY`.
9. Confirm exact source SHA256 in Drive manifest == staged SHA == final inbox SHA.
10. Confirm existing Controller independently observes the new inbox reference on its next poll and advances according to its unchanged semantics.
11. Test one hard-fail package such as hash mismatch and confirm quarantine + `REFERENCE_FAILED`, with no inbox overwrite.
12. Uninstall disposable bridge if production activation has not yet been authorized.

PASS requires proof of zero manual file copy and no Controller/SALVADOR mutation.

## 23. Acceptance criteria for Reference Bridge v1 implementation

Implementation may advance to OWNER production activation decision only when all are true:

- formal implementation plan approved;
- isolated LESTER TDD implementation complete;
- all tests pass on exact candidate HEAD;
- independent DUNCAN QC PASS;
- no Controller Daemon production code diff;
- no SALVADOR profile/model/workflow/prompt/denoise/dimensions diff;
- owner-PC Drive sync path verified;
- valid end-to-end delivery succeeds without manual copy;
- invalid/hash-mismatch delivery quarantines fail-closed;
- final inbox publish is atomic;
- bridge event authority remains separate from agent execution authority;
- production activation explicitly authorized by OWNER.

## 24. Required next gates

1. OWNER reviews and approves this written spec.
2. Write implementation plan with `superpowers:writing-plans`.
3. OWNER explicitly authorizes implementation.
4. LESTER implements under TDD in isolation.
5. DUNCAN performs independent QC on exact HEAD.
6. Owner-PC Google Drive Desktop + Reference Bridge disposable smoke.
7. OWNER decides production activation.

Until gate 1 passes:

`IMPLEMENTATION = NOT AUTHORIZED`
`GOOGLE_DRIVE_DESKTOP_INSTALL = NOT AUTHORIZED BY THIS SPEC ALONE`
`REFERENCE_BRIDGE_PRODUCTION = NO`
