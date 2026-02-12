---
phase: 96-navigation-overhaul
plan: 01
subsystem: ui
tags: [navigation, sidebar, routing, ux]

# Dependency graph
requires:
  - phase: 95-historical-analysis
    provides: Historical Analysis page complete
provides:
  - Odds Comparison as default landing page
  - Sidebar status widgets for at-a-glance system monitoring
  - Wider sidebar for improved readability
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sidebar status widget pattern with compact health indicators"

key-files:
  created: []
  modified:
    - web/src/routes.tsx
    - web/src/components/layout/app-sidebar.tsx
    - web/src/components/ui/sidebar.tsx

key-decisions:
  - "Odds Comparison as landing page reflects primary workflow"
  - "Dashboard moved to /dashboard, still accessible but not default"
  - "Status section shows events count and health dots, hidden in collapsed mode"

patterns-established:
  - "Compact status indicators in sidebar using health dots pattern"

issues-created: []

# Metrics
duration: 5min
completed: 2026-02-12
---

# Phase 96 Plan 01: Navigation Overhaul Summary

**Odds Comparison as default landing page, sidebar status widgets with event count and system health indicators, wider sidebar for improved readability**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-12T12:35:00Z
- **Completed:** 2026-02-12T12:40:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Odds Comparison now the default landing page at `/`
- Dashboard accessible at `/dashboard` with reordered navigation
- Sidebar shows compact Status section with event count badge and health indicator dots
- Sidebar width increased from 16rem to 19rem (~20% wider) for better readability

## Task Commits

Each task was committed atomically:

1. **Task 1: Make Odds Comparison the default landing page** - `84bb2f5` (feat)
2. **Task 2: Add compact status widgets to sidebar** - `d331544` (feat)
3. **Task 3: Widen sidebar by ~20%** - `4b425aa` (feat)

## Files Created/Modified

- `web/src/routes.tsx` - Changed "/" to render MatchList, Dashboard moved to "/dashboard"
- `web/src/components/layout/app-sidebar.tsx` - Added Status section with useCoverage, useHealth, useSchedulerStatus hooks
- `web/src/components/ui/sidebar.tsx` - SIDEBAR_WIDTH 16rem->19rem, SIDEBAR_WIDTH_MOBILE 18rem->20rem

## Decisions Made

- Odds Comparison as landing page reflects the primary user workflow (analyzing competitive odds)
- Navigation order: Odds Comparison, Coverage, Historical Analysis, Dashboard, Scrape Runs, Settings
- Status section hidden in icon-only collapsed mode using `group-data-[collapsible=icon]:hidden`
- Health indicators use green/yellow/red/gray dots for database and scheduler status

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed SchedulerStatus type usage**
- **Found during:** Task 2 (Status widgets implementation)
- **Issue:** Plan specified `scheduler?.state` but type has `running` and `paused` booleans instead
- **Fix:** Changed to `scheduler?.running && !scheduler?.paused` for schedulerHealthy calculation
- **Files modified:** web/src/components/layout/app-sidebar.tsx
- **Verification:** `npm run build` passes without TypeScript errors
- **Committed in:** `4b425aa` (included in Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor type correction, no scope change

## Issues Encountered

None

## Next Phase Readiness

Phase 96 complete, v2.6 UX Polish & Navigation milestone ready to ship

---
*Phase: 96-navigation-overhaul*
*Completed: 2026-02-12*
