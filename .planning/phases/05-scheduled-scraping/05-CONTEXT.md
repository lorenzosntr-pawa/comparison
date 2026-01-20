# Phase 5: Scheduled Scraping - Context

**Gathered:** 2026-01-20
**Status:** Ready for research

<vision>
## How This Should Work

Background scheduler runs automatically, scraping all three platforms at regular intervals. But this isn't a black box — there's active monitoring so you can see what's happening at any time.

The monitoring view shows two things: platform health status (is Betpawa up? SportyBet? Bet9ja? When did each last succeed?) and run history (recent scrape runs with timestamps, durations, success/failure). You glance at it and immediately know the system's state.

When platforms flake out, the scheduler handles it gracefully — retries, recovers, keeps going. Data stays fresh because scraping happens frequently enough to catch odds changes.

</vision>

<essential>
## What Must Be Nailed

- **Reliability** — Keeps running even when platforms flake out. Retries, recovers, doesn't die.
- **Fresh data** — Odds are never stale. Scraping happens frequently enough to catch changes.
- **Visibility** — Always know what's going on. Platform health and run history visible at a glance.

</essential>

<boundaries>
## What's Out of Scope

- External alerting/notifications (no Slack, email, etc.) — failures show in monitoring view only
- Fancy scheduling logic — simple "every X minutes" intervals, not cron expressions or complex triggers

</boundaries>

<specifics>
## Specific Ideas

- Simple intervals: one global "scrape every X minutes" setting, not per-platform configuration
- Monitoring shows both current platform health AND historical run data
- No external dependencies for alerting — keep it self-contained

</specifics>

<notes>
## Additional Context

User wants active monitoring rather than set-and-forget. They want to see the system working, not just trust it. All three aspects (reliability, freshness, visibility) are equally important — can't trade one off for another.

</notes>

---

*Phase: 05-scheduled-scraping*
*Context gathered: 2026-01-20*
