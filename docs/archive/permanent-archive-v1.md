# ZB Permanent Archive V1

## Goal

Preserve GitHub-side ZORR BLATT operational history without depending on chat memory or an always-on private server.

## Source of truth

The raw GitHub event payload is authoritative. Archive V1 stores the exact bytes from `GITHUB_EVENT_PATH` under a SHA-256 content address on the dedicated `zb-archive-v1` branch.

Derived envelopes are only pointers and provenance metadata. They never replace the raw payload.

## Flow

`GitHub event -> GitHub Actions -> exact raw payload -> SHA-256 object -> append-only Git commit -> integrity verification`

The workflow is event-driven. It does not poll and does not use a schedule.

## Captured events

Archive V1 captures repository events used by the current HQ workflow: issues, issue comments, pull-request lifecycle events, PR reviews, PR review comments, and pushes. Writes made by the archive itself to `zb-archive-v1` are excluded to prevent recursion.

## No-loss rules

1. Existing raw objects are never overwritten.
2. Existing event identities are never rewritten to different content.
3. Every event envelope points to a content-addressed raw object.
4. Verification fails closed if a raw object is missing, renamed, or its bytes no longer match its SHA-256.
5. Archive commits are appended to `zb-archive-v1`; the normal `main` branch remains the code/canonical-state branch.

## Agent continuity

LESTER and DUNCAN should use normal HQ state/tracker records for the current operational snapshot and use `zb-archive-v1` when they need original evidence or historical reconstruction. Chat memory is not authoritative.

## Explicit boundary

Archive V1 preserves events that actually reach GitHub. It cannot directly intercept a message that exists only inside the ChatGPT UI and was never emitted to GitHub or another connected event source. Such messages must first enter the HQ/GitHub communication path to become durably archived.

## External backup

This version intentionally uses existing Git/GitHub durability and does not add a second storage service. A second independent restic-backed copy can be added later when an external filesystem/S3/B2 target and its credentials are available. That is redundancy, not a prerequisite for the GitHub archive itself.
