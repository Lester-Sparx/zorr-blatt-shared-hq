# ZB Work Execution Adapter v1

This document defines the external ChatGPT Work execution adapter for Communication Orchestrator v0.

## Control-plane separation

Normal ChatGPT conversation is the control plane. GitHub is durable authority/evidence. ChatGPT Work is an execution plane only; it is not project memory and should not be used for unrelated analysis or planning.

## One webhook run = one logical-role execution

After a `ZB_AGENT_MESSAGE_V1` has passed source resolution, admission, authority, task/head/base/evidence bindings, and its `RECEIVED` receipt has been durably written and fresh-read MATCH, the same physical Work webhook run enters the target logical-role phase.

The adapter may then create `WorkRunContext(webhook_delivery_id, role_phase_started=True)` and call `start_current_work_run`.

The physical webhook delivery ID is the execution provenance. The canonical execution identity is `work-event:<WEBHOOK_DELIVERY_ID>`.

No delivery ID, unsafe delivery ID, or role phase before durable RECEIVED means `EXECUTION_START_FAILED`. No synthetic or guessed fallback execution ID is allowed.

## Truthful sequence

`MESSAGE -> verified RECEIVED -> role phase begins in current Work run -> verified RUNNING with work-event delivery identity -> role work -> RESULT|BLOCKED|DEAD_LETTER -> verified owner view -> at most one legal next MESSAGE`.

The current Work run must use only the message's legal logical role. GitHub transport remains `Lester-Sparx`; GitHub username never becomes logical-role authority.

## Stateless Work law

A Work run must reconstruct all durable protocol state from GitHub. Work-chat history is never authoritative. Self-generated receipt/owner-view events must not themselves become logical-role messages. No polling, schedule, sleep loop, manual relay, role-account switching, auto-merge, production activation, canon mutation, or OWNER LOCK is allowed.

OWNER remains a human gate and is never auto-executed.
