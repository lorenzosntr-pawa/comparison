---
phase: 86-betpawa-vs-competitor-comparison
plan: 01
subsystem: ui
tags: [react, shadcn, toggle, filter, comparison]

# Dependency graph
requires:
  - phase: 85.1
    provides: MarginMetrics with opening/closing margins, competitorAvgMargin
provides:
  - BookmakerFilter toggle component with brand colors
  - Filter bar bookmaker selection state
  - Multi-column tournament card margin display
  - Competitive badge (+/- vs best competitor)
affects: [86-02, 86-03, 86-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BookmakerFilter toggle component with brand-colored dots"
    - "Betpawa always enabled (not toggleable) as reference"
    - "Multi-column margin table (Market | Betpawa | Best Comp.)"
    - "CompetitiveBadge showing +/- difference for 1X2 market"

key-files:
  created:
    - web/src/features/historical-analysis/components/bookmaker-filter.tsx
  modified:
    - web/src/features/historical-analysis/components/filter-bar.tsx
    - web/src/features/historical-analysis/components/tournament-list.tsx
    - web/src/features/historical-analysis/components/index.ts
    - web/src/features/historical-analysis/index.tsx

key-decisions:
  - "Use 'Best Competitor' column (from competitorAvgMargin) until 86-02 extends per-bookmaker data"
  - "Show competitive badge only for 1X2 market (primary comparison)"
  - "Betpawa toggle disabled - always shown as reference"

patterns-established:
  - "BOOKMAKER_COLORS constant exported for consistent brand styling"
  - "Filter state lifted to page level, passed down via props"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-11
---

# Phase 86 Plan 01: Bookmaker Filter and Multi-Column Cards Summary

**BookmakerFilter toggle component with brand colors, multi-column tournament card margin display showing Betpawa vs Best Competitor**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-11T15:30:00Z
- **Completed:** 2026-02-11T15:38:00Z
- **Tasks:** 4 (3 auto + 1 verify checkpoint)
- **Files modified:** 5

## Accomplishments

- Created BookmakerFilter toggle component with Betpawa/SportyBet/Bet9ja buttons
- Added bookmaker selection state to FilterBar and HistoricalAnalysisPage
- Redesigned MarketBreakdown to table-like structure with bookmaker columns
- Added CompetitiveBadge showing +/- margin difference for 1X2 market
- Brand colors exported as BOOKMAKER_COLORS constant

## Task Commits

Each task was committed atomically:

1. **Task 1: Create BookmakerFilter toggle component** - `73ca339` (feat)
2. **Task 2: Add BookmakerFilter to FilterBar with state** - `bcf7923` (feat)
3. **Task 3: Update tournament cards with multi-bookmaker columns** - `86fa3d3` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `web/src/features/historical-analysis/components/bookmaker-filter.tsx` - New BookmakerFilter toggle component with brand colors
- `web/src/features/historical-analysis/components/filter-bar.tsx` - Added BookmakerFilter and new props
- `web/src/features/historical-analysis/components/tournament-list.tsx` - Multi-column MarketBreakdown, CompetitiveBadge
- `web/src/features/historical-analysis/components/index.ts` - Export BookmakerFilter and BOOKMAKER_COLORS
- `web/src/features/historical-analysis/index.tsx` - selectedBookmakers state management

## Decisions Made

- **Best Competitor column:** Use existing competitorAvgMargin field which represents the best (lowest) competitor margin. Individual bookmaker columns will be added in 86-02 when the hook is extended.
- **Competitive badge placement:** Only show on 1X2 row since it's the primary comparison market. Reduces visual noise.
- **Betpawa always enabled:** Betpawa toggle is disabled since it's the reference bookmaker - always shown.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Bookmaker filter and multi-column display working
- Ready for 86-02: Extend hook with per-bookmaker margin data
- Then 86-03 will add overlay lines and difference chart toggle

---
*Phase: 86-betpawa-vs-competitor-comparison*
*Completed: 2026-02-11*
