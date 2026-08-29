// ==UserScript==
// @name         ZORR MODE Toolbar V1
// @namespace    https://github.com/Lester-Sparx/zorr-blatt-shared-hq
// @version      1.0.0
// @description  One-click ZORR BLATT owner controls inside ChatGPT.
// @match        https://chatgpt.com/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(() => {
  "use strict";

  const TOOLBAR_ID = "zorr-mode-toolbar-v1";
  const NOTICE_ID = "zorr-mode-toolbar-notice-v1";
  const GITHUB_ROOT = "https://github.com/Lester-Sparx/zorr-blatt-shared-hq";
  const CONSTITUTION_URL = `${GITHUB_ROOT}/blob/main/ZORR_EXECUTION_CONSTITUTION.md`;
  let hiddenUntilReload = false;

  const PRIMARY_ACTIONS = [
    { label: "ZORR MODE", kind: "prompt", prompt: "ZORR MODE", primary: true },
    { label: "Делай", kind: "prompt", prompt: "ZORR MODE\nДЕЛАЙ ДО PASS" },
    { label: "Продолжить", kind: "prompt", prompt: "ZORR MODE\nПРОДОЛЖАЙ ОТ СВЕЖЕГО DURABLE СОСТОЯНИЯ. НЕ НАЧИНАЙ ЗАНОВО. ДОВЕДИ ДО PASS ИЛИ ОДНОГО ТОЧНОГО BLOCKER." },
    { label: "Проверить", kind: "prompt", prompt: "ZORR MODE\nТОЛЬКО СВЕЖАЯ ПРОВЕРКА. НИЧЕГО НЕ МЕНЯЙ. ПРОВЕРЬ EXACT HEAD / TESTS / RUNTIME EVIDENCE И ВЕРНИ PASS, FAIL ИЛИ NOT PROVEN." },
    { label: "Стоп", kind: "stop" },
    { label: "⋯", kind: "menu" },
  ];

  const BRAINSTORM_PROMPT = "ZORR MODE\nБРЕЙНШТОРМ. НЕ РЕАЛИЗОВЫВАЙ. СНАЧАЛА ИЗУЧИ СУЩЕСТВУЮЩЕЕ, ГОТОВЫЕ/NATIVE/OSS РЕШЕНИЯ И ДАЙ САМЫЙ ПРОСТОЙ ВАРИАНТ.";

  function isVisible(element) {
    if (!(element instanceof HTMLElement)) return false;
    const style = window.getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
  }

  function findComposer() {
    const selectors = [
      "#prompt-textarea[contenteditable='true']",
      "div[contenteditable='true'][data-virtualkeyboard]",
      "textarea#prompt-textarea",
      "form textarea",
    ];
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element && isVisible(element)) return element;
    }
    return null;
  }

  function setComposerText(composer, text) {
    composer.focus();

    if (composer instanceof HTMLTextAreaElement || composer instanceof HTMLInputElement) {
      const prototype = composer instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(prototype, "value")?.set;
      if (setter) setter.call(composer, text);
      else composer.value = text;
      composer.dispatchEvent(new Event("input", { bubbles: true }));
      return true;
    }

    if (composer.isContentEditable) {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(composer);
      selection.removeAllRanges();
      selection.addRange(range);
      document.execCommand("insertText", false, text);
      if ((composer.innerText || composer.textContent || "").trim() !== text.trim()) {
        composer.textContent = text;
      }
      composer.dispatchEvent(new InputEvent("input", {
        bubbles: true,
        inputType: "insertText",
        data: text,
      }));
      selection.removeAllRanges();
      return true;
    }

    return false;
  }

  function findSendButton(composer) {
    const scope = composer.closest("form") || document;
    const selectors = [
      "button[data-testid='send-button']",
      "button[aria-label='Send prompt']",
      "button[aria-label='Send message']",
      "button[aria-label='Отправить сообщение']",
      "button[aria-label='Надіслати повідомлення']",
    ];
    for (const selector of selectors) {
      const button = scope.querySelector(selector) || document.querySelector(selector);
      if (button && !button.disabled && isVisible(button)) return button;
    }
    return null;
  }

  function setNotice(message) {
    const notice = document.getElementById(NOTICE_ID);
    if (!notice) return;
    notice.textContent = message;
    window.setTimeout(() => {
      if (notice.textContent === message) notice.textContent = "";
    }, 2400);
  }

  function sendPrompt(text) {
    const composer = findComposer();
    if (!composer) {
      setNotice("COMPOSER_NOT_FOUND");
      return;
    }
    if (!setComposerText(composer, text)) {
      setNotice("COMPOSER_WRITE_FAILED");
      return;
    }

    const startedAt = Date.now();
    const trySend = () => {
      const button = findSendButton(composer);
      if (button) {
        button.click();
        setNotice("SENT");
        return;
      }
      if (Date.now() - startedAt >= 1500) {
        setNotice("SEND_NOT_AVAILABLE");
        return;
      }
      window.setTimeout(trySend, 60);
    };
    trySend();
  }

  function stopGeneration() {
    const selectors = [
      "button[data-testid='stop-button']",
      "button[aria-label='Stop generating']",
      "button[aria-label='Stop streaming']",
      "button[aria-label='Остановить создание']",
      "button[aria-label='Остановить ответ']",
      "button[aria-label='Зупинити генерування']",
    ];
    for (const selector of selectors) {
      const button = document.querySelector(selector);
      if (button && !button.disabled && isVisible(button)) {
        button.click();
        setNotice("STOPPED");
        return;
      }
    }
    setNotice("STOP_NOT_AVAILABLE");
  }

  function buttonStyle(button, { primary = false, stop = false } = {}) {
    Object.assign(button.style, {
      appearance: "none",
      border: "1px solid color-mix(in srgb, currentColor 25%, transparent)",
      borderRadius: "9px",
      background: "transparent",
      color: "inherit",
      font: "inherit",
      fontSize: "12px",
      lineHeight: "1",
      padding: primary ? "8px 12px" : "8px 10px",
      cursor: "pointer",
      whiteSpace: "nowrap",
      opacity: stop ? "0.82" : "1",
      fontWeight: primary ? "700" : "550",
    });
    if (stop) button.style.marginLeft = "6px";
  }

  function createMenu(toolbar) {
    const menu = document.createElement("div");
    menu.dataset.zorrMenu = "true";
    Object.assign(menu.style, {
      display: "none",
      position: "absolute",
      right: "0",
      bottom: "calc(100% + 8px)",
      minWidth: "180px",
      padding: "6px",
      border: "1px solid color-mix(in srgb, currentColor 25%, transparent)",
      borderRadius: "10px",
      background: "Canvas",
      color: "CanvasText",
      boxShadow: "0 8px 24px rgba(0,0,0,.16)",
      zIndex: "2147483647",
    });

    const items = [
      ["Брейншторм", () => sendPrompt(BRAINSTORM_PROMPT)],
      ["Конституция", () => window.open(CONSTITUTION_URL, "_blank", "noopener,noreferrer")],
      ["Shared HQ", () => window.open(GITHUB_ROOT, "_blank", "noopener,noreferrer")],
      ["Скрыть панель", () => {
        hiddenUntilReload = true;
        toolbar.remove();
      }],
    ];

    for (const [text, action] of items) {
      const item = document.createElement("button");
      item.type = "button";
      item.textContent = text;
      Object.assign(item.style, {
        display: "block",
        width: "100%",
        border: "0",
        borderRadius: "7px",
        background: "transparent",
        color: "inherit",
        font: "inherit",
        fontSize: "12px",
        textAlign: "left",
        padding: "8px 9px",
        cursor: "pointer",
      });
      item.addEventListener("click", () => {
        menu.style.display = "none";
        action();
      });
      menu.appendChild(item);
    }

    return menu;
  }

  function createToolbar() {
    const toolbar = document.createElement("div");
    toolbar.id = TOOLBAR_ID;
    toolbar.setAttribute("role", "toolbar");
    toolbar.setAttribute("aria-label", "ZORR MODE owner controls");
    Object.assign(toolbar.style, {
      position: "relative",
      display: "flex",
      alignItems: "center",
      gap: "5px",
      width: "min(100%, 768px)",
      boxSizing: "border-box",
      margin: "0 auto 6px",
      padding: "0 8px",
      color: "inherit",
      fontFamily: "inherit",
      zIndex: "100",
    });

    const menu = createMenu(toolbar);

    for (const action of PRIMARY_ACTIONS) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = action.label;
      button.dataset.zorrAction = action.kind;
      buttonStyle(button, { primary: action.primary === true, stop: action.kind === "stop" });

      button.addEventListener("click", () => {
        if (action.kind === "prompt") sendPrompt(action.prompt);
        else if (action.kind === "stop") stopGeneration();
        else if (action.kind === "menu") menu.style.display = menu.style.display === "none" ? "block" : "none";
      });
      toolbar.appendChild(button);
    }

    const notice = document.createElement("span");
    notice.id = NOTICE_ID;
    notice.setAttribute("aria-live", "polite");
    Object.assign(notice.style, {
      marginLeft: "auto",
      maxWidth: "170px",
      overflow: "hidden",
      textOverflow: "ellipsis",
      whiteSpace: "nowrap",
      fontSize: "10px",
      opacity: "0.65",
    });
    toolbar.appendChild(notice);
    toolbar.appendChild(menu);
    return toolbar;
  }

  function mountToolbar() {
    if (hiddenUntilReload || document.getElementById(TOOLBAR_ID)) return;
    const composer = findComposer();
    if (!composer) return;
    const form = composer.closest("form");
    const anchor = form || composer.parentElement;
    if (!anchor || !anchor.parentElement) return;
    anchor.parentElement.insertBefore(createToolbar(), anchor);
  }

  let mountQueued = false;
  function queueMount() {
    if (mountQueued) return;
    mountQueued = true;
    window.requestAnimationFrame(() => {
      mountQueued = false;
      mountToolbar();
    });
  }

  const observer = new MutationObserver(queueMount);
  observer.observe(document.documentElement, { childList: true, subtree: true });
  queueMount();
})();
