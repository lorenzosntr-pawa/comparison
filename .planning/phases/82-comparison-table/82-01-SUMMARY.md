---
phase: 82-comparison-table
plan: 01
subsystem: ui
tags: [recharts, comparison, odds, margin, highlighting]

# Dependency graph
requires:
  - phase: 81-interactive-chart
    provides: click-to-lock crosshair with synchronized charts
provides:
  - ComparisonTable component with best/worst highlighting
  - Delta columns showing vs Betpawa differences
  - Margin row with color-coded values
affects: [83-historical-analysis, future chart components]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Multi-outcome comparison via oddsDataByOutcome prop
    - Best/worst detection across bookmakers per row

key-files:
  created:
    - web/src/features/matches/components/comparison-table.tsx
  modified:
    - web/src/features/matches/components/odds-line-chart.tsx
    - web/src/features/matches/components/margin-line-chart.tsx
    - web/src/features/matches/components/market-history-panel.tsx
    - web/src/features/matches/components/index.ts

key-decisions:
  - "Betpawa column never highlighted (it's the reference)"
  - "Best odds highlighted green with * marker"
  - ">3% worse than Betpawa highlighted red (matches OddsBadge logic)"
  - "Margin: >0.5% worse than Betpawa highlighted red (matches MarginIndicator logic)"

patterns-established:
  - "oddsDataByOutcome prop for multi-outcome comparison tables"
  - "Consistent color logic with OddsBadge and MarginIndicator components"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-10
---

# Phase 82 Plan 01: Comparison Table Summary

**Reusable ComparisonTable component with best/worst odds highlighting, delta columns, and margin display for locked timestamp comparison**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-10T13:34:00Z
- **Completed:** 2026-02-10T13:42:38Z
- **Tasks:** 3 (2 auto + 1 checkpoint)
- **Files modified:** 5

## Accomplishments

- Created ComparisonTable component with best (green) / worst (red) highlighting
- Added delta columns showing +/- difference from Betpawa (e.g., "+0.12", "-0.05")
- Integrated margin row with color-coded values (green for lower, red for higher)
- Ensured Betpawa always appears as first column, others alphabetically
- Replaced existing locked panels in OddsLineChart, MarginLineChart, and MarketHistoryPanel

## Task Commits

Each task was committed atomically:

1. **Task 1: Create ComparisonTable component** - `0b156ff` (feat)
2. **Task 2: Integrate ComparisonTable into chart components** - `4f35baf` (feat)

**Plan metadata:** `39af688` (docs: complete plan)

## Files Created/Modified

- `web/src/features/matches/components/comparison-table.tsx` - New reusable comparison table component
- `web/src/features/matches/components/odds-line-chart.tsx` - Uses ComparisonTable for locked panel
- `web/src/features/matches/components/margin-line-chart.tsx` - Uses ComparisonTable for margin comparison
- `web/src/features/matches/components/market-history-panel.tsx` - Uses ComparisonTable with oddsDataByOutcome
- `web/src/features/matches/components/index.ts` - Exports ComparisonTable

## Decisions Made

- Betpawa column never gets highlighted (it's the reference point for comparisons)
- Best odds: highest value for each outcome row, highlighted green with * marker
- Significantly worse: >3% lower than Betpawa odds, highlighted red
- Margin comparison: >0.5% higher than Betpawa margin is "worse", highlighted red
- Multi-outcome mode uses oddsDataByOutcome prop (outcome -> { bookmaker -> odds })

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Phase 82 complete with 1/1 plans finished
- Ready for Phase 83: Historical Analysis Page Foundation

---
*Phase: 82-comparison-table*
*Completed: 2026-02-10*
