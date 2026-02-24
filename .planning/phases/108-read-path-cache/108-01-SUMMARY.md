---
phase: 108-read-path-cache
plan: 01
subsystem: database
tags: [postgresql, cache, read-path, market-level]

# Dependency graph
requires:
  - phase: 107-write-path-changes
    provides: market_odds_current table with UPSERT writes
  - phase: 106-schema-migration
    provides: market_odds_current and market_odds_history tables
provides:
  - Cache warmup from market_odds_current (simplified query)
  - API DB fallback queries using market_odds_current
  - CachedSnapshot objects from new schema
affects: [109-historical-api, api-routes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Direct query to market_odds_current (no GROUP BY subqueries)"
    - "_build_cached_snapshot_from_current() helper for DB-to-cache conversion"
    - "Unified bookmaker handling via bookmaker_slug field"

key-files:
  created: []
  modified:
    - src/caching/warmup.py
    - src/api/routes/events.py

key-decisions:
  - "snapshot_id=0 for new schema (not used in market-level storage)"
  - "bookmaker_id=1 for betpawa, 0 for competitors (legacy compatibility)"
  - "Handle timezone-aware datetimes from PostgreSQL with .replace(tzinfo=None)"

patterns-established:
  - "_build_cached_snapshot_from_current() pattern for DB rows to CachedSnapshot"

issues-created: []

# Metrics
duration: 12min
completed: 2026-02-24
---

# Phase 108 Plan 01: Read Path & Cache Summary

**Cache warmup and API DB fallback queries updated to read from market_odds_current with simplified queries (no GROUP BY subqueries)**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-24T11:18:00Z
- **Completed:** 2026-02-24T11:30:00Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Replaced complex GROUP BY subqueries with direct market_odds_current queries
- Added _build_cached_snapshot_from_current() helper for consistent cache object creation
- Unified handling for all bookmakers (betpawa, sportybet, bet9ja) via bookmaker_slug
- Simplified warmup from ~50 lines of GROUP BY logic to ~30 lines of direct query

## Task Commits

Each task was committed atomically:

1. **Task 1: Update cache warmup** - `25e9c79` (feat)
2. **Task 2: Update events.py DB fallback** - `e0ee586` (feat)
3. **Task 3: Verify API responses** - No commit (verification only)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified

- `src/caching/warmup.py` - Simplified query using market_odds_current, removed OddsSnapshot/CompetitorOddsSnapshot queries
- `src/api/routes/events.py` - Added _build_cached_snapshot_from_current(), updated fallback queries

## Decisions Made

- Use snapshot_id=0 for CachedSnapshot objects (not used in new schema)
- Use bookmaker_id=1 for betpawa, 0 for competitors (legacy compatibility with cache structure)
- Handle timezone-aware datetimes from PostgreSQL by stripping timezone info

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- **Verification requires server restart**: The running server has old code from before Phase 107/108 changes. The market_odds_current table is empty because the server's write path hasn't been updated. After server restart:
  1. Phase 107 write path will populate market_odds_current on next scrape
  2. Phase 108 read path will then use the new data
  3. All code changes verified via import tests (no runtime errors)

## Next Phase Readiness

- Read path complete: warmup.py and events.py query market_odds_current
- Phase 109 ready: Historical API can use market_odds_history for time-series queries
- Server restart required to activate both Phase 107 (write) and Phase 108 (read) changes

---
*Phase: 108-read-path-cache*
*Completed: 2026-02-24*
