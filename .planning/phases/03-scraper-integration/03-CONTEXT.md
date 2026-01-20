# Phase 3: Scraper Integration - Context

**Gathered:** 2026-01-20
**Status:** Ready for research

<vision>
## How This Should Work

A central FastAPI orchestrator that triggers the existing SportyBet, BetPawa, and Bet9ja scrapers on demand via API endpoints. When you hit the scrape endpoint, it runs the scrapers, transforms the data to a unified format, stores it in the database, and returns the results.

The response should be configurable — sometimes you want just a summary ("150 events from SportyBet, 2 errors"), sometimes you want the full data. There should be filtering options too: choose which platforms to scrape, and optionally filter by sport or league.

Scrapers should run independently — if SportyBet fails, BetPawa and Bet9ja should still complete. Partial success is fine; report what worked and what didn't.

Data goes through the market mapping from Phase 1. Store both the raw platform-specific data AND the mapped unified format — preserves original data while having the unified format ready for comparison.

</vision>

<essential>
## What Must Be Nailed

- **Unified data format** — All three scrapers output data in the same structure, ready for storage and comparison
- **Reliable execution** — Scrapers run without crashing, errors are captured and logged properly, partial failures don't kill the whole operation
- **Configurable timeouts** — Allow timeout to be set per request for flexibility

</essential>

<boundaries>
## What's Out of Scope

- **Scheduling/automation** — No background jobs or cron-like scheduling (that's Phase 5)
- **Event matching** — Just store raw scraped data; cross-platform matching is Phase 4
- **Authentication** — Skip auth for now, add it in a future phase if needed
- **Live/in-play events** — Pre-match/upcoming events only for this phase

</boundaries>

<specifics>
## Specific Ideas

- Health endpoint to verify scraper connectivity before running
- Filter by platform (e.g., just SportyBet) and/or by sport/league
- Configurable response detail: summary counts vs full data via query param
- Football-focused but architected to support other sports later (don't hardcode)
- Store both raw data AND market-mapped data for flexibility

</specifics>

<notes>
## Additional Context

The existing scrapers' output format is unknown — will need to examine the code during research to understand their current structure.

Concurrency (parallel vs sequential scraping) and API router organization are flexible — defer to whatever makes technical sense.

</notes>

---

*Phase: 03-scraper-integration*
*Context gathered: 2026-01-20*
