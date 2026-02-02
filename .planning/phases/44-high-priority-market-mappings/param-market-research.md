# UNKNOWN_PARAM_MARKET Research

**Phase:** 44-03
**Research Date:** 2026-02-02
**Impact:** ~1,500 market occurrences

## Overview

These markets are **recognized** (they have a `S_{KEY}` prefix for bet9ja or valid market ID for sportybet), but the mapper doesn't know how to handle the parameter (O/U line) because they're not in the parameterized market sets.

## Target Markets

### 1. Bet9ja: 1X2OU (1X2 + Over/Under)
- **Frequency:** 348 occurrences
- **Error:** UNKNOWN_PARAM_MARKET
- **Key Format:** `S_1X2OU@{line}_{outcome}` (e.g., `S_1X2OU@2.5_1O`)
- **Parameter:** O/U line (e.g., 2.5, 1.5, 3.5)
- **Expected Outcomes:** 6 combos (1X2 × O/U)
  - `1O` = Home & Over
  - `1U` = Home & Under
  - `XO` = Draw & Over
  - `XU` = Draw & Under
  - `2O` = Away & Over
  - `2U` = Away & Under
- **Root Cause:** `1X2OU` not in `BET9JA_OVER_UNDER_KEYS`

### 2. Bet9ja: DCOU (Double Chance + Over/Under)
- **Frequency:** 342 occurrences
- **Error:** UNKNOWN_PARAM_MARKET
- **Key Format:** `S_DCOU@{line}_{outcome}` (e.g., `S_DCOU@2.5_1XO`)
- **Parameter:** O/U line (e.g., 2.5, 1.5, 3.5)
- **Expected Outcomes:** 6 combos (DC × O/U)
  - `1XO` = Home or Draw & Over
  - `1XU` = Home or Draw & Under
  - `X2O` = Draw or Away & Over
  - `X2U` = Draw or Away & Under
  - `12O` = Home or Away & Over
  - `12U` = Home or Away & Under
- **Root Cause:** `DCOU` not in `BET9JA_OVER_UNDER_KEYS`

### 3. SportyBet: 37 (1X2 & Over/Under)
- **Frequency:** 264 occurrences
- **Error:** UNKNOWN_PARAM_MARKET
- **Market ID:** 37
- **Specifier:** `total={line}` (e.g., `total=2.5`)
- **Expected Outcomes:** 6 combos
  - "Home & Over" (position 0)
  - "Home & Under" (position 1)
  - "Draw & Over" (position 2)
  - "Draw & Under" (position 3)
  - "Away & Over" (position 4)
  - "Away & Under" (position 5)
- **Root Cause:** ID `37` not in `OVER_UNDER_MARKET_IDS`

### 4. SportyBet: 547 (Double Chance & Over/Under)
- **Frequency:** 264 occurrences
- **Error:** UNKNOWN_PARAM_MARKET
- **Market ID:** 547
- **Specifier:** `total={line}` (e.g., `total=2.5`)
- **Expected Outcomes:** 6 combos
  - "Home or Draw & Over" (position 0)
  - "Home or Draw & Under" (position 1)
  - "Draw or Away & Over" (position 2)
  - "Draw or Away & Under" (position 3)
  - "Home or Away & Over" (position 4)
  - "Home or Away & Under" (position 5)
- **Root Cause:** ID `547` not in `OVER_UNDER_MARKET_IDS`

### 5. SportyBet: 818 (Halftime/Fulltime & Over/Under)
- **Frequency:** 216 occurrences
- **Error:** UNKNOWN_PARAM_MARKET
- **Market ID:** 818
- **Specifier:** `total={line}` (e.g., `total=2.5`)
- **Expected Outcomes:** 18 combos (HT/FT 9 outcomes × O/U 2 outcomes)
  - "Home/Home & Over", "Home/Home & Under"
  - "Home/Draw & Over", "Home/Draw & Under"
  - ... (9 HT/FT results × 2 O/U options)
- **Root Cause:** ID `818` not in `OVER_UNDER_MARKET_IDS`

### 6. SportyBet: 36 (Over/Under & GG/NG)
- **Frequency:** 66 occurrences
- **Error:** UNKNOWN_PARAM_MARKET
- **Market ID:** 36
- **Specifier:** `total={line}` (e.g., `total=2.5`)
- **Expected Outcomes:** 4 combos (O/U × GG/NG)
  - "Over & Yes" (position 0)
  - "Over & No" (position 1)
  - "Under & Yes" (position 2)
  - "Under & No" (position 3)
- **Root Cause:** ID `36` not in `OVER_UNDER_MARKET_IDS`

## Solution Approach

### For Bet9ja (1X2OU, DCOU)

**Option A: Add to BET9JA_OVER_UNDER_KEYS (Recommended)**
1. Add `1X2OU` and `DCOU` to `BET9JA_OVER_UNDER_KEYS` set
2. Create MarketMapping entries with compound outcomes
3. `_map_over_under_market()` handles line extraction automatically
4. Outcome mapping uses the compound suffixes (1O, 1U, etc.)

This works because:
- The line parsing from param (@2.5) is already handled
- We just need proper outcome mappings for the compound suffixes

### For SportyBet (37, 547, 818, 36)

**Option A: Add to OVER_UNDER_MARKET_IDS (Recommended)**
1. Add IDs to `OVER_UNDER_MARKET_IDS`
2. Create MarketMapping entries with compound outcomes
3. `_map_over_under_market()` handles line extraction from specifier
4. Outcome mapping uses sportybet_desc matching

This works because:
- The specifier parsing (total=2.5) is already handled
- We just need proper outcome mappings

## Required Changes

### 1. src/market_mapping/mappers/bet9ja.py
```python
# Add to BET9JA_OVER_UNDER_KEYS:
"1X2OU",   # 1X2 + Over/Under - Full Time
"DCOU",    # Double Chance + Over/Under - Full Time
```

### 2. src/market_mapping/mappings/market_ids.py
```python
# Add to OVER_UNDER_MARKET_IDS:
"37",   # 1X2 & Over/Under - Full Time
"547",  # Double Chance & Over/Under - Full Time
"818",  # Halftime/Fulltime & Over/Under - Full Time
"36",   # Over/Under & GG/NG - Full Time

# Add MarketMapping entries for all 6 combo markets
```

### 3. New MarketMappings Needed

For each market, we need a MarketMapping with:
- canonical_id: Unique identifier
- name: Human-readable name
- betpawa_id: May be None if Betpawa doesn't offer this combo
- sportybet_id: SportyBet market ID (where applicable)
- bet9ja_key: Bet9ja market key (where applicable)
- outcome_mapping: Full list of compound outcomes

## Betpawa Equivalence

**Note:** These combo markets may not have direct Betpawa equivalents. Betpawa might offer them as separate markets (e.g., 1X2 separately from O/U). In that case:
- Set `betpawa_id=None` in the mapping
- The market will map successfully for storage/display purposes
- Comparison would show as "competitor-only market"

## Verification Plan

1. Add markets to appropriate sets
2. Create MarketMapping entries
3. Run tests to verify no import errors
4. Test with sample data from audit
5. Verify UNKNOWN_PARAM_MARKET error is resolved

---
*Research completed: 2026-02-02*
