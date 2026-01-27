# Phase 31: Backend Heartbeat & Stale Run Detection - Context

**Gathered:** 2026-01-27
**Status:** Ready for planning

<vision>
## How This Should Work

A silent background watchdog runs periodically (every few minutes), checking for scrape runs stuck in RUNNING status with no progress updates. If a run has gone stale — no heartbeat or progress event for a configurable timeout — the watchdog auto-marks it as FAILED with a clear reason.

This is purely reliability infrastructure. No UI changes, no user-facing indicators. Just a backend safety net that ensures no scrape run ever stays in RUNNING status forever.

</vision>

<essential>
## What Must Be Nailed

- **No more stuck runs** — If a scrape is dead, it gets marked dead. No run ever stays RUNNING forever.
- **Clear failure reasons** — When a run is auto-failed, the reason is obvious and specific: "stale: no progress for N minutes" with context about what the last known state was.

</essential>

<boundaries>
## What's Out of Scope

- No frontend changes — UI for showing errors/status comes in later phases (34, 35)
- No auto-retry logic — just detect and mark failed, don't restart
- No changes to the existing scraping flow — this is an independent monitor

</boundaries>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. User is open to recommendations on implementation details (timeout thresholds, check intervals, etc.).

</specifics>

<notes>
## Additional Context

Current pain point: scrapes stay in RUNNING status forever after disconnects or crashes. This is the foundational reliability layer that phases 32-35 build upon.

</notes>

---

*Phase: 31-backend-heartbeat*
*Context gathered: 2026-01-27*
