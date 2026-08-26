# ZB Control Room R01 — Design

## Goal

Give SPARX one ordinary browser link that shows the current operational state of the ZORR BLATT agent team and produces an audible alert when SPARX action is required or a blocker occurs.

## Product Rule

Keep this deliberately tiny.

- Static site only.
- No backend.
- No database.
- No React/Vue/Svelte.
- No custom design system.
- No custom audio engine.
- Reuse mature free/open-source pieces first.

## Stack

- GitHub Pages for hosting.
- NES.css v2.3.0 for the 8-bit UI shell.
- Beep.js (MIT) for browser-generated alert tones.
- Vanilla HTML/CSS/JavaScript only for glue.
- Shared HQ `CURRENT` JSON as data source.

NES.css latest published release currently verified as v2.3.0. Beep.js is MIT and wraps Web Audio.

## Visual Direction

Black and white only.

The page contains:

1. `ZORR BLATT CONTROL ROOM` header.
2. Agent rows for SPARX, JINGO, LESTER, DUNCAN, SALVADOR, LYNCH.
3. Columns: `AGENT`, `STATUS`, `CURRENT WORK`, `NEXT TRIGGER`.
4. `CURRENT GATE` section.
5. `LAST UPDATE` timestamp.
6. Large alert panel.
7. One `ARM ALARMS` button required because browsers may block sound until user interaction.

No animation except a simple high-contrast blink/pulse on an active alert.

## Data Model

The page reads one presentation-only file:

`hq/state/CONTROL_ROOM.json`

This file is not project authority. It is a dashboard view generated/maintained from durable project evidence.

Minimal schema:

```json
{
  "schemaVersion": 1,
  "updatedAt": "2026-08-26T12:00:00Z",
  "currentGate": "DUNCAN RE-QC",
  "alert": {
    "level": "NONE",
    "title": "",
    "message": "",
    "action": ""
  },
  "agents": [
    {
      "id": "LESTER",
      "status": "HOLD",
      "currentWork": "P1 repair complete",
      "nextTrigger": "DUNCAN CHANGES_REQUIRED"
    }
  ]
}
```

Allowed alert levels:

- `NONE`
- `BLOCKER`
- `ACTION_REQUIRED`

Allowed status vocabulary for R01:

- `ACTIVE`
- `WAITING`
- `HOLD`
- `DONE`
- `BLOCKED`
- `OFFLINE`
- `PROPOSED`

## Refresh Behavior

- Poll `CONTROL_ROOM.json` every 15 seconds.
- Add cache-busting query parameter using current timestamp.
- If fetch fails, keep the last good state visible and show a local `DATA STALE / FETCH FAILED` warning.
- Do not overwrite durable project state from the browser.

## Alert Behavior

When alert changes from `NONE` to `BLOCKER` or `ACTION_REQUIRED`:

- show the large alert panel immediately;
- play a short 8-bit beep sequence if alarms have been armed;
- do not repeat the sound continuously for the same alert payload;
- play again only when the alert identity/content materially changes.

The first page visit requires one click on `ARM ALARMS` to satisfy browser audio restrictions.

## Deployment

- Site source lives under `control-room/` in Shared HQ.
- Deployment uses GitHub Pages with official GitHub Pages Actions or a Pages branch, whichever is simpler under current repository settings.
- If repository settings require one manual OWNER action to enable Pages, implementation must STOP and raise `SPARX ACTION REQUIRED` with the exact single click path.

## Security / Privacy

Because Shared HQ is public, `CONTROL_ROOM.json` must contain only safe operational metadata.

Do not expose:

- secrets;
- tokens;
- private runtime source;
- sensitive attachments;
- private conversation content.

Exact commit SHA / PR number / workflow run IDs are allowed only when already intended as public project metadata.

## Acceptance Criteria

R01 is accepted when:

1. SPARX can open one ordinary browser URL.
2. The page renders all six roles in monochrome 8-bit style.
3. Status updates appear without manual refresh within 30 seconds.
4. `ACTION_REQUIRED` produces a large visible banner.
5. After `ARM ALARMS`, a new alert produces an audible beep.
6. A repeated unchanged alert does not beep forever.
7. A failed data fetch is visibly reported while last good state remains on screen.
8. No backend or database exists.
9. Implementation reuses NES.css and Beep.js rather than inventing equivalents.
10. DUNCAN independently verifies the result before JINGO marks the dashboard accepted.
