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
- `DELIVERY EVENT != AGENT EXECUTION EVENT`
- `UNKNOWN / INVALID TASK -> NO PUBLISH`
- `HASH MISMATCH -> QUARANTINE / STOP`
- `DUPLICATE CONFLICT -> QUARANTINE / STOP`
- `VALIDATED REFERENCE -> ATOMIC LOCAL PUBLISH`
- `UPLOAD_COMPLETE != LOCAL_REFERENCE_READY`

## 2. Selected v1 approach

Selected architecture:

`OWNER/CHAT -> JINGO -> Google Drive drop -> Google Drive Desktop sync -> local Reference Bridge validator -> ZB_AGENT_INBOX -> existing Controller Daemon`

The control/evidence plane and data plane are deliberately split:

- **GitHub task issue** = task authority and durable delivery metadata/event plane;
- **Google Drive** = image-byte transport only;
- **owner-PC Reference Bridge** = local validator and atomic publisher;
- **existing Controller Daemon** = unchanged task execution authority.

Rejected for v1:

1. GitHub issue attachments as primary byte transport — more brittle attachment discovery/auth/download coupling.
2. Local manual companion/drop UI — retains owner-PC file handling and defeats the main goal.

Google Drive Desktop is an OWNER-approved free dependency for v1. Dependency approval does not by itself authorize installation or implementation.

## 3. Existing compatibility and non-modification rule

Controller Daemon v1 exact `9e2ccfbaca88a95eac2e119e5eac720f9074dd35` already supports a task existing before its reference arrives:

- missing reference -> `WAITING_REFERENCE`;
- later valid reference arrival -> next daemon poll continues normal processing;
- normal execution remains `RUNNING -> RESULT_READY / FAILED`.

Therefore Reference Bridge v1 MUST NOT require Controller Daemon code changes.

The current local reference contract already enforces:

- exactly one supported image per task directory;
- `.png`, `.jpg`, `.jpeg`, `.webp`;
- magic-byte validation;
- non-empty content;
- maximum size 20 MiB.

Reference Bridge v1 MUST preserve this contract rather than expand it.

## 4. Authority model

The GitHub issue body containing valid `ZB_AGENT_TASK_V0` remains task authority.

A `ZB_REFERENCE_DELIVERY_V1` comment on that same valid task issue is a **transport binding instruction** only. It binds expected bytes to the already-authorized task but cannot create, activate, execute, approve, QC-pass, canonize, or mutate the task.

Google Drive is data transport only. Drive folder names, file names, file IDs, uploader identity, and file presence never create authority by themselves.

The bridge MUST NOT write or modify `ZB_AGENT_EVENT_V0` comments.

The bridge MUST NOT publish any file unless it can cross-check the delivery event against a valid task issue and exact `TASK_ID`.

## 5. V1 task/reference contract

V1 supports exactly one image reference per `TASK_ID`.

Multi-reference tasks are out of scope and require a future design gate.

Destination is derived only from validated `TASK_ID`:

`D:\BLATT2\ZB_AGENT_INBOX\<TASK_ID>\source.<ext>`

No filesystem destination from Drive or GitHub metadata is trusted.

Task IDs MUST satisfy the existing Controller path-boundary contract: uppercase letters, digits, underscore, hyphen only.

## 6. Drive delivery package

Each delivery uses one unique `DELIVERY_ID` and one private Drive folder named exactly by that ID.

The Drive folder contains exactly one image file:

`source.<png|jpg|jpeg|webp>`

There is **no Drive-side `manifest.json` or `READY.json` in v1**.

Reason: the connected producer surface reliably supports creating Drive folders and uploading existing file references, but does not reliably create arbitrary raw JSON files. The commit marker and manifest are therefore represented as a durable GitHub delivery event posted only after the source upload succeeds.

This keeps the architecture executable with the available connected surfaces and makes GitHub the durable metadata plane while Drive remains the byte plane.

## 7. Producer commit marker — `ZB_REFERENCE_DELIVERY_V1`

After the source image upload to the exact Drive delivery folder succeeds, JINGO posts one delivery event comment on the existing task issue.

Minimum canonical format:

