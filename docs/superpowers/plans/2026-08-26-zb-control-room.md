# ZB Control Room R01 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tiny monochrome 8-bit browser dashboard hosted by GitHub Pages that shows ZB agent state and audibly alerts SPARX on blockers/action-required events.

**Architecture:** A static page in `control-room/` polls one presentation-only JSON file, `hq/state/CONTROL_ROOM.json`, every 15 seconds. NES.css provides the UI shell, Beep.js provides sound, and minimal vanilla JavaScript renders state and deduplicates alerts. No backend/database/framework is introduced.

**Tech Stack:** HTML5, CSS, vanilla JavaScript ES modules, NES.css 2.3.0, Beep.js 1.0.1, GitHub Pages, Node built-in test runner for pure state logic.

**Spec:** `docs/superpowers/specs/2026-08-26-zb-control-room-design.md`

## Global Constraints

- Static site only; no backend/database.
- Reuse NES.css 2.3.0 and Beep.js 1.0.1.
- Black/white only.
- Poll every 15 seconds.
- Browser never writes project state.
- `CONTROL_ROOM.json` is presentation state, not authority.
- Public data only; no secrets/private runtime source/chat content.
- Audio must require explicit `ARM ALARMS` user interaction before first beep.
- DUNCAN performs independent QC before JINGO accepts the dashboard.

---

## File Structure

- Create `control-room/index.html` — page shell and CDN includes.
- Create `control-room/app.css` — tiny monochrome overrides only.
- Create `control-room/state.mjs` — pure validation/normalization/alert identity logic.
- Create `control-room/app.mjs` — fetch, render, polling, Beep.js integration.
- Create `control-room/tests/state.test.mjs` — unit tests for pure state logic.
- Create `hq/state/CONTROL_ROOM.json` — presentation snapshot used by the site.
- Create `.github/workflows/control-room-pages.yml` — official GitHub Pages deployment/check workflow if Pages settings allow Actions deployment.

### Task 1: Presentation-State Contract

**Files:**
- Create: `hq/state/CONTROL_ROOM.json`
- Create: `control-room/state.mjs`
- Test: `control-room/tests/state.test.mjs`

**Interfaces:**
- Consumes: JSON object shaped by the design spec.
- Produces: `normalizeControlRoomState(raw)` and `alertIdentity(alert)`.

- [ ] **Step 1: Write failing tests**

Create `control-room/tests/state.test.mjs` using `node:test` and `node:assert/strict` with cases proving:

```js
normalizeControlRoomState({ schemaVersion: 1, updatedAt: '2026-08-26T12:00:00Z', currentGate: 'TEST', alert: { level: 'NONE', title: '', message: '', action: '' }, agents: [] })
```

returns a normalized state; invalid alert level throws; missing agents throws; and `alertIdentity()` returns the same string for unchanged alert content but a different string when title/message/action changes.

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
node --test control-room/tests/state.test.mjs
```

Expected: FAIL because `state.mjs` does not exist yet.

- [ ] **Step 3: Implement minimal pure state module**

Implement only:

```js
export const ALERT_LEVELS = new Set(['NONE', 'BLOCKER', 'ACTION_REQUIRED']);
export const AGENT_STATUSES = new Set(['ACTIVE', 'WAITING', 'HOLD', 'DONE', 'BLOCKED', 'OFFLINE', 'PROPOSED']);
export function normalizeControlRoomState(raw) { /* validate and return normalized plain object */ }
export function alertIdentity(alert) { return [alert.level, alert.title, alert.message, alert.action].join('|'); }
```

No DOM/fetch/audio code in this file.

- [ ] **Step 4: Add initial `CONTROL_ROOM.json`**

Seed current visible state with all six roles and the current technical gate. Mark the file explicitly as presentation-only through fields such as `schemaVersion`, `updatedAt`, `currentGate`, `alert`, and `agents`; do not include secrets.

- [ ] **Step 5: Run tests**

```bash
node --test control-room/tests/state.test.mjs
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add control-room/state.mjs control-room/tests/state.test.mjs hq/state/CONTROL_ROOM.json
git commit -m "feat: add control room state contract"
```

### Task 2: Static 8-bit Page

**Files:**
- Create: `control-room/index.html`
- Create: `control-room/app.css`

**Interfaces:**
- Consumes: DOM data rendered later by `app.mjs`.
- Produces DOM targets: `#agent-table-body`, `#current-gate`, `#last-update`, `#alert-panel`, `#alert-title`, `#alert-message`, `#alert-action`, `#arm-alarms`, `#data-health`.

- [ ] **Step 1: Create page shell**

