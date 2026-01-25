---
phase: 22-history-retention
plan: 02
subsystem: database
tags: [sqlalchemy, alembic, cleanup, async, batch-delete]

# Dependency graph
requires:
  - phase: 22-01
    provides: Retention settings (odds_retention_days, match_retention_days)
provides:
  - Cleanup service with stats, preview, execute functions
  - CleanupRun history tracking table
  - Batch deletion pattern for performance
affects: [22-03, scheduled-cleanup, manage-data-dialog]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Batch deletion (1000 records at a time) to avoid long locks"
    - "CleanupRun tracking for audit trail"

key-files:
  created:
    - src/services/__init__.py
    - src/services/cleanup.py
    - src/api/schemas/cleanup.py
    - src/db/models/cleanup_run.py
    - alembic/versions/c9d5e3f6g7h8_add_cleanup_runs.py
  modified:
    - src/db/models/__init__.py

key-decisions:
  - "Batch size of 1000 for deletion to balance performance and lock duration"
  - "Delete in FK order: market_odds → odds → runs → events → tournaments"
  - "Track both BetPawa and competitor data separately"

patterns-established:
  - "Cleanup service pattern with preview before execute"
  - "Run history tracking for scheduled jobs"

issues-created: []

# Metrics
duration: 5min
completed: 2026-01-25
---

# Phase 22 Plan 02: Cleanup Service Summary

**Created cleanup service with data analysis, deletion preview, batch execution, and run history tracking in CleanupRun table**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-25T03:19:48Z
- **Completed:** 2026-01-25T03:24:24Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Cleanup service with get_data_stats, preview_cleanup, execute_cleanup functions
- DataStats, CleanupPreview, CleanupResult Pydantic schemas
- CleanupRun model tracking all cleanup executions
- Batch deletion pattern (1000 records) to avoid database locks
- Proper FK order handling for both BetPawa and competitor tables

## Task Commits

Each task was committed atomically:

1. **Task 1: Create cleanup service with stats/preview/execute** - `d1c3abe` (feat)
2. **Task 2: Add cleanup run history table** - `405ef4b` (feat)

**Plan metadata:** `dd943fa` (docs: complete plan)

## Files Created/Modified

- `src/services/__init__.py` - New services package
- `src/services/cleanup.py` - Core cleanup logic (530+ lines)
- `src/api/schemas/cleanup.py` - Pydantic response/request models
- `src/db/models/cleanup_run.py` - CleanupRun SQLAlchemy model
- `alembic/versions/c9d5e3f6g7h8_add_cleanup_runs.py` - Migration for cleanup_runs table
- `src/db/models/__init__.py` - Export CleanupRun

## Decisions Made

- Batch size of 1000 records per deletion cycle for lock management
- Separate tracking of BetPawa (odds_snapshots, events) and competitor data
- FK deletion order: child tables first, then parents, then orphaned tournaments
- Run history includes all counts, date ranges, duration, and error tracking

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Cleanup service ready for API endpoint exposure (Plan 22-03)
- CleanupRun table ready for history display in UI
- Scheduled cleanup job can use execute_cleanup_with_tracking

---
*Phase: 22-history-retention*
*Completed: 2026-01-25*
