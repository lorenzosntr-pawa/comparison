---
phase: 86-betpawa-vs-competitor-comparison
plan: 02-FIX
subsystem: ui
tags: [react, tailwind, grid-layout, margins]

# Dependency graph
requires:
  - phase: 86-02
    provides: Multi-bookmaker MarketCard implementation
provides:
  - Fixed column alignment with consistent grid template
  - Opening/closing margins for all bookmakers (not just Betpawa)
  - Visible CompetitiveBadge with background colors
affects: [86-03, 86-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "gridStyle object for consistent grid layout across rows"
    - "tabular-nums class for aligned numeric columns"
    - "text-right for right-aligned numbers in grid cells"

key-files:
  created: []
  modified:
    - web/src/features/historical-analysis/hooks/use-tournament-markets.ts
    - web/src/features/historical-analysis/tournament-detail.tsx

key-decisions:
  - "Use fixed first column width (5.5rem) and minmax for bookmaker columns"
  - "Show opening/closing for ALL markets, not just tracked 4"
  - "Pill-style badge with bg-red-100/bg-green-100 for visibility"

patterns-established:
  - "gridStyle object pattern for consistent multi-row grids"

issues-created: []

# Metrics
duration: 3min
completed: 2026-02-11
---

# Phase 86 Plan 02-FIX: UAT Issue Fixes Summary

**Fixed 3 UAT issues: column alignment, missing competitor opening/closing margins, and CompetitiveBadge visibility**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-11T13:35:18Z
- **Completed:** 2026-02-11T13:38:15Z
- **Tasks:** 3 (combined into single commit)
- **Files modified:** 2

## Accomplishments

- Fixed column alignment using consistent gridStyle with 5.5rem label column and minmax bookmaker columns
- Extended MarketMarginStats interface with openingMargin/closingMargin fields
- Added Opening/Closing rows to multi-column table for all bookmakers
- Made CompetitiveBadge more visible with bg-red-100/bg-green-100 background colors and semibold text

## Task Commits

All fixes combined into single atomic commit:

1. **All fixes** - `dfc0e62` (fix)

## Files Created/Modified

- `web/src/features/historical-analysis/hooks/use-tournament-markets.ts` - Extended MarketMarginStats with openingMargin/closingMargin, compute from sorted timeline
- `web/src/features/historical-analysis/tournament-detail.tsx` - Fixed grid layout, added Opening/Closing rows, improved CompetitiveBadge styling

## Decisions Made

- **Unified opening/closing display:** Removed special tracked-market-only opening/closing and unified into table for ALL markets
- **Right-aligned numbers:** Used text-right and tabular-nums for proper numeric alignment
- **Removed unused code:** Cleaned up isTrackedMarket function and TRACKED_MARKETS import since opening/closing now shows for all markets

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- All 3 UAT issues from 86-02-ISSUES.md addressed
- Ready for re-verification
- Tournament detail MarketCard now has clean, aligned multi-bookmaker comparison

---

*Phase: 86-betpawa-vs-competitor-comparison*
*Completed: 2026-02-11*
