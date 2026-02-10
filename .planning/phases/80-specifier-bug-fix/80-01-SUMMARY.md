---
phase: 80-specifier-bug-fix
plan: 01
subsystem: api
tags: [history, specifier, line, filtering]

# Dependency graph
requires:
  - phase: 79-investigation
    provides: Bug report documenting specifier line filtering issue
provides:
  - Line parameter support in history API endpoints
  - Line parameter support in frontend hooks and API client
affects: [81-interactive-chart, 82-comparison-table]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Line parameter as optional filter for specifier markets"

key-files:
  created: []
  modified:
    - src/api/routes/history.py
    - web/src/lib/api.ts
    - web/src/features/matches/hooks/use-odds-history.ts
    - web/src/features/matches/hooks/use-margin-history.ts
    - web/src/features/matches/hooks/use-multi-odds-history.ts
    - web/src/features/matches/hooks/use-multi-margin-history.ts

key-decisions:
  - "Use result_line local variable to avoid shadowing line parameter"
  - "Include line in queryKey arrays for proper cache invalidation"

patterns-established:
  - "Line filtering pattern for specifier markets (Over/Under, Handicap)"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-10
---

# Phase 80 Plan 01: Backend and Frontend Data Layer Summary

**Line parameter added to history API endpoints and all frontend hooks, enabling filtering of historical data by specifier value (e.g., Over 2.5 vs Over 3.5)**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-10T14:30:00Z
- **Completed:** 2026-02-10T14:38:00Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Added `line` query parameter to `get_odds_history` and `get_margin_history` backend endpoints
- Updated frontend API client (`api.ts`) to pass line parameter to backend
- Added line parameter to all 4 history hooks with proper queryKey inclusion for cache invalidation

## Task Commits

Each task was committed atomically:

1. **Task 1: Add line query parameter to backend history API** - `0964b5f` (feat)
2. **Task 2: Add line parameter to frontend API client** - `2f405af` (feat)
3. **Task 3: Add line parameter to frontend hooks** - `41fc68e` (feat)

## Files Created/Modified

- `src/api/routes/history.py` - Added line parameter to both history endpoints with WHERE clause filtering
- `web/src/lib/api.ts` - Added line to getOddsHistory and getMarginHistory params
- `web/src/features/matches/hooks/use-odds-history.ts` - Added line to interface, queryKey, and API call
- `web/src/features/matches/hooks/use-margin-history.ts` - Added line to interface, queryKey, and API call
- `web/src/features/matches/hooks/use-multi-odds-history.ts` - Added line to interface, queryKey, and API call
- `web/src/features/matches/hooks/use-multi-margin-history.ts` - Added line to interface, queryKey, and API call

## Decisions Made

- Used `result_line` as local variable name in backend functions to avoid shadowing the `line` parameter
- Added line as last element in queryKey arrays to maintain backward compatibility while enabling proper cache invalidation when line changes

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Data layer ready for Plan 80-02 (frontend components)
- Components can now pass line parameter through to fetch filtered historical data
- Plan 80-02 will wire up click handlers to pass line from market data to history dialog

---
*Phase: 80-specifier-bug-fix*
*Completed: 2026-02-10*
