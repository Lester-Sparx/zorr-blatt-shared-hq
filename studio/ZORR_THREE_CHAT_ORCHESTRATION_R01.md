# ZORR THREE-CHAT ORCHESTRATION R01

STATUS = ACTIVE COORDINATION CONTRACT
BRANCH = `duncan/zorr-studio-r01`
ROOT = DUNCAN PRIME

Purpose: use **three dedicated ChatGPT conversations** with one durable GitHub authority and no competing locks.

## CHAT C — MASTER / DUNCAN PRIME INTEGRATOR

Tracker: #251
Bootstrap: `studio/ZORR_MASTER_CHAT_BOOTSTRAP_R01.md`

This dedicated new master chat owns:

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
Active gate authority: #248 `COSTUME_MECHANICS_R01`.

Owns:

`COSTUME_MECHANICS_R01 -> POSE_MECHANICS_VISUAL_R01`

Boundaries:

- existing character model remains fixed by #245 PASS;
- no generic BODY/HAIR/HANDS reinvestigation;
- no character redesign;
- no S001 physical build;
- no camera/world lock;
- no image generation/editing without exact OWNER authorization.

Required handoff format:

`RESULT / EVIDENCE / OPEN / NEXT`

## CHAT B — WORLD / CAMERA / SHOT CONTRACT

Tracker: #250

Owns downstream preparation only while #248 remains the active production gate:

- `CAMERA_LAYOUT_VISUAL_R01` requirements;
- ZORR world integration;
- S001 contract audit;
- aspect/resolution/FPS/framing/overscan/max-push questions;
- physical BG/MID/FG/CHAR source requirements.

Boundaries:

- may prepare specs and evidence;
- may not claim downstream production PASS before prerequisites;
- `9:16` remains S001-specific assumption, not global canon;
- Babylon remains optional spatial evidence only;
- no image generation/editing without exact OWNER authorization.

Required handoff format:

`RESULT / EVIDENCE / OPEN / NEXT`

## SHARED DURABLE STATE

All three chats must fresh-read:

1. current `main` HEAD;
2. `ZORR_EXECUTION_CONSTITUTION.md`;
3. `AGENTS.md`;
4. their exact tracker;
5. latest master/studio route evidence.

GitHub is the shared memory and authority transport. The OWNER must not manually relay long status text between chats when the information is already in GitHub.

## CONCURRENCY LAW

Parallelism is allowed only where responsibilities do not compete.

Current arrangement:

- CHAT A = active character-mechanics critical-path execution;
- CHAT B = downstream specification/preparation;
- CHAT C = DUNCAN PRIME integration/QC/orchestration.

No two chats may independently redefine the same lock.

If two workstreams discover a conflict:

`STOP LOCAL PROMOTION -> RECORD CONFLICT -> CHAT C MASTER ARBITRATION -> ONE AUTHORITY DECISION -> CONTINUE`

## START COMMANDS

CHAT A:

`ZORR MODE. Ты WORKSTREAM A. Возьми issue #249 и активный gate #248. Работай по GitHub, не проси меня пересказывать контекст. ПРОД.`

CHAT B:

`ZORR MODE. Ты WORKSTREAM B. Возьми issue #250. Готовь WORLD / CAMERA / S001 CONTRACT по GitHub, не открывая downstream PASS раньше gate. ПРОД.`

CHAT C / MASTER:

`ZORR MODE. Ты DUNCAN PRIME MASTER / INTEGRATOR. Возьми issue #251, studio/ZORR_MASTER_CHAT_BOOTSTRAP_R01.md, orchestration R01, trackers #249/#250 и активный gate #248. Сам восстанови всё из GitHub. Координируй два workstream, не дублируй их работу. ПРОД.`

After boot, all three coordinate through GitHub directly.

## CURRENT ROUTE

`#245 MODEL LOCK PASS`
-> `#248 COSTUME MECHANICS` [CHAT A]
-> `POSE MECHANICS` [CHAT A]
-> `CAMERA / WORLD / S001 CONTRACT` [CHAT B prepared, CHAT C promotes]
-> `LINE/COLOR/SHADOW/MATERIAL`
-> `GOLDEN KEYFRAME`
-> `SEPARATED OPENTOONZ SOURCE`
-> `S001 PHYSICAL BASE`
-> `OPENTOONZ CUT`
-> `FINAL QC`
