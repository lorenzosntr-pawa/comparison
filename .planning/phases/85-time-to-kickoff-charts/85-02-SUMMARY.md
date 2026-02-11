---
phase: 85-time-to-kickoff-charts
plan: 02
subsystem: ui
tags: [dialog, recharts, margin-timeline, shadcn]

# Dependency graph
requires:
  - phase: 85-01
    provides: TimeToKickoffChart component, TournamentMarket with opening/closing margins
provides:
  - TimelineDialog component for margin timeline visualization
  - Dialog-based timeline access from market cards and page level
  - Opening/closing margin display on tracked market cards
affects: [86-betpawa-vs-competitor, tournament-detail-page]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dialog-based timeline: on-demand visualization instead of inline chart"
    - "Multi-market mode via Select dropdown for page-level access"
    - "Bucket stats table with largest-change highlighting"

key-files:
  created:
    - web/src/features/historical-analysis/components/timeline-dialog.tsx
  modified:
    - web/src/features/historical-analysis/tournament-detail.tsx
    - web/src/features/historical-analysis/components/index.ts

key-decisions:
  - "Dialog-based approach over inline charts for cleaner main page"
  - "Tracked markets (1X2, O/U 2.5, BTTS, DC) show opening/closing on cards"
  - "Two access points: card-level button for single market, page-level for all markets"

patterns-established:
  - "TimelineDialog with summary stats header, bucket breakdown, and chart"
  - "TRACKED_MARKET_IDS Set for quick market type lookup"

issues-created: []

# Metrics
duration: 4min
completed: 2026-02-11
---

# Phase 85 Plan 02: TimelineDialog & Page Integration Summary

**Created TimelineDialog component with summary stats and bucket breakdown, integrated into TournamentDetailPage with opening/closing margin display on tracked market cards**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-11T09:53:52Z
- **Completed:** 2026-02-11T09:57:48Z
- **Tasks:** 2 (+ 1 checkpoint)
- **Files modified:** 3

## Accomplishments

- Created TimelineDialog with summary stats header showing opening→closing margin with delta
- Added per-bucket breakdown table with largest-change highlighting
- Integrated TimeToKickoffChart into dialog with bucket zone visualization
- Updated market cards to show opening/closing for tracked markets (1X2, O/U 2.5, BTTS, DC)
- Added card-level Timeline button and page-level "View All Timelines" button
- Removed inline timeline section, replaced with dialog-based approach

## Task Commits

Each task was committed atomically:

1. **Task 1: Create TimelineDialog with summary stats** - `f4022f5` (feat)
2. **Task 2: Update TournamentDetailPage with timeline integration** - `2b368be` (feat)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified

- `web/src/features/historical-analysis/components/timeline-dialog.tsx` - New dialog component with stats, bucket table, and chart
- `web/src/features/historical-analysis/tournament-detail.tsx` - Integrated TimelineDialog, added opening/closing to cards, removed inline chart
- `web/src/features/historical-analysis/components/index.ts` - Export TimelineDialog

## Decisions Made

- Used dialog-based approach instead of inline chart for cleaner page layout
- Show opening/closing margin only for tracked markets (1X2, O/U 2.5, BTTS, DC) to reduce noise
- Multi-market mode uses Select dropdown for market switching (simpler than tabs)
- Highlight bucket with largest margin change in breakdown table

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Phase 85 complete with time-to-kickoff visualization
- Ready for Phase 86: Betpawa vs Competitor Comparison (overlay lines and difference charts)

---
*Phase: 85-time-to-kickoff-charts*
*Completed: 2026-02-11*
