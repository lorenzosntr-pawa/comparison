---
phase: 91-event-details-ui
plan: 01
subsystem: ui
tags: [react, tooltip, availability, shadcn]

# Dependency graph
requires:
  - phase: 90-odds-comparison-ui
    provides: Three-state availability patterns, formatUnavailableSince utility
provides:
  - OddsBadge component with availability rendering
  - Event Details page with consistent unavailable market styling
affects: [history-charts]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - web/src/features/matches/components/odds-badge.tsx
    - web/src/features/matches/components/market-row.tsx
    - web/src/features/matches/components/market-grid.tsx

key-decisions:
  - "Reuse formatUnavailableSince from market-utils for consistent tooltip format"

patterns-established:
  - "OutcomeDisplay extended with availability fields for prop drilling"

issues-created: []

# Metrics
duration: 4min
completed: 2026-02-11
---

# Phase 91 Plan 01: Event Details UI Summary

**OddsBadge component updated with three-state availability rendering: available (normal), unavailable (strikethrough + tooltip), never_offered (plain dash)**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-11T19:45:00Z
- **Completed:** 2026-02-11T19:49:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Extended OddsBadge to handle availability props with Tooltip for unavailable markets
- Updated MarketRow to extract and propagate availability data from MarketOddsDetail
- Wrapped MarketGrid table with TooltipProvider for tooltip support

## Task Commits

Each task was committed atomically:

1. **Task 1: Update OddsBadge component with availability props** - `d80a1cb` (feat)
2. **Task 2: Update MarketRow to pass availability data and wrap with TooltipProvider** - `268d696` (feat)

## Files Created/Modified

- `web/src/features/matches/components/odds-badge.tsx` - Added available/unavailableSince props, three-state rendering logic
- `web/src/features/matches/components/market-row.tsx` - Extended OutcomeDisplay interface, propagate availability to OddsBadge
- `web/src/features/matches/components/market-grid.tsx` - Added TooltipProvider wrapper for tooltip support

## Decisions Made

- Reuse formatUnavailableSince utility from market-utils.ts for consistent tooltip text format across both Odds Comparison and Event Details pages

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Event Details page now shows unavailable markets with same styling as Odds Comparison page
- Ready for Phase 92: History Charts with availability visualization

---
*Phase: 91-event-details-ui*
*Completed: 2026-02-11*