```text
ZB_REFERENCE_DELIVERY_V1
TASK_ID = <task id>
DELIVERY_ID = <delivery id>
DRIVE_FOLDER_ID = <google drive folder id>
DRIVE_FILE_ID = <google drive file id>
SOURCE_FILE_NAME = source.<ext>
SIZE_BYTES = <integer>
SOURCE_SHA256 = <64 lowercase hex>
MIME_TYPE = <supported image mime>
SOURCE_STATUS = OWNER_PROVIDED_REFERENCE
TRANSPORT = GOOGLE_DRIVE
```

Required constraints:

- comment lives on the exact valid task issue;
- `TASK_ID` exact match with task body;
- `DELIVERY_ID` non-empty and unique by producer contract;
- Drive folder/file IDs non-empty provider identifiers;
- source filename is basename only and must match the sole local synced image;
- size is exact byte count;
- SHA256 is exact source-byte hash;
- MIME agrees with extension/magic bytes;
- source status exact `OWNER_PROVIDED_REFERENCE` for v1;
- transport exact `GOOGLE_DRIVE`.

Posting this comment is the producer-side commit marker.

The local bridge MUST ignore Drive folders that have no corresponding valid `ZB_REFERENCE_DELIVERY_V1` event on a valid task issue.

## 8. Producer-side behavior

For one reference delivery JINGO MUST:

1. Ensure an existing valid GitHub task issue exists with `REFERENCE = LOCAL_INBOX`.
2. Obtain the exact source image bytes from the owner-provided attachment/file reference.
3. Validate extension/magic/non-empty/max 20 MiB before upload.
4. Compute exact size, MIME, and SHA256.
5. Generate unique `DELIVERY_ID`.
6. Create the exact private Drive folder `<DELIVERY_ID>` under the pinned drop root.
7. Upload exactly one source image into that folder as `source.<ext>`.
8. Capture provider folder ID and file ID from successful Drive operations.
9. Only after upload success, post `ZB_REFERENCE_DELIVERY_V1` with exact metadata.
10. Never claim local readiness from Drive upload success alone.
11. Wait for durable `ZB_REFERENCE_EVENT_V1 / REFERENCE_READY` before saying the owner-PC bridge accepted the reference.

If exact source bytes cannot be obtained and hashed by the producer, automatic delivery MUST fail closed rather than post guessed metadata.

## 9. Local Reference Bridge process

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

Bridge configuration MUST pin:

- GitHub repository identity;
- Drive drop folder ID for provenance;
- exact local Google Drive synced drop root;
- inbox root;
- runtime root;
- quarantine root;
- polling interval;
- max source bytes = 20 MiB;
- allowed extension/MIME/magic mappings.

No credentials or tokens may be stored in events, receipts, health, or logs.

## 10. Discovery model

The bridge uses GitHub as the discovery/metadata plane, not blind Drive folder scanning.

Each poll:

1. list/inspect eligible valid task issues;
2. parse valid `ZB_REFERENCE_DELIVERY_V1` comments;
3. identify delivery events not yet accepted/rejected in the local journal;
4. derive expected local Drive folder path from pinned synced root + validated `DELIVERY_ID`;
5. wait until the expected local folder/file is fully readable;
6. validate and publish.

A random/unreferenced Drive folder is ignored and MUST NOT create GitHub state.

## 11. Validation sequence

For each unprocessed valid delivery event, execute this order and fail closed:

1. Parse the parent issue as valid `ZB_AGENT_TASK_V0`.
2. Require task `REFERENCE = LOCAL_INBOX`.
3. Validate event schema and required fields.
4. Require event task ID == issue task ID.
5. Validate `TASK_ID` path boundary.
6. Validate `DELIVERY_ID` against a safe identifier grammar defined by implementation plan; it cannot contain path separators or traversal.
7. Derive local delivery folder only as `<PINNED_DRIVE_SYNC_ROOT>\<DELIVERY_ID>`.
8. Wait until exact delivery folder exists and is fully locally readable.
9. Require exactly one supported image in that folder and no additional source candidates.
10. Require local source basename == event `SOURCE_FILE_NAME`.
11. Read source bytes completely.
12. Require non-empty and <= 20 MiB.
13. Require byte length == event `SIZE_BYTES`.
14. Require SHA256 == event `SOURCE_SHA256`.
15. Require extension, event MIME, and magic bytes to agree.
16. Apply duplicate/replay/terminal/conflict rules.
17. Copy validated source to same-volume local staging under `D:`.
18. Re-hash staged bytes and require identical SHA256.
19. Atomically publish completed task directory into final inbox.
20. Persist accepted receipt/journal state.
21. Post durable `ZB_REFERENCE_EVENT_V1 / REFERENCE_READY` on the task issue.

