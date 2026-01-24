---
phase: 15-full-event-scraping
plan: 01
subsystem: scraping
tags: [sportybet, bet9ja, competitor-events, odds-snapshots, api]

# Dependency graph
requires:
  - phase: 14-tournament-discovery-scraping
    provides: competitor_tournaments table with discovered tournaments
  - phase: 13-database-schema-extension
    provides: CompetitorEvent, CompetitorOddsSnapshot, CompetitorMarketOdds models
provides:
  - CompetitorEventScrapingService for full event scraping
  - fetch_events_by_tournament() in SportyBetClient
  - POST /api/scheduler/scrape-competitor-events endpoint
  - competitor_events population from both platforms
  - competitor_odds_snapshots with parsed market odds
affects: [16-cross-platform-matching, 18-palimpsest-api-endpoints]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Competitor event upsert by source + external_id
    - Market parsing reusing orchestrator patterns
    - Semaphore-based concurrent tournament fetching

key-files:
  created:
    - src/scraping/competitor_events.py
  modified:
    - src/scraping/clients/sportybet.py
    - src/api/routes/scheduler.py
    - src/api/schemas/scheduler.py

key-decisions:
  - "Use source + external_id as unique key for competitor events"
  - "Link betpawa_event_id when SR ID matches existing Event record"

patterns-established:
  - "CompetitorEventScrapingService pattern for platform-specific event scraping"

issues-created: []

# Metrics
duration: 5 min
completed: 2026-01-24
---

# Phase 15 Plan 01: Full Event Scraping Summary

**CompetitorEventScrapingService with SportyBet/Bet9ja event scraping, market parsing, and API endpoint**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-24T16:35:31Z
- **Completed:** 2026-01-24T16:40:03Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- SportyBetClient.fetch_events_by_tournament() for tournament-based event fetching
- CompetitorEventScrapingService with full scraping for both SportyBet and Bet9ja
- Market parsing logic adapted from orchestrator patterns
- Competitor events linked to betpawa events via SportRadar ID matching
- API endpoint for triggering competitor event scraping

## Task Commits

Each task was committed atomically:

1. **Task 1: Add fetch_events_by_tournament() to SportyBetClient** - `64b8dea` (feat)
2. **Task 2: Create CompetitorEventScrapingService** - `d818246` (feat)
3. **Task 3: Add API endpoint for competitor event scraping** - `aca2c8d` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `src/scraping/competitor_events.py` - New service with ~650 lines: scrape methods, parsers, upserters
- `src/scraping/clients/sportybet.py` - Added fetch_events_by_tournament() method
- `src/api/routes/scheduler.py` - Added POST /api/scheduler/scrape-competitor-events
- `src/api/schemas/scheduler.py` - Added CompetitorScrapeResult, CompetitorScrapeResponse

## Decisions Made

- Used source + external_id as unique key for competitor_events (consistent with tournament_discovery)
- Link betpawa_event_id when SR ID matches existing Event record for cross-platform matching
- Reused market parsing patterns from orchestrator.py for consistency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- Competitor events from both platforms ready for cross-platform matching
- SR ID matching foundation in place (betpawa_event_id linkage)
- Ready for Phase 16: Cross-Platform Matching Enhancement

---
*Phase: 15-full-event-scraping*
*Completed: 2026-01-24*
