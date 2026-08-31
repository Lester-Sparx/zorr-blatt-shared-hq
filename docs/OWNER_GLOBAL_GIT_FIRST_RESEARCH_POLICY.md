# OWNER GLOBAL GIT-FIRST RESEARCH / NO FILE DELIVERY POLICY

STATUS = OWNER-DIRECTED DURABLE POLICY CANDIDATE
DATE = 2026-08-31
SCOPE = ALL ZORR CHATS / AGENTS / RESEARCH / PRODUCTION SUPPORT

## Rule

GitHub is the cross-chat durable record for ZORR research.

Unless OWNER explicitly asks for a file in a specific task:

1. Do not send SPARX generated research files, downloadable attachments, handoff files, manifests, proof bundles, calculation files, or code/test artifacts in chat.
2. Persist all substantive research information, calculations, formulas, measurements, exact upstream refs/versions/licenses/tests, code, tests, proof, manifests, handoffs, PASS/FAIL/BLOCKED boundaries, and next-gate state to GitHub.
3. Chat output should normally contain only a concise status/result and the Git commit/PR/path/reference needed to recover the durable evidence.
4. Container files, ChatGPT Library files, local scratch files, and chat attachments are temporary working media only and must not be the sole durable authority for a substantive ZORR result.
5. Every new chat/session must restore prior ZORR research from current GitHub state instead of depending on old chat attachments or asking OWNER to resend them.
6. Calculations that affect production decisions must be reproducible from committed formulas/code/data or from committed exact inputs and derivation steps.
7. Preserve evidence classes explicitly in Git: `SOURCE-DERIVED`, `MEASURED`, `DERIVED`, `UNKNOWN`, `NOT PROVEN`.
8. If a necessary binary or oversized artifact cannot reasonably live in Git, commit its exact hash/identity, authoritative location, provenance, and relationship to the result so Git remains sufficient to recover and verify state. This exception does not permit research text, calculations, or proof logic to remain chat-only.
9. No substantive terminal result may exist only in ChatGPT Library. Library may remain a temporary cache during migration, but Git is the durable authority.

Required pattern:

`RESEARCH / CALCULATION -> TEST / EVIDENCE -> GIT DURABLE RECORD -> CHAT STATUS ONLY`

`CHAT ATTACHMENT != DURABLE ZORR MEMORY`

## Relationship to existing law

This policy strengthens the existing `GITHUB MEMORY LAW`, `DURABLE TERMINAL-STATE LAW`, `OWNER-IS-NOT-A-COURIER LAW`, and the `AGENTS.md` rule that GitHub is the durable system of record.

It does not weaken repository protection, required review/status checks, OWNER gates, evidence requirements, or fail-closed behavior.