No final inbox path may be created or overwritten before all validation steps pass.

## 12. Partial sync and cloud-placeholder handling

Google Drive Desktop may expose folder metadata before all image bytes are locally available.

Bridge behavior:

- valid delivery event exists but local folder absent -> waiting/retry, no failure;
- local folder exists but source not fully readable -> transient retry, no publish;
- cloud/placeholder read errors that may resolve -> bounded retry/backoff;
- complete readable file with wrong size/hash/magic -> hard failure/quarantine;
- bridge MUST never publish from a partial stream.

The implementation may use complete-read semantics and/or file stability checks, but hash verification of fully readable bytes is mandatory.

## 13. Atomic publish

Validated content MUST first be staged on the same `D:` volume as the inbox.

The staging directory is private to Reference Bridge and must not appear as a Controller task inbox.

After validation and staged re-hash:

- if final `ZB_AGENT_INBOX\<TASK_ID>` does not exist, atomically rename staged directory to final task directory;
- if final directory already contains the exact same accepted source SHA, treat as idempotent accepted replay;
- if final directory exists with conflicting bytes or unexpected files, quarantine incoming delivery and fail closed;
- bridge MUST never automatically delete or overwrite an accepted conflicting inbox reference.

## 14. Journal, receipts, duplicates, replay, terminal tasks

Persistent delivery identity:

`deliveryId + taskId + sourceSha256`

Journal MUST survive bridge restarts.

Required behavior:

- exact already-accepted delivery event/package reappears -> idempotent skip;
- same `DELIVERY_ID` with changed task/hash/file metadata -> `REFERENCE_DELIVERY_ID_CONFLICT`;
- same task ID with a different source SHA after acceptance -> `REFERENCE_TASK_CONFLICT`;
- same source SHA under a new delivery ID for same task may be idempotent after exact issue/task validation;
- delivery for task already terminal in `ZB_AGENT_EVENT_V0` (`FAILED` or `RESULT_READY`) MUST NOT overwrite or create a new reference and is rejected as `REFERENCE_TASK_TERMINAL`;
- historical receipts are append-only evidence and never rewritten by later deliveries.

## 15. Quarantine and failure semantics

Hard validation failure after a valid task/delivery binding is known:

- preserve/copy relevant local delivery bytes into quarantine where practical;
- persist a local failure receipt;
- post narrow `ZB_REFERENCE_EVENT_V1 / REFERENCE_FAILED` on the same valid task issue.

If the bridge cannot establish a valid task issue and exact task identity, it MUST NOT post a task-scoped reference event to an arbitrary issue. Such malformed/untrusted material is ignored or recorded locally only.

Minimum error-code vocabulary:

- `REFERENCE_DELIVERY_EVENT_INVALID`
- `REFERENCE_TASK_CONTRACT_INVALID`
- `REFERENCE_TASK_ID_MISMATCH`
- `REFERENCE_TASK_ID_INVALID`
- `REFERENCE_DELIVERY_ID_INVALID`
- `REFERENCE_TASK_TERMINAL`
- `REFERENCE_DRIVE_FOLDER_TIMEOUT`
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

Transient Drive read failures MUST NOT be reported as permanent until bounded retry policy is exhausted.

## 16. Durable Reference Bridge result events

Reference Bridge posts separate transport-result schema:

`ZB_REFERENCE_EVENT_V1`

Success:

```text
ZB_REFERENCE_EVENT_V1
TASK_ID = <task id>
DELIVERY_ID = <delivery id>
STATE = REFERENCE_READY
SOURCE_SHA256 = <sha256>
TRANSPORT = GOOGLE_DRIVE
```

`REFERENCE_READY` is allowed only after successful atomic local publish.

