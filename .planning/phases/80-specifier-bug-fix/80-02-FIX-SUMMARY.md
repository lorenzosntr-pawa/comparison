---
phase: 80-specifier-bug-fix
plan: 02-FIX
subsystem: ui
tags: [react, history-dialog, match-table, line-filter]

# Dependency graph
requires:
  - phase: 80-02
    provides: Line parameter support in history dialog
provides:
  - O/U 2.5 inline market correctly passes line=2.5 for history filtering
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Market-specific line value mapping for inline markets"

key-files:
  created: []
  modified:
    - web/src/features/matches/components/match-table.tsx

key-decisions:
  - "O/U 2.5 (market ID 5000) passes line: 2.5; other inline markets (1X2, BTTS, DC) pass null"

patterns-established: []

issues-created: []

# Metrics
duration: 3min
completed: 2026-02-10
---

# Phase 80 Plan 02-FIX: UAT Issue Fix Summary

**O/U 2.5 inline market on Odds Comparison page now passes line=2.5 for history filtering, showing only 2.5 line data**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-10T12:30:00Z
- **Completed:** 2026-02-10T12:33:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Fixed UAT-001: O/U 2.5 history on Odds Comparison page now shows only 2.5 line data
- Changed `line: null` to `line: marketId === '5000' ? 2.5 : null` in both OddsValue and MarginValue click handlers
- Maintained backward compatibility: 1X2, BTTS, DC still pass null (no specifier)

## Task Commits

1. **Task 1: Fix UAT-001** - `def055d` (fix)

## Files Created/Modified

- `web/src/features/matches/components/match-table.tsx` - Pass line=2.5 for O/U market ID 5000

## Decisions Made

- Only O/U 2.5 (market ID 5000) gets line=2.5; the other inline markets (1X2, BTTS, DC) continue to pass null since they have no specifier values

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- UAT-001 resolved
- Phase 80 specifier bug fix complete
- Ready for re-verification via /gsd:verify-work 80 02

---
*Phase: 80-specifier-bug-fix*
*Completed: 2026-02-10*
