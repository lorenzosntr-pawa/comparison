# Phase 15: Full Event Scraping - Context

**Gathered:** 2026-01-24
**Status:** Ready for planning

<vision>
## How This Should Work

Transform the scraping service from betpawa-centric to parallel full-palimpsest scraping for all three bookmakers. This is still a betpawa comparison tool, but now we scrape the complete football palimpsest from each platform.

The scraping runs in parallel across:
- **Betpawa** — continues using existing feed (not scraped)
- **SportyBet** — full tournament/event/odds scraping
- **Bet9ja** — full tournament/event/odds scraping

Events are matched by SportRadar ID using the priority chain: betpawa > sportybet > bet9ja. This means we now capture events where betpawa doesn't offer — competitor-only events become visible.

The result: a foundation for both odds comparison AND palimpsest comparison (which platforms offer what events).

</vision>

<essential>
## What Must Be Nailed

- **Complete coverage** — Get ALL football events from all three platforms, no gaps
- **Matching accuracy** — Every event has correct SportRadar ID for cross-platform matching
- **Data freshness** — Scheduled scraping keeps tournaments, events, and odds continuously current
- **Priority chain** — betpawa > sportybet > bet9ja for metadata when matching across platforms

</essential>

<boundaries>
## What's Out of Scope

- Other sports — football only for this version, expansion is a future concern
- UI changes — backend/scraping only, no new pages or components
- Betpawa scraping — betpawa data continues from existing feed
- Data retention logic — 30-day cleanup already exists, don't rebuild

</boundaries>

<specifics>
## Specific Ideas

- Replace existing betpawa-centric scraping approach entirely with new parallel approach
- Same scraping frequency as current scheduled runs
- Match existing scraping behavior and patterns
- Events + odds scraped together in the same run
- 30-day retention enables historical comparison analysis (already in place)

</specifics>

<notes>
## Additional Context

This phase enables the palimpsest comparison feature in later phases (Phase 19-20). By capturing events from all platforms — including those betpawa doesn't offer — we can show:
1. Which events each platform covers
2. Where betpawa has gaps vs competitors
3. Historical availability patterns over 30 days

The existing matches page already has filters for bookmaker availability. Phase 19 will add a filter to show/exclude non-betpawa events.

</notes>

---

*Phase: 15-full-event-scraping*
*Context gathered: 2026-01-24*