Failure:

```text
ZB_REFERENCE_EVENT_V1
TASK_ID = <task id>
DELIVERY_ID = <delivery id>
STATE = REFERENCE_FAILED
ERROR_CODE = <narrow code>
TRANSPORT = GOOGLE_DRIVE
```

These events describe transport only.

They MUST NOT create or imply `RUNNING`, `RESULT_READY`, `QC_PASS`, `OWNER_APPROVED`, or canon state.

If posting `REFERENCE_READY` fails after successful local publish, the bridge must retain local receipt state and retry the event without rolling back or duplicating the published inbox.

## 17. Security boundaries

- Drive drop folder is private; no public sharing required.
- Exact Drive folder ID is pinned on producer side and in bridge config for provenance.
- Exact local synced root is pinned in bridge config.
- Destination derives only from validated `TASK_ID`.
- Delivery folder path derives only from validated `DELIVERY_ID` under pinned root.
- Source file name must be basename only; no `..`, absolute path, drive letter, separator, or alternate traversal form.
- Symlink/reparse-point escapes from Drive/staging roots must be rejected.
- Bridge never executes delivered files.
- Bridge reads only supported image bytes and GitHub metadata.
- Secrets never appear in GitHub comments/logs/receipts.
- Compromised Drive contents remain untrusted; task authority and expected SHA come from the valid task issue + delivery event.

## 18. Process lifecycle and deployment

Reference Bridge v1 may have its own Windows Task Scheduler tooling, separate from `ZB Controller Daemon v1`.

Required actions:

- install;
- start;
- stop;
- restart;
- status;
- enable;
- disable;
- uninstall;
- non-mutating preflight.

Normal v1 installation should not require administrator privileges if current-user Task Scheduler supports the contract.

Bridge startup/preflight MUST fail closed when config, GitHub access, Drive synced root, runtime root, or inbox root is invalid.

Bridge failure must not stop, restart, reconfigure, or mutate Controller Daemon v1.

## 19. Health and logs

Bridge status MUST expose at least:

- schema/version;
- PID;
- instance ID;
- state: `STARTING | HEALTHY | DEGRADED | FATAL | STOPPING`;
- last heartbeat UTC;
- pinned config SHA256;
- Drive synced root reachability;
- GitHub reachability/auth preflight state;
- last poll time;
- accepted delivery count;
- quarantined/rejected delivery count;
- last error code if any.

Logs must be bounded/rotated and contain no secrets or image bytes.

## 20. Restart safety and convergence

Reference Bridge must be restart-safe.

A crash before atomic publish cannot create a partial final inbox.

A crash after atomic publish but before receipt/event write must be recoverable by comparing:

- final inbox source SHA;
- delivery event metadata;
- journal/receipt state;
- existing `ZB_REFERENCE_EVENT_V1` comments.

Recovery must converge to one accepted local reference without overwrite, duplicate task execution state, or fabricated authority.

## 21. Interaction with Controller Daemon

No direct IPC is required for v1.

Integration boundary is the validated final inbox directory.

Expected flow:

`task ASSIGNED -> Controller may emit WAITING_REFERENCE -> JINGO uploads Drive source -> JINGO posts DELIVERY event -> bridge sync/validate/publish -> bridge posts REFERENCE_READY -> Controller next poll sees local reference -> existing execution path continues`.

Controller may consume the valid local reference even if the bridge success comment is temporarily delayed, because atomic local publish is the data-plane event. The bridge comment is durable observability, not a second execution gate.

Reference Bridge MUST NOT acquire or bypass the Controller global execution lock because it does not execute tasks.

## 22. V1 scope

### In scope

- Google Drive Desktop dependency;
- private Drive drop root;
- one Drive folder + one image per delivery;
- `ZB_REFERENCE_DELIVERY_V1` GitHub manifest/commit marker;
- local validator process;
- SHA256/size/extension/MIME/magic validation;
- GitHub task cross-check;
- staging + atomic publish;
- persistent journal/receipts;
- duplicate/replay/terminal/conflict handling;
- quarantine;
- `ZB_REFERENCE_EVENT_V1` result comments;
- Windows install/status/uninstall tooling;
- preflight/health/logging;
- disposable owner-PC end-to-end smoke.

