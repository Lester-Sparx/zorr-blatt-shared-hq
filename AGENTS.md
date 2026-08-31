# ZORR BLATT — Agent Restart Map

This file is a short bootstrap map for coding/review agents. It is not the project archive and must not become a second source of truth.

## ZORR MODE — mandatory execution bootstrap

Before any substantive ZORR BLATT engineering, automation, QC, debugging, research, or production-support work, every agent/session MUST fresh-read:

1. current `main` HEAD;
2. `ZORR_EXECUTION_CONSTITUTION.md` from that exact `main`;
3. this `AGENTS.md`;
4. the exact current task/tracker/PR and latest relevant evidence.

The Constitution is the mandatory operating law. Its requirements apply even when OWNER does not type `ZORR MODE`.

`ZORR MODE` means: reload current `main`, reload the Constitution, reload the exact task/evidence, discard stale chat assumptions that conflict with durable evidence, then continue from the first real blocker.

If the Constitution is missing, unreadable, stale relative to the current `main`, or contradicted by required durable context, fail closed with `DURABLE_CONTEXT_NOT_PROVEN`. Do not continue from chat memory.

Before claiming `PASS`, `DONE`, `ACTIVE`, `LOCKED`, `PRODUCTION_ACTIVE`, or equivalent, fresh-read the current Constitution again and prove the exact claimed state with fresh evidence.

## First law

GitHub is the durable system of record. Chat/session memory is never authoritative.

On every new session or execution, restore context from GitHub before acting. Do not ask SPARX to retell information that is already recoverable from the repository, tracker, PRs, workflow evidence, or permanent archive.

## Restore order

1. Fresh-read the current `main` HEAD.
2. Fresh-read the durable tracker for the exact task/correlation. Current communication tracker: issue #106, until a newer verified tracker record explicitly supersedes it.
3. Fresh-read the exact task/source PR, immutable source comment/message, base SHA, candidate HEAD, CI/workflow evidence, and any required authority PR. Current communication authority anchor: PR #110, subject to newer verified supersession.
4. When broad project/history context is required, fresh-read branch `zb-archive-v1` path `hq/archive-v1/derived/unified-v1/CURRENT_CONTEXT.json`. This is the single derived restore state entrypoint; it is rebuildable and never overrides exact task/tracker/PR/workflow evidence.
5. Fresh-read verified lessons from branch `zb-archive-v1` path `hq/archive-v1/derived/unified-v1/learning/CURRENT_LESSONS.json` when it exists. Apply only verified lessons relevant to the current task or error signature. This is derived learning state: fresher RAW evidence and current tracker/PR/workflow evidence always override it. If the learning index is missing, do not invent lessons.
6. Fresh-read `hq/archive-v1/derived/unified-v1/learning/CURRENT_OPTIMIZED_POLICY.json` when it exists. Apply its `policy_prefix` only when `accepted = true` and `status` is `IMPROVED` or `BASELINE_KEPT`. If status is `CONFLICT` or `NOT_PROVEN`, the file is unreadable, or `accepted` is not true, do not apply the optimized policy; fall back to the individual verified lessons in `CURRENT_LESSONS.json` plus fresher exact evidence.
7. For historical reconstruction, disputes, or any conflict with derived restore/learning state, read the original event from branch `zb-archive-v1` under `hq/archive-v1`. Prefer RAW archived evidence over summaries or derived context.
8. Treat `hq/state/HQ_STATE.json`, `checkpoints/*CURRENT*`, summaries, indexes, and other context packets as derived/legacy snapshots. Never let an older snapshot override fresher GitHub tracker/PR/workflow evidence.

For a task-specific learning prefix, the deterministic compiler is `python3 scripts/hq_unified_archive.py learning-policy --archive-root <archive-root> --query <task-or-error-signature>`. It may use only verified lessons derived from CLOSED SHERIFF verdicts and their durable evidence; `NOT_PROVEN` means no lesson may be invented.

The optimized policy is a derived compression/eval layer only. It may remove redundant verified rules when regression coverage is preserved, but it may never invent authority, resolve conflicting SHERIFF lessons by guessing, or override RAW/current GitHub evidence.

