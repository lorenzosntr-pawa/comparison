# Phase 32: Connection Loss Logging - Context

**Gathered:** 2026-01-27
**Status:** Ready for planning

<vision>
## How This Should Work

When an SSE connection drops during a scrape, the system should detect the loss and mark the run with a new `connection_failed` status instead of leaving it stuck as "running." The user sees clearly that the connection was lost — not a scrape error, a connection issue.

Once the connection is back, the scheduler should know to trigger a new scrape immediately rather than waiting for the next scheduled interval. The trigger mechanism (backend vs frontend driven) is open — figure out the best approach during planning.

</vision>

<essential>
## What Must Be Nailed

- **Failed status visibility** — The run must clearly show `connection_failed` as a distinct status, not stuck on "running" and not confused with regular "failed"
- **Proper logging** — Connection loss events are logged so there's a record of what happened
- **Auto-rescrape on recovery** — When connection comes back, a new scrape runs immediately without waiting for the next interval

</essential>

<boundaries>
## What's Out of Scope

- SSE reconnection logic — no auto-reconnect, just detect the loss and update status
- Retry counting / backoff — no tracking how many times connection was lost
- Detailed partial progress messages (e.g., "2/3 platforms scraped") — defer to Phases 33-35 which will overhaul progress and messaging
- Keep this phase focused on the new status and logging, not progress enrichment

</boundaries>

<specifics>
## Specific Ideas

- New `connection_failed` status distinct from regular `failed`
- History should show the status badge for connection_failed runs
- Detailed "what was completed before failure" display deferred to later phases (33-35)

</specifics>

<notes>
## Additional Context

User wants tight scope: show the new status clearly and log it properly. Progress detail and partial completion visibility belong in the later progress/messaging phases (33-35).

Timing for declaring connection failure (immediate vs grace period) is open — builder decides what makes sense.

</notes>

---

*Phase: 32-connection-loss-logging*
*Context gathered: 2026-01-27*
