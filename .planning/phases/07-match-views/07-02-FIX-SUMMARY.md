---
phase: 07-match-views
plan: 02-FIX
subsystem: ui
tags: [react, frontend, market-ids, betpawa]

# Dependency graph
requires:
  - phase: 07-02
    provides: Match list view component structure
provides:
  - Fixed inline odds display in match list table
affects: [match-detail-view, future-market-displays]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - web/src/features/matches/components/match-table.tsx
    - web/src/features/matches/hooks/use-column-settings.ts

key-decisions:
  - "Use Betpawa market IDs (3743, 5000, 3795) consistently across frontend and backend"

patterns-established:
  - "Frontend market ID constants must match backend INLINE_MARKET_IDS"

issues-created: []

# Metrics
duration: 2min
completed: 2026-01-21
---

# Phase 7: Match Views - Fix 02 Summary

**Aligned frontend market IDs with Betpawa taxonomy to display inline odds in match list table**

## Performance

- **Duration:** 2 min
- **Started:** 2026-01-21T14:56:00Z
- **Completed:** 2026-01-21T14:58:35Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- Fixed market ID mismatch between frontend and backend
- Match list table now displays inline odds columns (1X2, O/U 2.5, BTTS) for all three bookmakers
- Color coding works correctly (green = Betpawa better, red = Betpawa worse)

## Task Commits

1. **Task 1: Fix UAT-001 market ID alignment** - `da806ee` (fix)

**Plan metadata:** [committed with task]

## Files Created/Modified

- `web/src/features/matches/components/match-table.tsx` - Updated MARKET_CONFIG with Betpawa market IDs
- `web/src/features/matches/hooks/use-column-settings.ts` - Updated AVAILABLE_COLUMNS and defaults

## Decisions Made

- Use Betpawa market IDs consistently: 3743 (1X2), 5000 (O/U), 3795 (BTTS)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## UAT Issue Resolved

- **UAT-001:** Match list table doesn't display inline odds columns - **RESOLVED**

## Next Phase Readiness

- Match list view now fully functional with inline odds
- Ready for match detail view (07-03) or re-verification

---
*Phase: 07-match-views*
*Plan: 02-FIX*
*Completed: 2026-01-21*
