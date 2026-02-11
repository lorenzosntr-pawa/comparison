---
phase: 86-betpawa-vs-competitor-comparison
plan: 04
subsystem: ui
tags: [react, recharts, comparison, margins, bar-chart]

# Dependency graph
requires:
  - phase: 86-03
    provides: Timeline dialog with view mode toggle
provides:
  - DifferenceBarChart component for margin gap visualization
  - Betpawa vs competitor difference by time bucket
  - Green/red color coding for competitive advantage
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Bar chart with per-cell color based on value sign"
    - "calculateBucketStats helper for timeline-to-bucket conversion"
    - "Best competitor selection for difference calculation"

key-files:
  created:
    - web/src/features/historical-analysis/components/difference-bar-chart.tsx
  modified:
    - web/src/features/historical-analysis/components/index.ts
    - web/src/features/historical-analysis/components/timeline-dialog.tsx

key-decisions:
  - "Compare to best (lowest) competitor at each bucket by default"
  - "Green = Betpawa lower margin (better for bettors)"
  - "Red = Betpawa higher margin (competitor advantage)"
  - "Calculate competitor bucket stats on-demand from timeline data"

patterns-established:
  - "DifferenceBucket interface for chart data structure"
  - "Custom Tooltip component for multi-field display"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-11
---

# Phase 86 Plan 04: Difference Bar Chart View Summary

**Difference view in timeline dialog showing Betpawa vs competitor margin gaps by time bucket**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-11T17:30:00Z
- **Completed:** 2026-02-11T17:38:00Z
- **Tasks:** 2 (auto) + 1 (human-verify)
- **Files created:** 1
- **Files modified:** 2

## Accomplishments

- Created DifferenceBarChart component with colored bars by time bucket
- Integrated with TimelineDialog view mode toggle (Overlay/Difference)
- Added calculateBucketStats helper for competitor timeline-to-bucket conversion
- Custom tooltip showing Betpawa margin, competitor margin, and difference
- Legend explaining green (Betpawa better) vs red (competitor better)

## Task Commits

1. **All tasks** - `38443f9` (feat)

## Files Created/Modified

- `web/src/features/historical-analysis/components/difference-bar-chart.tsx` (created) - DifferenceBarChart component with recharts BarChart, Cell coloring, custom tooltip
- `web/src/features/historical-analysis/components/index.ts` - Export DifferenceBarChart
- `web/src/features/historical-analysis/components/timeline-dialog.tsx` - Import DifferenceBarChart, add getTimeBucket/calculateBucketStats helpers, render in difference mode

## Decisions Made

- **Best competitor by default:** When comparing, use the lowest competitor margin at each bucket
- **On-demand bucket calculation:** Calculate competitor bucket stats from timeline data when needed rather than pre-computing
- **Same bucket breakdown table:** Keep showing Betpawa's bucket table in both views for context

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Phase 86 Completion

With 86-04 complete, Phase 86 (Betpawa vs Competitor Comparison) is now finished:
- 86-01: Bookmaker filter and multi-column cards ✓
- 86-02: Per-bookmaker margin data in hook ✓
- 86-03: Multi-bookmaker chart overlay ✓
- 86-04: Difference chart toggle ✓

Ready for Phase 87: Market Coverage & Export

---

*Phase: 86-betpawa-vs-competitor-comparison*
*Completed: 2026-02-11*
