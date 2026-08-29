# ZORR MODE Toolbar V1 Design

**Status:** OWNER-approved direction / implementation authority
**Base:** `333550e4a9d4754471c49d3573a370e559212451`

## Goal

Give OWNER a small persistent toolbar directly in `chatgpt.com` so recurring ZORR control prompts can be sent with one click instead of retyping them.

## Why this path

Personal Plus cannot create a new Custom GPT or custom Apps SDK UI. Do not build a new local web service or paid OpenAI API client. Reuse a mature browser userscript manager instead. Target manager: Violentmonkey (MIT, WebExtensions).

## Visible toolbar

Exact primary order:

`ZORR MODE | Делай | Продолжить | Проверить | Стоп | ⋯`

Rules:
- keep only these five primary actions plus overflow;
- do not expose internal agent names (LESTER/DUNCAN/JINGO/SHERIFF/Copilot) as primary controls;
- place the toolbar immediately above the ChatGPT composer when possible;
- reattach after ChatGPT SPA navigation/remounts;
- do not cover the composer or message content.

## Command contract

Clicking a command inserts and sends exactly one prompt:

- `ZORR MODE` → `ZORR MODE`
- `Делай` → `ZORR MODE\nДЕЛАЙ ДО PASS`
- `Продолжить` → `ZORR MODE\nПРОДОЛЖАЙ ОТ СВЕЖЕГО DURABLE СОСТОЯНИЯ. НЕ НАЧИНАЙ ЗАНОВО. ДОВЕДИ ДО PASS ИЛИ ОДНОГО ТОЧНОГО BLOCKER.`
- `Проверить` → `ZORR MODE\nТОЛЬКО СВЕЖАЯ ПРОВЕРКА. НИЧЕГО НЕ МЕНЯЙ. ПРОВЕРЬ EXACT HEAD / TESTS / RUNTIME EVIDENCE И ВЕРНИ PASS, FAIL ИЛИ NOT PROVEN.`

`Стоп` is not a prompt command. It first tries to press ChatGPT's visible stop-generation control. If no stop control exists, it must do nothing destructive and show a local toolbar notice.

## Overflow

Overflow contains only:
- `Брейншторм` → send `ZORR MODE\nБРЕЙНШТОРМ. НЕ РЕАЛИЗОВЫВАЙ. СНАЧАЛА ИЗУЧИ СУЩЕСТВУЮЩЕЕ, ГОТОВЫЕ/NATIVE/OSS РЕШЕНИЯ И ДАЙ САМЫЙ ПРОСТОЙ ВАРИАНТ.`
- `Конституция` → open the current `main/ZORR_EXECUTION_CONSTITUTION.md` GitHub page in a new tab;
- `Shared HQ` → open repository root in a new tab;
- `Скрыть панель` → hide toolbar until page reload.

## Composer behavior

- support current ChatGPT contenteditable composer first;
- allow textarea fallback;
- dispatch normal input events so React sees the value;
- wait briefly for send button enablement;
- click only a visible enabled send button;
- if composer/send cannot be found, do not synthesize keyboard shortcuts or click unrelated elements; show a local notice.

## Safety

- `@match` only `https://chatgpt.com/*`;
- no external `fetch`, XHR, websocket, storage sync, telemetry, remote code, `@require`, or API key;
- no GitHub writes;
- no automatic execution without an explicit OWNER click;
- no mutation of messages already sent;
- do not claim project state from the userscript; it has no GitHub authority.

## Styling

Use a compact neutral toolbar. `ZORR MODE` is visually primary, `Стоп` visually separated, overflow minimal. Do not hardcode theme-specific foreground/background colors; inherit ChatGPT colors where practical and use borders/opacity for separation.

## Acceptance

CI PASS requires:
1. userscript has exactly the approved primary labels and order;
2. exact prompt strings are present;
3. script matches only `chatgpt.com`;
4. no network/API/remote dependency primitives are present;
5. no internal-agent primary buttons are present;
6. stop behavior is non-destructive;
7. install documentation names Violentmonkey and the raw GitHub userscript path;
8. repository `hq-validate` stays green.

Physical browser activation remains a separate OWNER-PC gate because browser-extension installation requires local user approval.