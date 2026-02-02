---
phase: 44-high-priority-market-mappings
plan: 02
subsystem: market-mapping
tags: [market-ids, sportybet, bet9ja, competitor-mapping]

# Dependency graph
requires:
  - phase: 43-market-mapping-audit
    provides: audit_raw_data.json with unmapped markets and priorities
provides:
  - 20 new MarketMapping entries for HIGH priority UNKNOWN_MARKET errors
  - Market research documentation
  - Improved competitor mapping coverage
affects: [44-03-unknown-param-markets, ui-comparison]

# Tech tracking
tech-stack:
  added: []
  patterns: [competitor-only-mappings-with-none-betpawa-id]

key-files:
  created:
    - .planning/phases/44-high-priority-market-mappings/new-market-research.md
  modified:
    - src/market_mapping/mappings/market_ids.py

key-decisions:
  - "Markets without BetPawa equivalent use betpawa_id=None for competitor-only tracking"
  - "Added S_LASTSCORE as separate mapping for Bet9ja alternate key (vs S_LASTGOAL)"
  - "Grouped new mappings under dedicated section header for clarity"

patterns-established:
  - "Competitor-only markets: betpawa_id=None, still valuable for comparison data"
  - "Alternate keys: Same market concept can have different keys on same platform"

issues-created: []

# Metrics
duration: 25min
completed: 2026-02-02
---

# Phase 44 Plan 02: UNKNOWN_MARKET Fixes Summary

**Added 20 MarketMapping entries for HIGH priority markets including Home/Away No Bet, First Goal, 1X2-5min, Team-to-Score, BTTS variants, and Result+O/U combos**

## Performance

- **Duration:** 25 min
- **Started:** 2026-02-02
- **Completed:** 2026-02-02
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Researched and documented 20+ target markets from audit_raw_data.json
- Added 20 new MarketMapping entries to market_ids.py (129 total mappings)
- Verified all new mappings are findable via lookup functions
- All 32 existing mapper tests pass - no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Research market structures** - `c57d1f1` (feat)
2. **Task 2: Add market mappings** - `21e56cb` (feat)
3. **Task 3: Verify new mappings** - No changes (verification only, tests passed)

## Files Created/Modified
- `.planning/phases/44-high-priority-market-mappings/new-market-research.md` - Research documentation for target markets
- `src/market_mapping/mappings/market_ids.py` - 20 new MarketMapping entries

## Markets Added

| # | canonical_id | Name | SportyBet ID | Bet9ja Key |
|---|-------------|------|--------------|------------|
| 1 | home_no_bet_ft | Home No Bet - Full Time | 12 | S_HOMENOBET |
| 2 | away_no_bet_ft | Away No Bet - Full Time | 13 | S_AWAYNOBET |
| 3 | first_goal_ft | First Goal - Full Time | 8 | S_1STGOAL |
| 4 | last_score_ft | Last Score (Bet9ja alternate) | - | S_LASTSCORE |
| 5 | 1x2_5min | 1X2 - First 5 Minutes | 900069 | S_1X21ST5MIN |
| 6 | home_win_1plus_ft | Home Win by 1+ Goals | 60200 | - |
| 7 | home_win_2plus_ft | Home Win by 2+ Goals | 60100 | - |
| 8 | home_or_clean_sheet_ft | Home or Any Clean Sheet | 863 | - |
| 9 | draw_or_clean_sheet_ft | Draw or Any Clean Sheet | 864 | - |
| 10 | away_or_clean_sheet_ft | Away or Any Clean Sheet | 865 | - |
| 11 | home_to_score_ft | Home Team To Score Yes/No | 900015 | - |
| 12 | away_to_score_ft | Away Team To Score Yes/No | 900014 | - |
| 13 | btts_2plus_ft | Both Teams Score 2+ Goals | 60000 | S_GGNG2PLUS |
| 14 | btts_both_halves | BTTS in Both Halves | 900027 | - |
| 15 | no_draw_btts_ft | No Draw Both Teams Score | 900041 | - |
| 16 | home_or_over_25_ft | Home or Over 2.5 | 854 | - |
| 17 | draw_or_over_25_ft | Draw or Over 2.5 | 856 | - |
| 18 | away_or_over_25_ft | Away or Over 2.5 | 858 | - |
| 19 | home_or_btts_ft | Home or GG | 860 | - |
| 20 | both_halves_over_15 | Both Halves Over 1.5 | 58 | - |

## Markets Deferred

Markets not added in this plan:
- **1X21 / 1X22** - Already covered by existing 1x2_1h / 1x2_2h mappings
- **GOALSHOME / GOALSAWAY** - Already covered by home_exact_goals_ft / away_exact_goals_ft
- **Player props** - Out of scope (complex, separate phase)
- **UNKNOWN_PARAM_MARKET items** - Deferred to plan 44-03

## Decisions Made
- Markets without BetPawa equivalent use `betpawa_id=None` (still useful for competitor data)
- Added `last_score_ft` as separate mapping for Bet9ja's S_LASTSCORE alternate key
- Grouped all new mappings under a dedicated section header for clarity

## Deviations from Plan
None - plan executed exactly as written

## Issues Encountered
None

## Test Results

```
25 lookup tests passed (all new mappings findable)
32 existing mapper tests passed (no regressions)
129 total mappings loaded successfully
```

## Estimated Impact

~1,800+ market occurrences now mappable across:
- SportyBet: 14 new market IDs recognized
- Bet9ja: 7 new market keys recognized

## Next Phase Readiness
- Ready for 44-03-PLAN.md (UNKNOWN_PARAM_MARKET fixes)
- All HIGH priority UNKNOWN_MARKET items addressed
- Mapping coverage significantly improved

---
*Phase: 44-high-priority-market-mappings*
*Completed: 2026-02-02*
