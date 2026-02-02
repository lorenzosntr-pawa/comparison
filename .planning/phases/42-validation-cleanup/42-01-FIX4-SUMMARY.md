---
phase: 42-validation-cleanup
plan: FIX4
subsystem: scraping
tags: [sportradar, tournament, country, event-coordinator]

# Dependency graph
requires:
  - phase: 42-FIX3
    provides: BetPawa SR ID extraction using widget.id
provides:
  - Confirmed widget.id IS correct SportRadar ID (8-digit numeric)
  - Competitor tournament extraction from raw API responses
  - Country/region data for competitor tournaments
affects: [coverage, odds-comparison, tournament-filtering]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Competitor tournament from raw data extraction

key-files:
  created: []
  modified:
    - src/scraping/event_coordinator.py

key-decisions:
  - "widget.id IS the correct SR ID - no fallback to widget.data.matchId needed"
  - "Extract tournament info from competitor raw responses instead of using fallback"

patterns-established:
  - "_get_or_create_competitor_tournament_from_raw() for dynamic tournament creation with country"

issues-created: []

# Metrics
duration: ~45min
completed: 2026-02-02
---

# Phase 42 Plan FIX4: BetPawa Matching & Competitor Tournaments Summary

**Confirmed BetPawa widget.id IS correct SR ID; added competitor tournament extraction from raw data with country field**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-02-02T09:30:00Z
- **Completed:** 2026-02-02T10:18:03Z
- **Tasks:** 6
- **Files modified:** 3 (event_coordinator.py, ISSUES.md, STATE.md)

## Accomplishments

- Debugged BetPawa widget structure - confirmed widget.id is 8-digit numeric SR ID (same format as competitors)
- Cleaned up SR ID extraction code - removed unnecessary fallback to widget.data.matchId (which doesn't exist)
- Added `_get_or_create_competitor_tournament_from_raw()` method for dynamic tournament creation
- SportyBet now extracts tournamentName and categoryName (country)
- Bet9ja now extracts GN (group name) and SGN (sport group name/country)
- Updated ISSUES.md - moved BUG-001 and BUG-002 to Closed section
- Updated STATE.md with FIX4 completion and new pattern

## Task Commits

1. **Tasks 1-3: SR ID cleanup and competitor tournament fix** - `a636ab1` (fix)

**Plan metadata:** pending

## Files Created/Modified

- `src/scraping/event_coordinator.py` - Cleaned up SR ID extraction, added competitor tournament method
- `.planning/ISSUES.md` - Moved BUG-001 and BUG-002 to Closed section
- `.planning/STATE.md` - Updated position, patterns, and session continuity

## Decisions Made

1. **widget.id IS correct** - Investigation confirmed BetPawa's widget.id field contains the actual SportRadar ID (8-digit numeric like "61272779"), which matches the format competitors use. The hypothesis that it was a UUID was incorrect.

2. **widget.data.matchId doesn't exist** - The BetPawa API response doesn't include a `data.matchId` field in the SPORTRADAR widget. The entire widget structure is just `{id, type, retention}`.

3. **Extract tournaments from raw data** - Instead of using fallback "Discovered Events" tournaments, extract proper tournament info from competitor raw responses to get country data.

## Deviations from Plan

### Task 2 Deviation

**Plan expected:** Reverse SR ID extraction priority to use widget.data.matchId first
**Actual finding:** widget.data.matchId doesn't exist in API response
**Action taken:** Kept widget.id extraction (which is correct), just cleaned up code

This was a deviation from the plan's hypothesis, but the actual fix was simpler - just confirming the code was correct and removing unnecessary fallback logic.

---

**Total deviations:** 1 (Task 2 approach changed based on findings)
**Impact on plan:** No negative impact - actual fix was simpler than planned

## Issues Encountered

None - all tasks completed successfully.

## Next Steps

**User action required:** Run a fresh scrape to validate fixes:

1. Clear stale data with fallback tournaments:
```sql
DELETE FROM odds_snapshots;
DELETE FROM competitor_odds_snapshots;
DELETE FROM event_scrape_status;
DELETE FROM events WHERE tournament_id IN (SELECT id FROM tournaments WHERE name = 'Discovered Events');
DELETE FROM competitor_events WHERE tournament_id IN (SELECT id FROM competitor_tournaments WHERE name = 'Discovered Events');
DELETE FROM tournaments WHERE name = 'Discovered Events';
DELETE FROM competitor_tournaments WHERE name = 'Discovered Events';
```

2. Trigger fresh scrape via UI or POST /api/scrape/start

3. Verify on coverage page:
   - BetPawa events > 0
   - Tournament regions populated for competitors
   - Cross-platform matching working

---
*Phase: 42-validation-cleanup*
*Completed: 2026-02-02*
