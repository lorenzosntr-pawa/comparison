---
phase: 67-event-details-history
plan: 01
subsystem: ui
tags: [dialog, click-handlers, market-grid, react, event-details]

# Dependency graph
requires:
  - phase: 66-odds-comparison-history
    provides: HistoryDialog component and click handler pattern from Odds Comparison page
provides:
  - Clickable odds and margin cells in Event Details page (MarketGrid) that open HistoryDialog
affects: [68-market-level-history]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Reused click handler pattern from Phase 66 in MarketGrid/MarketRow components

key-files:
  created: []
  modified:
    - web/src/features/matches/components/odds-badge.tsx
    - web/src/features/matches/components/margin-indicator.tsx
    - web/src/features/matches/components/market-row.tsx
    - web/src/features/matches/components/market-grid.tsx
    - web/src/features/matches/index.tsx

key-decisions:
  - "Shared onClick prop on OddsBadge and MarginIndicator components"
  - "Same handleHistoryClick handler for both odds and margin clicks"
  - "Extract marketId from any available bookmaker market (prefer BetPawa)"

patterns-established:
  - "Reusable OddsBadge/MarginIndicator onClick for any page using these components"

issues-created: []

# Metrics
duration: 5min
completed: 2026-02-08
---

# Phase 67 Plan 01: Event Details History Summary

**Clickable odds and margin cells in Event Details page (MarketGrid) that open HistoryDialog with market and bookmaker context**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-08T14:30:00Z
- **Completed:** 2026-02-08T14:35:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added optional onClick prop to OddsBadge component with conditional cursor-pointer styling
- Added optional onClick prop to MarginIndicator component with stopPropagation for tooltip
- Wired up MarketRow to pass onClick handlers to odds/margin components
- Added HistoryDialog state and handlers to MarketGrid
- Event Details page now opens history dialog when clicking any odds or margin value

## Task Commits

Each task was committed atomically:

1. **Task 1: Add onClick prop to OddsBadge and MarginIndicator** - `56fb892` (feat)
2. **Task 2: Wire up HistoryDialog in MarketGrid and MarketRow** - `1040a45` (feat)

**Plan metadata:** (pending)

## Files Created/Modified

- `web/src/features/matches/components/odds-badge.tsx` - Added onClick prop and hover styling
- `web/src/features/matches/components/margin-indicator.tsx` - Added onClick prop with stopPropagation
- `web/src/features/matches/components/market-row.tsx` - Added eventId/onOddsClick/onMarginClick props
- `web/src/features/matches/components/market-grid.tsx` - Added HistoryDialog state, handlers, and rendering
- `web/src/features/matches/index.tsx` - Pass eventId to MarketGrid

## Decisions Made

- Reused same OddsBadge/MarginIndicator components rather than creating Event Details-specific versions
- Single handler function for both odds and margin clicks (same dialog, different tab default)
- Extract marketId from any available bookmaker market since Event Details shows multi-bookmaker data

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Phase 67 complete (1/1 plans)
- Ready for Phase 68: Market-Level History View

---
*Phase: 67-event-details-history*
*Completed: 2026-02-08*
