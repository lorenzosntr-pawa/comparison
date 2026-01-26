---
phase: 25-include-started-toggle
plan: 01
subsystem: ui
tags: [react, tanstack-query, shadcn-ui, switch]

# Dependency graph
requires:
  - phase: 24-country-filters-ux
    provides: Coverage page filter patterns
provides:
  - Include Started toggle component
  - includeStarted param in coverage hooks
affects: [dashboard-coverage-widgets]

# Tech tracking
tech-stack:
  added: []
  patterns: [toggle-in-header-pattern]

key-files:
  created: []
  modified:
    - web/src/lib/api.ts
    - web/src/features/coverage/hooks/use-coverage.ts
    - web/src/features/coverage/components/filter-bar.tsx
    - web/src/features/coverage/index.tsx

key-decisions:
  - "Toggle placed in header row next to event count for visibility"
  - "Default OFF to hide started events (pre-match focus)"

patterns-established:
  - "Header toggle pattern: Switch + Label in header justify-between layout"

issues-created: []

# Metrics
duration: 3min
completed: 2026-01-26
---

# Phase 25 Plan 01: Include Started Toggle Summary

**Switch toggle in coverage page header to show/hide started (in-play) events with dynamic stats card updates**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-26T15:30:00Z
- **Completed:** 2026-01-26T15:33:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Wired `includeStarted` parameter through API client and hooks
- Added Switch toggle in coverage page header
- Stats cards and tournament table update dynamically when toggle changes
- Default state correctly hides started events (toggle OFF)

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire include_started through API client and hooks** - `d060122` (feat)
2. **Task 2: Add Include Started toggle to coverage page** - `70d0add` (feat)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified

- `web/src/lib/api.ts` - Added includeStarted param to getCoverage() and include_started to getPalimpsestEvents()
- `web/src/features/coverage/hooks/use-coverage.ts` - Added includeStarted to useCoverage() and usePalimpsestEvents()
- `web/src/features/coverage/components/filter-bar.tsx` - Added includeStarted to CoverageFilters interface
- `web/src/features/coverage/index.tsx` - Added Switch toggle in header, wired to filters state

## Decisions Made

- Toggle placed in header row, right side, near event count for visibility
- Default state is OFF (hide started events) to focus on pre-match view
- Used shadcn/ui Switch + Label components following established patterns

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Include Started toggle complete and functional
- Ready for Phase 26: Tournament Gaps Cards

---
*Phase: 25-include-started-toggle*
*Completed: 2026-01-26*
