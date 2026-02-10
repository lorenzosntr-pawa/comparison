---
phase: 84-tournament-summary-metrics
plan: 01
subsystem: ui
tags: [react, tanstack-query, tailwind, margin-calculation, trend-analysis]

# Dependency graph
requires:
  - phase: 83-historical-analysis-page
    provides: Historical Analysis page with tournament list and useTournaments hook
provides:
  - Tournament-level margin metrics (avgMargin, competitorAvgMargin)
  - Bookmaker coverage percentages by tournament
  - Margin trend indicators (up/down/stable)
  - Visual metrics display on tournament cards
affects: [85-time-to-kickoff-charts, 86-betpawa-vs-competitor-comparison]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Accumulator pattern for multi-field aggregation during iteration"
    - "First-half vs second-half trend calculation with 0.5% threshold"
    - "Coverage bar with proportional bookmaker segments"

key-files:
  created: []
  modified:
    - web/src/features/historical-analysis/hooks/use-tournaments.ts
    - web/src/features/historical-analysis/components/tournament-list.tsx

key-decisions:
  - "Use market_id 3743 for 1X2 margin extraction"
  - "Best competitor margin = lowest of sportybet/bet9ja"
  - "Trend requires minimum 4 events for meaningful comparison"
  - "Sort tournaments by Betpawa avgMargin ascending (best first)"

patterns-established:
  - "TournamentAccumulator pattern: aggregate multiple metrics during single event iteration"
  - "Trend calculation: first-half vs second-half with 0.5% threshold"
  - "Coverage bar: proportional width segments with tooltip"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-10
---

# Phase 84 Plan 01: Tournament Summary Metrics Summary

**Extended tournament cards with margin comparison (Betpawa vs best competitor), bookmaker coverage bars, and trend indicators calculated from events data.**

## Performance

- **Duration:** ~8 minutes
- **Started:** 2026-02-10T14:30:00Z
- **Completed:** 2026-02-10T14:38:00Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments

- Extended `TournamentWithCount` interface with avgMargin, competitorAvgMargin, coverageByBookmaker, and trend fields
- Implemented metrics calculation from events data using accumulator pattern
- Added helper functions for margin extraction, competitor comparison, and trend analysis
- Created TrendIndicator component with colored arrows (green=improving, red=worsening, gray=stable)
- Created CoverageBar component with bookmaker-colored segments and tooltip
- Created MarginBadge component with comparison coloring and delta display
- Sorted tournaments by best Betpawa margin (ascending)

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend useTournaments hook with metrics calculation** - `f93e6ee` (feat)
2. **Task 2: Add metrics display to tournament cards** - `ad6f743` (feat)

**Plan metadata:** Pending

## Files Created/Modified

- `web/src/features/historical-analysis/hooks/use-tournaments.ts` - Extended with TournamentAccumulator pattern, helper functions for margin/coverage/trend calculation
- `web/src/features/historical-analysis/components/tournament-list.tsx` - Added TrendIndicator, CoverageBar, MarginBadge components with proper styling

## Decisions Made

- **Market ID 3743 for 1X2**: Used canonical market ID for consistent margin extraction across bookmakers
- **Best competitor = lowest margin**: Between sportybet and bet9ja, use the one with lower margin for comparison
- **Minimum 4 events for trend**: Trend calculation requires sufficient data points for meaningful first/second half comparison
- **0.5% threshold for trend**: Differences less than 0.5% considered stable to avoid noise

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Phase 84 Plan 01 complete
- Tournament cards now display comprehensive metrics
- Ready to check remaining plans in Phase 84 or proceed to Phase 85: Time-to-Kickoff Charts

---
*Phase: 84-tournament-summary-metrics*
*Completed: 2026-02-10*
