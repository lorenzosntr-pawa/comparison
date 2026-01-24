# Phase 17: Palimpsest API Endpoints - Context

**Gathered:** 2026-01-24
**Status:** Ready for planning

<vision>
## How This Should Work

A flexible API endpoint that lets callers query events with full control over what they see. You can filter by availability (betpawa-only, competitor-only, matched, or all) AND by platform (sportybet, bet9ja).

The response groups events under their tournaments, with coverage summaries at both the overall level and per-tournament level. Full-text search lets you find events by team, tournament, or league name. Caller can choose sort order. No pagination needed — return all matching data and let the frontend handle display.

</vision>

<essential>
## What Must Be Nailed

- **Accurate counts** — Coverage stats (matched count, competitor-only count, betpawa-only count, percentages)
- **Query performance** — Fast responses even with thousands of events
- **Rich event details** — Full data per event (odds, teams, tournament, timestamps)
- **Full coverage picture** — Summary shows counts, percentages, AND per-platform breakdown

</essential>

<boundaries>
## What's Out of Scope

No explicit exclusions — open to including what makes sense for a complete API.

</boundaries>

<specifics>
## Specific Ideas

- **Response structure**: Events grouped by tournament, summaries at top
- **Tournament context**: Each tournament includes name, sport, platform presence, and its own coverage stats
- **Filters**: Availability filter (`betpawa-only|competitor-only|matched|all`) + platform filter (`sportybet,bet9ja`)
- **Search**: Full-text search across teams, tournaments, and leagues
- **Sorting**: User-selectable sort order (by kickoff time, by status, alphabetical, etc.)
- **Pagination**: None — return all data, frontend handles display

</specifics>

<notes>
## Additional Context

This phase creates the data layer that Phase 18 (UI filters) and Phase 19 (Palimpsest Comparison Page) will consume. The API should be rich enough to support those future phases without needing changes.

Current state: ~954 competitor-only events identified. SR ID matching working at 75% match rate.

</notes>

---

*Phase: 17-palimpsest-api-endpoints*
*Context gathered: 2026-01-24*
