# Phase 2: Database Schema - Context

**Gathered:** 2026-01-20
**Status:** Ready for planning

<vision>
## How This Should Work

The database is both event-centric AND snapshot-based. Everything organizes around matched events, but each event has a history of odds snapshots that can be queried over time.

Analysts should be able to:
- Track margin trends over days/weeks for a tournament or league
- See how odds moved in the hours/days before kickoff for specific events
- Find moments when one bookmaker had significantly different odds than others

The data structure follows a hierarchy: Sport → Tournament/League → Event. This allows grouping by tournament for aggregate analysis (e.g., "How do Betpawa's margins on Premier League compare to Sportybet's?").

Internal use only — the React UI consumes it, and analysts run direct SQL queries for deeper analysis.

</vision>

<essential>
## What Must Be Nailed

- **Query performance** - Fast queries even with lots of historical snapshots
- **Data integrity** - Never lose odds data, solid cross-platform matching
- **Flexibility** - Easy to add new bookmakers or market types later
- **Balance** - Fast UI queries AND reasonable performance for analyst SQL

</essential>

<boundaries>
## What's Out of Scope

- User accounts/authentication — no user management or saved preferences yet
- Betting history — only odds data, not actual bet records
- Real-time streaming infrastructure — just store snapshots, no live change tracking
- Snapshot frequency decisions — that's Phase 5 (Scheduled Scraping)

</boundaries>

<specifics>
## Specific Ideas

**Data retention:** 30 days of historical data — recent history focused, keep storage lean.

**Event matching:** Partial matches are OK — show events even if only 2 of 3 bookmakers have them (not all platforms cover every match).

**Market storage:** Store all 111+ market types we can map, filter in the UI for display.

**Bookmaker configuration:** Full config per bookmaker:
- Identity (name, ID, logo)
- Scrape settings (endpoints, rate limits, credentials)
- Market mappings (which markets each bookmaker supports)

**Error handling:** Comprehensive approach:
- Log failures but keep scraping what works
- Flag data as potentially stale when scrapes fail
- Track failure history to identify recurring issues

</specifics>

<notes>
## Additional Context

Schema needs to support three analysis patterns equally:
1. Margin trends over time (league/tournament level)
2. Pre-match odds movement timelines (event level)
3. Cross-bookmaker gap analysis (snapshot level)

No specific technology preferences (TimescaleDB vs standard relational) — open to whatever makes sense for these requirements.

</notes>

---

*Phase: 02-database-schema*
*Context gathered: 2026-01-20*
