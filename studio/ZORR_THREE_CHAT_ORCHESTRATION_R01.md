# ZORR THREE-CHAT ORCHESTRATION R01

STATUS = ACTIVE COORDINATION CONTRACT
BRANCH = `duncan/zorr-studio-r01`
ROOT = DUNCAN PRIME

Purpose: use two additional ChatGPT conversations plus the current master conversation without creating three competing authorities.

## MASTER CHAT — DUNCAN PRIME / INTEGRATOR

This current chat owns:

- production order;
- cross-workstream arbitration;
- PASS/FAIL promotion;
- owner-taste / ZORR-style integration;
- durable GitHub checkpointing;
- conflict resolution between character, world, camera, shot, and animation layers;
- final decision on when a downstream gate is legally opened.

The master chat should not duplicate work that is already delegated unless fresh evidence shows a blocker or conflict.

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

- CHAT A = active critical-path execution;
- CHAT B = downstream specification/preparation;
- MASTER = integration/QC/orchestration.

No two chats may independently redefine the same lock.

If two workstreams discover a conflict:

`STOP LOCAL PROMOTION -> RECORD CONFLICT -> MASTER ARBITRATION -> ONE AUTHORITY DECISION -> CONTINUE`

## START COMMANDS

OWNER only needs to open two new chats and send one short command to each.

CHAT A:

`ZORR MODE. Ты WORKSTREAM A. Возьми issue #249 и активный gate #248. Работай по GitHub, не проси меня пересказывать контекст. ПРОД.`

CHAT B:

`ZORR MODE. Ты WORKSTREAM B. Возьми issue #250. Готовь WORLD / CAMERA / S001 CONTRACT по GitHub, не открывая downstream PASS раньше gate. ПРОД.`

After that, the master chat coordinates from GitHub directly.

## CURRENT ROUTE

`#245 MODEL LOCK PASS`
-> `#248 COSTUME MECHANICS` [CHAT A]
-> `POSE MECHANICS` [CHAT A]
-> `CAMERA / WORLD / S001 CONTRACT` [CHAT B prepared, MASTER promotes]
-> `LINE/COLOR/SHADOW/MATERIAL`
-> `GOLDEN KEYFRAME`
-> `SEPARATED OPENTOONZ SOURCE`
-> `S001 PHYSICAL BASE`
-> `OPENTOONZ CUT`
-> `FINAL QC`
