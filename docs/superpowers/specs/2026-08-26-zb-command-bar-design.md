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

The bar appears at the bottom of ChatGPT web conversations and provides these always-visible core buttons:

- `ПРОСЫПАЙСЯ`
- `ПРОДОЛЖАЙ`
- `ПРИНЯТО`
- `ПРОВЕРЬ`
- `СТОП`
- `ДА`
- `НЕТ`

A compact secondary menu provides:

- `БЕРИ ЗАДАНИЕ`
- `СТАТУС`
- `REPAIR`
- `PASS`
- `HOLD`
- `ГЕНЕРИРУЙ`

R01 does not dynamically replace the core button set. Context is used only to form agent-aware command text and to preselect the most relevant secondary menu section.

## 4. AGENT CONTEXT

The extension attempts lightweight agent detection from visible current-page information such as conversation title and recent visible conversation text.

Known logical names:

- JINGO
- LESTER / ЛЕСТЕР
- DUNCAN / ДУНКАН
- SALVADOR / САЛЬВАДОР
- LYNCH / ЛИНЧ

If exactly one agent is detected confidently, pressing `ПРОСЫПАЙСЯ` sends `<agent>, просыпайся.`

If no agent or multiple agents are detected, `ПРОСЫПАЙСЯ` does not send anything immediately. It opens a compact picker containing the five known agents. Selecting one sends that exact agent wake command. R01 never guesses an ambiguous agent and never sends a generic wake command.

Agent detection is convenience metadata only and never changes durable ZB agent identity.

## 5. ONE-CLICK SEND FLOW

Normal R01 flow:

`BUTTON CLICK -> COMMAND TEXT -> CHATGPT COMPOSER -> SEND`

The extension uses the visible ChatGPT composer and its normal send interaction. It must not use private OpenAI APIs, read authentication cookies/tokens, or bypass normal ChatGPT account behavior.

If the composer/send control cannot be found, the extension fails visibly instead of silently doing nothing.

Commands are never automatically retried after an uncertain send result.

## 6. COMMAND TEXT R01

The exact default texts are:

- `ПРОДОЛЖАЙ` -> `Продолжай.`
- `ПРИНЯТО` -> `Принято.`
- `ПРОВЕРЬ` -> `Проверь текущий результат.`
- `СТОП` -> `Стоп.`
- `ДА` -> `Да.`
- `НЕТ` -> `Нет.`
- `СТАТУС` -> `Дай текущий статус по фактическому результату.`
- `БЕРИ ЗАДАНИЕ` -> `Бери текущее назначенное задание и начинай.`
- `REPAIR` -> `Исправляй по текущему точному замечанию. Не расширяй scope.`
- `PASS` -> `PASS.`
- `HOLD` -> `HOLD.`
- `ГЕНЕРИРУЙ` -> `ГЕНЕРИРУЙ`

Wake text is `<detected-or-selected-agent>, просыпайся.`

Custom user-defined command text is out of scope for R01.

## 7. SAFETY / ACCIDENTAL ACTIONS

Most commands are true one-click actions.

`ГЕНЕРИРУЙ` is special because ZB art governance uses it as a live execution token. To prevent accidental image execution, the first click only arms the button for 3 seconds; a second click inside that window sends `ГЕНЕРИРУЙ`. If the second click does not happen, the button automatically returns to safe state.

The extension does not create durable generation authorization. It only sends the live token when SPARX deliberately confirms it.

No button may merge PRs, activate runtime, issue OWNER LOCK, or directly mutate GitHub/project authority.

## 8. UI

Keep the bar visually minimal and fast:

- compact fixed bottom strip;
- dark/black base compatible with the ZB control-room visual language;
- high-contrast labels;
- no animation except short feedback for success/error/armed state;
- collapsible to one small `ZB` button;
- no external UI framework.

The bar must not cover the ChatGPT composer or primary navigation.

## 9. STORAGE

Local browser storage only.

R01 stores only:

- bar collapsed/expanded state;
- last selected secondary menu section.

R01 does not store conversation contents, authentication data, GitHub credentials, OpenAI tokens, or custom command text.

## 10. FILE STRUCTURE

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

## 11. ERROR HANDLING

Visible compact error states are required for:

- composer not found;
- send control not found;
- DOM changed / injection failed;
- ambiguous agent detection (opens picker instead of erroring).

The extension must not retry-send a command automatically after an uncertain failure because duplicate commands can cause duplicate agent actions.

## 12. TESTING / ACCEPTANCE

R01 acceptance requires:

1. Extension loads unpacked in Chrome or Edge.
2. Command bar appears on a normal ChatGPT conversation page.
3. Bar does not block normal ChatGPT controls.
4. `ПРОДОЛЖАЙ`, `ПРИНЯТО`, `ПРОВЕРЬ`, `СТОП`, `ДА`, `НЕТ` send their exact default text exactly once.
5. Agent-specific `ПРОСЫПАЙСЯ` sends the detected agent name when exactly one agent is confidently detected.
6. Ambiguous agent state opens the five-agent picker and sends nothing until SPARX selects an agent.
7. `ГЕНЕРИРУЙ` cannot be sent by a single click and requires the defined two-click 3-second arm flow.
8. No private API/token/cookie access is used.
9. DOM integration failure is visibly reported.
10. Reloading/new chats retains collapsed state and secondary menu preference.
11. Commands are never auto-retried after uncertain send results.

## 13. NON-GOALS R01

Not included:

- mobile ChatGPT support;
- direct GitHub writes;
- direct agent spawning;
- background autonomous execution;
- ChatGPT API usage;
- cloud sync;
- backend/database;
- custom command editor;
- automatic approval/merge/OWNER LOCK;
- replacing Control Room.

## 14. CORE LAW

`SPARX PRESSES INTENT. THE BAR SENDS THE ROUTINE MESSAGE.`

`THE BAR IS INPUT AUTOMATION — NOT AUTHORITY.`

`NO SERVER. NO PRIVATE API. NO OWNER-AS-SECRETARY.`
