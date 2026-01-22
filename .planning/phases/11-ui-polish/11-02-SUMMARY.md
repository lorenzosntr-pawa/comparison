---
phase: 12-ui-polish
plan: 02
subsystem: ui
tags: [react, dashboard, layout, scheduler, status-bar]

# Dependency graph
requires:
  - phase: 12-01
    provides: pawaRisk rebrand and sidebar defaults
provides:
  - Three-tier dashboard layout with integrated scheduler controls
  - Compact status bar combining all system indicators
  - Real-time scheduler info in RecentRuns header

affects: [dashboard, settings]

# Tech tracking
tech-stack:
  added: []
  patterns: [Compact status indicators, Integrated scheduler controls in card headers]

key-files:
  created:
    - web/src/features/dashboard/components/status-bar.tsx
  modified:
    - web/src/features/dashboard/index.tsx
    - web/src/features/dashboard/components/recent-runs.tsx
    - web/src/features/dashboard/components/stats-cards.tsx
    - web/src/features/dashboard/components/index.ts

key-decisions:
  - "Consolidated all status indicators into single horizontal bar"
  - "Moved scheduler controls into RecentRuns header instead of separate cards"
  - "Reduced stats cards from 4 to 2 (events only)"

patterns-established:
  - "Status bar pattern: horizontal layout with icons, dots, and abbreviations"
  - "Integrated controls pattern: embed related controls in card headers"

issues-created: []

# Metrics
duration: 13min
completed: 2026-01-22
---

# Phase 12 Plan 2: Dashboard Layout Restructure Summary

**Clean three-tier dashboard with scheduler controls integrated in RecentRuns header and compact status bar consolidating all indicators**

## Performance

- **Duration:** 13 min
- **Started:** 2026-01-22T12:13:50Z
- **Completed:** 2026-01-22T12:26:43Z
- **Tasks:** 3 completed + 2 improvements
- **Files modified:** 5

## Accomplishments

- Created StatusBar component combining DB, scheduler, and platform status indicators in single row
- Integrated scheduler controls (interval, next run, status) into RecentRuns card header
- Restructured dashboard to three-tier layout: stats → runs → status bar
- Removed duplicate scheduler information from StatsCards (Scrape Interval and Scheduler cards)
- Added next scheduled scrape time display in RecentRuns header

## Task Commits

Each task was committed atomically:

1. **Task 1: Create compact status bar component** - `9a08544` (feat)
2. **Task 2: Add scheduler controls to RecentRuns header** - `2165009` (feat)
3. **Task 3: Update Dashboard layout** - `9027871` (feat)
4. **Improvement: Add next scheduled scrape time to header** - `0969d37` (feat)
5. **Fix: Remove scheduler cards from StatsCards** - `4f938bf` (fix)

**Plan metadata:** (to be committed)

## Files Created/Modified

- `web/src/features/dashboard/components/status-bar.tsx` - New compact status bar with all indicators
- `web/src/features/dashboard/components/index.ts` - Added StatusBar export
- `web/src/features/dashboard/components/recent-runs.tsx` - Added scheduler badges to header
- `web/src/features/dashboard/index.tsx` - Restructured to three-tier layout
- `web/src/features/dashboard/components/stats-cards.tsx` - Removed scheduler cards, kept only events

## Decisions Made

None - followed plan as specified with minor enhancements during user verification.

## Deviations from Plan

### Enhancements Added

**1. Next scheduled scrape time (discovered during verification)**
- **Found during:** Task verification
- **Enhancement:** Added "Next: in 3 minutes" badge to RecentRuns header
- **Rationale:** User requested visibility of next scheduled scrape time
- **Implementation:** Uses `scheduler.jobs[0].next_run` with `formatDistanceToNow()`
- **Files modified:** web/src/features/dashboard/components/recent-runs.tsx
- **Verification:** Badge shows relative time, updates every 10s, hidden when paused
- **Committed in:** 0969d37

**2. Fixed StatsCards showing wrong cards (bug discovered during verification)**
- **Found during:** Task verification
- **Issue:** StatsCards component was rendering 4 cards including "Scrape Interval" and "Scheduler" which duplicated info now in RecentRuns header
- **Fix:** Removed scheduler-related cards, kept only Total Events and Matched Events
- **Files modified:** web/src/features/dashboard/components/stats-cards.tsx
- **Verification:** Top row now shows only 2 cards (events stats)
- **Committed in:** 4f938bf

---

**Total deviations:** 2 enhancements (1 user-requested, 1 bug fix during verification)
**Impact on plan:** Both improvements enhance the consolidation goal. No scope creep.

## Issues Encountered

None - all tasks completed successfully.

## Next Phase Readiness

Dashboard restructure complete. Layout is cleaner with consolidated status information. All scheduler data correctly reflects database settings and updates in real-time (10s polling).

Ready to continue Phase 12 if more UI polish tasks exist.

---
*Phase: 12-ui-polish*
*Completed: 2026-01-22*
