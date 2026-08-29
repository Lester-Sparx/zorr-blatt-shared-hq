# ZORR MODE Toolbar V1

A tiny OWNER-side userscript that adds these controls directly above the ChatGPT composer:

`ZORR MODE | Делай | Продолжить | Проверить | Стоп | ⋯`

It does not use an API key, server, daemon, telemetry, or GitHub write access. Each action requires an explicit OWNER click.

## Why Violentmonkey

Violentmonkey is an MIT-licensed open-source userscript manager for Chromium/Firefox browsers. This avoids building a custom browser extension or paid OpenAI API client.

## One-time OWNER-PC activation

Browser extension installation is a browser security approval and cannot be completed remotely by a ChatGPT/GitHub connector.

1. Install **Violentmonkey** from the extension source/store appropriate for the browser.
2. Open the raw userscript URL:

   `https://raw.githubusercontent.com/Lester-Sparx/zorr-blatt-shared-hq/main/tools/browser/zorr-mode-toolbar.user.js`

3. Violentmonkey should offer to install the script. Review that it matches only `https://chatgpt.com/*`, then approve installation.
4. Reload `https://chatgpt.com/`.

After the script is merged to `main`, reopening the same raw URL installs/updates the current canonical version.

## Button meanings

- **ZORR MODE** — sends `ZORR MODE`.
- **Делай** — reload laws/context and continue work to PASS or an exact blocker.
- **Продолжить** — continue from fresh durable state instead of reinvestigating from zero.
- **Проверить** — fresh read-only verification; no changes.
- **Стоп** — presses ChatGPT's visible stop-generation button if one exists; otherwise it performs no mutation.
- **⋯** — Brainstorm prompt, Constitution link, Shared HQ link, hide toolbar until reload.

## Important

The toolbar is only a shortcut surface. `ZORR_EXECUTION_CONSTITUTION.md` and `AGENTS.md` remain authoritative and apply even when the toolbar is not installed or a command is typed manually.

The userscript must never display a fake `MAIN`, `PASS`, `CI`, or archive status because it has no GitHub authority. Project state must come from ChatGPT/connected GitHub evidence under ZORR MODE.

## Disable/remove

Disable or delete `ZORR MODE Toolbar V1` in Violentmonkey, then reload ChatGPT. No project or GitHub state is changed by disabling the userscript.
