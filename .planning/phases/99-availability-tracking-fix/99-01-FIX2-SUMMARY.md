---
phase: 99-availability-tracking-fix
plan: 01-FIX2
subsystem: frontend
tags: [availability, ui, odds-comparison, match-table]

# Dependency graph
requires:
  - phase: 99-availability-tracking-fix
    provides: availability tracking infrastructure, OddsBadge component with availability support
provides:
  - Consistent unavailable styling on Odds Comparison page
  - Margin hiding when market unavailable
affects: [odds-comparison-page]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Case-based availability rendering: null+unavailable, null+available, value+unavailable, value+available"

key-files:
  created: []
  modified:
    - web/src/features/matches/components/match-table.tsx

key-decisions:
  - "Match OddsBadge 4-case availability logic in OddsValue component"
  - "Show stale odds with strikethrough rather than hiding them (more informative)"

patterns-established:
  - "Four-case availability pattern for odds/margin display: null+unavailable, null+available, value+unavailable, value+available"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-12
---

# Phase 99 Plan 01-FIX2: UAT Issues Fix Summary

**Fix Odds Comparison page unavailable styling: show stale odds with strikethrough, hide margin when unavailable**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-12
- **Completed:** 2026-02-12
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Fixed UAT-004: MarginValue now checks availability and shows strikethrough dash when market unavailable
- Fixed UAT-003: OddsValue now shows stale odds with strikethrough (matching OddsBadge behavior from Event Details)
- Consistent four-case availability logic across both OddsValue and MarginValue components

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix UAT-004 - Hide margin when market unavailable** - `fa7fe2a` (fix)
2. **Task 2: Fix UAT-003 - Consistent unavailable styling** - `5ad7ca0` (fix)

## Files Created/Modified

- `web/src/features/matches/components/match-table.tsx` - Added availability props to MarginValue, fixed OddsValue to match OddsBadge 4-case logic

## Decisions Made

- **Match OddsBadge pattern:** Used same four-case availability logic (null+unavailable, null+available, value+unavailable, value+available) to ensure consistent behavior across pages
- **Show stale odds:** When market becomes unavailable but had previous odds, show those odds with strikethrough rather than just a dash (more informative for users)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation followed plan without issues.

## Next Phase Readiness

UAT-003 and UAT-004 both resolved. Odds Comparison page now matches Event Details page styling for unavailable markets:
- Unavailable odds show with strikethrough (stale value visible)
- Unavailable margins show strikethrough dash with tooltip
- Both have "Unavailable since X" tooltip

Ready for re-verification with `/gsd:verify-work 99-01-FIX2`.

---
*Phase: 99-availability-tracking-fix*
*Completed: 2026-02-12*
