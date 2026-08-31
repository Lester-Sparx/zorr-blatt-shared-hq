# ZORR THREE-CHAT ORCHESTRATION R01

STATUS = ACTIVE COORDINATION CONTRACT
BRANCH = `duncan/zorr-studio-r01`
ROOT = DUNCAN PRIME
SHARED SHERIFF LAW = `studio/ZORR_SHERIFF_THREE_CHAT_LAW_R01.md`
MORNING BOOTSTRAP = `studio/ZORR_MORNING_BOOTSTRAP_R01.md`

Purpose: use **three dedicated ChatGPT conversations** with one durable GitHub authority and no competing locks.

All three chats are constrained by `studio/ZORR_SHERIFF_THREE_CHAT_LAW_R01.md` and recover through `studio/ZORR_MORNING_BOOTSTRAP_R01.md`. Both are fresh-read at restart and before material promotion. Neither replaces the exact workstream tracker or fresh GitHub evidence.

## CHAT C — MASTER / DUNCAN PRIME INTEGRATOR

Tracker: #251
Bootstrap: `studio/ZORR_MASTER_CHAT_BOOTSTRAP_R01.md`

This dedicated master chat owns:

- production order;
- cross-workstream arbitration;
- PASS/FAIL promotion from fresh evidence;
- OWNER-taste / ZORR-style integration;
- durable GitHub checkpointing;
- conflict resolution between character, world, camera, shot, and animation layers;
- final decision on when a downstream gate is legally opened.

The master chat does not duplicate work already delegated unless fresh evidence shows a blocker or conflict.

## CHAT A — CHARACTER MECHANICS

Tracker: #249

The active character/costume gate must be fresh-read from current tracker evidence. At orchestration creation, #248 `COSTUME_MECHANICS_R01` was the known active gate; that historical note is not self-updating authority.

Owns:

`COSTUME_MECHANICS_R01 -> POSE_MECHANICS_VISUAL_R01`

Boundaries:

- existing character model remains fixed by proven model-lock evidence unless fresher authority changes it;
- no generic BODY/HAIR/HANDS reinvestigation;
- no character redesign;
- no S001 physical build;
- no camera/world lock;
- no image generation/editing without exact OWNER authorization.

Required handoff format:

`ROLE / RESULT / DELTA / EVIDENCE / OPEN / NEXT`

## CHAT B — WORLD / CAMERA / SHOT CONTRACT

Tracker: #250

Owns downstream preparation while upstream gates remain unresolved:

- `CAMERA_LAYOUT_VISUAL_R01` requirements;
- ZORR world integration;
- S001 contract audit;
- aspect/resolution/FPS/framing/overscan/max-push questions;
- physical BG/MID/FG/CHAR source requirements.

Boundaries:

- may prepare specs and evidence;
- may not claim downstream production PASS before prerequisites;
- local aspect assumptions remain local until globally promoted;
- Babylon remains optional spatial evidence only;
- no image generation/editing without exact OWNER authorization.

Required handoff format:

`ROLE / RESULT / DELTA / EVIDENCE / OPEN / NEXT`

## SHARED DURABLE STATE

All three chats must fresh-read:

1. current `main` HEAD;
2. `ZORR_EXECUTION_CONSTITUTION.md`;
3. `AGENTS.md`;
4. authoritative `studio/ZORR_MORNING_BOOTSTRAP_R01.md`;
5. authoritative `studio/ZORR_SHERIFF_THREE_CHAT_LAW_R01.md`;
6. their exact tracker;
7. latest master/studio route evidence;
8. current `duncan/zorr-studio-r01` HEAD and relevant open PR state;
9. current active production gate.

A SHA written in a prior chat, bootstrap, handoff, summary, or checkpoint is historical evidence only until fresh-read. Do not encode a static SHA as the durable current HEAD.

GitHub is the shared memory and authority transport. The OWNER must not manually relay long status text between chats when the information is already in GitHub.

## CONCURRENCY LAW

Parallelism is allowed only where responsibilities do not compete.

Current role partition:

- CHAT A = character-mechanics critical-path execution;
- CHAT B = downstream specification/preparation;
- CHAT C = DUNCAN PRIME integration/QC/orchestration.

No two chats may independently redefine the same lock.

If two workstreams discover a conflict:

`STOP LOCAL PROMOTION -> RECORD CONFLICT -> CHAT C MASTER ARBITRATION -> ONE AUTHORITY DECISION -> CONTINUE`

## MORNING START COMMANDS

CHAT A:

`ZORR MORNING A. Репозиторий Lester-Sparx/zorr-blatt-shared-hq. Сам восстанови fresh durable state по issue #249, PR #252 если он ещё authoritative, studio/ZORR_MORNING_BOOTSTRAP_R01.md и SHERIFF law. Не проси меня пересказывать контекст. Работай только CHARACTER / COSTUME -> POSE. SHERIFF ON. ПРОД.`

CHAT B:

`ZORR MORNING B. Репозиторий Lester-Sparx/zorr-blatt-shared-hq. Сам восстанови fresh durable state по issue #250, PR #252 если он ещё authoritative, studio/ZORR_MORNING_BOOTSTRAP_R01.md и SHERIFF law. Не проси меня пересказывать контекст. Работай только WORLD / CAMERA / S001 в пределах открытых gates. SHERIFF ON. ПРОД.`

CHAT C / MASTER:

`ZORR MORNING C. Репозиторий Lester-Sparx/zorr-blatt-shared-hq. Ты DUNCAN PRIME MASTER / INTEGRATOR. Сам восстанови fresh durable state по issue #251, trackers #249/#250, PR #252 если он ещё authoritative, studio/ZORR_MORNING_BOOTSTRAP_R01.md, master bootstrap, orchestration и SHERIFF law. Не проси меня пересказывать контекст. Не дублируй A/B. SHERIFF ON. ПРОД.`

After boot, all three coordinate through GitHub directly.

## CURRENT ROUTE

The route itself must be fresh-read from GitHub. Historical studio route at this contract revision:

`MODEL LOCK`
-> `COSTUME MECHANICS` [CHAT A]
-> `POSE MECHANICS` [CHAT A]
-> `CAMERA / WORLD / S001 CONTRACT` [CHAT B prepared, CHAT C promotes]
-> `LINE/COLOR/SHADOW/MATERIAL`
-> `GOLDEN KEYFRAME`
-> `SEPARATED OPENTOONZ SOURCE`
-> `S001 PHYSICAL BASE`
-> `OPENTOONZ CUT`
-> `FINAL QC`