### Out of scope

- Drive-side raw JSON manifest/READY files;
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

## 23. Testing requirements

Implementation must use TDD and cover at least:

- valid PNG/JPEG/WebP delivery event + synced source;
- delivery event absent -> Drive folder ignored;
- malformed delivery event;
- event task ID mismatch;
- invalid task ID/path traversal;
- invalid delivery ID/path traversal;
- task `REFERENCE` incompatible;
- local Drive folder missing -> retry/no publish;
- unreadable cloud placeholder -> retry/no premature failure;
- extra image files;
- unsupported extension;
- magic/MIME mismatch;
- zero bytes;
- >20 MiB;
- size mismatch;
- source SHA mismatch;
- duplicate exact package -> idempotent;
- delivery ID conflict;
- task conflicting second image;
- terminal task delivery rejected;
- final destination conflict;
- staged re-hash mismatch;
- crash before publish;
- crash after publish before receipt;
- restart recovery;
- quarantine behavior;
- GitHub delivery-event parser;
- GitHub reference-result event formatting;
- GitHub success-event post failure does not roll back valid local publish;
- health/status fail-closed parsing;
- no modification of Controller/SALVADOR production files.

## 24. Owner-PC disposable end-to-end acceptance smoke

No Reference Bridge production activation is allowed before independent QC and owner-PC live smoke.

Smoke sequence:

1. Install/authenticate Google Drive Desktop on owner-PC under explicit installation gate.
2. Create/confirm private pinned Drive drop folder and exact local synced path.
3. Install Reference Bridge candidate in disposable test mode while production Controller Daemon remains unchanged.
4. Create one disposable valid `ZB_AGENT_TASK_V0` with `REFERENCE = LOCAL_INBOX`.
5. Confirm Controller can report `WAITING_REFERENCE` with no local reference.
6. Producer uploads one owner-provided image to Drive under one new `DELIVERY_ID` folder.
7. Producer posts `ZB_REFERENCE_DELIVERY_V1` only after upload success.
8. No owner manual file copy is allowed.
9. Confirm bridge detects event, waits for sync, validates bytes/task/hash, atomically publishes one local image, and posts `REFERENCE_READY`.
10. Confirm source SHA in delivery event == locally synced source SHA == staged SHA == final inbox SHA.
11. Confirm existing Controller independently sees final inbox reference on next poll and advances using unchanged semantics.
12. Create one hard-fail delivery with wrong expected hash; confirm no inbox overwrite, local quarantine/failure receipt, and `REFERENCE_FAILED` on the valid task issue.
13. Uninstall disposable bridge unless OWNER production activation is separately authorized.

PASS requires zero manual file copy and zero Controller/SALVADOR production mutation.

## 25. Acceptance criteria for implementation

Reference Bridge may advance to OWNER production activation decision only when all are true:

- approved implementation plan;
- isolated LESTER TDD implementation complete;
- all tests pass on exact candidate HEAD;
- independent DUNCAN QC PASS;
- no Controller Daemon production code diff;
- no SALVADOR profile/model/workflow/prompt/denoise/dimensions diff;
- owner-PC Drive Desktop installed/authenticated under explicit gate;
- exact local Drive sync root verified;
- valid end-to-end delivery succeeds without manual copy;
- invalid/hash-mismatch delivery fails closed/quarantines;
- final inbox publish is atomic;
- bridge transport events remain separate from agent execution authority;
- production activation explicitly authorized by OWNER.

## 26. Required next gates

1. OWNER reviews and approves this written spec.
2. Write implementation plan using `superpowers:writing-plans`.
3. OWNER explicitly authorizes implementation.
4. LESTER implements under TDD in isolation.
5. DUNCAN performs independent QC on exact HEAD.
6. Owner-PC Google Drive Desktop + Reference Bridge disposable smoke.
7. OWNER decides production activation.

Until gate 1 passes:

`IMPLEMENTATION = NOT AUTHORIZED`
`GOOGLE_DRIVE_DESKTOP_INSTALL = NOT AUTHORIZED BY THIS SPEC ALONE`
`REFERENCE_BRIDGE_PRODUCTION = NO`
