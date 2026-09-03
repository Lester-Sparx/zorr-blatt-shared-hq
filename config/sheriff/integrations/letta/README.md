# SHERIFF Letta event bridge

This agent-scoped Letta Code mod connects real DUNCAN turns and failures to the
existing SHERIFF V1 JetStream path without publishing NATS or PostgreSQL ports
to the host and without adding another daemon or policy engine.

The bridge:

- emits `zb.agent.task.started` for each outbound user turn;
- emits evidence-pointer-only honest `FAIL` events for tool and provider errors;
- never sends prompt text, tool output, model output, or secrets;
- never infers or automatically emits `PASS`;
- reuses `podman exec -i` and the existing `nats-py` client inside the running
  `zb-sheriff-sheriff-worker-1` container, preserving Compose-internal NATS.
- requires `SHERIFF_LETTA_AGENT_ID` to match the exact Letta agent and
  `SHERIFF_EVENT_HMAC_KEY` to pseudonymize stable runtime identifiers.

Install for the current MemFS-backed DUNCAN agent:

```powershell
& .\config\sheriff\integrations\letta\Install-SheriffLettaBridge.ps1
```

`MEMORY_DIR` must identify the target agent memory filesystem. Run `/reload` or
restart the Letta host after installation. A stopped SHERIFF worker fails
closed into a local mod diagnostic; it never becomes permission or PASS.

This bridge cannot emit a successful result. PASS remains outside the author
agent and requires a separate deterministic verifier or independent QC path.
