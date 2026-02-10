---
phase: 80-specifier-bug-fix
plan: 02
subsystem: ui
tags: [react, typescript, history-dialog, market-grid, match-table]

# Dependency graph
requires:
  - phase: 80-01
    provides: line parameter in API layer and frontend hooks
provides:
  - Line parameter flows from UI clicks through to history API calls
  - Over/Under and Handicap markets now fetch line-specific history
affects: [81-interactive-chart, history-dialog]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Line parameter threading through component hierarchy"
    - "Inline markets pass null for line (fixed configurations)"

key-files:
  created: []
  modified:
    - web/src/features/matches/components/history-dialog.tsx
    - web/src/features/matches/components/market-row.tsx
    - web/src/features/matches/components/market-grid.tsx
    - web/src/features/matches/components/match-table.tsx

key-decisions:
  - "Inline markets (1X2, O/U 2.5, BTTS, DC) pass line: null for backward compatibility"
  - "Dialog title includes line value when present (e.g., 'Over/Under 2.5')"

patterns-established:
  - "Line parameter as optional prop in history-related components"

issues-created: []

# Metrics
duration: 5min
completed: 2026-02-10
---

# Phase 80 Plan 02: Frontend Components Summary

**Line parameter flows from UI clicks through MarketRow/MarketGrid/MatchTable to HistoryDialog and history hooks**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-10T12:00:00Z
- **Completed:** 2026-02-10T12:05:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- HistoryDialog accepts line prop and passes it to all four history hooks
- Dialog title shows line value when present (e.g., "Over/Under 2.5 - BetPawa")
- MarketRow callbacks include line parameter, passed through click handlers
- MarketGrid stores line in dialog state and passes to HistoryDialog
- MatchTable passes null for inline markets (fixed configurations like 1X2, O/U 2.5)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add line prop to HistoryDialog** - `cb2d3be` (feat)
2. **Task 2: Update market-row and market-grid** - `5c84c13` (feat)
3. **Task 3: Update match-table** - `06a43bb` (feat)

## Files Created/Modified

- `web/src/features/matches/components/history-dialog.tsx` - Added line prop, pass to hooks, include in title
- `web/src/features/matches/components/market-row.tsx` - Updated callback signatures with line parameter
- `web/src/features/matches/components/market-grid.tsx` - Added line to state, handleHistoryClick, and HistoryDialog
- `web/src/features/matches/components/match-table.tsx` - Added line to state, passes null for inline markets

## Decisions Made

- Inline markets (1X2, O/U 2.5, BTTS, DC) pass `line: null` since they use fixed configurations - API returns all data when line is null which is correct for these markets
- Dialog title includes line value when present for clarity (e.g., "Over/Under 2.5" instead of just "Over/Under")

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Phase 80 complete: Specifier bug fixed
- Over/Under and Handicap charts now show only the specific line data (e.g., 2.5 line only)
- Ready for Phase 81: Interactive Chart (hover tooltip and click-to-lock crosshair)

---
*Phase: 80-specifier-bug-fix*
*Completed: 2026-02-10*
