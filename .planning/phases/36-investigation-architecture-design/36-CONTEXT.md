# Phase 36: Investigation & Architecture Design - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<vision>
## How This Should Work

Event-centric scraping architecture where odds for each event are captured simultaneously across all bookmakers. When you look at Event X, all bookmaker odds were scraped together — not minutes apart.

**Scrape flow:**
1. **Parallel discovery** — Get events from all bookmakers simultaneously
2. **Merge event universe** — Combine into unified SR ID list
3. **Priority queue** — Process events by priority
4. **Per-event multi-bookmaker scraping** — Scrape all available bookmakers for each event together

**Priority queue logic:**
- Primary: Start time (urgency — events starting soon get priority)
- Secondary: Bookmaker coverage count
  - 3 bookmakers first (full comparison value)
  - BetPawa + at least 1 competitor second
  - 2 bookmakers (any pair) third
  - Single bookmaker last (no comparison value regardless of which bookmaker)

</vision>

<essential>
## What Must Be Nailed

- **Full profiling of current system** — Timing, throughput, memory, failure rates. Understand what's actually slow before designing.
- **Architecture design that enables parallel per-event scraping** — Blueprint for the coordination layer clear enough to drive Phases 37-42 implementation.
- **Rate limit investigation** — Discover any API constraints across bookmakers that affect parallel requests.
- **Observability redesign** — Fresh approach to progress visibility for the new event-centric architecture.

</essential>

<boundaries>
## What's Out of Scope

- No implementation — investigation and design only, no code changes to scraping
- No DB schema changes — design docs only, schema changes come in later phases
- Resilience patterns — specific error handling emerges from design, implemented in later phases
- All implementation deferred to Phases 37-42

</boundaries>

<specifics>
## Specific Ideas

- Priority queue approach for event processing
- Start time as primary urgency factor
- Bookmaker count as secondary priority (3 > BP+1 > 2 > 1)
- Parallel discovery from all platforms before per-event scraping
- Current bottlenecks: both sequential platform flow AND individual API speeds

</specifics>

<notes>
## Additional Context

- v1.5 observability (SSE progress, stale detection) should be redesigned for new architecture, not just wired in
- Deliverable format should be practical — whatever helps break down Phases 37-42 clearly
- Rate limits are unknown territory — investigation needed to understand constraints

</notes>

---

*Phase: 36-investigation-architecture-design*
*Context gathered: 2026-01-29*
