---
phase: 107-write-path-changes
plan: 02
subsystem: database
tags: [postgresql, upsert, on-conflict, market-level, write-handler]

# Dependency graph
requires:
  - phase: 107-01
    provides: MarketCurrentWrite, MarketWriteBatch DTOs, classify_market_changes()
  - phase: 106-schema-migration
    provides: market_odds_current and market_odds_history tables
provides:
  - handle_market_write_batch() for UPSERT/INSERT market-level writes
  - AsyncWriteQueue routing for MarketWriteBatch
  - event_coordinator integration with new write path
affects: [108-read-path-cache, api-routes, historical-api]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "PostgreSQL INSERT...ON CONFLICT for UPSERT pattern"
    - "index_where for COALESCE(line, 0) matching in unique constraint"
    - "Batch type routing in AsyncWriteQueue via isinstance()"

key-files:
  created: []
  modified:
    - src/storage/write_handler.py
    - src/storage/write_queue.py
    - src/scraping/event_coordinator.py

key-decisions:
  - "UPSERT all markets to market_odds_current, INSERT to history only when changed"
  - "Use index_where with COALESCE for NULL line handling in ON CONFLICT"
  - "Keep existing cache update logic (Phase 108 will update cache structure)"

patterns-established:
  - "Market-level write batch routing via isinstance() type check"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-24
---

# Phase 107 Plan 02: Write Handler & Integration Summary

**handle_market_write_batch() with PostgreSQL UPSERT pattern and event_coordinator integration for market-level writes**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-24T12:05:00Z
- **Completed:** 2026-02-24T12:13:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Implemented handle_market_write_batch() with UPSERT to market_odds_current and conditional INSERT to market_odds_history
- Updated AsyncWriteQueue to route MarketWriteBatch to new handler via isinstance() check
- Integrated new write path into event_coordinator.py store_batch_results()
- Unified storage for all bookmakers via bookmaker_slug field (betpawa, sportybet, bet9ja)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement handle_market_write_batch()** - `978d31e` (feat)
2. **Task 2: Add MarketWriteBatch support to AsyncWriteQueue** - `f54b802` (feat)
3. **Task 3: Update store_batch_results() for new write path** - `454f023` (feat)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified

- `src/storage/write_handler.py` - Added handle_market_write_batch() with UPSERT + INSERT logic
- `src/storage/write_queue.py` - Updated AsyncWriteQueue for MarketWriteBatch routing
- `src/scraping/event_coordinator.py` - Integrated classify_market_changes and MarketWriteBatch

## Decisions Made

- Use index_where with COALESCE(line, 0) for NULL line handling in PostgreSQL ON CONFLICT clause
- Update last_updated_at only when market.changed=True, always update last_confirmed_at
- Skip competitor data without corresponding BetPawa event (rare edge case)
- Keep existing cache update logic for backward compatibility (Phase 108 scope)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Write path complete: market_odds_current receives UPSERT, market_odds_history receives INSERT for changed markets
- Phase 107 complete, ready for Phase 108 (Read Path & Cache)
- Old snapshot tables still receive data via existing cache update logic (dual-write safety)

---
*Phase: 107-write-path-changes*
*Completed: 2026-02-24*
