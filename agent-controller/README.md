# ZB Local Agent Controller v0 — RETIRED EXECUTION ROUTE

`STATUS = EXECUTION RETIRED / READ-ONLY CONSOLE RETAINED`

The old Windows-local SALVADOR execution route is no longer an active ZORR production path.

Fresh product authority is issue #251. Tooling is selected only when the current studio phase requires it. The former fixed route:

`SALVADOR -> PRODUCTION_IMAGE_EDIT -> COMFYUI_LOCAL`

must not be used as a global prerequisite, fallback production path, or substitute for the current product phase.

## Fail-closed execution boundary

The former daemon entrypoint is deliberately retired:

```powershell
python -m zb_local_controller --once
```

returns non-zero with `RETIRED_PRODUCTION_ROUTE` and does not initialize GitHub polling, task dispatch, or a ComfyUI backend.

`agent-controller/scripts/run-controller.cmd` is also fail-closed with the same retirement marker.

Historical controller/backend/task-contract modules remain in the repository for evidence compatibility and bounded later cleanup. Their presence does not establish production authority or activation.

## Read-only owner console retained

The useful read-only `zb` console remains available. It reads GitHub owner-view evidence and validated local result files; it does not submit production jobs.

Install the local `zb` PowerShell command when needed:

```powershell
cd D:\BLATT2\zb-local-agent-controller
powershell -ExecutionPolicy Bypass -File .\scripts\install-zb-console.ps1
```

Commands:

```powershell
zb
zb why
zb agents
zb gates
zb scout
zb output
zb watch
```

The console cannot post comments, submit jobs, merge or approve changes, activate production, mutate canon, or create OWNER LOCK.

`zb output` opens only a `result.png` whose PNG signature and SHA-256 match its parseable `result.json`. A local result never establishes production or canon approval by itself.
