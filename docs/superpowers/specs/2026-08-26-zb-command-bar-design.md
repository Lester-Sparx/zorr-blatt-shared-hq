# ZB COMMAND BAR R01 — DESIGN

STATUS: DESIGN READY / IMPLEMENTATION NOT STARTED
OWNER: SPARX
COORDINATION: JINGO

## 1. PURPOSE

SPARX should not have to repeatedly type routine control messages such as `ПРОСЫПАЙСЯ`, `ПРОДОЛЖАЙ`, `ПРИНЯТО`, `СТОП`, `ПРОВЕРЬ`, or agent-specific wake commands.

ZB COMMAND BAR R01 is a tiny local browser extension for Chrome/Edge that overlays a compact command strip on ChatGPT pages and sends approved command text into the current conversation with one click.

It is a convenience/control layer only. It does not become project memory, agent authority, or a replacement for Shared HQ.

## 2. APPROACHES CONSIDERED

### A. Browser extension — SELECTED

Manifest V3 extension, local-only, injected into ChatGPT pages.

Pros:
- persistent across chats;
- one-click commands;
- can react to page/chat context;
- no server or API required;
- easy to install as an unpacked extension in Chrome/Edge;
- can later grow a small settings panel without changing ChatGPT itself.

Cons:
- depends on ChatGPT DOM and may need maintenance if the web UI changes.

### B. Userscript

Tampermonkey/Violentmonkey script.

Rejected for R01 because it adds another third-party runtime/installation dependency and makes the owner setup less self-contained.

### C. Bookmarklet / manual snippets

Rejected because it is not persistent enough, has weak contextual behavior, and would still make SPARX perform unnecessary repeated steps.

## 3. R01 SCOPE

Build one local extension named `ZB COMMAND BAR`.

The bar appears at the bottom of ChatGPT web conversations and provides compact buttons.

Core buttons:

- `ПРОСЫПАЙСЯ`
- `ПРОДОЛЖАЙ`
- `ПРИНЯТО`
- `ПРОВЕРЬ`
- `СТОП`
- `ДА`
- `НЕТ`

Contextual buttons when useful:

- `БЕРИ ЗАДАНИЕ`
- `СТАТУС`
- `REPAIR`
- `PASS`
- `HOLD`
- `ГЕНЕРИРУЙ`

R01 may show different button groups for normal, technical/QC, art, and agent-wake contexts.

## 4. AGENT CONTEXT

The extension should attempt lightweight agent detection from visible current-page information such as conversation title and recent visible conversation text.

Known logical names:

- JINGO
- LESTER / ЛЕСТЕР
- DUNCAN / ДУНКАН
- SALVADOR / САЛЬВАДОР
- LYNCH / ЛИНЧ

If the active agent can be determined confidently, pressing `ПРОСЫПАЙСЯ` sends `<agent>, просыпайся.`

If no agent is confidently detected, the generic wake command must not guess an identity. R01 should either send `Просыпайся.` or present the user with compact agent choices.

Agent detection is convenience metadata only and never changes durable ZB agent identity.

## 5. ONE-CLICK SEND FLOW

Normal R01 flow:

`BUTTON CLICK -> COMMAND TEXT -> CHATGPT COMPOSER -> SEND`

The extension should use the visible ChatGPT composer and its normal send interaction. It must not use private OpenAI APIs, steal tokens, read cookies, or bypass normal ChatGPT account behavior.

If the composer/send control cannot be found, the extension must fail visibly instead of silently doing nothing.

## 6. SAFETY / ACCIDENTAL ACTIONS

Most commands are true one-click actions.

`ГЕНЕРИРУЙ` is special because ZB art governance uses it as a live execution token. To prevent accidental image execution, R01 must require a deliberate confirmation gesture before sending it — either a second click within a short armed window or a hold action.

The extension does not create durable generation authorization. It only sends the live token when SPARX deliberately presses the control.

No button may merge PRs, activate runtime, issue OWNER LOCK, or directly mutate GitHub/project authority.

## 7. UI

Keep the bar visually minimal and fast:

- compact fixed bottom strip;
- dark/black base compatible with the ZB control-room visual language;
- high-contrast labels;
- no animation except short feedback for success/error/armed state;
- collapsible to one small `ZB` button;
- no external UI framework.

The bar must not cover the ChatGPT composer or primary navigation.

## 8. STORAGE

Local browser storage only.

Allowed local preferences:

- bar collapsed/expanded state;
- button-group preference;
- optional custom command text in future revisions.

R01 does not store conversation contents, authentication data, GitHub credentials, or OpenAI tokens.

## 9. FILE STRUCTURE

Planned implementation area:

`tools/zb-command-bar/`

Expected minimal files:

- `manifest.json`
- `content.js`
- `command-bar.js`
- `command-bar.css`
- `README.md`
- tests for pure command/context logic where practical

Keep DOM integration separated from command-definition/context logic so ChatGPT UI selector changes can be repaired without rewriting command behavior.

## 10. ERROR HANDLING

Visible compact error states are required for:

- composer not found;
- send control not found;
- DOM changed / injection failed;
- ambiguous agent detection.

The extension must not retry-send a command automatically after an uncertain failure because duplicate commands can cause duplicate agent actions.

## 11. TESTING / ACCEPTANCE

R01 acceptance requires:

1. Extension loads unpacked in Chrome or Edge.
2. Command bar appears on a normal ChatGPT conversation page.
3. Bar does not block normal ChatGPT controls.
4. `ПРОДОЛЖАЙ`, `ПРИНЯТО`, `СТОП`, `ДА`, `НЕТ` send exactly once.
5. Agent-specific `ПРОСЫПАЙСЯ` sends the detected agent name when detection is confident.
6. Ambiguous agent state never invents a role.
7. `ГЕНЕРИРУЙ` cannot be sent by a single accidental click.
8. No private API/token/cookie access is used.
9. DOM integration failure is visibly reported.
10. Reloading/new chats retains the local bar preference.

## 12. NON-GOALS R01

Not included:

- mobile ChatGPT support;
- direct GitHub writes;
- direct agent spawning;
- background autonomous execution;
- ChatGPT API usage;
- cloud sync;
- backend/database;
- automatic approval/merge/OWNER LOCK;
- replacing Control Room.

## 13. CORE LAW

`SPARX PRESSES INTENT. THE BAR SENDS THE ROUTINE MESSAGE.`

`THE BAR IS INPUT AUTOMATION — NOT AUTHORITY.`

`NO SERVER. NO PRIVATE API. NO OWNER-AS-SECRETARY.`
