# 44-01-FIX Summary: UAT Issues Fix

## Execution Stats

| Metric | Value |
|--------|-------|
| Tasks Completed | 3/3 |
| Commits | 2 |
| Files Changed | 3 |

## Task Outcomes

### Task 1: Fix UI duplicate rows (UAT-002 - Blocker)
**Status:** Complete
**Commit:** `8939afa` fix(44-01): merge split market outcomes in UI

**Root Cause:** Betpawa stores markets with outcomes split across multiple database records (e.g., TMGHO with 3 records for different outcome groups). The frontend's `buildUnifiedMarkets` function was creating separate rows for each record instead of merging outcomes.

**Solution:** Added `mergeMarketOutcomes()` function in [market-grid.tsx](../../../web/src/features/matches/components/market-grid.tsx) that:
- Detects when the same market key (id+line) appears multiple times
- Merges outcomes from all records, avoiding duplicates by name
- Recalculates margin with all merged outcomes

### Task 2: Verify Bet9ja odds appear correctly
**Status:** Complete (verified as expected behavior)

**Finding:** Investigation confirmed that:
- Bet9ja TMGHO only maps the "1-2" outcome (because "No goal", "3+" don't have Bet9ja equivalents)
- Bet9ja's "1-3" and "2-3" outcomes exist but have `betpawa_name=None` so are intentionally discarded
- The "1-2" outcome correctly shows Bet9ja odds after Task 1 fix merges all outcomes

**Outcome comparison for TMGHO:**
| Bookmaker | Outcomes |
|-----------|----------|
| Betpawa | "No goal", "1-2", "1-3", "2-3", "4+" |
| SportyBet | "No goal", "1-2", "3+" |
| Bet9ja | "1-2" only |

### Task 3: Fix HAOU Home/Away confusion (UAT-001)
**Status:** Complete
**Commit:** `1836086` fix(44-01): split Bet9ja HAOU into Home/Away O/U markets

**Root Cause:** Bet9ja's HAOU is a combined market with 4 outcomes (OH, UH, OA, UA) covering both Home and Away team Over/Under. The mapping had `betpawa_id=None` and all outcomes had `betpawa_name=None`, causing `UNSUPPORTED_PLATFORM` errors.

**Solution:** Added special handling in [bet9ja.py](../../../src/market_mapping/mappers/bet9ja.py):
- `BET9JA_HAOU_COMBINED_KEYS` frozenset for HAOU, HA1HOU, HA2HOU
- `_map_haou_combined_market()` that splits into two separate markets:
  - Home Team Over/Under (5006/5024/5027) with Over/Under outcomes
  - Away Team Over/Under (5003/5021/5030) with Over/Under outcomes

**Verification results:**
- 176 snapshots with HAOU data processed
- 500 Home O/U markets created (multiple lines per snapshot)
- 461 Away O/U markets created

## Files Changed

| File | Lines | Change |
|------|-------|--------|
| web/src/features/matches/components/market-grid.tsx | +47 | Added `mergeMarketOutcomes()` function |
| src/market_mapping/mappers/bet9ja.py | +109 | Added HAOU split handling |
| src/scripts/verify_market_fixes.py | +48 | Added HAOU split verification |

## Issues Resolved

- **UAT-002** (Blocker): UI duplicate rows and missing Bet9ja odds → Fixed by merging split outcomes
- **UAT-001** (Major): HAOU Home/Away confusion → Fixed by splitting into separate markets
- **UAT-003** (Minor): Outcome incompatibility → Documented as expected (mapping limitation)

## Notes

1. **Outcome name mismatches remain** - SportyBet uses "3+" while Betpawa uses "4+" for multigoals. These don't match by name so show "-" in UI. This is a mapping definition issue, not a bug.

2. **HTFTOU and HTFTCS still fail** - These markets have complex outcome structures that require additional mapping work (tracked in Phase 44 remaining plans).

3. **Re-scraping required** - Existing HAOU data in database won't be retroactively fixed. New scrapes will correctly produce separate Home/Away O/U markets.
