# ZB Work Execution Adapter v1

This document defines the external ChatGPT Work execution adapter for Communication Orchestrator v0.

## Control-plane separation

Normal ChatGPT conversation is the control plane. GitHub is durable authority/evidence. ChatGPT Work is an execution plane only; it is not project memory and should not be used for unrelated analysis or planning.

## Bodyless event reconciliation

A Work `issue_comment.created` run may expose neither source comment ID nor body. The adapter performs one event-local PR-comment reconciliation against the configured ingress epoch and the durable processed-source ledger.

If there are zero unprocessed protocol-message candidates, the run is a benign `NOOP`: this is how bodyless events caused by self-generated receipts/owner views are ignored. It must not write a blocker or start any role.

If there is more than one unprocessed candidate, fail closed with `SOURCE_COMMENT_RESOLUTION_FAILED`.

If there is exactly one candidate, fresh-read that exact numeric source ID/body before admission.

No repeated discovery, polling, sleep loop, or scheduled fallback is permitted.

## One webhook run = one logical-role execution

After a `ZB_AGENT_MESSAGE_V1` has passed source resolution, admission, authority, task/head/base/evidence bindings, and its `RECEIVED` receipt has been durably written and fresh-read MATCH, the same physical Work webhook run enters the target logical-role phase.

The adapter may then create `WorkRunContext(webhook_delivery_id, role_phase_started=True)` and call `start_current_work_run`.

The physical webhook delivery ID is the execution provenance. The canonical execution identity is `work-event:<WEBHOOK_DELIVERY_ID>`.

No delivery ID, unsafe delivery ID, or role phase before durable RECEIVED means `EXECUTION_START_FAILED`. No synthetic or guessed fallback execution ID is allowed.

## Deterministic claim against concurrent bodyless runs

A persisted `RECEIVED` receipt is also the execution claim for its exact `MESSAGE_ID` + `SOURCE_COMMENT_ID`.

After fresh read-back of its own `RECEIVED`, the Work run performs one fresh read of PR comments and gathers all valid `RECEIVED` receipts for that same immutable message/source pair. The receipt with the smallest numeric remote comment ID owns the execution claim.

Only the claim owner may enter RUNNING. Any later claimant stops before role execution as `DUPLICATE`; it must not emit RUNNING or a second terminal result.

This rule makes simultaneous bodyless event-runs deterministic without a polling loop or external lock.

## Truthful sequence

`MESSAGE -> verified RECEIVED -> deterministic claim -> role phase begins in current Work run -> verified RUNNING with work-event delivery identity -> role work -> RESULT|BLOCKED|DEAD_LETTER -> verified owner view -> at most one legal next MESSAGE`.

The current Work run must use only the message's legal logical role. GitHub transport remains `Lester-Sparx`; GitHub username never becomes logical-role authority.

The validated incoming evidence pair may be carried forward as the protocol evidence binding when the role does not create stronger evidence. The physical Work execution identity remains the proof that the logical role actually ran.

## Stateless Work law

A Work run must reconstruct all durable protocol state from GitHub. Work-chat history is never authoritative. Self-generated receipt/owner-view events must not themselves become logical-role messages. The Work run does not open or depend on a separate Work chat/task for the logical role; the current event-run is the execution surface.

No polling, schedule, sleep loop, manual relay, role-account switching, auto-merge, production activation, canon mutation, or OWNER LOCK is allowed.

OWNER remains a human gate and is never auto-executed.
