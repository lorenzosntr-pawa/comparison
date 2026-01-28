---
phase: 35-remediation
plan: 01
subsystem: api
tags: [sql, coverage, deduplication, data-fix]

# Dependency graph
requires:
  - phase: 34.1-api-ui-data-flow-audit
    provides: Identified API-001 (coverage inflation) and timing bug root causes
provides:
  - Accurate coverage statistics on palimpsest page
  - 100% event matching for matchable events
affects: [palimpsest, coverage-widgets]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified: [src/api/routes/palimpsest.py]

key-decisions:
  - "One-time SQL fix for timing-affected events (not a migration)"

patterns-established: []

issues-created: []

# Metrics
duration: 4min
completed: 2026-01-28
---

# Phase 35 Plan 01: Coverage Stats & Matching Fixes Summary

**Fixed coverage inflation (92% reduction) with DISTINCT SR ID counting and linked 2 timing-orphaned events**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-28T12:15:00Z
- **Completed:** 2026-01-28T12:19:00Z
- **Tasks:** 2
- **Files modified:** 1 (code) + database (data fix)

## Accomplishments

- Fixed API-001: Coverage stats now use `COUNT(DISTINCT sportradar_id)` instead of raw row count
- Reduced competitor_only_count from 252 to 131 (was 92% inflated)
- Match rate now accurate at 83.86% (was incorrectly showing ~75%)
- Remediated 2 timing-affected orphaned events with one-time SQL
- 0 matchable events remain unlinked

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix coverage count deduplication (API-001)** - `d1d4ad2` (fix)
2. **Task 2: Run timing remediation SQL for orphaned events** - No commit (database operation, not code)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified

- `src/api/routes/palimpsest.py` - Changed competitor_only_query to use DISTINCT on sportradar_id

## Database Changes

- One-time UPDATE on `competitor_events` table: Set `betpawa_event_id` for 2 events that were scraped before their BetPawa counterparts existed

## Decisions Made

- Ran timing remediation as direct SQL (not a migration) since it's a one-time data fix for historical timing edge case
- No periodic re-matching job needed - the timing bug only affected 2 events from initial scraping

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - both fixes applied cleanly.

## Verification Results

| Metric | Before | After |
|--------|--------|-------|
| competitor_only_count | 252 (raw rows) | 131 (distinct SR IDs) |
| Match rate | ~75% (inflated) | 83.86% (accurate) |
| Orphaned events | 2 | 0 |

## Next Phase Readiness

Phase 35 complete. Ready for:
- Phase 36 (Coverage Gap Analysis) - optional business analysis
- Phase 37 (Documentation Update) - optional cleanup

Both Phase 36 and 37 are marked optional in the roadmap - may skip based on business priorities.

---
*Phase: 35-remediation*
*Completed: 2026-01-28*
