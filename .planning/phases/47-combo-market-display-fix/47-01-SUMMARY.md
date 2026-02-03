---
phase: 47-combo-market-display-fix
plan: 01
subsystem: frontend
tags: [combo-markets, outcome-matching, normalization, bug-fix]

# Dependency graph
requires:
  - phase: 46
    provides: handicap market line fix
provides:
  - Combo markets (1X2OU, DCOU, etc.) now display outcomes correctly
  - Cross-bookmaker outcome name normalization (" - " vs " & ")
  - Margin only displays when outcomes exist
affects: [market-comparison, odds-display]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Outcome presence check: outcomes.length > 0 before using market as reference"
    - "Outcome name normalization: normalizeOutcomeName() for cross-bookmaker matching"

key-files:
  created: []
  modified:
    - web/src/features/matches/components/market-row.tsx

key-decisions:
  - "Normalize at match time rather than storage - keeps data intact, fixes display"
  - "Replace ' - ' with ' & ' for consistency (Betpawa uses dash, others use ampersand)"

patterns-established:
  - "Outcome name normalization for cross-bookmaker combo market matching"
  - "Gate margin display on outcomeNames.length > 0"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-03
---

# Phase 47 Plan 01: Combo Market Display Fix Summary

**Combo markets (1X2OU, DCOU, etc.) now display outcomes correctly by checking outcomes.length and normalizing outcome names for cross-bookmaker matching**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-03T12:00:00Z
- **Completed:** 2026-02-03T12:08:00Z
- **Tasks:** 2 (1 auto + 1 checkpoint)
- **Files modified:** 1

## Accomplishments

- Fixed BUG-004: combo markets now show odds, not just margins
- Added `normalizeOutcomeName()` to handle Betpawa " - " vs SportyBet/Bet9ja " & " separators
- `getUnifiedOutcomes()` now checks `outcomes.length > 0` before using market as reference
- Margin indicator only displays when `outcomeNames.length > 0`

## Task Commits

1. **Task 1: Fix outcome presence check and add name normalization** - (pending commit)

## Files Created/Modified

- `web/src/features/matches/components/market-row.tsx` - Added normalizeOutcomeName(), outcomes.length checks, margin gating

## Decisions Made

- **Normalize at match time:** Applied fix in frontend matching logic rather than storage because:
  - Keeps raw data intact for debugging
  - Single point of fix in UI layer
  - Both separator formats are valid, just different conventions

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - fix applied cleanly, visual verification confirmed combo markets display correctly.

## Next Step

Phase 47 complete. v1.8 Market Matching Accuracy milestone ready to ship.

---
*Phase: 47-combo-market-display-fix*
*Completed: 2026-02-03*
