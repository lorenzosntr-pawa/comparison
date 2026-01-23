---
phase: 14-tournament-discovery-scraping
plan: 01
subsystem: scraping
tags: [httpx, sqlalchemy, sportybet, bet9ja, tournament-discovery]

# Dependency graph
requires:
  - phase: 13-database-schema-extension
    provides: CompetitorTournament, CompetitorSource models, source+external_id unique constraint
provides:
  - SportyBetClient.fetch_tournaments() method
  - TournamentDiscoveryService for competitor tournament discovery
  - POST /api/scheduler/discover-tournaments endpoint
  - Upsert pattern for competitor tournaments
affects: [15-full-event-scraping, 16-cross-platform-matching]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Tournament discovery service layer separates API fetching from data storage
    - Partial failure handling in discover_all() - one platform can fail independently
    - Upsert via source + external_id unique constraint lookup

key-files:
  created:
    - src/scraping/tournament_discovery.py
  modified:
    - src/scraping/clients/sportybet.py
    - src/api/routes/scheduler.py
    - src/api/schemas/scheduler.py

key-decisions:
  - "SportyBet sportradar_id extracted from tournament.id (sr:tournament:17 -> 17)"
  - "Bet9ja sportradar_id = None (no SR IDs at tournament level)"
  - "Football sport auto-created if missing during discovery"

patterns-established:
  - "Tournament discovery as separate service from event scraping"
  - "Partial failure handling - continue with working platforms"
  - "API endpoint triggers discovery, returns counts per platform"

issues-created: []

# Metrics
duration: 8min
completed: 2026-01-23
---

# Phase 14 Plan 1: Tournament Discovery Scraping Summary

**SportyBet and Bet9ja tournament discovery service with API endpoint, storing ~200+ tournaments per platform in competitor_tournaments table**

## Performance

- **Duration:** 8 min
- **Started:** 2026-01-23T17:00:00Z
- **Completed:** 2026-01-23T17:08:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Added fetch_tournaments() to SportyBetClient for complete tournament hierarchy
- Created TournamentDiscoveryService with upsert logic for both platforms
- Added POST /api/scheduler/discover-tournaments endpoint with partial failure handling
- SportyBet tournaments capture SportRadar IDs, Bet9ja tournaments store external IDs only

## Task Commits

Each task was committed atomically:

1. **Task 1: Add fetch_tournaments() to SportyBetClient** - `658cd64` (feat)
2. **Task 2: Create TournamentDiscoveryService** - `0f7ce30` (feat)
3. **Task 3: Add API endpoint for tournament discovery** - `e84e4a5` (feat)

## Files Created/Modified

- `src/scraping/clients/sportybet.py` - Added fetch_tournaments() method
- `src/scraping/tournament_discovery.py` - New service with discover_sportybet/bet9ja/all methods
- `src/api/routes/scheduler.py` - Added POST /discover-tournaments endpoint
- `src/api/schemas/scheduler.py` - Added PlatformDiscoveryResult and TournamentDiscoveryResponse

## Decisions Made

- SportRadar ID extraction: "sr:tournament:17" -> numeric "17" stored in sportradar_id
- Bet9ja has no SR IDs at tournament level, so sportradar_id = NULL for all Bet9ja tournaments
- Football sport record auto-created if not found (edge case for fresh database)
- Upsert returns (new, updated) counts to track what changed

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Tournament scaffolding complete for both competitor platforms
- Ready for Phase 15: Full Event Scraping to populate CompetitorEvent records
- Tournament discovery should be run before event scraping to have tournament FKs available
- API endpoint can be called manually or integrated with scheduler later

---
*Phase: 14-tournament-discovery-scraping*
*Completed: 2026-01-23*
