---
phase: 66-odds-comparison-history
plan: 02
subsystem: history
tags: [history-api, recharts, multi-bookmaker, comparison, competitor]

# Dependency graph
requires:
  - phase: 66-01
    provides: History dialog basic implementation
provides:
  - Competitor history API (SportyBet/Bet9ja)
  - Multi-bookmaker comparison mode
  - Overlay charts for odds/margin comparison
affects: [67-event-details-history, 68-market-level-history]

# Tech tracking
tech-stack:
  added: []
  patterns: [multi-series-charts, useQueries-parallel-fetch, comparison-toggle]

key-files:
  created:
    - web/src/features/matches/hooks/use-multi-odds-history.ts
    - web/src/features/matches/hooks/use-multi-margin-history.ts
  modified:
    - src/api/routes/history.py
    - web/src/features/matches/components/history-dialog.tsx
    - web/src/features/matches/components/odds-line-chart.tsx
    - web/src/features/matches/components/margin-line-chart.tsx
    - web/src/features/matches/components/match-table.tsx

key-decisions:
  - "Competitor history via existing CompetitorEvent/CompetitorOddsSnapshot tables"
  - "useQueries for parallel multi-bookmaker API calls"
  - "Outcome selector in comparison mode (show one outcome at a time per bookmaker)"

patterns-established:
  - "Multi-series chart pattern: merge by timestamp, different color per bookmaker"
  - "Comparison mode toggle with bookmaker checkboxes"

issues-created: []

# Metrics
duration: 12min
completed: 2026-02-08
---

# Phase 66 Plan 02: History Dialog Fixes Summary

**Backend competitor history API + redundant margin removal + multi-bookmaker comparison mode with overlay charts**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-08T13:40:00Z
- **Completed:** 2026-02-08T13:52:00Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- BUG-010: Backend API now queries CompetitorEvent/CompetitorOddsSnapshot tables for sportybet/bet9ja history
- BUG-011: Removed redundant margin line from Odds tab (separate Margin tab exists)
- BUG-012: Multi-bookmaker comparison mode with toggle, checkboxes, and overlay charts

## Task Commits

Each task was committed atomically:

1. **BUG-010: Backend competitor history** - `bf44509` (fix)
2. **BUG-011: Remove redundant margin** - `725aa1e` (fix)
3. **BUG-012: Multi-bookmaker comparison** - `5873a2b` (feat)

## Files Created/Modified

- `src/api/routes/history.py` - Added competitor table query logic for sportybet/bet9ja
- `web/src/features/matches/hooks/use-multi-odds-history.ts` - NEW: Parallel fetch for multiple bookmakers
- `web/src/features/matches/hooks/use-multi-margin-history.ts` - NEW: Parallel fetch for margin history
- `web/src/features/matches/components/odds-line-chart.tsx` - Multi-series support with outcome selector
- `web/src/features/matches/components/margin-line-chart.tsx` - Multi-series support with bookmaker legend
- `web/src/features/matches/components/history-dialog.tsx` - Comparison mode toggle and bookmaker checkboxes
- `web/src/features/matches/components/match-table.tsx` - Pass available bookmakers to dialog

## Decisions Made

- Query competitor tables (CompetitorEvent/CompetitorOddsSnapshot/CompetitorMarketOdds) when bookmaker_slug is sportybet or bet9ja
- Link via CompetitorEvent.betpawa_event_id to find competitor snapshots for a BetPawa event
- Use TanStack Query's useQueries for parallel API calls per bookmaker
- In comparison mode, show one outcome at a time with outcome selector buttons

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all bugs fixed successfully.

## Next Phase Readiness

- Phase 66 complete, all 2 plans finished
- Ready for Phase 67: Event Details History

---
*Phase: 66-odds-comparison-history*
*Completed: 2026-02-08*
