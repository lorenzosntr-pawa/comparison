# Phase 37: Event Coordination Layer - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<vision>
## How This Should Work

The EventCoordinator is a complete replacement for the current scraping flow — a queue-based engine that orchestrates the entire scrape cycle:

1. **Discovery Phase** — Trigger tournament discovery across all 3 bookmakers (Betpawa, SportyBet, Bet9ja). This collects all event SR IDs with their bookmaker availability mapping.

2. **Queue Build** — Build a priority queue from discovered events. Priority is determined by:
   - **Primary**: Kickoff time (soonest matches first)
   - **Secondary**: Comparison value based on bookmaker availability:
     - Events on all 3 bookmakers (highest value)
     - Betpawa events with at least 1 competitor
     - Non-Betpawa events with 2 competitors
     - Single-bookmaker events (lowest priority — no comparison possible)

3. **Parallel Event Processing** — Multiple events scrape concurrently (not one-by-one). For each event, all available bookmakers scrape simultaneously. Worker pool pattern consuming from priority queue.

4. **Immediate Persistence** — Data saves to DB right after each event's scrapes complete. This makes the priority model meaningful — high-priority events show fresh data to users first, not just scrape-order.

5. **Continuous Cycle** — When queue empties, re-run discovery to catch new events. Configurable pause between cycles. The scheduler triggers the coordinator, which then runs continuously until stopped.

When a new scrape is triggered while one is running, the new events merge into the active queue with fresh priorities rather than waiting.

</vision>

<essential>
## What Must Be Nailed

All three are equally critical:

- **Simultaneous scraping** — All bookmakers for an event get scraped at the same moment. No timing gaps between platforms.
- **Smart prioritization** — Queue always processes highest-value events first based on kickoff time + comparison value model.
- **Resilience** — If one bookmaker fails, others still get scraped. One platform's failure doesn't block the rest.

</essential>

<boundaries>
## What's Out of Scope

- **DB storage optimization** — That's Phase 39. This phase uses existing storage, just with immediate persistence.
- **Concurrency tuning** — That's Phase 40. This phase implements configurable limits, tuning comes later.
- **On-demand API** — That's Phase 41. Single-event refresh endpoint is a separate phase.
- **Validation & legacy cleanup** — That's Phase 42.

Other explicit exclusions:
- Started events — excluded entirely, pre-match focus only
- Country/tournament filtering — coordinator scrapes everything, filtering happens at display time
- Other sports — football first (designed so other sports could be added later)

</boundaries>

<specifics>
## Specific Ideas

**Failure Handling:**
- Quick retry on failed bookmaker scrape, then save whatever succeeded
- Don't let one platform block the rest

**Observability:**
- Per-event status tracking (queued → scraping → completed/failed)
- Best approach for status exposure TBD during planning (balancing real-time visibility, historical tracking, maintainability)

**Configuration:**
- Concurrency limits should be configurable (tune based on what bookmakers can handle)
- Cycle pause duration should be configurable

**Data:**
- Same data as current scrapers collect — this is about coordination, not changing what gets scraped
- Discovery data provides SR ID → bookmaker mapping for queue building

</specifics>

<notes>
## Additional Context

**Phase 37/38 Split:**
The complete vision described here may span Phases 37 and 38. The optimal split will be determined during planning:
- Phase 37: EventCoordinator core — discovery integration, queue structure, priority logic, orchestration flow
- Phase 38: Parallel scraping implementation details

The important thing is that the complete coordination system described here gets built across these phases.

**Integration:**
- Replaces current scraping flow entirely
- Scheduler triggers the coordinator
- Coordinator then runs continuously (discovery → scrape → discovery → ...)

</notes>

---

*Phase: 37-event-coordination-layer*
*Context gathered: 2026-01-29*
