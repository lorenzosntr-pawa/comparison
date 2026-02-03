---
phase: 46-remaining-market-gaps
plan: 01
subsystem: market-mapping
tags: [handicap, asian-handicap, 3-way-handicap, line-field, event-coordinator]

# Dependency graph
requires:
  - phase: 45
    provides: audit identifying handicap line mismatch as root cause
provides:
  - Competitor handicap markets now populate `line` field from `handicap_home`
  - Frontend matching works for 3-Way and Asian Handicap markets
affects: [market-comparison, odds-display]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Line field fallback: use handicap.home when line is None for handicap markets"

key-files:
  created: []
  modified:
    - src/scraping/event_coordinator.py

key-decisions:
  - "Fix at storage time (event_coordinator) rather than mapping or frontend"
  - "Use handicap.home as fallback only when line is explicitly None"

patterns-established:
  - "Handicap market line population: line = mapped.line ?? mapped.handicap.home"

issues-created: []

# Metrics
duration: 12min
completed: 2026-02-03
---

# Phase 46 Plan 01: Handicap Market Line Fix Summary

**Competitor handicap markets (3-Way and Asian) now display odds correctly by populating `line` field from `handicap_home` at storage time**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-03T11:00:00Z
- **Completed:** 2026-02-03T11:12:00Z
- **Tasks:** 2 (1 auto + 1 checkpoint)
- **Files modified:** 1

## Accomplishments

- Fixed line field population for competitor handicap markets in both SportyBet and Bet9ja parsers
- Frontend now correctly matches handicap markets using `${market_id}_${line}` key
- 3-Way Handicap (4724, 4716, 4720) and Asian Handicap (3774, 3747, 3756) markets all display competitor odds

## Task Commits

1. **Task 1: Populate competitor handicap market line field** - `6f6605b` (fix)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified

- `src/scraping/event_coordinator.py` - Added line fallback logic in `_parse_sportybet_markets` (line 1875) and `_parse_bet9ja_markets` (line 1925)

## Decisions Made

- **Fix at storage time:** Applied fix in event_coordinator.py rather than mapping layer or frontend because:
  - Mapping layer correctly distinguishes `line` (O/U) from `handicap` (handicap markets)
  - Frontend matching logic is correct — it just needed consistent data
  - Single point of fix, minimal code change (2 lines)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Initial verification showed `line=None` in database — backend needed restart to pick up code change
- After restart and fresh scrape, handicap markets displayed correctly

## Next Step

Phase 46 Plan 01 complete. Evaluate remaining market mapping gaps (OUA, CHANCEMIX, other non-handicap issues) for potential Phase 47.

---
*Phase: 46-remaining-market-gaps*
*Completed: 2026-02-03*
