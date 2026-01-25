---
phase: 22-history-retention
plan: 01
subsystem: database
tags: [sqlalchemy, alembic, pydantic, typescript, settings]

# Dependency graph
requires:
  - phase: 21-settings-persistence-integration
    provides: Settings sync pattern and history_retention_days field
provides:
  - Separate odds and match retention settings
  - Cleanup frequency configuration
  - Updated API schemas and routes
affects: [22-02, 22-03, cleanup-job, settings-ui]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created:
    - alembic/versions/b8c4d2e5f9g3_update_retention_settings.py
  modified:
    - src/db/models/settings.py
    - src/api/schemas/settings.py
    - src/api/routes/settings.py
    - web/src/types/api.ts

key-decisions:
  - "Separate retention for odds (by snapshot) and matches (by kickoff)"
  - "365 days max retention, 168 hours (7 days) max cleanup frequency"
  - "Default 30 days for both retention settings, 24 hours cleanup"

patterns-established: []

issues-created: []

# Metrics
duration: 3min
completed: 2026-01-25
---

# Phase 22 Plan 01: Retention Settings Model Summary

**Extended Settings model with odds_retention_days, match_retention_days, and cleanup_frequency_hours replacing single history_retention_days field**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-25T03:14:04Z
- **Completed:** 2026-01-25T03:17:09Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Settings model extended with three new retention fields
- Migration created to rename and add columns with proper defaults
- Pydantic schemas updated with validation (1-365 days, 1-168 hours)
- API routes handle all new field updates
- Frontend TypeScript types aligned with backend

## Task Commits

Each task was committed atomically:

1. **Task 1: Update Settings model and create migration** - `49d84a1` (feat)
2. **Task 2: Update Pydantic schemas, routes, and frontend types** - `725dbfb` (feat)

**Plan metadata:** `61534fe` (docs: complete plan)

## Files Created/Modified

- `alembic/versions/b8c4d2e5f9g3_update_retention_settings.py` - Migration for column rename and additions
- `src/db/models/settings.py` - Extended model with retention fields
- `src/api/schemas/settings.py` - Pydantic schemas with validation
- `src/api/routes/settings.py` - Update handlers for new fields
- `web/src/types/api.ts` - Frontend types (camelCase)

## Decisions Made

- Renamed history_retention_days to odds_retention_days for clarity
- Set default retention to 30 days (up from 7) for both odds and matches
- Cleanup frequency default of 24 hours (once daily)
- Max limits: 365 days retention, 168 hours (7 days) cleanup frequency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Settings model ready for cleanup job implementation (Plan 22-02)
- API can read/write all retention configuration
- Frontend types ready for Settings UI updates

---
*Phase: 22-history-retention*
*Completed: 2026-01-25*
