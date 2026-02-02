---
phase: 44-high-priority-market-mappings
plan: 01
subsystem: market-mapping
tags: [bet9ja, sportybet, outcome-mapping, NO_MATCHING_OUTCOMES]

# Dependency graph
requires:
  - phase: 43-market-mapping-audit
    provides: Audit findings identifying 6 HIGH priority NO_MATCHING_OUTCOMES markets
provides:
  - TMGHO/TMGAW bet9ja outcome suffix mappings (HO12/HO13/HO23, AW12/AW13/AW23)
  - HAOU combined market mapping with all 4 outcomes
  - Complete outcome definitions for HTFTOU, HTFTCS, Multiscores (551), HT/FT CS (46)
affects: [44-02, market-mapping-audit]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Combined market pattern for bet9ja HAOU (4 outcomes in single market)"
    - "Outcome analysis workflow for mapping debugging"

key-files:
  created:
    - .planning/phases/44-high-priority-market-mappings/outcome-analysis.md
    - src/scripts/analyze_outcomes.py
    - src/scripts/verify_market_fixes.py
  modified:
    - src/market_mapping/mappings/market_ids.py

key-decisions:
  - "HAOU: Create combined mapping for bet9ja (was incorrectly split into two mappings with same key)"
  - "Multigoals suffixes: Bet9ja uses different ranges than Betpawa (1-2/1-3/2-3 vs 0/1-2/3+)"
  - "Markets without Betpawa equivalents: Complete outcome definitions anyway for future use"

patterns-established:
  - "Outcome analysis script pattern for debugging market mapping issues"

issues-created: []

# Metrics
duration: 25min
completed: 2026-02-02
---

# Phase 44 Plan 01: NO_MATCHING_OUTCOMES Fixes Summary

**Corrected bet9ja outcome suffixes for TMGHO/TMGAW (100% success), created combined HAOU mapping, added complete outcome definitions for combo markets**

## Performance

- **Duration:** 25 min
- **Started:** 2026-02-02T16:00:00Z
- **Completed:** 2026-02-02T16:25:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- TMGHO bet9ja mapping now 100% successful (was 99 NO_MATCHING_OUTCOMES)
- TMGAW bet9ja mapping now 100% successful (was 99 NO_MATCHING_OUTCOMES)
- HAOU now correctly returns UNSUPPORTED_PLATFORM (was 50 NO_MATCHING_OUTCOMES with wrong mapping)
- Added complete outcome definitions for HTFTOU (18 combos), HTFTCS (46 scores), Multiscores (11 outcomes)

## Task Commits

Each task was committed atomically:

1. **Task 1: Analyze raw outcome structures** - `1e2b15f` (feat)
2. **Task 2: Fix outcome mappings** - `946eba7` (fix)
3. **Task 3: Verify fixes** - `234ef30` (test)

## Files Created/Modified

- `src/market_mapping/mappings/market_ids.py` - Updated 6 market mappings with corrected outcomes
- `.planning/phases/44-high-priority-market-mappings/outcome-analysis.md` - Documented actual vs expected structures
- `src/scripts/analyze_outcomes.py` - Script to extract outcome data from API responses
- `src/scripts/verify_market_fixes.py` - Verification script for spot-checking fixes

## Decisions Made

1. **HAOU combined mapping:** Created single mapping with all 4 outcomes (OH, UH, OA, UA) because bet9ja sends them together, unlike Sportybet which separates home/away
2. **Multigoal suffixes:** Bet9ja uses HO12/HO13/HO23 and AW12/AW13/AW23 for goal ranges, not the 0/1-2/3+ structure we assumed
3. **Markets without Betpawa equivalents:** Still added complete outcome definitions for HTFTOU, HTFTCS, 551, 46 for future use if Betpawa adds them

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**Expected behavior discovery:** Markets like HTFTOU, HTFTCS, and Multiscores have correct outcome definitions now, but still show NO_MATCHING_OUTCOMES because there are no Betpawa equivalent outcomes (betpawa_name=None). This is correct behavior - you can only compare markets that exist on both platforms.

## Metrics

| Market | Before | After | Improvement |
|--------|--------|-------|-------------|
| TMGHO | 0% (99 errors) | 100% success | +99 occurrences |
| TMGAW | 0% (99 errors) | 100% success | +99 occurrences |
| HAOU | NO_MATCHING_OUTCOMES | UNSUPPORTED_PLATFORM | Better classification |
| HTFTOU | NO_MATCHING_OUTCOMES | NO_MATCHING_OUTCOMES | Complete definitions added |
| HTFTCS | NO_MATCHING_OUTCOMES | NO_MATCHING_OUTCOMES | Complete definitions added |
| 551 (Multiscores) | NO_MATCHING_OUTCOMES | NO_MATCHING_OUTCOMES | Complete definitions added |
| 46 (HT/FT CS) | NO_MATCHING_OUTCOMES | NO_MATCHING_OUTCOMES | Complete definitions added |

**Total NO_MATCHING_OUTCOMES resolved:** 198 occurrences (TMGHO 99 + TMGAW 99)
**Additional classification improved:** HAOU (50 occurrences now correctly classified)

## Next Phase Readiness

- Ready for 44-02-PLAN.md (UNKNOWN_MARKET fixes)
- TMGHO and TMGAW fixes verified working
- Outcome analysis methodology established for future mapping work

---
*Phase: 44-high-priority-market-mappings*
*Completed: 2026-02-02*
