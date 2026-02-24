---
phase: 110-retention-cleanup-storage-fix
plan: 01
subsystem: database
tags: [cleanup, retention, datetime, alembic, postgresql]

# Dependency graph
requires:
  - phase: 106-schema-migration
    provides: market_odds_history table with timezone-aware captured_at
  - phase: 107-write-path-changes
    provides: v2.9 schema with market-level storage
provides:
  - Working cleanup preview/execute endpoints (no 500 errors)
  - market_odds_history retention cleanup
  - 14-day retention setting via migration
affects: [cleanup-jobs, storage-management, data-retention]

# Tech tracking
tech-stack:
  added: []
  patterns: [timezone-naive-for-legacy-tables, timezone-aware-for-v29-tables]

key-files:
  created:
    - alembic/versions/o9p8q1r2s3t4_update_retention_to_14_days.py
  modified:
    - src/services/cleanup.py
    - src/api/schemas/cleanup.py

key-decisions:
  - "Use datetime.utcnow() for legacy tables (TIMESTAMP WITHOUT TIMEZONE)"
  - "Use datetime.now(timezone.utc) for v2.9 tables (TIMESTAMP WITH TIMEZONE)"
  - "Add market_odds_history cleanup after competitor_odds_snapshots (step 4.5)"

patterns-established:
  - "Dual timezone handling: naive for legacy, aware for v2.9 tables"

issues-created: []

# Metrics
duration: 12min
completed: 2026-02-24
---

# Phase 110 Plan 01: Retention, Cleanup & Storage Fix Summary

**Fixed cleanup timezone bug, added market_odds_history retention, updated to 14-day retention**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-24T15:20:00Z
- **Completed:** 2026-02-24T15:32:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Fixed timezone bug in cleanup.py (naive vs aware datetime mismatch)
- Added market_odds_history cleanup for v2.9 schema
- Updated retention setting to 14 days via Alembic migration

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix cleanup.py timezone bug** - `8defc9d` (fix)
2. **Task 2: Add market_odds_history cleanup** - `2152ac0` (feat)
3. **Task 3: Update retention setting to 14 days** - `1136c5f` (feat)

## Files Created/Modified
- `src/services/cleanup.py` - Timezone fix + market_odds_history cleanup
- `src/api/schemas/cleanup.py` - Added market_odds_history_count fields
- `alembic/versions/o9p8q1r2s3t4_update_retention_to_14_days.py` - Settings migration

## Decisions Made
- Used `datetime.utcnow()` for legacy tables that use TIMESTAMP WITHOUT TIMEZONE
- Used `datetime.now(timezone.utc)` for market_odds_history which uses TIMESTAMP WITH TIMEZONE
- Added market_odds_history cleanup as step 4.5 (after competitor_odds_snapshots, no FKs reference it)

## Deviations from Plan

None - plan executed exactly as written

## Issues Encountered

None

## Next Phase Readiness
- Cleanup preview endpoint ready for verification
- market_odds_history cleanup integrated
- 14-day retention ready to apply via `alembic upgrade head`
- Phase complete. v2.9 milestone ready to ship.

---
*Phase: 110-retention-cleanup-storage-fix*
*Completed: 2026-02-24*
