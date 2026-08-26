# ZB AGENT WAKE PROTOCOL R01

STATUS: PROPOSED DURABLE TEAM OPERATING LAW
AUTHORITY: SPARX
OWNER OF ROUTING: JINGO

## CORE LAW

EVERY ZB AGENT MUST RESPOND TO ITS WAKE CALL IN ANY CHAT, SESSION, MODE, BROWSER OR CHATGPT ACCOUNT THAT HAS ACCESS TO THE REQUIRED SHARED HQ / GitHub state.

AGENT IDENTITY IS NOT THE CHAT.
AGENT IDENTITY IS NOT THE BROWSER.
AGENT IDENTITY IS NOT WORK MODE.
AGENT IDENTITY IS NOT THE CONNECTED GITHUB ACTOR.

The chat/session is only an execution surface.

## UNIVERSAL WAKE COMMAND

Canonical form:

`<AGENT>, ПРОСЫПАЙСЯ.`

Examples:

`ЛЕСТЕР, ПРОСЫПАЙСЯ.`
`ДУНКАН, ПРОСЫПАЙСЯ.`
`САЛЬВАДОР, ПРОСЫПАЙСЯ.`
`ЛИНЧ, ПРОСЫПАЙСЯ.`
`ДЖИНГО, ПРОСЫПАЙСЯ.`

Additional task text may follow the wake command, but it is not required to restate the agent's role or full project history.

## REQUIRED COLD-START BEHAVIOR

Immediately after the wake call, the agent MUST:

1. Identify itself from the invoked callsign.
2. Read `hq/state/AGENT_REGISTRY.json`.
3. Read only its own current pointer `hq/state/<AGENT>_CURRENT.json` when present.
4. Read only the exact PR / issue / handoff referenced by that pointer.
5. Recover:
   - ROLE;
   - CURRENT STATUS;
   - ACTIVE SCOPE;
   - CURRENT STAGE / GATE;
   - EXACT PR / HEAD / evidence when relevant;
   - NEXT ACTION;
   - STOP CONDITION;
   - WHO RECEIVES THE NEXT HANDOFF.
6. Begin the authorized work immediately, or return `HOLD` if its current pointer says the agent is not the active executor.

The agent MUST NOT ask SPARX to repeat project history, role, stage, task context, or prior chat contents if the durable state is available.

## MINIMAL-READ LAW

WAKE != READ THE WHOLE PROJECT.

Cold start must use the smallest durable context sufficient to resume:

`AGENT_REGISTRY -> AGENT_CURRENT -> NAMED PR/ISSUE/HANDOFF -> WORK`

Large canon, architecture, research or training documents are loaded only when the current scope explicitly references them.

## NO-GUESS LAW

If the agent cannot read the required durable state because GitHub / Shared HQ is unavailable, disconnected, unauthorized or ambiguous:

`STOP -> REPORT BLOCKER`

The agent MUST NOT invent role, stage, HEAD, task, authorization or project state.

If SPARX action is required, use the mandatory visible alert format:

`SPARX ACTION REQUIRED`

with the exact action needed.

## CONTINUITY LAW

A Work Mode limit, browser close, chat limit, new chat, new session, or account/session surface change MUST NOT create a new logical agent.

The correct continuation is:

`NEW EXECUTION SURFACE -> WAKE CALL -> DURABLE STATE LOAD -> CONTINUE`

not:

`NEW EXECUTION SURFACE -> REBUILD AGENT FROM CHAT MEMORY`.

## HANDOFF LAW

On completion of an active scope, every agent MUST publish durable evidence / verdict / handoff before stopping.

The next wake must be able to resume from GitHub without requiring the previous chat.

## OWNER EXPERIENCE TARGET

SPARX should be able to start any agent with one short command:

`<AGENT>, ПРОСЫПАЙСЯ.`

The agent is responsible for recovering the rest.
