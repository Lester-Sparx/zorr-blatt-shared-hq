# ZORR MODE Toolbar V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use TDD and verification-before-completion. This plan is intentionally one small implementation slice.

**Goal:** Add one installable userscript that places the approved ZORR owner controls directly above the ChatGPT composer.

**Architecture:** A dependency-free userscript observes ChatGPT SPA DOM mounts, injects one toolbar, writes approved prompts into the current composer, and clicks the enabled send control. It performs no network calls and owns no project state.

**Tech Stack:** vanilla browser JavaScript; Violentmonkey userscript metadata; Python unittest static contract; existing `hq-validate`.

**Spec:** `docs/superpowers/specs/2026-08-29-zorr-mode-toolbar-v1-design.md`

## Global Constraints

- one script only for runtime behavior;
- no OpenAI API key or paid API;
- no server/daemon/database;
- no GitHub writes;
- explicit click required for every command;
- no internal-agent primary buttons;
- no project-state claims from browser DOM.

---

### Task 1: Contract test

**Files:**
- Create: `tests/test_zorr_mode_toolbar.py`

**Produces:** static enforcement of metadata scope, exact labels/order, exact prompts, no external networking/dependencies, and install-doc contract.

- [ ] Write the test first.
- [ ] Confirm it would fail while the userscript/doc files do not exist.
- [ ] Commit the RED contract.

### Task 2: Userscript

**Files:**
- Create: `tools/browser/zorr-mode-toolbar.user.js`

**Produces:** one injected toolbar with primary buttons and overflow menu.

- [ ] Add userscript metadata with only `https://chatgpt.com/*` match and no remote requirements.
- [ ] Implement composer discovery for `#prompt-textarea`/contenteditable and textarea fallback.
- [ ] Implement input-event-compatible text insertion.
- [ ] Implement bounded send-button wait and safe click.
- [ ] Implement stop-button discovery with no fallback mutation.
- [ ] Implement primary toolbar in exact approved order.
- [ ] Implement overflow menu and GitHub links.
- [ ] Add MutationObserver reattachment for SPA remounts.
- [ ] Keep styles neutral and compact.

### Task 3: Installation note

**Files:**
- Create: `docs/ZORR_MODE_TOOLBAR_V1.md`

**Produces:** exact one-time OWNER-PC activation instructions using the raw userscript URL and Violentmonkey.

- [ ] State that installation is a browser security approval and cannot be performed remotely.
- [ ] Give the minimal install/update/disable path.
- [ ] State exact button meanings and that Constitution still applies even without toolbar use.

### Task 4: Fresh verification

- [ ] Run/observe `hq-validate` on exact PR HEAD.
- [ ] Verify changed-file scope is only spec, plan, test, userscript, install doc.
- [ ] Re-read exact PR HEAD and status.
- [ ] Merge only when CI is green and PR is mergeable.
- [ ] Re-read `main` after merge.
- [ ] Record `CI PASS / PHYSICAL BROWSER ACTIVATION REQUIRED` unless a real owner-browser smoke is also obtained.