Use pinned CDN URLs:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/nes.css@2.3.0/css/nes.min.css">
<script src="https://cdn.jsdelivr.net/npm/beepjs@1.0.1/build/beep.min.js"></script>
```

The page must contain only the dashboard sections defined in the spec and load `app.mjs` as `type="module"`.

- [ ] **Step 2: Add monochrome CSS overrides**

In `app.css`, force:

```css
:root { color-scheme: dark; }
body { background: #000; color: #fff; font-family: monospace; }
```

Use only black, white and transparency; square/pixel borders; no gradients; no decorative color.

- [ ] **Step 3: Static smoke check**

Run:

```bash
python3 -m http.server 8000
```

Open `/control-room/` and confirm the shell loads without console errors except expected missing dynamic data before Task 3.

- [ ] **Step 4: Commit**

```bash
git add control-room/index.html control-room/app.css
git commit -m "feat: add control room 8-bit shell"
```

### Task 3: Polling, Rendering and Audible Alerts

**Files:**
- Create: `control-room/app.mjs`
- Modify: `control-room/index.html`
- Test: `control-room/tests/state.test.mjs`

**Interfaces:**
- Consumes: `normalizeControlRoomState`, `alertIdentity`, and `hq/state/CONTROL_ROOM.json`.
- Produces: live DOM rendering, 15-second polling, stale-data warning, deduplicated beep behavior.

- [ ] **Step 1: Add failing pure tests for alert transition helper**

Extend `state.mjs` with planned pure helper:

```js
export function shouldBeep({ armed, previousIdentity, nextAlert })
```

Test that it returns false when not armed, false for `NONE`, false for unchanged alert identity, and true for a new `BLOCKER`/`ACTION_REQUIRED` identity.

- [ ] **Step 2: Run tests and verify failure**

```bash
node --test control-room/tests/state.test.mjs
```

Expected: FAIL because `shouldBeep` is missing.

- [ ] **Step 3: Implement helper and make tests pass**

Keep this function DOM/audio-free.

- [ ] **Step 4: Implement browser glue**

`app.mjs` must:

1. Fetch `../hq/state/CONTROL_ROOM.json?ts=<Date.now()>` when served from repository-root Pages; if deployment path differs, use a single constant for the JSON URL.
2. Normalize state.
3. Render all agent rows.
4. Update current gate and timestamp.
5. Show/hide the alert panel.
6. Keep last good state on fetch failure and set `#data-health` to `DATA STALE / FETCH FAILED`.
7. Poll every 15,000 ms.
8. On `ARM ALARMS`, initialize `Beep` once and set armed state.
9. For a new blocker/action alert, play a short sequence such as `[[880,100],[0,80],[880,100],[0,80],[1200,160]]` through Beep.js.
10. Never beep again for an unchanged alert identity.

- [ ] **Step 5: Run unit tests**

```bash
node --test control-room/tests/state.test.mjs
```

Expected: PASS.

- [ ] **Step 6: Manual browser checks**

With `python3 -m http.server 8000`:

- change local JSON alert from `NONE` to `ACTION_REQUIRED`;
- verify visible banner appears on next poll;
- click `ARM ALARMS` and change alert content again;
- verify one beep sequence;
- leave alert unchanged for 30+ seconds and verify no repeating beep;
- temporarily break JSON URL and verify stale warning while last good state stays rendered.

- [ ] **Step 7: Commit**

```bash
git add control-room/app.mjs control-room/state.mjs control-room/tests/state.test.mjs control-room/index.html
git commit -m "feat: add control room live alerts"
```

### Task 4: GitHub Pages Deployment Gate

**Files:**
- Create/Modify: `.github/workflows/control-room-pages.yml` only if Pages Actions deployment is usable without violating current repo settings.

**Interfaces:**
- Consumes: `control-room/` static site and repository settings.
- Produces: one ordinary browser URL.

- [ ] **Step 1: Inspect current Pages capability/settings available through GitHub**

Determine whether Pages is already configured. Do not guess.

- [ ] **Step 2A: If Pages is configurable by workflow without SPARX action**

Use official pinned GitHub Pages actions only (`actions/checkout`, `actions/configure-pages`, `actions/upload-pages-artifact`, `actions/deploy-pages`) and deploy only the required static content/data.

- [ ] **Step 2B: If GitHub requires repository-owner UI enablement**

STOP. Post a durable handoff containing exactly:

```text
SPARX_ACTION_REQUIRED
REASON = GitHub Pages must be enabled in repository Settings
ACTION = exact Settings -> Pages click path
AFTER = rerun deployment / verify URL
```

Do not invent a workaround/server.

- [ ] **Step 3: Verify deployed URL**

Open the final Pages URL and verify HTTP success, live JSON polling, and static assets.

- [ ] **Step 4: Commit deployment config if used**

```bash
git add .github/workflows/control-room-pages.yml
git commit -m "ci: deploy ZB control room to Pages"
```

### Task 5: Lester Handoff and Duncan Independent QC

**Files:**
- No new product files unless fixing a verified defect.

**Interfaces:**
- Consumes: exact PR HEAD, test results, Pages URL.
- Produces: `LESTER_CONTROL_ROOM_READY` then `DUNCAN_CONTROL_ROOM_QC_COMPLETE`.

- [ ] **Step 1: LESTER posts durable handoff**

Required fields:

```text
LESTER_CONTROL_ROOM_READY
EXACT_HEAD = <sha>
PAGES_URL = <url or SPARX_ACTION_REQUIRED>
STATE_TESTS = PASS
BROWSER_SMOKE = PASS
ALERT_VISIBLE = PASS
ALERT_AUDIO_AFTER_ARM = PASS
UNCHANGED_ALERT_NO_REPEAT = PASS
FETCH_FAILURE_STALE_VIEW = PASS
REQUEST = DUNCAN_CONTROL_ROOM_QC
```

- [ ] **Step 2: DUNCAN independently verifies**

DUNCAN checks reuse-first requirement, no backend/database/framework, public-data boundary, alert behavior, stale behavior, exact HEAD, and deployed URL when available.

- [ ] **Step 3: DUNCAN posts verdict**

```text
DUNCAN_CONTROL_ROOM_QC_COMPLETE
QC = PASS | CHANGES_REQUIRED
EXACT_HEAD = <sha>
PAGES_URL = <url or pending owner action>
ISSUES = NONE | <exact issues>
NEXT = JINGO_ACCEPTANCE | LESTER_REPAIR | SPARX_ACTION_REQUIRED
```

- [ ] **Step 4: Stop at governance boundary**

No automatic OWNER LOCK and no unrelated runtime changes.
