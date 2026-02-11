---
phase: 86-betpawa-vs-competitor-comparison
plan: 03
subsystem: ui
tags: [recharts, timeline, multi-bookmaker, overlay-chart]

# Dependency graph
requires:
  - phase: 86-02
    provides: Per-bookmaker margin data in hook
provides:
  - Multi-bookmaker overlay chart with brand colors
  - Dialog-level bookmaker filter independent from page filter
  - View mode toggle (overlay/difference) in TimelineDialog
affects: [86-04, historical-analysis]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Merged data points for multi-line recharts
    - Dialog-specific filter state (independent from page)

key-files:
  created: []
  modified:
    - web/src/features/historical-analysis/hooks/use-tournament-markets.ts
    - web/src/features/historical-analysis/components/timeline-dialog.tsx
    - web/src/features/historical-analysis/components/time-to-kickoff-chart.tsx

key-decisions:
  - "Merge data by hoursToKickoff with 1 decimal precision for time alignment"
  - "Dialog bookmaker filter resets on open (fresh state each time)"
  - "connectNulls on Line components for sparse competitor data"

patterns-established:
  - "MergedDataPoint interface for multi-bookmaker chart data"
  - "BOOKMAKER_LABELS constant for tooltip formatting"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-11
---

# Phase 86 Plan 03: Multi-Bookmaker Chart Overlay Summary

**Multi-line timeline chart with per-bookmaker colored lines, dialog-specific filter, and view mode toggle**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-11T14:30:00Z
- **Completed:** 2026-02-11T14:38:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Extended useTournamentMarkets hook with competitorTimelineData per market
- Added dialog-specific bookmaker filter (independent from page filter)
- Implemented view mode toggle (overlay/difference) with placeholder for difference view
- Created multi-line overlay chart with brand colors and legend
- Custom tooltip showing all selected bookmaker values at hover point

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend hook with competitor timeline data** - `2992ee4` (feat)
2. **Task 2: Add bookmaker filter and view toggle to TimelineDialog** - `870dc4a` (feat)
3. **Task 3: Create multi-line overlay chart** - `a7e16d8` (feat)

## Files Created/Modified

- `web/src/features/historical-analysis/hooks/use-tournament-markets.ts` - Added competitorTimelineData to TournamentMarket interface and accumulator
- `web/src/features/historical-analysis/components/timeline-dialog.tsx` - Added dialog-level bookmaker filter and view mode toggle
- `web/src/features/historical-analysis/components/time-to-kickoff-chart.tsx` - Multi-bookmaker overlay chart with merged data and legend

## Decisions Made

- Merged data by rounding hoursToKickoff to 1 decimal place for time alignment across bookmakers
- Dialog bookmaker filter state resets to all selected when dialog opens
- Used connectNulls on Line components to handle sparse competitor data gracefully

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Overlay chart complete with multi-bookmaker support
- Ready for 86-04: Difference chart toggle implementation
- Placeholder already in place for difference view

---
*Phase: 86-betpawa-vs-competitor-comparison*
*Completed: 2026-02-11*
