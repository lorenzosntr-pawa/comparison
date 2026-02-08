---
phase: 66-odds-comparison-history
plan: 01
subsystem: ui
tags: [dialog, click-handlers, match-table, react]

# Dependency graph
requires:
  - phase: 65-history-dialog-component
    provides: HistoryDialog component with tabbed Odds/Margin views
provides:
  - Clickable odds and margin cells in Odds Comparison page that open HistoryDialog
affects: [67-event-details-history]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Click handlers with e.stopPropagation to prevent row navigation while enabling cell clicks

key-files:
  created: []
  modified:
    - web/src/features/matches/components/match-table.tsx

key-decisions:
  - "BOOKMAKER_NAMES constant for dialog titles (BetPawa, SportyBet, Bet9ja)"
  - "onClick prop on OddsValue/MarginValue with optional React.MouseEvent parameter"
  - "Cursor pointer + hover ring visual feedback on clickable cells"

patterns-established:
  - "e.stopPropagation on cell click to prevent row click navigation"

issues-created: []

# Metrics
duration: 4min
completed: 2026-02-08
---

# Phase 66 Plan 01: Odds Comparison History Summary

**Clickable odds and margin cells in MatchTable that open HistoryDialog with market and bookmaker context**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-08T12:45:00Z
- **Completed:** 2026-02-08T12:49:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Added HistoryDialog state management to MatchTable component
- Added onClick prop to OddsValue and MarginValue components with cursor-pointer styling
- Wired click handlers with e.stopPropagation to prevent row navigation
- Added BOOKMAKER_NAMES constant for full bookmaker display names in dialog titles
- Rendered HistoryDialog with market/bookmaker context from clicked cell

## Task Commits

Each task was committed atomically:

1. **Task 1+2: Add history dialog click handlers to odds comparison table** - `85c0606` (feat)

**Plan metadata:** pending

## Files Created/Modified

- `web/src/features/matches/components/match-table.tsx` - Added HistoryDialog import, BOOKMAKER_NAMES constant, HistoryDialogState type, useState hook, onClick props on OddsValue/MarginValue, and HistoryDialog render

## Decisions Made

- Combined Task 1 and Task 2 into single commit since both tasks modified the same file for the same feature
- Used BOOKMAKER_NAMES separate from BOOKMAKER_LABELS (short form for table display)
- Added hover:ring-1 hover:ring-primary/50 visual feedback on clickable cells
- Used conditional onClick (only when odds/margin not null and bookmaker exists)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Odds Comparison page history clicks fully functional
- Ready for Phase 67: Event Details History (add click handlers in Event Details page)
- Same pattern (onClick with stopPropagation, HistoryDialog state) can be applied

---
*Phase: 66-odds-comparison-history*
*Completed: 2026-02-08*
