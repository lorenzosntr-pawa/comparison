---
phase: 62-historical-data-api
plan: 01
subsystem: api
tags: [pydantic, alembic, postgresql, index, historical-data]

# Dependency graph
requires:
  - phase: 60-investigation-schema-design
    provides: Query patterns for odds trend lookup, schema analysis
provides:
  - Historical data Pydantic schemas (6 schemas)
  - Composite index for efficient market history queries
affects: [63-snapshot-list-endpoint, 64-odds-history-endpoint, 65-margin-history-endpoint]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Historical data schemas reuse OutcomeOdds for consistency"

key-files:
  created:
    - alembic/versions/b314393d6ef5_add_market_history_index.py
  modified:
    - src/matching/schemas.py

key-decisions:
  - "Reuse OutcomeOdds in OddsHistoryPoint for consistency with existing schemas"
  - "Composite index on (snapshot_id, betpawa_market_id) for efficient JOIN operations"
  - "ConfigDict(from_attributes=True) only on HistoricalSnapshot for ORM mapping"

patterns-established:
  - "Historical data schemas separate full-data (OddsHistoryResponse) from chart-only (MarginHistoryResponse)"

issues-created: []

# Metrics
duration: 3min
completed: 2026-02-06
---

# Phase 62 Plan 01: Historical Data Schemas Summary

**Pydantic response schemas for historical data APIs plus composite index migration for efficient market history queries**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-06T13:20:00Z
- **Completed:** 2026-02-06T13:23:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created 6 Pydantic schemas for historical data API responses
- Added composite index on market_odds (snapshot_id, betpawa_market_id)
- Established response contracts for snapshot list, odds history, and margin history endpoints

## Task Commits

Each task was committed atomically:

1. **Task 1: Create historical data Pydantic schemas** - `94d1825` (feat)
2. **Task 2: Add composite index migration for market history queries** - `7749deb` (feat)

## Files Created/Modified

- `src/matching/schemas.py` - Added 6 historical data schemas (HistoricalSnapshot, SnapshotHistoryResponse, OddsHistoryPoint, OddsHistoryResponse, MarginHistoryPoint, MarginHistoryResponse)
- `alembic/versions/b314393d6ef5_add_market_history_index.py` - Migration to create idx_market_odds_snapshot_market composite index

## Decisions Made

- **Reuse OutcomeOdds**: OddsHistoryPoint reuses the existing OutcomeOdds schema for consistency
- **Two response levels**: Full odds history (OddsHistoryResponse) includes outcomes; margin-only (MarginHistoryResponse) is lightweight for charts
- **Composite index order**: (snapshot_id, betpawa_market_id) optimizes the JOIN pattern where snapshot_id is from the join condition

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Alembic command needed to run from project root (alembic.ini location), not src/db as documented in plan - minor path adjustment

## Next Phase Readiness

- All 6 response schemas ready for endpoint implementation
- Composite index in place for efficient queries
- Ready for Phase 62-02 (snapshot list endpoint) or Phase 63 (endpoint implementation)

---
*Phase: 62-historical-data-api*
*Completed: 2026-02-06*
