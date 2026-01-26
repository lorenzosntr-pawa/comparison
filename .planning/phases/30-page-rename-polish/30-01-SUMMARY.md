---
phase: 30-page-rename-polish
plan: 01
subsystem: ui
tags: [react, lucide-react, routing]

requires:
  - phase: 29-double-chance-margins
    provides: Table restructure with bookmaker rows complete

provides:
  - Consistent "Odds Comparison" naming throughout UI
  - New /odds-comparison URL route
  - BarChart3 navigation icon

affects: []

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - web/src/features/matches/index.tsx
    - web/src/features/matches/components/match-header.tsx
    - web/src/features/matches/components/match-table.tsx
    - web/src/components/layout/app-sidebar.tsx
    - web/src/routes.tsx

key-decisions:
  - "BarChart3 icon chosen over List for better visual representation of odds comparison"
  - "URL changed from /matches to /odds-comparison for full naming consistency"

patterns-established: []

issues-created: []

duration: 4min
completed: 2026-01-26
---

# Phase 30 Plan 01: Page Rename & Polish Summary

**Renamed page from "Matches" to "Odds Comparison" with new URL route and BarChart3 navigation icon**

## Performance

- **Duration:** 4 min
- **Tasks:** 3 (2 auto + 1 checkpoint)
- **Files modified:** 5

## Accomplishments

- Renamed page title from "Matches" to "Odds Comparison"
- Updated back link text to "Back to Odds Comparison"
- Changed navigation icon from List to BarChart3
- Changed URL route from /matches to /odds-comparison (user-approved deviation)

## Task Commits

1. **Task 1: Rename page title and back link** - `0167c6f` (feat)
2. **Task 2: Update navigation icon** - `b9c1b67` (feat)
3. **Deviation: URL route change** - `54a23eb` (feat) - user-approved architectural change

**Plan metadata:** (pending)

## Files Created/Modified

- `web/src/features/matches/index.tsx` - Page title rename
- `web/src/features/matches/components/match-header.tsx` - Back link text and URL
- `web/src/features/matches/components/match-table.tsx` - Row navigation URL
- `web/src/components/layout/app-sidebar.tsx` - Icon and nav URL
- `web/src/routes.tsx` - Route paths

## Decisions Made

- BarChart3 icon chosen over List for better visual representation of odds comparison data
- URL changed from /matches to /odds-comparison for full naming consistency (user requested)

## Deviations from Plan

### User-Requested Changes

**1. [Rule 4 - Architectural] URL route change from /matches to /odds-comparison**
- **Found during:** Checkpoint verification
- **Issue:** User noted URL was still /matches despite page rename
- **Fix:** Changed all route references from /matches to /odds-comparison
- **Files modified:** routes.tsx, app-sidebar.tsx, match-header.tsx, match-table.tsx
- **Verification:** Build passes, navigation works
- **Committed in:** 54a23eb

---

**Total deviations:** 1 architectural (user-approved)
**Impact on plan:** URL change provides full naming consistency as user expected

## Issues Encountered

None

## Next Phase Readiness

- v1.4 Odds Comparison UX milestone complete
- All 3 phases (28, 29, 30) finished
- Ready for milestone completion (/gsd:complete-milestone)

---
*Phase: 30-page-rename-polish*
*Completed: 2026-01-26*
