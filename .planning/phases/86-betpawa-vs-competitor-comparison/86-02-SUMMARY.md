---
phase: 86-betpawa-vs-competitor-comparison
plan: 02
subsystem: ui
tags: [react, tanstack-query, shadcn, comparison, margins]

# Dependency graph
requires:
  - phase: 86-01
    provides: BookmakerFilter component, BOOKMAKER_COLORS constant
provides:
  - MarketMarginStats interface for per-bookmaker margin data
  - competitorMargins field in TournamentMarket with sportybet/bet9ja stats
  - BookmakerFilter in TournamentDetailPage header
  - Multi-column MarketCard with bookmaker comparison table
  - CompetitiveBadge showing +/- vs best competitor
affects: [86-03, 86-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Multi-column grid table in MarketCard for bookmaker comparison"
    - "CompetitiveBadge pattern for difference display"
    - "getStats helper for unified Betpawa/competitor stat access"
    - "Single-column fallback when no competitor data"

key-files:
  created: []
  modified:
    - web/src/features/historical-analysis/hooks/use-tournament-markets.ts
    - web/src/features/historical-analysis/hooks/index.ts
    - web/src/features/historical-analysis/tournament-detail.tsx

key-decisions:
  - "Extract competitor margins during event detail processing loop"
  - "Use COMPETITOR_SLUGS array for easy future bookmaker additions"
  - "Competitive badge shows +X.X% (red) if worse, -X.X% (green) if better"
  - "Fall back to single-column when only Betpawa selected or no competitor data"

patterns-established:
  - "MarketMarginStats interface for consistent margin statistics"
  - "Multi-bookmaker table grid with CSS grid-template-columns"
  - "Em dash for missing competitor data"

issues-created: []

# Metrics
duration: 12min
completed: 2026-02-11
---

# Phase 86 Plan 02: Multi-Bookmaker Margin Display Summary

**Tournament detail MarketCard with per-bookmaker columns showing Betpawa vs SportyBet vs Bet9ja margins, plus competitive badge**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-11T16:00:00Z
- **Completed:** 2026-02-11T16:12:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Extended useTournamentMarkets hook with competitorMargins field containing per-bookmaker avg/min/max/eventCount
- Added BookmakerFilter to TournamentDetailPage header with state management
- Redesigned MarketCard with multi-column table layout showing all bookmakers
- Added CompetitiveBadge comparing Betpawa margin to best competitor

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend useTournamentMarkets with competitor margin data** - `2c08a61` (feat)
2. **Task 2: Add BookmakerFilter to TournamentDetailPage** - `687e200` (feat)
3. **Task 3: Update MarketCard with multi-bookmaker columns** - `7b2fc98` (feat)

## Files Created/Modified

- `web/src/features/historical-analysis/hooks/use-tournament-markets.ts` - Added MarketMarginStats interface, COMPETITOR_SLUGS, competitorMargins extraction and aggregation
- `web/src/features/historical-analysis/hooks/index.ts` - Export MarketMarginStats type
- `web/src/features/historical-analysis/tournament-detail.tsx` - BookmakerFilter in header, CompetitiveBadge component, multi-column MarketCard

## Decisions Made

- **Competitor extraction during existing loop:** Rather than a second pass, competitor data is extracted in the same event detail processing loop after Betpawa markets are processed. More efficient.
- **CSS grid for table layout:** Used inline style grid-template-columns for dynamic column count based on selected bookmakers.
- **Single-column fallback:** When only Betpawa selected or no competitor data exists, card falls back to original simpler layout to avoid empty columns.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Tournament detail page now shows per-market comparison across bookmakers
- Ready for 86-03: Timeline chart with competitor overlay lines
- CompetitiveBadge pattern can be reused in other views

---
*Phase: 86-betpawa-vs-competitor-comparison*
*Completed: 2026-02-11*