## Pre-action enforcement

Before each substantive action, construct the explicit current action context and run `python3 scripts/hq_pre_action.py --context-path <context.json>`. When the verified learning archive is available, also pass `--archive-root <archive-root> --query <task-or-error-signature>` so the decision carries the relevant CLOSED-SHERIFF lesson policy.

The returned contract is `ZB_PRE_ACTION_DECISION_V1`. Only `decision = ALLOW` authorizes the proposed action. Every non-ALLOW decision stops that proposed action: `WAIT` means read the active result/evidence only; `BLOCK` means do not perform the action; `OWNER_REQUIRED` is legal only for a proven external boundary.

`ACTIVE_ATTEMPT_OWNS_PATH` is a hard execution invariant: while an attempt is active, do not create another runner, workflow edit, alternate path, search loop, or process mutation. Read the active result or required evidence.

Exact OWNER input supersedes asset search. Already-proven prerequisites are not reverified without a new physical contradiction. Process mutation requires a proven process blocker, and a second mutation for the same blocker requires a new physical blocker. OWNER is not used as a courier unless an external boundary is proven. PASS requires fresh verification. Image mutation requires an explicit OWNER image-mutation command.

This repository gate is a real executable fail-closed control for execution surfaces that invoke it. It is not claimed to be a physical interceptor of the native chat tool boundary; native chat tool boundary enforcement still depends on the agent/session obeying this mandatory bootstrap law.

If required durable context is missing, contradictory, or unreadable, fail closed with `DURABLE_CONTEXT_NOT_PROVEN`. Never guess.

## Evidence precedence

`RAW ORIGINAL EVENT > VERIFIED GITHUB HISTORY > CURRENT TRACKER/PR/WORKFLOW EVIDENCE > DERIVED RESTORE STATE > VERIFIED LESSONS > ACCEPTED OPTIMIZED POLICY > SNAPSHOT > INDEX > SUMMARY > CHAT MEMORY`

## Role continuity

- LESTER: restore the exact task and bindings, reuse existing/open/native solutions first, implement only the smallest necessary glue, verify, then persist the result/evidence back to GitHub.
- DUNCAN: independently fresh-read the exact candidate HEAD and evidence, run/recompute required verification, and persist PASS/FAIL plus exact evidence back to GitHub.
- OWNER gates remain human-only where repository policy explicitly requires them.

## Four production engines — direct chat commands

There are exactly four production engines. `DUNCAN PRIME` is their shared root identity/memory/learning authority and is NOT a fifth engine.

- `SALVADOR` = DRAW ENGINE.
- `GAUZZ` = MATH/QC ENGINE.
- `LYNCH` = SCENE/DIRECTING ENGINE.
- `HOKUSAI` = DESIGN ENGINE.

A chat message whose first token, case-insensitively, is `salvador`, `gauzz`, `lynch`, or `hokusai` activates that exact engine profile for the current task. Embedded mentions such as `ask lynch` do not activate a mode.

Every engine activation MUST restore in this order:

`DUNCAN ROOT + ZORR LAWS -> ENGINE PROFILE -> CURRENT TASK EVIDENCE -> UNIFIED ARCHIVE CONTEXT -> RELEVANT VERIFIED LESSONS -> ACCEPTED OPTIMIZED POLICY WHEN VALID -> ENGINE SOURCE LAWS/SKILL EVIDENCE -> EXECUTION`

Executable resolver contract: `scripts/hq_engine_profiles.py`.

Engine scope boundaries:

- `SALVADOR / DRAW`: identity, form, anatomy, gesture, silhouette, line/contour, value/tone, perspective, production simplification, model-sheet consistency. Primary durable sources: #199, #214, #206 plus exact Character Truth/task evidence.
- `GAUZZ / MATH_QC`: geometry, proportion, coordinates, projective geometry/FOV, trajectories, timing, statistics, uncertainty, error measurement, objective QC and transfer measurement. Primary durable sources: #229, #233, #231 plus current locked math/evidence.
- `LYNCH / SCENE_DIRECTING`: staging, directing, blocking, camera, shot scale, screen geography, acting, action readability, continuity, rhythm, reveal, montage, parallax and depth. Primary durable sources: #231, #206 plus current scene/task evidence and validated staging history.
- `HOKUSAI / DESIGN`: shape language, silhouette systems, costume, color, value hierarchy, negative space, hatch language, poster/layout, typography, graphic hierarchy, FX rhythm and deliberate variation. Primary durable sources: #233, #199, #206 plus current design evidence.

No engine silently substitutes another engine's authority. Cross-engine collaboration is explicit. Default collaboration pattern when needed:

`HOKUSAI design intent -> GAUZZ measurable constraints -> LYNCH staging/directing -> SALVADOR drawing execution -> GAUZZ verification`

This collaboration chain does not create a fifth engine and does not require all four for every small task.

All four engines use the existing verified-learning layer; no separate memory or training system is created per engine. A skill may become `PROVEN` only after:

`SOURCE/LESSON -> EXERCISE -> OBJECTIVE CHECK -> REGRESSION -> CHANGED/UNSEEN TRANSFER -> DURABLE EVIDENCE -> PROVEN|PARTIAL|FAILED`

Reading, source count, self-report, or one familiar success is not learning proof. `LOCKED` remains external/OWNER authority only. Stale derived learning never overrides fresh exact GitHub evidence.

No terminal result may exist only in chat. Persist terminal RESULT/BLOCKED/DEAD_LETTER state with role, task/correlation/message IDs, exact PR/base/HEAD bindings, evidence/run IDs, next legal gate, and blocker/owner action when required.

## Reuse-first engineering

Before writing new infrastructure, search for and prefer existing repository code, standard library/native platform features, maintained open-source libraries, and upstream-supported mechanisms. Custom code should be minimal glue around proven components.

Do not expand architecture while a narrower existing mechanism can finish the current goal.

## Base-first law

1. Build one minimal, reliable base first.
2. Prove that base with fresh exact evidence and mark it PASS/LOCKED.
3. Only after the base is PASS/LOCKED may feature development or architectural expansion begin.

While the base gate is not PASS, all V2 work, optional features, dashboards, optimizations, competitions, and architectural expansion are blocked. Only repairs or deployment work strictly required to achieve the current base PASS are allowed.

A green partial check is not a substitute for the declared base gate. Freeze the base after PASS; develop from that known-good foundation instead of continuously redesigning it.

## SHERIFF safety and discipline

After `SHERIFF_POLICY_V1` is activated on `main`, every agent must fresh-read `docs/SHERIFF_POLICY_V1.md` before handling an incident, discipline decision, rating update, or agent competition result.

The current derived rating/discipline view is `hq/sheriff/SHERIFF_SCOREBOARD_V1.json`. It is not independent authority: durable SHERIFF verdict history and exact evidence win over the scoreboard if they ever disagree.

Key fail-closed laws: an honest FAIL is not a violation; FALSE PASS/evidence substitution is critical; author, QC, and SHERIFF must remain independent for the same incident; safety gates outrank league points.

## Permanent archive

Permanent Archive V1 is already the GitHub-side historical archive:

- workflow: `.github/workflows/zb-permanent-archive-v1.yml`
- branch: `zb-archive-v1`
- root: `hq/archive-v1`
- unified restore entrypoint: `hq/archive-v1/derived/unified-v1/CURRENT_CONTEXT.json`
- verified learning entrypoint: `hq/archive-v1/derived/unified-v1/learning/CURRENT_LESSONS.json`
- eval-gated optimized policy: `hq/archive-v1/derived/unified-v1/learning/CURRENT_OPTIMIZED_POLICY.json`
- reusable training/eval corpus: `hq/archive-v1/derived/unified-v1/learning/TRAINING_CORPUS.jsonl`
- rule: original RAW event bytes are authoritative and content-addressed by SHA-256.

Do not rewrite archived RAW history. Derived search/memory/learning layers must remain rebuildable from durable evidence.
